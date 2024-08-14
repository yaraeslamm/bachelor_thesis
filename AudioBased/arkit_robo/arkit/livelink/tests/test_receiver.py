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

import omni.kit.test


class TestReceiverBase(omni.kit.test.AsyncTestCase):

    async def setUp(self):
        from omni.avatar.livelink.scripts import receiver

        self.receiver = receiver.ReceiverBase()
        self.host, self.port = self.receiver.start('localhost', 0, timeout=1)
        self.receiver.server.timeout_client = 1
        self.receiver.server.timeout_service = 1

    async def tearDown(self):
        self.receiver.stop()
        self.receiver = None

    async def test_receiver_start_and_stop(self):
        from omni.avatar.livelink.scripts import receiver

        receiver2 = receiver.ReceiverBase()

        self.assertEqual(receiver2.is_running(), False)

        host, port = receiver2.start(host='localhost', port=0, timeout=1)
        # await asyncio.sleep(0.1)
        self.assertEqual(receiver2.is_running(), True)

        self.assertEqual(receiver2.address, (host, port))
        self.assertEqual(receiver2.url, f'{host}:{port}')

        receiver2.stop()
        await asyncio.sleep(0.1)
        self.assertEqual(receiver2.is_running(), False)
        self.assertIsNone(receiver2.server)

    async def test_check_client_is_connected(self):
        import socket
        self.assertEqual(self.receiver.is_connected(), False)

        self.client = socket.socket()
        self.client.settimeout(1)
        self.client.connect(('localhost', self.port))
        await asyncio.sleep(0.1)
        addr = self.client.getsockname()

        self.assertEqual(self.receiver.is_connected(), True)
        self.assertIn(addr, self.receiver.list_client_addresses())
