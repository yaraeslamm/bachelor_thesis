# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# pylint: disable=import-outside-toplevel missing-class-docstring
import asyncio

import omni.kit
import omni.kit.test


class TestBurstAudioReceiver(omni.kit.test.AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        import os
        cls.test_dir = os.path.dirname(__file__)
        # 48k, 10sec, 1channel, 16bit pcm
        cls.wav_path = os.path.join(cls.test_dir, 'data', 'voice_male_p1_neutral.wav')

    def setUp(self):
        import socket
        import wave
        from omni.avatar.livelink.scripts.audioreceiver import BurstAudioReceiver
        from omni.avatar.livelink.scripts.burst import FORMAT_AUDIO_HEADER

        # prepare sample audio data
        self.wave = wave.open(self.wav_path, 'r')
        self.specs = {
            'frequency': self.wave.getframerate(),
            'format': 1,
            'channels': self.wave.getnchannels(),
            'bits_per_sample': self.wave.getsampwidth() * 8,
        }
        self.header = FORMAT_AUDIO_HEADER.format(**self.specs)

        # setup test receiver and client
        self.receiver = BurstAudioReceiver()
        host, port = self.receiver.start('localhost', 0, timeout=1)
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        self.client = socket.socket()
        self.client.settimeout(1)
        self.client.connect((host, port))

    def tearDown(self):
        self.wave.close()
        # self.wave = None
        self.client.close()
        # self.client = None
        self.receiver.stop()
        # self.receiver = None

    async def test_player_start_and_wait(self):
        from omni.avatar.livelink.scripts.livelink import pack_block_data

        # send header data to initiate a player
        block_header = pack_block_data(self.header)
        self.client.sendall(block_header)
        await asyncio.sleep(0.1)

        self.receiver.download_received()
        self.assertEqual(len(self.receiver.players), 0)

    async def test_player_receive_and_play(self):
        from omni.avatar.livelink.scripts.livelink import pack_block_data

        # send header data to initiate a player
        block_header = pack_block_data(self.header)
        self.client.sendall(block_header)

        # send actual audio data
        for _ in range(3):
            body = self.wave.readframes(8000)
            block_body = pack_block_data(body)
            # print('send body', len(body), block_body[:20])
            self.client.sendall(block_body)
            await asyncio.sleep(0.1)
            self.receiver.download_received()
        self.assertTrue(self.receiver.players)

        # wait while buffer is playing
        for i in range(10):
            if not self.receiver.actives:
                break
            self.receiver.download_received()
            await asyncio.sleep(0.1)
        self.receiver.stop()
        self.receiver.download_received()

    async def test_player_terminate_after_eos(self):
        from omni.avatar.livelink.scripts.livelink import pack_block_data

        # send header data to initiate a player
        block_header = pack_block_data(self.header)
        self.client.sendall(block_header)

        # send actual audio data
        for _ in range(3):
            body = self.wave.readframes(6000)
            block_body = pack_block_data(body)
            self.client.sendall(block_body)
            await asyncio.sleep(0.1)
            self.receiver.download_received()

        # terminate after play finishes
        block_tail = pack_block_data('EOS')
        self.client.sendall(block_tail)

        # wait while buffer is playing
        while self.receiver.actives:
            self.receiver.download_received()
            await asyncio.sleep(0.1)
        self.receiver.download_received()

        self.assertEqual(len(self.receiver.players), 0)
