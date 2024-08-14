# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import re
from typing import Union
from protocol import BlockProtocol

EOS = "EOS"
BYTES_EOS = bytes(EOS, encoding='ascii')
START_AUDIO = 'WAVE'
BYTES_START_AUDIO = bytes(START_AUDIO, 'ascii')
REGEX_AUDIO_HEADER = START_AUDIO + (
    r":(?P<frequency>\d+):(?P<channels>\d+)"
    r":(?P<bits_per_sample>\d+):(?P<format>\d+)"
)
FORMAT_AUDIO_HEADER = START_AUDIO + (
    ":{frequency:d}:{channels:d}"
    ":{bits_per_sample:d}:{format:d}"
)
START_LIVELINK = "A2F"
BYTES_START_LIVELINK = bytes(START_LIVELINK, 'ascii')
REGEX_LIVELINK_HEADER = START_LIVELINK + r":(?P<framerate>\d+)"
FORMAT_LIVELINK_HEADER = START_LIVELINK + ":{framerate:d}"


class BurstAudioProtocol(BlockProtocol):
    """https://gitlab-master.nvidia.com/omniverse/connect/unreal-connector/
        -/blob/5.1/OmniverseLiveLink/README.md
    """

    _regex_header = re.compile(REGEX_AUDIO_HEADER)
    _format_header = FORMAT_AUDIO_HEADER

    _eos = EOS
    _header_start = START_AUDIO

    @property
    def eos(self):
        """Returns the magic keyword
        """
        return self._eos

    @property
    def header_start(self):
        """Returns the magic keyword
        """
        return self._header_start

    @classmethod
    def extract_header(cls, text: Union[str, bytes]):
        """Extract audio specs from header packet.

        Args:
            text: (str or bytes) header string

        Returns:
            (dict) key and values (int)

        Examples:
            - {frequency: 8000, channels: 1, bits_per_sample: 8, format: 1}
        """
        if isinstance(text, bytes):
            text = text.decode(encoding='ascii')

        match = cls._regex_header.match(text)
        if not match:
            return {}
        data = match.groupdict()
        for k, v in data.items():
            if v.isdigit():
                data[k] = int(v)
        return data

    @classmethod
    def format_header(cls, **kwargs):
        """Build burst audio header from specs.

        Args:
            frequency: (int) audio frequency
            channels: (int) number of audio channels. typically 1.
            bits_per_sample: (int) number of bits per sample; such as 16, 32, and 64
            format: (int) pcm format type; 1 = unsigned int, 3 = signed float

        Returns:
            (str) formatted header string
        """
        return cls._format_header.format(**kwargs)


class BurstLivelinkProtocol(BurstAudioProtocol):
    """https://gitlab-master.nvidia.com/omniverse/connect/unreal-connector/
        -/blob/5.1/OmniverseLiveLink/README.md
    """

    _regex_header = re.compile(REGEX_LIVELINK_HEADER)
    _format_header = FORMAT_LIVELINK_HEADER

    _eos = EOS
    _header_start = START_LIVELINK

    @classmethod
    def extract_header(cls, text: str):
        """Extract audio specs from header packet.

        Args:
            text: (str) header string

        Returns:
            (dict) key and values (int)

        Examples:
            - {framerate: 30}
        """
        return super().extract_header(text)

    @classmethod
    def format_header(cls, **kwargs):
        """Build burst audio header from specs.

        Args:
            framerate: (int) frames per second

        Returns:
            (str) formatted header string
        """
        return super().format_header(**kwargs)
