# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
# pylint: disable=import-outside-toplevel missing-class-docstring
import socket
import asyncio

import omni.kit
import omni.kit.test


class TestReceiveAudioStreamNode(omni.kit.test.AsyncTestCase):

    node_type = 'omni.avatar.ReceiveAudioStream'
    node_name = 'TestReceiveAudioStream'

    @classmethod
    def setUpClass(cls):
        import os
        cls.test_dir = os.path.dirname(__file__)
        cls.wav_path = os.path.join(cls.test_dir, 'data', 'voice_male_p1_neutral.wav')

    async def setUp(self):
        import wave
        import omni.usd
        import omni.graph.core as og
        from omni.avatar.livelink.scripts.burst import FORMAT_AUDIO_HEADER

        # prepare a test node
        await omni.usd.get_context().new_stage_async()

        stage = omni.usd.get_context().get_stage()
        dp = stage.GetDefaultPrim()
        root_path = dp.GetPath()

        self.stage = stage
        self.graph_path = f'{root_path}/graph1'
        (graph, nodes, _, _) = og.Controller.edit(
            {"graph_path": self.graph_path, "evaluator_name": 'dirty_push'}, {}
        )
        self.graph = graph

        (graph, nodes, _, _) = og.Controller.edit(
            self.graph,
            {og.Controller.Keys.CREATE_NODES: (self.node_name, self.node_type)}
        )
        self.node = nodes[0]
        og.Controller().evaluate_sync()

        attr_host = self.node.get_attribute('inputs:host')
        attr_host.set('localhost')
        attr_port = self.node.get_attribute('inputs:port')
        attr_port.set(0)
        attr_timeout = self.node.get_attribute('inputs:timeout')
        attr_timeout.set(1)

        # prepare sample audio data
        self.wave = wave.open(self.wav_path, 'r')
        self.specs = {
            'frequency': self.wave.getframerate(),
            'format': 1,
            'channels': self.wave.getnchannels(),
            'bits_per_sample': self.wave.getsampwidth() * 8,
        }
        self.header = FORMAT_AUDIO_HEADER.format(**self.specs)
        self.client = None

    async def tearDown(self):
        import omni.usd

        self.node = None
        self.graph = None
        self.graph_path = None
        self.stage = None

        self.wave.close()
        self.wave = None

        omni.usd.get_context().new_stage()
        await omni.usd.get_context().new_stage_async()

    async def test_setup_and_teardown(self):
        pass

    async def test_make_node_connected(self):
        import omni.graph.core as og

        attr_activate = self.node.get_attribute('inputs:activate')
        attr_address = self.node.get_attribute('outputs:address')

        # start server
        attr_activate.set(True)
        og.Controller().evaluate_sync()
        url = attr_address.get()

        host, port = url.split(':')

        # connect client
        self.client = socket.socket()
        self.client.settimeout(1)
        self.client.connect((host, int(port)))
        await asyncio.sleep(0.1)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

        client_addr = self.client.getsockname()
        client_url = f'{client_addr[0]}:{client_addr[1]}'
        attr_connected = self.node.get_attribute('outputs:connected')
        self.assertIn(client_url, attr_connected.get())

        # close
        self.client.close()
        attr_activate.set(False)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()
        self.assertNotIn(client_url, attr_connected.get())

    async def test_receive_data_through_node(self):
        import omni.graph.core as og
        from omni.avatar.livelink.scripts.livelink import pack_block_data

        attr_activate = self.node.get_attribute('inputs:activate')
        attr_address = self.node.get_attribute('outputs:address')
        attr_playing = self.node.get_attribute('outputs:playing')

        # start server
        attr_activate.set(True)
        og.Controller().evaluate_sync()
        url = attr_address.get()

        host, port = url.split(':')

        # make a test client and connect
        counter = 1
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(1)
        self.client.connect((host, int(port)))
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

        # send header data to initiate a player
        counter += 1
        block_header = pack_block_data(self.header)
        self.client.sendall(block_header)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

        # send actual audio data
        counter += 1
        body = self.wave.readframes(3000)
        block_body = pack_block_data(body)
        self.client.sendall(block_body)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

        # send EOS
        counter += 1
        self.client.sendall(pack_block_data('EOS'))
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()
        while attr_playing.get() and counter < 10:
            # wait while playing
            await asyncio.sleep(0.1)
            self.node.request_compute()  # force evaluate
            og.Controller().evaluate_sync()
            counter += 1
        self.assertLess(len(attr_playing.get()), 1)

        # close
        self.client.close()
        attr_activate.set(False)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

    async def test_playing_attribute_true_while_playing(self):
        import omni.graph.core as og
        from omni.avatar.livelink.scripts.livelink import pack_block_data

        attr_activate = self.node.get_attribute('inputs:activate')
        attr_address = self.node.get_attribute('outputs:address')
        attr_playing = self.node.get_attribute('outputs:playing')

        # start server
        attr_activate.set(True)
        og.Controller().evaluate_sync()

        # make a test client and connect
        counter = 1
        url = attr_address.get()
        host, port = url.split(':')
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(1)
        self.client.connect((host, int(port)))
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

        # send header data to initiate a player
        counter += 1
        block_header = pack_block_data(self.header)
        self.client.sendall(block_header)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()

        # send actual audio data
        counter += 1
        body = self.wave.readframes(12000)  # 12000 samples ~ 0.24sec
        block_body = pack_block_data(body)
        self.client.sendall(block_body)
        await asyncio.sleep(0.1)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()
        self.assertGreater(len(attr_playing.get()), 0)

        # close
        self.client.sendall(pack_block_data('EOS'))
        while attr_playing.get() and counter < 10:
            # wait while playing
            await asyncio.sleep(0.1)
            self.node.request_compute()  # force evaluate
            og.Controller().evaluate_sync()
            counter += 1
        self.client.close()
        attr_activate.set(False)
        self.node.request_compute()  # force evaluate
        og.Controller().evaluate_sync()
