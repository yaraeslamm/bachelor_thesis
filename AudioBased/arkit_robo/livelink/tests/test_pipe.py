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


class TestLivelinkPipe(omni.kit.test.AsyncTestCase):

    async def setUp(self):
        import omni.usd
        await omni.usd.get_context().new_stage_async()
        from omni.avatar.livelink.scripts import pipe

        self.graph = pipe.get_or_create_graph('TestGraph')
        self.graph_path = self.graph.get_path_to_graph()

    async def tearDown(self):
        import omni.usd
        omni.usd.get_context().new_stage()
        await omni.usd.get_context().new_stage_async()

        self.graph = None

    async def test_create_graph(self):
        import omni.graph.core as og
        from omni.avatar.livelink.scripts import pipe

        graph = pipe.get_or_create_graph('TestGraph2')

        self.assertTrue(graph.is_valid())
        self.assertEqual(type(graph), og.Graph)

        graph2 = pipe.get_or_create_graph('TestGraph')
        self.assertEqual(graph2, self.graph)

    async def test_create_graph_with_slash(self):
        from omni.avatar.livelink.scripts import pipe

        graph = pipe.get_or_create_graph('/TestGraph')
        self.assertEqual(graph, self.graph)

    async def test_undo_create_graph(self):
        import omni.kit.undo as undo
        import omni.usd
        from omni.avatar.livelink.scripts import pipe

        stage = omni.usd.get_context().get_stage()
        graph = pipe.get_or_create_graph('TestGraph2')

        prim = stage.GetPrimAtPath('/TestGraph2')
        self.assertTrue(prim.IsValid())
        undo.undo()
        prim = stage.GetPrimAtPath('/TestGraph2')
        self.assertFalse(prim.IsValid())

    async def test_create_node(self):
        import omni.graph.core as og
        from omni.avatar.livelink.scripts import pipe

        node = pipe.create_node(self.graph_path, 'omni.graph.nodes.WritePrim')
        await og.Controller().evaluate()

        self.assertTrue(node.is_valid())
        self.assertEqual(type(node), og.Node)

    async def test_create_node_with_name(self):
        import omni.graph.core as og
        from omni.avatar.livelink.scripts import pipe

        node = pipe.create_node(
            self.graph_path, 'omni.graph.nodes.WritePrim', name='TestWrite')
        await og.Controller().evaluate()

        self.assertIn('TestWrite', node.get_prim_path())

    async def test_create_node_with_stage(self):
        import omni.usd
        import omni.graph.core as og
        from omni.avatar.livelink.scripts import pipe

        stage = omni.usd.get_context().get_stage()
        node = pipe.create_node(self.graph_path, 'omni.graph.nodes.WritePrim', stage=stage)
        await og.Controller().evaluate()

        prim = stage.GetPrimAtPath(node.get_prim_path())
        self.assertTrue(prim.IsValid())

    async def test_undo_create_node(self):
        import omni.kit.undo as undo
        import omni.usd
        import omni.graph.core as og
        from omni.avatar.livelink.scripts import pipe

        stage = omni.usd.get_context().get_stage()
        node = pipe.create_node(self.graph_path, 'omni.graph.nodes.WritePrim')
        await og.Controller().evaluate()

        prim = stage.GetPrimAtPath(f'{self.graph_path}/WritePrim')
        self.assertTrue(prim.IsValid())
        undo.undo()
        prim = stage.GetPrimAtPath(f'{self.graph_path}/WritePrim')
        self.assertFalse(prim.IsValid())

    # TODO: add testing_scripts for add_receive_blendshape_pipe()
