# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import socket
import threading
import time
import typing
from collections import defaultdict, deque
from typing import List, Any

#import carb

AddressType = typing.Tuple[str, int]

MAX_BUFFER = 10000
MAX_CONNECTIONS = 100
CLIENT_TIMEOUT = 600
SERVER_TIMEOUT = 600
SERVICE_TIMEOUT = 600

_LAST_ACCESSED = {}


def update_last_accessed(method):
    global _LAST_ACCESSED

    def wrapped(self, *args, **kwargs):
        _LAST_ACCESSED[self] = time.time()
        return method(self, *args, **kwargs)
    return wrapped


class ThreadedServer:
    """Runs a TCP/IP server as multi-threaded.
    """

    def __init__(self):
        self._sock = None
        self._clients = {}
        self._client_threads = {}
        self._server_thread = None
        self._received = defaultdict(deque)
        self._closing_threads = deque(maxlen=MAX_CONNECTIONS * 3)

        self.timeout_client = CLIENT_TIMEOUT
        self.timeout_service = SERVICE_TIMEOUT

    def __del__(self):
        self.close_all()
        self._clients.clear()
        self._received.clear()
        if self._sock is not None:
            self._sock.close()
        self._sock = None

    @property
    def address(self) -> AddressType:
        if not self._sock:
            return (None, None)
        try:
            addr = self._sock.getsockname()
        except socket.error:
            return (None, None)
        return addr

    @property
    def url(self) -> str:
        host, port = self.address
        if host is None:
            return ''
        return f'{host}:{port}'

    @property
    @update_last_accessed
    def connected(self) -> bool:
        return len(self._clients) > 0

    @property
    @update_last_accessed
    def client_addresses(self) -> List[AddressType]:
        """Returns all connected addresses.
        """
        return list(self._clients.keys())

    @property
    @update_last_accessed
    def received_addresses(self) -> List[AddressType]:
        """Returns all addresses having data in the receive buffer.
        """
        return list(self._received.keys())

    @property
    @update_last_accessed
    def clients(self) -> List[socket.socket]:
        """Returns all client sockeets.
        """
        return list(self._clients.values())

    @update_last_accessed
    def is_running(self) -> bool:
        """Returns True if the server thread is alive.
        """
        if self._server_thread is None:
            return False
        return self._server_thread.is_alive()

    @update_last_accessed
    def has_client(self, addr: AddressType) -> bool:
        """Returns True if there's any client socket.
        """
        return (addr in self._clients)

    @update_last_accessed
    def get_client(self, addr: AddressType) -> socket.socket:
        """Get a client socket for the address.
        """
        return self._clients.get(addr)

    @update_last_accessed
    def close_all(self):
        """Close all client sockets.
        """
        for addr in self.client_addresses:
            self.close(addr)

        if self._sock is not None:
            self._close_socket(self._sock)
        if self._server_thread:
            self._server_thread.join()
        return

    @update_last_accessed
    def close(self, addr: AddressType):
        """Close a client socket.
        """
        conn = self.get_client(addr)
        if conn:
            # generally, this will stop the client thread
            self._close_socket(conn)

        thread = self._client_threads.get(addr)
        self._close_after(addr, parent_thread=thread)

    def _close_after(self, addr: AddressType, parent_thread: threading.Thread = None):
        conn = self.get_client(addr)
        if conn:
            try:
                _ = conn.getsockname()
            except socket.error:
                pass
            else:
                # the socket is still connected.
                self._close_socket(conn)

        if parent_thread and parent_thread.is_alive():
            parent_thread.join(timeout=self.timeout_client * 2)

        if addr in self._clients:
            self._clients.pop(addr)

        return

    def _close_socket(self, conn: socket.socket):
        try:
            _ = conn.getsockname()
            # the socket is still connected.
            conn.settimeout(0.0001)
        except socket.error:
            pass
        else:
            conn.close()

    @update_last_accessed
    def has_received(self) -> bool:
        for addr in self.received_addresses:
            if self.len_received(addr):
                return True
        return False

    @update_last_accessed
    def len_received(self, addr: AddressType) -> int:
        return len(self._received[addr])

    @update_last_accessed
    def pop_received(self, addr: AddressType) -> Any:
        # get received data. FIFO
        try:
            return self._received[addr].popleft()
        except IndexError:
            return None

    @update_last_accessed
    def next_received(self, addr: AddressType) -> Any:
        # get received data. FIFO
        try:
            return self._received[addr][0]
        except IndexError:
            return None

    @update_last_accessed
    def listen(self, host='localhost', port=0, timeout=SERVER_TIMEOUT) -> AddressType:
        """Assign an address to the socket.
        """
        if self._sock:
            self._sock.close()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.bind((host, port))
        self._sock.listen(MAX_CONNECTIONS)  # maximum clients
        self._sock.settimeout(timeout)
        return self._sock.getsockname()

    @update_last_accessed
    def start(self):
        """Start accepting external connections.
        """
        self._server_thread = threading.Thread(target=self._handle_server, args=(self._sock,))
        self._server_thread.start()

    def _handle_server(self, server_socket):
        while True:
            if not isinstance(server_socket, socket.socket):
                break

            # kill server when no activity for certain time.
            # Added to handle the case that user does not terminate the server properly.
            now = time.time()
            elapsed = (now - _LAST_ACCESSED.get(self, 0)) / 1000000
            if elapsed > self.timeout_service:
                #carb.log_warn(f'Terminate server due to no activity for {elapsed} seconds.')
                break

            # Accept incoming connections from clients
            try:
                conn, addr = server_socket.accept()
            except socket.error:
                # socket closed
                break

            conn.settimeout(self.timeout_client)
            # Create a new thread to handle the connection with the client
            client_thread = threading.Thread(target=self._handle_client, args=(conn, addr))

            self._client_threads[addr] = client_thread
            self._clients[addr] = conn
            client_thread.start()
        try:
            server_socket.getsockname()  # raises OSError if socket is alrady closed.
        except socket.error:
            # ignore errors by already-closed sockets
            pass
        else:
            server_socket.close()
        return

    def _handle_client(self, client_socket: socket.socket, client_address: AddressType):
        # Handle the connection with the client
        while True:
            # Wait when receive buffer is full
            if len(self._received[client_address]) > MAX_BUFFER:
                time.sleep(1)
                continue
            # Receive data from the client
            try:
                data = self.receive(client_socket)
            except ConnectionResetError:
                # connection closed by client
                break
            except ConnectionAbortedError:
                # connection closed by server
                break
            except socket.error:
                break

            # Check if the client has disconnected
            if not data:
                break

            self._received[client_address].append(data)

        # Close the client socket
        client_socket.close()
        closing = threading.Thread(target=self._close_after, args=(client_address, ))
        self._closing_threads.append(closing)
        closing.start()

    @update_last_accessed
    def receive(self, client_socket: socket.socket) -> bytes:
        data = client_socket.recv(1024)
        return data
