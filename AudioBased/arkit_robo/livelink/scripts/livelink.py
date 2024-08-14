# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import json
import typing

from protocol import BlockProtocol, pack_block_data

WeightsType = typing.List[float]
ControlsType = typing.List[str]


class LivelinkReceiveProtocol(BlockProtocol):
    """Livelink protocol handler to receive data
    """

    def get_next_as_json(self):
        raw_data = self.get_next()
        return json.loads(raw_data)


class LivelinkSendProtocol:
    """Livelink protocol handler to send data
    """
    def __init__(self, subject: str, face_controls: ControlsType = None, body_controls: ControlsType = None):
        self.subject = subject
        self.face_controls = face_controls
        self.body_controls = body_controls

    def build_data(self, face_weights: WeightsType = None, body_weights: WeightsType = None):
        out_dict = self.build_dict(face_weights, body_weights)
        out_data = self.pack_data(out_dict)
        return out_data

    def build_dict(self, face_weights: WeightsType = None, body_weights: WeightsType = None):
        if not face_weights and not body_weights:
            return {}

        face_dict = {}
        if face_weights:
            face_dict = self._build_part_dict(face_weights, self.face_controls)

        body_dict = {}
        if body_weights:
            body_dict = self._build_part_dict(body_weights, self.body_controls)

        out_dict = {
            self.subject: {
                'Facial': face_dict,
                'Body': body_dict,  # placeholder
            }
        }
        return out_dict

    def _build_part_dict(self, weights: WeightsType, controls: ControlsType):
        data = {
            'Names': controls,
            'Weights': weights,
        }
        return data

    @staticmethod
    def pack_data(data: dict):
        """Convert to a json serialized bytes block

        Args:
            data: (dict) a data to serialize in json format

        Returns:
            (bytes) ready-to-send bytes sequence
        """
        frame_data = json.dumps(data, separators=(",", ":"))
        return pack_block_data(frame_data)
