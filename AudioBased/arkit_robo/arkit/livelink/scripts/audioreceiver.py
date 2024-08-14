# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# pylint: disable=unused-argument missing-class-docstring missing-function-docstring
import time
import socket
from typing import Dict, List, Tuple, Callable

import numpy as np
# import scipy.io
from sounddevice import RawOutputStream

import carb

from .server import ThreadedServer, update_last_accessed, AddressType
from .burst import BurstAudioProtocol, BYTES_EOS
from .receiver import ReceiverBase


class InvalidHeaderError(ValueError):
    """Raised when audio header format is not valid.
    """


class BurstAudioReceiver(ReceiverBase):
    """Convenience class for maintaining per-node state information"""

    def __init__(self):
        """Instantiate the per-node state information.
        """
        super().__init__()

        self.players = {}  # address: player

    @property
    def times(self) -> dict:
        return {addr: player.time for addr, player in self.players.items()}

    @property
    def play_times(self) -> dict:
        return {addr: player.play_time for addr, player in self.players.items()}

    @property
    def actives(self) -> list:
        """Active player addreses.
        """
        return [addr for addr, player in self.players.items() if player.active]

    def download_received(self, max_frames=1000):
        """Loop all connected clients to push received audio.
        """
        for _ in range(max_frames):
            if not self.server.has_received():
                # stop iteration
                break

            for addr in self.list_received_addresses():
                if self.server.len_received(addr) < 1:
                    continue
                self.push_received_to_player(addr)

    def push_received_to_player(self, addr: AddressType):
        """Push Burst audio data into sound device buffer.
            Following the sequence of Burst Audio Protocol in Unreal Connector.

        Args:
            addr: (AddressType) connected client address

        Returns:
            (None)
        """
        received = self.server.next_received(addr)
        if received is None:
            # nothing new is received
            return

        player = self.players.get(addr)
        if player:
            # fill buffer or terminate
            if isinstance(received, dict):
                # received a new header (missed EOS)
                if player.num_buffer_samples:
                    # pass until buffer is cleared
                    return
                else:
                    carb.log_info(f'Buffer ended. Ending audio receiving from {addr}')
                    player.stop()
                    self.players.pop(addr)
            elif not isinstance(received, bytes):
                # pass invalid data
                self.server.pop_received(addr)
                return
            elif BYTES_EOS in received:
                # received EOS
                if player.num_buffer_samples:
                    # continue until buffer is cleared
                    return
                else:
                    carb.log_info(f'EOS received. Ending audio receiving from {addr}')
                    player.stop()
                    self.players.pop(addr)
                    self.server.pop_received(addr)
            else:
                # wav stream
                player.add_buffer(self.server.pop_received(addr))
        elif isinstance(received, dict):
            # received a new audio header
            if self.server.len_received(addr) < 2:
                # wait until playable wav data is received after the header
                return
            spec = self.server.pop_received(addr)

            # define dtype
            dtype = np.float32
            if spec.get('format', 1) == 1:
                dtype = get_int_dtype(spec.get('bits_per_sample', 16) // 8)

            # start a new player
            player = RawStreamPlayer(
                samplerate=spec.get('frequency', 48000),
                channels=spec.get('channels', 1),
                dtype=dtype,
            )
            self.players[addr] = player
            player.start()
        else:
            # invalid sequence. proceed received queue
            self.server.pop_received(addr)

    def start(self, host: str = 'localhost', port: int = 12030, timeout: float = None):
        if self.is_connected():
            self.stop()

        self.host = host
        self.port = port

        self.server = AudioReceiveServer()
        _host, _port = self.server.listen(host, port, timeout=timeout)
        self.server.start()  # start accept and receiving

        return _host, _port

    def stop(self):
        for _, player in self.players.items():
            player.stop()
        super().stop()


class AudioReceiveServer(ThreadedServer):
    """Receive audio stream data through burst protocol.
    """

    @update_last_accessed
    def receive(self, client_socket: socket.socket) -> dict:
        prot = BurstAudioProtocol(client_socket)
        raw_data = prot.get_next()

        # HEADER, EOS, or audio stream
        if b'WAVE' in raw_data:
            text = raw_data.decode('ascii')
            data = prot.extract_header(text)
            if not data:
                raise InvalidHeaderError(f'Cannot decode header: {raw_data}')
            return data
        # else
        return raw_data


class RawStreamPlayer:
    """Play raw(bytes) audio stream data
    """

    def __init__(
        self,
        samplerate: int = 48000,
        channels: int = 1,
        dtype: np.dtype = np.int16,
        callback: Callable = None
    ):
        self.samplerate = samplerate
        self.channels = channels
        self.dtype = dtype
        self.callback = callback

        self.device = None
        self._buffer = b''
        self._callback_time = None
        self._callback_status = None
        self._start_time = 0.0

    @property
    def dtype_size(self):
        return np.dtype(self.dtype).itemsize

    @property
    def num_buffer_samples(self):
        return len(self._buffer) // self.dtype_size

    @property
    def time(self):
        if not self.device:
            return 0.0
        return self.device.time

    @property
    def dac_time(self):
        if self._callback_time is None:
            return 0.0
        return self._callback_time

    @property
    def play_time(self):
        if self._callback_time is None:
            return 0.0
        played_time = self.dac_time - self._start_time
        return played_time

    @property
    def active(self):
        if not self.device:
            return False
        return self.device.active

    @property
    def buffer(self):
        return self._buffer

    def add_buffer(self, buffer: bytes):
        self._buffer += buffer

    def start(self):
        if self.device:
            self.device.stop()

        self.device = RawOutputStream(
            samplerate=self.samplerate,
            channels=self.channels,
            dtype=self.dtype,
            callback=self._play_callback,
        )
        self.device.start()
        self._callback_time = None
        self._callback_status = None
        self._start_time = 0.0

    def stop(self, wait_clear_buffer=False):
        if not self.device:
            return
        if wait_clear_buffer:
            for _ in range(10000):
                if not self.active:
                    break
                if not self._buffer:
                    break
                time.sleep(0.01)
        self.device.stop()

    def _play_callback(self, out_data, num_samples, stream_time, stream_status):
        valid_samples = min(num_samples, self.num_buffer_samples)
        buf_size = valid_samples * self.dtype_size
        out_data[:buf_size] = self._buffer[:buf_size]
        out_data[buf_size:] = self.dtype(0).tobytes() * (num_samples - valid_samples)
        self._buffer = self._buffer[buf_size:]
        self._callback_time = stream_time.outputBufferDacTime
        if self._start_time < 1E-6:
            # initialize start time
            self._start_time = self._callback_time
        self._callback_status = stream_status
        if self.callback:
            self.callback(out_data, num_samples, stream_time, stream_status)
        return

    # def _finished_callback(self, block_until_playback_is_finished=False):
    #     if block_until_playback_is_finished:
    #         while self.device.active:
    #             time.sleep(0.001)


def get_int_dtype(num_bytes: int = 2):
    dtype = np.int16
    if num_bytes == 1:
        dtype = np.uint8
    elif num_bytes == 2:
        dtype = np.int16
    elif num_bytes == 4:
        dtype = np.int32
    return dtype
