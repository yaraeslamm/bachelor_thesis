# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
"""
This is the implementation of the OGN node defined in FloatArrayTunerNode.ogn
"""
# Array or tuple values are accessed as numpy arrays so you probably need this import
import carb
import numpy as np
import omni.graph.core as og


class FloatArrayTunerNodeState:
    """Convenience class for maintaining per-node state information"""

    def __init__(self):
        """Instantiate the per-node state information.
        """
        self.array = np.zeros(0, dtype=np.float32)

    def resize_array(self, new_size: int):
        """Resize internal array
        """
        old = self.array
        self.array = np.zeros(new_size, dtype=np.float32)
        if self.array.size:
            valid = min(old.size, new_size)
            self.array[:valid] = old[:valid]
        return


class FloatArrayTunerNode:
    """Multiply and Offset values of an array.
    """
    @staticmethod
    def internal_state():
        """Returns an object that will contain per-node state information"""
        return FloatArrayTunerNodeState()

    @staticmethod
    def initialize(context, node):
        """Runs first after instancing a node"""
        pass

    @staticmethod
    def release(node):
        """Runs before deleting a node"""
        pass

    @staticmethod
    def compute(db) -> bool:
        """Compute the outputs from the current input"""
        storage = db.internal_state.array  # numpy.array[52]

        array = db.inputs.array

        names = db.inputs.names
        if storage.size != len(names):
            db.internal_state.resize_array(len(names))
            storage = db.internal_state.array

        # input
        valid_weights = min(storage.size, len(array))
        storage[:valid_weights] = array[:valid_weights]
        storage[valid_weights:] = 0.0

        # gain
        gains = db.inputs.gains
        if len(gains):
            valid_gains = min(storage.size, len(gains))
            storage[:valid_gains] *= gains[:valid_gains]

        # offset
        offsets = db.inputs.offsets
        if len(offsets):
            valid_offsets = min(storage.size, len(offsets))
            storage[:valid_offsets] += offsets[:valid_offsets]

        db.outputs.array = storage

        return True
