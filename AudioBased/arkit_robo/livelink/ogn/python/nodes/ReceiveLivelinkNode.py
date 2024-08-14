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


class ReceiveLivelinkNode:
    """Receive Livelink data through Socket connection.
    """
    @staticmethod
    def internal_state():
        """Returns an object that will contain per-node state information"""
        from omni.avatar.livelink.scripts.livelinkreceiver import LivelinkReceiver
        return LivelinkReceiver()

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

        face_filter = db.inputs.face_filter

        if not internal.face_filter or internal.face_filter.pattern != face_filter:
            try:
                internal.face_filter = re.compile(face_filter)
            except re.error:
                carb.log_warn(f'Filter is not a valid regular expression: "{face_filter}". Using default.')
                cur_regex = internal.face_filter
                db.inputs.face_filter = cur_regex.pattern if cur_regex else ''

        if db.inputs.activate:
            if not internal.is_running():
                try:
                    host = db.inputs.livelink_host
                    port = db.inputs.livelink_port
                    timeout = db.inputs.timeout
                    if timeout <= 0:
                        timeout = None
                    internal.start(host=host, port=port, timeout=timeout)
                except OSError:
                    # likely the socket is timed out
                    db.inputs.activate = False  # writing back db.inputs may cause off-sync from property widget
                    return False

            subject = db.inputs.livelink_subject
            track_time = db.inputs.time
            for _ in range(internal.has_received()):
                internal.download_received()
                break

            received = internal.get_received(subject, track_time) or {}
            if received:
                facial = received.get('Facial', {'Names': [], 'Weights': []})
                # filter weights
                if internal.face_filter:
                    names, weights = internal.filter_weights(
                        facial['Names'], facial['Weights'], internal.face_filter)
                else:
                    names, weights = facial['Names'], facial['Weights']
                db.outputs.subjects = internal.subjects
                db.outputs.face_weights = weights
                db.outputs.face_names = names
        elif internal.is_running():
            internal.stop()

        db.outputs.address = internal.url
        db.outputs.connected = [f'{a[0]}:{a[1]}' for a in internal.list_client_addresses()]

        return True
