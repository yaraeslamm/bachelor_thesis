import asyncio

import carb
import omni.kit.commands
import omni.kit.undo
import omni.usd


class AddBlendshapeReceiveSetup(omni.kit.commands.Command):
    """Add Blendshape SkelAnimation Setup with Receive Livelink
    """
    def __init__(self, driven_mesh, graph_name='avatar_stream'):
        """
        Args:
            driven_mesh: (str) A prim path of the blendshape target mesh.

        Keywords:
            graph_name: (str) A prim path of the OmniGraph.
        """
        self._driven = driven_mesh
        self._graph_name = graph_name
        self._notifications = []
        super().__init__()

    def do(self):
        from .pipe import is_valid_prim_path, add_blendshape_receive_pipe

        stage = omni.usd.get_context().get_stage()

        if not is_valid_prim_path(self._driven, prim_type='Mesh', stage=stage):
            msg = "Please specify a valid Blendshape Mesh"
            carb.log_error(msg)
            try:
                import omni.kit.notification_manager as nm
            except ImportError:
                # gui is unavailable
                pass
            else:
                message = str(msg)
                notification = nm.post_notification(
                    message,
                    hide_after_timeout=False,
                    status=nm.NotificationStatus.WARNING,
                    button_infos=[nm.NotificationButtonInfo("OK")]
                )
                self._notifications.append(notification)
            return

        # Start Undo Group
        omni.kit.undo.begin_group()

        # store current selected prims to be used in the selection command later
        selected_prims = omni.usd.get_context().get_selection().get_selected_prim_paths()

        bs_receive_node = add_blendshape_receive_pipe(self._driven, graph_name=self._graph_name)

        omni.kit.commands.execute(
            "SelectPrimsCommand",
            old_selected_paths=selected_prims,
            new_selected_paths=[bs_receive_node.get_prim_path()],
            expand_in_stage=True,
        )

        # End Undo Group
        omni.kit.undo.end_group()

        return bs_receive_node
