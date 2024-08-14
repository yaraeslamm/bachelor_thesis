# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import socket
from typing import List

from server import AddressType, ThreadedServer


class ReceiverBase:
    """Convenience class for maintaining per-node state information"""

    def __init__(self):
        """Instantiate the per-node state information.
        """
        self.host = None
        self.port = None

        self.server = None

    @property
    def address(self) -> AddressType:
        if not self.server:
            return (None, None)
        return self.server.address

    @property
    def url(self) -> str:
        if not self.server:
            return ''
        return self.server.url

    def unload(self):
        self.server = None

    def is_running(self) -> bool:
        if not self.server:
            return False
        return self.server.is_running()

    def is_connected(self) -> bool:
        if not self.server:
            return None
        return self.server.connected

    def has_received(self) -> bool:
        if not self.server:
            return False
        return self.server.has_received()

    def list_clients(self) -> List[socket.socket]:
        if not self.server:
            return []
        return self.server.clients

    def list_received_addresses(self) -> List[AddressType]:
        if not self.server:
            return []
        return self.server.received_addresses

    def list_client_addresses(self) -> List[AddressType]:
        if not self.server:
            return []
        return self.server.client_addresses

    def start(self, host: str = 'localhost', port: int = 12030, timeout: float = None):
        if self.is_connected():
            self.stop()

        self.host = host
        self.port = port

        self.server = ThreadedServer()
        _host, _port = self.server.listen(host, port, timeout=timeout)
        self.server.start()  # start accept and receiving

        return _host, _port

    def stop(self):
        if not self.server:
            return
        self.server.close_all()
        self.server = None
