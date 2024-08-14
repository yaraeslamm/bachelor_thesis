# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import re
import json
import socket
import time
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Any

#from carb import log_warn, log_error

from livelink import LivelinkReceiveProtocol, ControlsType, WeightsType
from receiver import ReceiverBase
from server import ThreadedServer, update_last_accessed, MAX_BUFFER, AddressType
from burst import BurstLivelinkProtocol, BYTES_START_LIVELINK, BYTES_EOS, EOS

KEY_START_BURST = '__START_BURST_STREAM__'


class LivelinkReceiver(ReceiverBase):
    """Convenience class for maintaining per-node state information"""

    def __init__(self):
        """Instantiate the per-node state information.
        """
        super().__init__()
        self._received = defaultdict(LivelinkSequence)
        self.face_filter = None
        self._holdings = defaultdict(list)

    def __del__(self):
        self.stop()

    @property
    def received(self) -> Dict[str, dict]:
        return dict(self._received)

    @property
    def subjects(self) -> List[str]:
        return list(self._received.keys())

    def get_received(self, subject: str, track_time: float = 0.0) -> dict:
        """Returns livelink data for the given subject and frame number

        Args:
            subject: (str) a livelink subject name
            track_time: (float) seconds of track time on playing

        Returns:
            (dict) livelink frame data.

        Examples:
            receiver.get_received('Audio2Face', 0)
            -> {'Facial': {'Names': [], 'Weights': []}}
        """
        return self._received[subject].get_data_for_seconds(track_time)

    def download_received(self, max_frames=1000) -> dict:
        """Download latest received data to self.received
            Use the property to get the historical latest status of received data.

        Returns:
            (dict) All received data indexed by subjects. {subject:{frame data}}
        """
        total = {}
        for _ in range(max_frames):
            if not self.server.has_received():
                # stop iteration
                break

            for addr in self.server.received_addresses:
                if self.server.len_received(addr) < 1:
                    # double check if there's any index issue
                    continue

                next_frame = self.server.next_received(addr)
                # OM-98515: ignore port to support socket changes while receiving
                host, _ = addr

                if not next_frame:
                    continue

                if EOS in next_frame:
                    # end burst receiving
                    self._holdings[host].clear()
                    self.server.pop_received(addr)
                    continue

                if KEY_START_BURST in next_frame:
                    # start burst receiving
                    if self.server.len_received(addr) < 2:
                        # wait for the next frame to identify subjects
                        continue
                    # else
                    framerate = next_frame.get('framerate', 30)
                    self.server.pop_received(addr)
                    next_frame = self.server.next_received(addr)
                    for subject, data in next_frame.items():
                        self._received[subject].reset(framerate)
                        # TODO: use addr instead of host to support multi-stream
                        self._holdings[host].append(subject)

                for subject, data in next_frame.items():
                    if not data:
                        # no data in the subject
                        continue
                    # add or update frame data
                    if subject in self._holdings.get(host, []):
                        self._received[subject].append(data)
                    else:
                        if self._received[subject].num_frames > 1:
                            self._received[subject].reset()
                        self._received[subject].update(data)

                total.update(next_frame)
                self.server.pop_received(addr)

        return total

    def update_received(self):
        """Download latest received data to self.received
            Please use the property to get the historical latest status of received data.

        Returns:
            (dict) All received data indexed by subjects. {subject:{frame data}}
        """
        received = self.receive_latest()

        if not received:
            return

        for subj, data in received.items():
            self._received[subj].update(data)

        return received

    def receive_latest(self) -> dict:
        """Receive all, and get the latest received data.
        """
        total = {}
        cnt = 0
        while self.server.has_received():
            for addr in self.server.received_addresses:
                if self.server.len_received(addr) < 1:
                    continue
                data = self.server.pop_received(addr)
                total.update(data)
            cnt += 1
            if cnt > MAX_BUFFER:
                raise StopIteration('Exceeded maximum receiving iteration.')
        return total

    def start(self, host: str = 'localhost', port: int = 12030, timeout: float = None):
        if self.is_connected():
            self.stop()
        self.server = LivelinkServer()
        self.host = host
        self.port = port
        _host, _port = self.server.listen(host, port, timeout=timeout)
        self.server.start()  # start accept and receiving
        return _host, _port

    @staticmethod
    def filter_weights(
        names: ControlsType, weights: WeightsType, regex: re.Pattern = None
    ) -> Tuple[ControlsType, WeightsType]:
        """Reduce controls/weights filtered by a regular expression.
        """
        out_names, out_weights = [], []
        re_match = regex
        if isinstance(re_match, str):
            re_match = re.compile(regex)

        for i, name in enumerate(names):
            if re_match and not re_match.match(name):
                continue
            if i >= len(weights):
                break
            out_names.append(name)
            out_weights.append(weights[i])
        return out_names, out_weights


