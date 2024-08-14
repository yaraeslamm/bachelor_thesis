# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import socket
import struct
from typing import Union


class BlockProtocol:
    """An abstract protocol handler to receive raw block data with a size header
        {uint64 little endian - bytes size of body data}{bytes - body data}
    """
    def __init__(self, client_socket: socket.socket):
        self._sock = client_socket

    def get_next(self):
        """Receives the next block with leading size information

        Returns:
            (bytes) received raw data
        """
        data_size = self.read_size()
        return self.read_block(data_size)

    def read_block(self, size):
        """Receive until the size is acquired or all data is received.

        Args:
            size: (int) the number of bytes to receive

        Returns:
            (bytes) received raw data
        """
        ret = b""
        while len(ret) != size:
            buf = self._sock.recv(size - len(ret))
            if not buf:
                raise OSError("socket closed")
            ret += buf
        return ret

    def read_size(self):
        """Receive and read size portion from the socket.
        """
        size = struct.calcsize("!Q")
        data = self.read_block(size)
        return struct.unpack("!Q", data)[0]


def pack_block_data(data: Union[str, bytes]):
    """Generate bytes block with unsigned long block size header.

    Args:
        data: (str, bytes) data to pack

    Returns:
        (bytes) unsigned int long data size + ascii decode of data
    """
    header = struct.pack("!Q", len(data))
    if isinstance(data, str):
        send_data = header + bytes(data, "ascii")
    elif isinstance(data, bytes):
        send_data = header + data
    else:
        send_data = header + bytes(data)

    return send_data
