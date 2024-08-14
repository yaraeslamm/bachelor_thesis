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

TEST_DICT = {"TestSubject":{"Facial":{"Names":["a","b"],"Weights":[1.0,2.0]},"Body":{}}}
TEST_BODY = b'{"TestSubject":{"Facial":{"Names":["a","b"],"Weights":[1.0,2.0]},"Body":{}}}'
TEST_HEAD = b'\x00\x00\x00\x00\x00\x00\x00L'
TEST_DATA = TEST_HEAD + TEST_BODY


class TestReceiveLivelinkNode(omni.kit.test.AsyncTestCase):

    node_type = 'omni.avatar.ReceiveLivelink'
    node_name = 'TestReceiveLivelinkNode'

    async def setUp(self):
        import omni.graph.core as og
        import omni.usd

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
            self.graph, {og.Controller.Keys.CREATE_NODES: (self.node_name, self.node_type)}
        )
        self.node = nodes[0]

        attr_port = self.node.get_attribute('inputs:livelink_port')
        attr_host = self.node.get_attribute('inputs:livelink_host')
        attr_subject = self.node.get_attribute('inputs:livelink_subject')
        attr_timeout = self.node.get_attribute('inputs:timeout')
        attr_filter = self.node.get_attribute('inputs:face_filter')
        attr_host.set('localhost')
        attr_port.set(0)
        attr_subject.set('TestSubject')
        attr_filter.set('a')
        attr_timeout.set(1)
        self.node.request_compute()
        og.Controller().evaluate_sync()

    async def tearDown(self):
        import omni.usd

        self.node = None
        self.graph = None
        self.graph_path = None
        self.stage = None

        omni.usd.get_context().new_stage()
        await omni.usd.get_context().new_stage_async()

    async def test_check_created_receivelivelink_node(self):
        self.assertTrue(self.node.is_valid())
        self.assertEqual(self.node.get_type_name(), self.node_type)
        self.assertTrue(self.node.get_attribute('outputs:face_weights'))

    async def test_activate_receivelivelink_node(self):
        import omni.graph.core as og

        attr_activate = self.node.get_attribute('inputs:activate')
        attr_address = self.node.get_attribute('outputs:address')

        attr_activate.set(True)
        self.node.request_compute()
        og.Controller().evaluate_sync()

        self.assertIn('127.0.0.1:', attr_address.get())

    # async def test_make_node_connected(self):
    #     import omni.graph.core as og

    #     attr_activate = self.node.get_attribute('inputs:activate')
    #     attr_address = self.node.get_attribute('outputs:address')

    #     attr_activate.set(True)
    #     og.Controller().evaluate_sync()
    #     url = attr_address.get()

    #     host, port = url.split(':')

    #     self.client = socket.socket()
    #     self.client.settimeout(1)
    #     self.client.connect((host, int(port)))
    #     await asyncio.sleep(0.1)
    #     self.node.request_compute()
    #     og.Controller().evaluate_sync()

    #     addr_client = self.client.getsockname()
    #     hostname_client = f'{addr_client[0]}:{addr_client[1]}'
    #     attr_connected = self.node.get_attribute('outputs:connected')
    #     self.assertIn(hostname_client, attr_connected.get())

    #     attr_names = self.node.get_attribute('outputs:face_names')
    #     attr_weights = self.node.get_attribute('outputs:face_weights')
    #     self.assertLess(len(attr_names.get()), 1)
    #     self.assertLess(len(attr_weights.get()), 1)

    # async def test_receive_data_through_node(self):
    #     import omni.graph.core as og

    #     attr_activate = self.node.get_attribute('inputs:activate')
    #     attr_address = self.node.get_attribute('outputs:address')

    #     attr_activate.set(True)
    #     self.node.request_compute()
    #     og.Controller().evaluate_sync()

    #     url = attr_address.get()
    #     host, port = url.split(':')
    #     self.client = socket.socket()
    #     self.client.settimeout(1)
    #     self.client.connect((host, int(port)))
    #     self.node.request_compute()
    #     og.Controller().evaluate_sync()

    #     attr_names = self.node.get_attribute('outputs:face_names')
    #     attr_weights = self.node.get_attribute('outputs:face_weights')
    #     self.assertLess(len(attr_names.get()), 1)
    #     self.assertLess(len(attr_weights.get()), 1)

    #     self.client.send(TEST_DATA)
    #     await asyncio.sleep(0.1)
    #     self.node.request_compute()
    #     og.Controller().evaluate_sync()

    #     self.assertIn('a', attr_names.get())
    #     self.assertIn(1.0, attr_weights.get())
    #     self.assertNotIn('b', attr_names.get())
    #     self.assertNotIn(2.0, attr_weights.get())


