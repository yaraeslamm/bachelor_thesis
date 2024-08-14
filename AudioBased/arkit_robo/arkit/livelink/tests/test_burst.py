# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import asyncio
import socket

import omni.kit
import omni.kit.test

TEST_HEAD = b'\x00\x00\x00\x00\x00\x00\x00\x11WAVE:48000:1:16:1'
TEST_DATA = TEST_HEAD


class TestBurstAudioProtocol(omni.kit.test.AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        import os
        from omni.avatar.livelink.scripts import burst

        cls.test_dir = os.path.dirname(__file__)
        cls.wav_path = os.path.join(cls.test_dir, 'data', 'voice_male_p1_neutral.wav')
        cls.protocol = burst.BurstAudioProtocol

        return super().setUpClass()

    async def test_match_burst_audio_header(self):
        """Test matching header regular expression
        """
        import re
        from omni.avatar.livelink.scripts import burst

        in_data = 'WAVE:100000:1:16:1'

        match = re.match(burst.REGEX_AUDIO_HEADER, in_data)
        self.assertIsNotNone(match)

        data = match.groupdict()
        self.assertEqual(data.get('frequency'), '100000')
        self.assertEqual(data.get('channels'), '1')
        self.assertEqual(data.get('bits_per_sample'), '16')
        self.assertEqual(data.get('format'), '1')

    async def test_extract_burst_audio_header(self):
        """Extract header info through regular expression
        """
        in_data = 'WAVE:100000:1:16:1'

        data = self.protocol.extract_header(in_data)
        self.assertEqual(data.get('frequency'), 100000)
        self.assertEqual(data.get('channels'), 1)
        self.assertEqual(data.get('bits_per_sample'), 16)
        self.assertEqual(data.get('format'), 1)

    async def test_load_and_format_audio_data(self):
        """Format header from a sample wave file.
        """
        import wave
        from omni.avatar.livelink.scripts import burst

        wf = wave.open(self.wav_path, 'r')
        self.assertEqual(wf.getframerate(), 48000)
        self.assertEqual(wf.getnchannels(), 1)

        data = {
            'frequency': wf.getframerate(),
            'channels': wf.getnchannels(),
            'bits_per_sample': wf.getsampwidth() * 8,
            'format': 1,
        }
        header = burst.FORMAT_AUDIO_HEADER.format(**data)
        self.assertEqual(header, 'WAVE:48000:1:16:1')

    async def test_format_burst_audio_header(self):
        """Format header from sample data.
        """
        data = {
            'frequency': 48000,
            'channels': 1,
            'bits_per_sample': 16,
            'format': 1,
        }
        header = self.protocol.format_header(**data)
        self.assertEqual(header, 'WAVE:48000:1:16:1')


class TestBurstLivelinkProtocol(omni.kit.test.AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        from omni.avatar.livelink.scripts import burst

        cls.protocol = burst.BurstLivelinkProtocol

    async def test_match_burst_livelink_header(self):
        """Test matching header regular expression
        """
        import re
        from omni.avatar.livelink.scripts import burst

        in_data = 'A2F:12'

        match = re.match(burst.REGEX_LIVELINK_HEADER, in_data)
        self.assertIsNotNone(match)

        data = match.groupdict()
        self.assertEqual(data.get('framerate'), '12')

    async def test_extract_burst_livelink_header(self):
        """Extract header info through regular expression
        """
        in_data = 'A2F:12'

        data = self.protocol.extract_header(in_data)
        self.assertEqual(data.get('framerate'), 12)

    async def test_format_burst_audio_header(self):
        """Format header from sample data.
        """
        data = {
            'framerate': 99,
        }
        header = self.protocol.format_header(**data)
        self.assertEqual(header, 'A2F:99')
