# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
This is the implementation of the OGN node defined in Livelink.ogn
"""
import re

import carb

# Array or tuple values are accessed as numpy arrays so you probably need this import
import numpy as np
import numpy.typing as npt
import omni.graph.core as og


class ReceiveAudioStreamNode:
    """Receive Livelink data through Socket connection.
    """
    @staticmethod
    def internal_state():
        """Returns an object that will contain per-node state information"""
        from omni.avatar.livelink.scripts.audioreceiver import BurstAudioReceiver
        return BurstAudioReceiver()

    @staticmethod
    def initialize(context, node):
        pass

    @staticmethod
    def release(node):
        pass

    @staticmethod
    def compute(db) -> bool:
        """Compute the outputs from the current input"""

        internal = db.internal_state

        if db.inputs.activate:
            if not internal.is_running():
                try:
                    host = db.inputs.host
                    port = db.inputs.port
                    timeout = db.inputs.timeout
                    if timeout <= 0:
                        timeout = None
                    internal.start(host=host, port=port, timeout=timeout)
                except OSError:
                    # likely the socket is timed out
                    # writing back db.inputs may cause off-sync from property widget
                    db.inputs.activate = False
                    return False
            for _ in range(internal.has_received()):
                internal.download_received()
                break
        elif internal.is_running():
            internal.stop()

        db.outputs.address = internal.url
        db.outputs.connected = [f'{a[0]}:{a[1]}' for a in internal.list_client_addresses()]
        db.outputs.playing = [f'{a[0]}:{a[1]}' for a in internal.actives]
        if internal.play_times:
            db.outputs.time = max(internal.play_times.values())

        return True
