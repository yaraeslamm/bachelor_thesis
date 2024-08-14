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


class TestPlayAudio(omni.kit.test.AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        import os
        cls.test_dir = os.path.dirname(__file__)
        cls.wav_path = os.path.join(cls.test_dir, 'data', 'voice_male_p1_neutral.wav')

    def setUp(self):
        import wave
        import scipy.io

        self.wave = wave.open(self.wav_path, 'r')
        self.samplerate, self.audio = scipy.io.wavfile.read(self.wav_path)

    def tearDown(self):
        self.audio = None
        self.wave.close()
        self.wave = None

    async def test_load_sample_audio(self):
        self.assertEqual(self.wave.getframerate(), 48000)
        self.assertEqual(self.wave.getnchannels(), 1)
        self.assertEqual(self.wave.getnframes(), self.audio.shape[0])
        self.assertEqual(self.wave.getframerate(), self.samplerate)

    async def test_raw_output_stream(self):
        import numpy as np
        import sounddevice

        stream = sounddevice.RawOutputStream(
            samplerate=self.wave.getframerate(),
            channels=self.wave.getnchannels(),
            dtype=np.int16,
        )
        buffer = self.wave.readframes(24000)
        stream.start()
        stream.write(buffer)

    async def test_output_stream(self):
        import numpy as np
        import sounddevice

        stream = sounddevice.OutputStream(
            samplerate=self.samplerate,
            channels=1 if len(self.audio.shape) < 2 else self.audio.shape[1],
            dtype=self.audio.dtype,
        )
        stream.start()
        stream.write(self.audio[:24000])


class TestRawStreamPlayer(omni.kit.test.AsyncTestCase):

    @classmethod
    def setUpClass(cls):
        import os
        cls.test_dir = os.path.dirname(__file__)
        cls.wav_path = os.path.join(cls.test_dir, 'data', 'voice_male_p1_neutral.wav')

    def setUp(self):
        import wave
        import numpy as np
        from omni.avatar.livelink.scripts import audioreceiver

        self.wave = wave.open(self.wav_path, 'r')
        self.player = audioreceiver.RawStreamPlayer(
            samplerate=self.wave.getframerate(),
            channels=self.wave.getnchannels(),
            dtype=np.int16,
        )

    def tearDown(self):
        self.wave.close()
        self.wave = None
        self.player.stop(wait_clear_buffer=True)
        self.player = None

    async def test_player_properties(self):
        self.assertEqual(self.player.dtype_size, 2)

    async def test_player_start_and_wait(self):
        """Wait player to finish the buffer
        """
        self.player.start()
        self.player.add_buffer(self.wave.readframes(12000))
        while self.player.num_buffer_samples:
            await asyncio.sleep(0.01)
        self.assertEqual(self.player.num_buffer_samples, 0)

    async def test_player_start_and_stop(self):
        """Stop player before buffer finishes.
        """
        self.player.start()
        self.player.add_buffer(self.wave.readframes(12000))
        self.player.stop()
        self.assertFalse(self.player.active)
        self.assertGreater(self.player.num_buffer_samples, 0)