class TestLivelinkReceiver(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts.livelinkreceiver import LivelinkReceiver
        self.raw_data_1 = TEST_DATA
        self.raw_data_2 = self.raw_data_1.replace(b'Test', b'Next')
        self.raw_data_3 = self.raw_data_1.replace(b'"a","b"', b'"c","d"')

        self.receiver = LivelinkReceiver()

    def tearDown(self):
        self.receiver.stop()
        self.receiver = None

    async def test_download_receive_realtime(self):
        from collections import deque

        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        self.receiver.server._received = {
            ('host1', 1111): deque([
                {
                    'TestSubj1': {
                        'Facial': {
                        }
                    }
                },
                {
                    'TestSubj2': {
                        'Facial': {
                        }
                    }
                }
            ])
        }
        received = self.receiver.download_received(1)
        self.assertIn('TestSubj1', received)
        self.assertNotIn('TestSubj2', self.receiver.received)

        received = self.receiver.download_received(1)
        self.assertIn('TestSubj2', self.receiver.received)

    async def test_download_receive_burst(self):
        from collections import deque
        from omni.avatar.livelink.scripts import livelinkreceiver

        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        self.receiver.server._received = {
            ('host1', 1111): deque([
                {
                    livelinkreceiver.KEY_START_BURST: True,
                    'framerate': 5
                },
                {
                    'TestSubj2': {
                        'frame': 1
                    }
                },
                {
                    'TestSubj2': {
                        'frame': 2
                    }
                }
            ])
        }
        self.receiver.download_received(1)
        self.assertIn('TestSubj2', self.receiver.received)

    async def test_download_receive_burst2(self):
        from collections import deque
        from omni.avatar.livelink.scripts import livelinkreceiver

        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        self.receiver.server._received = {
            ('host1', 1111): deque([
                {
                    livelinkreceiver.KEY_START_BURST: True,
                    'framerate': 5
                },
                {
                    'TestSubj2': {
                        'frame': 1
                    }
                },
                {
                    'TestSubj2': {
                        'frame': 2
                    }
                }
            ])
        }
        self.receiver.download_received(2)
        self.assertEqual(self.receiver.received['TestSubj2'].get('frame'), 2)
        self.assertDictEqual(
            self.receiver.received['TestSubj2'].get_data(0), {'frame': 1})

    async def test_download_receive_burst_eos(self):
        from collections import deque
        from omni.avatar.livelink.scripts import livelinkreceiver

        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        self.receiver.server._received = {
            ('host1', 1111): deque([
                {
                    livelinkreceiver.KEY_START_BURST: True,
                    'framerate': 5
                },
                {
                    'TestSubj2': {
                        'frame': 1
                    }
                },
                {
                    'TestSubj2': {
                        'frame': 2
                    }
                },
                {
                    'EOS': True
                },
                {
                    # non-burst frame. will update the latest frame
                    'TestSubj2': {
                        'frame': 3
                    }
                }
            ])
        }
        self.receiver.download_received(1)
        self.assertEqual(self.receiver.received['TestSubj2'].get('frame'), 1)

        self.receiver.download_received(1)
        self.assertEqual(self.receiver.received['TestSubj2'].get('frame'), 2)
        self.assertEqual(self.receiver.received['TestSubj2'].num_frames, 2)

        self.receiver.download_received(1)
        self.assertEqual(self.receiver.received['TestSubj2'].num_frames, 2)

        self.receiver.download_received(1)
        self.assertEqual(self.receiver.received['TestSubj2'].get('frame'), 3)
        print(self.receiver.received)
        self.assertEqual(self.receiver.received['TestSubj2'].num_frames, 1)

    async def test_download_client_data(self):
        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        client = socket.socket()
        client.settimeout(1)
        client.connect(('localhost', self.port))

        # data received to the buffer, but not downloaded to the node
        client.send(self.raw_data_1)
        await asyncio.sleep(0.1)
        self.assertGreater(len(self.receiver.server._received), 0)
        self.assertEqual(self.receiver.subjects, [])

        # data downloaded to the receiver
        self.receiver.update_received()
        self.assertEqual(self.receiver.subjects, ['TestSubject'])

    async def test_download_and_get_all_data(self):
        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        # two subjects are received, both are kept as the last state
        client = socket.socket()
        client.settimeout(1)
        client.connect(('localhost', self.port))
        await asyncio.sleep(0.1)

        self.assertEqual(self.receiver.subjects, [])

        client.send(self.raw_data_1)
        client.send(self.raw_data_2)
        await asyncio.sleep(0.1)

        self.assertGreater(len(self.receiver.server._received), 0)

        self.receiver.update_received()
        self.assertEqual(self.receiver.subjects, ['TestSubject', 'NextSubject'])

    async def test_download_and_get_latest_data(self):
        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        # two dictionaries are received. latest one is kept.
        client = socket.socket()
        client.settimeout(1)
        client.connect(('localhost', self.port))
        client.send(self.raw_data_1)
        client.send(self.raw_data_3)
        await asyncio.sleep(0.1)

        self.assertGreater(len(self.receiver.server._received), 0)
        self.receiver.update_received()

        data1 = self.receiver.get_received('TestSubject')
        self.assertEqual(data1['Facial']['Names'], ['c', 'd'])

    async def test_recv_latest_data(self):
        """Receive multiple frames and get the latest
        """
        self.url, self.port = self.receiver.start(
            host='localhost', port=0, timeout=1
        )
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

        client = socket.socket()
        client.settimeout(1)
        client.connect(('localhost', self.port))

        client.send(self.raw_data_1)
        client.send(self.raw_data_2)
        await asyncio.sleep(0.1)

        received = self.receiver.receive_latest()
        self.assertIsInstance(received, dict)
        self.assertIn('NextSubject', received)

    async def test_get_filtered_weights(self):
        import re
        controls_in = ['A1', 'A2', 'B1']
        weights_in = [1, 2, 3, 4]
        regex = re.compile('B(.)')

        c_out, w_out = self.receiver.filter_weights(
            controls_in, weights_in, regex
        )
        self.assertListEqual(c_out, ['B1'])
        self.assertListEqual(w_out, [3])


class TestLivelinkServerWithSocket(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts import livelinkreceiver

        self.raw_data_1 = TEST_DATA
        self.raw_data_2 = self.raw_data_1.replace(b'Test', b'Next')

        self.server = livelinkreceiver.LivelinkServer()
        self.server.timeout_client = 1
        self.server.timeout_service = 1
        url, self.port = self.server.listen('127.0.0.1', 0, timeout=1)

        self.server.start()

        self.client = socket.socket()
        self.client.settimeout(1)
        self.client.connect(('localhost', self.port))

    def tearDown(self):
        self.client.close()
        self.server.close_all()

        self.client = None
        self.server = None

    async def test_recv_client_data(self):
        """Receive and transform livelink frame data
        """
        response = self.client.send(self.raw_data_1)
        await asyncio.sleep(0.1)

        received = self.server.pop_received(self.client.getsockname())
        self.assertDictEqual(received, TEST_DICT)


class TestLivelinkServer(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts import livelinkreceiver

        self.server = livelinkreceiver.LivelinkServer()

    def tearDown(self):
        self.server = None

    async def test_transform_livelink_data(self):
        received = self.server._transform_raw_data(TEST_BODY)
        self.assertDictEqual(received, TEST_DICT)

    async def test_transform_livelink_burst_header(self):
        received = self.server._transform_raw_data(b'A2F:8')
        self.assertEqual(received.get('framerate'), 8)

    async def test_transform_livelink_burst_end(self):
        received = self.server._transform_raw_data(b'EOS')
        self.assertDictEqual(received, {'EOS': True})


class TestLivelinkSequence(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts import livelinkreceiver

        self.seq = livelinkreceiver.LivelinkSequence(framerate=5)
        self.dummy = {
            'TestSubject': self.seq
        }

    def test_livelinksequence_properties(self):
        """Check properties returning va;ies
        """
        self.assertEqual(self.seq.framerate, 5)
        self.assertEqual(self.seq.num_frames, 0)
        self.assertEqual(self.seq.seconds, 0.0)

    def test_livelinksequence_append_data(self):
        """Add one livelink frame to the end of sequence.
        """
        self.seq.append({'Control1': 1})
        self.seq.append({'Control1': 2})

        self.assertEqual(self.seq.num_frames, 2)
        self.assertEqual(self.seq.seconds, 2.0/5)
        self.assertEqual(self.seq._frames[0], {'Control1': 1})

    def test_livelinksequence_insert_data(self):
        """Insert data to a given index
        """
        self.seq.append({'Control1': 1})
        self.seq.insert(0, {'Control1': 2})

        self.assertEqual(self.seq._frames[0], {'Control1': 2})

    def test_livelinksequence_prepend_data(self):
        """Add one livelink frame data to the front of the sequence.
        """
        self.seq.append({'Control1': 1})
        self.seq.prepend({'Control1': 2})

        self.assertEqual(self.seq._frames[0], {'Control1': 2})

    def test_livelinksequence_get_data(self):
        self.seq.append({'Control1': 1})
        self.seq.append({'Control1': 2})

        self.assertEqual(self.seq.get_data(0), {'Control1': 1})
        self.assertEqual(self.seq.get_data(1), {'Control1': 2})
        self.assertEqual(self.seq.get_data(-1), {'Control1': 2})

    def test_livelinksequence_get_data_for_seconds(self):
        self.seq.append({'Control1': 1})
        self.seq.append({'Control1': 2})

        self.assertEqual(self.seq.get_data_for_seconds(0.0), {'Control1': 1})
        self.assertEqual(self.seq.get_data_for_seconds(1.0 / 5), {'Control1': 2})

    def test_livelinksequence_get_by_key(self):
        """get the latest livelink frame when used like a dict
        """
        self.seq.append({'Control1': 1})
        self.seq.append({'Control1': 2})

        self.assertEqual(self.seq['Control1'], 2)

    def test_livelinksequence_get_by_method(self):
        """get the latest livelink frame when used like a dict
        """
        self.seq.append({'Control1': 1})
        self.seq.append({'Control1': 2})

        self.assertEqual(self.seq.get('Control1'), 2)
        self.assertEqual(self.seq.get('ControlX'), None)


class TestLivelinkSendProtocol(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts import livelink

        self.ref_dict = {"Facial": {"Names": ['a', 'b'], "Weights": [1.0, 2.0]}, "Body": {}}
        self.body_data = b'{"Facial":{"Names":["a","b"],"Weights":[1.0,2.0]},"Body":{}}'
        self.head_data = b'\x00\x00\x00\x00\x00\x00\x00<'
        raw_data = self.head_data + self.body_data
        self.raw_data = raw_data

        self.protocol = livelink.LivelinkSendProtocol('TestSubject', ['a', 'b'], ['c', 'd'])

    def tearDown(self):
        self.protocol = None

    async def test_pack_dict(self):
        data = self.protocol.pack_data(self.ref_dict)
        self.assertEqual(data, self.raw_data)

    async def test_build_facial_dict(self):
        data = self.protocol._build_part_dict([1.0, 2.0], ['a', 'b'])
        ref = {"Names": ['a', 'b'], "Weights": [1.0, 2.0]}
        self.assertDictEqual(data, ref)

    async def test_build_dict(self):
        data = self.protocol.build_dict([1.0, 2.0])
        self.assertDictEqual(data, {'TestSubject': self.ref_dict})

    async def test_build_data(self):
        data = self.protocol.build_data([1.0, 2.0])
        ref = (
            b'\x00\x00\x00\x00\x00\x00\x00L'
            b'{"TestSubject":{"Facial":{"Names":["a","b"],"Weights":[1.0,2.0]},"Body":{}}}'
        )
        self.assertEqual(data, ref)


class TestLivelinkReceiveProtocol(omni.kit.test.AsyncTestCase):

    async def setUp(self):
        from omni.avatar.livelink.scripts import livelink

        self.ref_data = {"a":1,"b":2}
        self.body_data = b'{"a":1,"b":2}'
        self.head_data = b'\x00\x00\x00\x00\x00\x00\x00\r'
        raw_data = self.head_data + self.body_data
        self.raw_data = raw_data

        class MockClientSocket:
            def __init__(self):
                self.data = raw_data
                self.sent = 0

            def recv(self, size):
                out_data = self.data[self.sent:self.sent + size]
                self.sent += len(out_data)
                return out_data

        self.socket = MockClientSocket()
        self.protocol = livelink.LivelinkReceiveProtocol(self.socket)

    async def tearDown(self):
        self.protocol = None

    async def test_read_size(self):
        read = self.protocol.read_size()
        self.assertEqual(read, len(self.body_data))

    async def test_get_next(self):
        read = self.protocol.get_next()
        self.assertEqual(read, self.body_data)

    async def test_get_json(self):
        read = self.protocol.get_next_as_json()
        self.assertDictEqual(read, self.ref_data)
