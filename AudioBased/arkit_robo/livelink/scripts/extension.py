# Copyright (c) 2018-2022, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import carb
import omni.ext
import omni.usd

from omni.audio2face.player_deps import import_a2f_audio

from .commands import AddBlendshapeReceiveSetup
from .protocol import BlockProtocol, pack_block_data
from .livelink import (
    LivelinkReceiveProtocol, LivelinkSendProtocol,
    WeightsType, ControlsType,
)
from .server import ThreadedServer
from .livelinkreceiver import LivelinkServer, LivelinkReceiver
from .burst import FORMAT_AUDIO_HEADER, REGEX_AUDIO_HEADER, EOS

EXTENSION_NAME = "Avatar Livelink"

_EXT = None

a2f_audio = import_a2f_audio()


class AvatarLivelinkExtension(omni.ext.IExt):

    def get_name(self):
        return EXTENSION_NAME

    def __init__(self):
        super().__init__()

    def on_startup(self, ext_id):
        global _EXT
        _EXT = self
        try:
            # (ui) load property view widget
            from omni.anim.shared.ui.scripts.ognNodePropertyWidget import (
                register_property_widget,
            )
            from .property_widgets import floatarraytuner
            register_property_widget(floatarraytuner.FloatArrayTunerPropertyWidget)
        except ImportError as exc:
            carb.log_warn(f'Cannot import property widgets. {exc}')
            pass

    def on_shutdown(self):
        global _EXT
        _EXT = None
        try:
            # (ui) unload property view widget
            from omni.anim.shared.ui.scripts.ognNodePropertyWidget import (
                unregister_property_widget,
            )
            from .property_widgets import floatarraytuner
            unregister_property_widget(floatarraytuner.FloatArrayTunerPropertyWidget)
        except ImportError as exc:
            carb.log_warn(f'Cannot import property widgets. {exc}')
            pass


def get_ext() -> AvatarLivelinkExtension:
    global _EXT
    return _EXT
