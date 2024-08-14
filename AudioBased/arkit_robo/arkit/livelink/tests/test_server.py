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
import time

import omni.kit
import omni.kit.test


class TestThreadedServerConnection(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts import server
        self.server = server.ThreadedServer()
        self.server.timeout_client = 1
        self.server.timeout_service = 1

    def tearDown(self):
        self.server.close_all()
        self.server = None

    async def test_get_server_address(self):
        result1 = self.server.address
        self.assertEqual(result1[-1], None)

        host, port = self.server.listen('localhost', 0, timeout=1)

        address = self.server.address
        self.assertEqual(address, (host, port))

        url = self.server.url
        self.assertEqual(url, f'{host}:{port}')

    async def test_accept_client_connection(self):
        url, port = self.server.listen('localhost', 0, timeout=1)

        self.server.start()

        client = socket.socket()
        client.settimeout(1)
        client.connect(('localhost', port))
        await asyncio.sleep(0.1)

        self.assertTrue(self.server.connected)

    async def test_get_server_is_running(self):
        self.assertEqual(self.server.is_running(), False)

        url, port = self.server.listen('localhost', 0, timeout=1)
        self.assertEqual(self.server.is_running(), False)

        self.server.start()
        self.assertEqual(self.server.is_running(), True)

    async def test_accept_multiple_connections(self):
        url, port = self.server.listen('localhost', 0, timeout=1)

        self.server.start()

        clients = []
        addresses = []
        for i in range(3):
            client = socket.socket()
            client.settimeout(1)
            client.connect(('localhost', port))
            clients.append(client)
            addresses.append(client.getsockname())
        await asyncio.sleep(0.1)

        self.assertEqual(self.server.client_addresses, addresses)

    async def test_accept_but_no_connection(self):
        url, port = self.server.listen('localhost', 0, timeout=1)
        self.server.start()
        self.assertFalse(self.server.connected)


class TestThreadedServerCommunicate(omni.kit.test.AsyncTestCase):

    def setUp(self):
        from omni.avatar.livelink.scripts import server
        self.server = server.ThreadedServer()
        self.server.timeout_client = 1
        self.server.timeout_service = 1
        url, self.port = self.server.listen('localhost', 0, timeout=1)

        self.server.start()

        self.client = socket.socket()
        self.client.settimeout(1)
        self.client.connect(('localhost', self.port))

    def tearDown(self):
        self.client.close()
        self.server.close_all()

        self.server = None
        self.client = None

    async def test_pop_recv_client_data(self):
        response = self.client.send(b'11')
        await asyncio.sleep(0.1)
        received = self.server.pop_received(self.client.getsockname())
        self.assertEqual(received, b'11')
        self.assertEqual(response, 2)
        self.assertEqual(self.server.len_received(self.client.getsockname()), 0)

    async def test_look_recv_client_data(self):
        response = self.client.send(b'11')
        await asyncio.sleep(0.1)
        received = self.server.next_received(self.client.getsockname())
        self.assertEqual(received, b'11')
        self.assertEqual(response, 2)
        self.assertEqual(self.server.len_received(self.client.getsockname()), 1)

    async def test_has_received(self):
        self.assertEqual(self.server.has_received(), False)
        response = self.client.send(b'11')
        await asyncio.sleep(0.1)
        self.assertEqual(self.server.has_received(), True)

    async def test_recv_data_fail_no_data(self):
        received = self.server.pop_received(self.client.getsockname())
        self.assertEqual(received, None)

    async def test_recv_data_fail_no_connection(self):
        addr = self.client.getsockname()
        self.client.close()
        await asyncio.sleep(0.1)
        received = self.server.pop_received(addr)
        self.assertEqual(received, None)
        self.assertFalse(self.server.has_client(addr))

    async def test_clear_thread_after_disconnected(self):
        addr = self.client.getsockname()
        self.client.close()
        await asyncio.sleep(1.1)
        self.assertFalse(self.server.has_client(addr))

    async def test_clear_thread_after_close_all(self):
        addr = self.client.getsockname()
        self.server.close_all()
        await asyncio.sleep(1.1)
        self.assertFalse(
            self.server.has_client(addr),
            msg=f'Threads: {self.server._client_threads}',
        )

    async def test_clear_thread_after_close(self):
        addr = self.client.getsockname()
        self.server.close(addr)
        await asyncio.sleep(1.1)
        self.assertFalse(
            self.server.has_client(addr),
            msg=f'Threads: {self.server._client_threads}',
        )