class LivelinkSequence(dict):
    """Manages a uniform time-series of livelink data(dictionaries).
        - hold a series of livelink data for one subject.
        - manage frames through frame number and time
    """

    def __init__(self, framerate=30, **kwargs):
        # initialize
        self._framerate = framerate
        self._frames = deque()

        if kwargs:
            self.append(kwargs)

    def __getitem__(self, key: str) -> Any:
        if not self._frames:
            raise KeyError('No frame data in the sequence.')
        return self._frames[-1][key]

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        preview = [self.get_data(i) for i in range(min(3, self.num_frames))]
        text = f'{preview}'
        if self.num_frames > 3:
            text += '...'
        return text

    @property
    def framerate(self):
        return self._framerate

    @property
    def num_frames(self):
        return len(self._frames)

    @property
    def seconds(self):
        return float(self.num_frames) / self._framerate

    def reset(self, framerate=30):
        """Reinitialize the sequence.
        """
        self._framerate = framerate
        self._frames = deque()

    def get(self, key: str, default=None) -> Any:
        if not self._frames:
            return default
        return self._frames[-1].get(key, default)

    def update(self, new_dict: dict):
        if not self._frames:
            self.append(new_dict)
        else:
            self._frames[-1].update(new_dict)

    def append(self, data: dict):
        self._frames.append(data)

    def insert(self, index: int, data: dict):
        self._frames.insert(index, data)

    def prepend(self, data: dict):
        self._frames.appendleft(data)

    def get_data(self, frame_number=-1):
        """Returns a frame data by frame number or index

        Args:
            frame_number: (int) frame index. [-length, length-1]

        Returns:
            (dict) data of one frame
        """
        if not self._frames:
            return {}
        frame_number = min(self.num_frames - 1, frame_number)
        frame_number = max(-self.num_frames, frame_number)
        return self._frames[frame_number]

    def get_frame_for_seconds(self, seconds):
        return int(seconds * self.framerate)

    def get_data_for_seconds(self, seconds):
        return self.get_data(self.get_frame_for_seconds(seconds))


class LivelinkServer(ThreadedServer):
    """Runs a livelink receiving server as multi-threaded
    """

    @update_last_accessed
    def receive(self, client_socket) -> dict:
        """Receive and decode socket data.

        Args:
            client_socket: (socket.socket) a connected client socket

        Returns:
            (dict) received data converted to a dictionary.

        Examples:
            - {'Audio2Face': {'Facial': {'Names': [], 'Weights': []}}}
            - {'framerate': 30}
            - {'EOS': True}
        """
        prot = LivelinkReceiveProtocol(client_socket)
        raw_data = prot.get_next()
        try:
            dict_data = self._transform_raw_data(raw_data)
        except json.JSONDecodeError:
            print(f'Cannot decode data to JSON: {raw_data[:20]}')
            dict_data = {}
        except UnicodeDecodeError:
            print(f'Cannot decode received data: {raw_data[:20]}')
        return dict_data

    def _transform_raw_data(self, raw_data: bytes):
        """Transform raw socket data to a dict
        """
        data = {}
        if BYTES_START_LIVELINK in raw_data:
            # burst start
            data = BurstLivelinkProtocol.extract_header(raw_data)
            data[KEY_START_BURST] = True  # set a key to check starting burst
        elif BYTES_EOS in raw_data:
            # burst end
            data = {EOS: True}
        else:
            data = json.loads(raw_data)
        return data

    def next_received(self, addr: AddressType) -> dict:
        return super().next_received(addr=addr)


def main():
    # Step 1: Initialize the LivelinkReceiver
    receiver = LivelinkReceiver()

    # Step 2: Start the Receiver
    host, port = receiver.start(host= 'localhost', port= 12031)
    print(f"Listening on {host}:{port}")

    # Step 3: Loop to keep the program running
    try:
        while True:
            # Check for new data
            received_data = receiver.receive_latest()

            if received_data:
                # Step 4: Print the Received Data
                print("Received Data:", received_data)
            else:
                # Sleep for a short period to avoid overloading the CPU
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("Stopping LivelinkReceiver...")
    finally:
        # Ensure the receiver is properly stopped
        receiver.stop()


if __name__ == "__main__":
    main()
