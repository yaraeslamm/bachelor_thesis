# Copyright (c) 2023, NVIDIA CORPORATION.  All rights reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
import os
import json
import asyncio
import tempfile
from typing import List
import numpy as np

from pxr import Sdf, Tf, Trace, Usd, UsdUtils

import carb
import omni.ui as ui
import omni.kit.undo
import omni.graph.core as og
from omni.kit.window.file_exporter import get_file_exporter
from omni.kit.window.popup_dialog import MessageDialog
from omni.anim.shared.ui.scripts.ognNodePropertyWidget import (
    OgnNodePropertyWidget,
)

from omni.avatar.livelink.scripts.pipe import set_property
from omni.avatar.livelink.scripts import fileio

# Styles are from audio2face.ui.common
ELEM_MARGIN = 4
BTN_WIDTH = 32
StatusSecondaryStyle = {"font_size": 14, "color": 0xFFAAAAAA}
LABEL_WIDTH = 160
LABEL_STYLE = {"font_size": 14, "color": 0xFFCCCCCC, "margin_width": 4}
TREE_STYLE = {
    "TreeView.Item": {"margin": 4},
    "TreeView.Header": {"margin_width": 1, "font_size": 14}
}

NODE_TYPE = "omni.avatar.FloatArrayTuner"
NODE_NAME = "Float Array Tuner"


class FloatArrayTunerPropertyWidget(OgnNodePropertyWidget):

    node_type = NODE_TYPE
    node_name = NODE_NAME

    def __init__(self, title: str, collapsed: bool):
        super().__init__(title=title, collapsed=collapsed, node_type=NODE_TYPE)

        self.pause_reload = False

        self._dlg_save_preset = None
        self._dlg_load_preset = None
        self._cur_dir = ''
        self._popups = []

    @property
    def prim_path(self):
        """
        Returns:
            (str) prim path of the last selected node
        """
        if not len(self._payload):
            return
        return self._payload[-1]

    @property
    def prim(self):
        """
        Returns:
            (omni.usd.Prim) prim of the last selected node
        """
        if not len(self._payload):
            return
        return og.ObjectLookup.prim(self._payload[-1])

    @property
    def prims(self):
        """
        Returns:
            (list[Prim]) selected prims
        """
        if not len(self._payload):
            return []
        return [og.ObjectLookup.prim(p) for p in self._payload]

    @property
    def node(self):
        """
        Returns:
            (omni.graph.Node) the last selected node
        """
        if not len(self._payload):
            return
        return og.ObjectLookup.node(self._payload[-1])

    def build_items(self):
        """Build widget
        """
        if not len(self._payload):
            return

        if self.prim.GetTypeName() != "OmniGraphNode":
            return
        if self.node.get_type_name() != NODE_TYPE:
            return

        stage = self.prim.GetStage()
        if not stage:
            return

        if self._listener:
            self._listener.Revoke()
        self._listener = Tf.Notice.Register(
            Usd.Notice.ObjectsChanged, self._on_usd_changed, stage)

        with ui.VStack(spacing=ELEM_MARGIN):
            self.scroll_frame = ui.ScrollingFrame(
                height=300,
                horizontal_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_OFF,
                vertical_scrollbar_policy=ui.ScrollBarPolicy.SCROLLBAR_ALWAYS_ON,
                style_type_name_override="TreeView",
                style={"Field": {"background_color": 0xFF000000}},
            )
            with self.scroll_frame:
                self._name_value_model = NamedMappingModel()
                self._name_value_delegate = EditMappingDelegate(self)
                self._tree = ui.TreeView(
                    self._name_value_model,
                    delegate=self._name_value_delegate,
                    root_visible=False,
                    header_visible=True,
                    column_widths=[
                        ui.Fraction(0.10),
                        ui.Fraction(0.50),
                        ui.Fraction(0.20),
                        ui.Fraction(0.20)
                    ],
                    columns_resizable=True,
                    style=TREE_STYLE,
                )
            btn_add_element = ui.Button(
                "ADD ELEMENT", tooltip="Add a new element to the list",
            )
            btn_add_element.set_clicked_fn(
                self._on_click_add_element
            )
            btn_remove_element = ui.Button(
                "REMOVE ELEMENT", tooltip="Remove selected elements the list",
            )
            btn_remove_element.set_clicked_fn(
                self._on_click_remove_element
            )
            with ui.HStack(spacing=ELEM_MARGIN):
                ui.Label(
                    'SET SELECTED GAINS',
                    tooltip='Set gain of selected items.',
                    style=StatusSecondaryStyle,
                    width=LABEL_WIDTH
                )
                btn_gain_min = ui.Button(
                    "0.0", tooltip="Set to 0.0",
                )
                btn_gain_min.set_clicked_fn(
                    lambda: self._on_click_set_gains(0.0)
                )
                btn_gain_max = ui.Button(
                    "1.0", tooltip="Set to 1.0",
                )
                btn_gain_max.set_clicked_fn(
                    lambda: self._on_click_set_gains(1.0)
                )
                btn_gain_reset = ui.Button(
                    "RESET", tooltip="Set to default(state:gain_defaults)",
                )
                btn_gain_reset.set_clicked_fn(
                    self._on_click_reset_gains,
                )
            with ui.HStack(spacing=ELEM_MARGIN):
                ui.Label(
                    'SET SELECTED OFFSETS',
                    tooltip='Set offset of selected items',
                    style=StatusSecondaryStyle,
                    width=LABEL_WIDTH
                )
                btn_offset_min = ui.Button(
                    "0.0", tooltip="Set to 0.0",
                )
                btn_offset_min.set_clicked_fn(
                    lambda: self._on_click_set_offsets(0.0)
                )
                btn_offset_max = ui.Button(
                    "1.0", tooltip="Set to 1.0",
                )
                btn_offset_max.set_clicked_fn(
                    lambda: self._on_click_set_offsets(1.0)
                )
                btn_offset_reset = ui.Button(
                    "RESET", tooltip="Set to default(state:offset_defaults)",
                )
                btn_offset_reset.set_clicked_fn(
                    self._on_click_reset_offsets,
                )
            with ui.HStack(spacing=ELEM_MARGIN):
                    self._btn_load_reset = ui.Button(
                        "LOAD PRESET", tooltip="Load Face Tuner preset from a .json file"
                    )
                    self._btn_load_reset.set_clicked_fn(self._on_bs_preset_load_clicked)
                    self._btn_save_preset = ui.Button(
                        "SAVE PRESET", tooltip="Save Face Tuner preset as a .json file"
                    )
                    self._btn_save_preset.set_clicked_fn(self._on_bs_preset_save_clicked)
        self._load_mapping()

    def _load_mapping(self):
        """Load attributes and create tree items
        """
        names = self.prim.GetAttribute('inputs:names').Get()
        selected_items = self._tree.selection
        selected = [it.index_model.as_int for it in selected_items]

        def _init_array(attr_name, cur_vals, ones=False):
            if ones:
                vals = np.ones(len(names))
            else:
                vals = np.zeros(len(names))
            vals[:len(cur_vals)] = cur_vals[:]
            # og.Controller(f"{self._payload[-1]}.inputs:{name}").set(val)
            attr = self.prim.GetAttribute(attr_name)
            set_property(attr.GetPath(), vals)
            return vals

        def _iter_map():
            gains = self.prim.GetAttribute('inputs:gains').Get()
            offsets = self.prim.GetAttribute('inputs:offsets').Get()
            gain_defs = self.prim.GetAttribute('state:gain_defaults').Get()
            offs_defs = self.prim.GetAttribute('state:offset_defaults').Get()
            for idx, name in enumerate(names):
                yield idx
                yield name
                # gain
                if gains is None or idx >= len(gains):
                    gains = _init_array('inputs:gains', gains, ones=True)
                yield gains[idx]
                # offset
                if offsets is None or idx >= len(offsets):
                    offsets = _init_array('inputs:offsets', offsets)
                yield offsets[idx]
                # gain default
                if gain_defs is None or idx >= len(gain_defs):
                    gain_defs = _init_array('state:gain_defaults', gain_defs, ones=True)
                yield gain_defs[idx]
                # offset default
                if offs_defs is None or idx >= len(offs_defs):
                    offs_defs = _init_array('state:offset_defaults', offs_defs)
                yield offs_defs[idx]
            return

        try:
            # restore selection
            self.pause_reload = True
            self._name_value_model.set_values(*_iter_map())
            new_items = self._name_value_model.get_item_children(None)
            new_selection = [it for i, it in enumerate(new_items) if i in selected]
            self._tree.selection = new_selection
        finally:
            self.pause_reload = False

    def _on_usd_changed(self, notice, stage):
        if self.pause_reload:
            return

        carb.profiler.begin(1, "FloatArrayTunerPropertyWidget._on_usd_changed")
        try:
            if stage != self._payload.get_stage():
                return

            if len(self._payload) == 0:
                return

            # Widget is pending rebuild, no need to check for dirty
            if self._pending_rebuild_task is not None:
                return

            prim = stage.GetPrimAtPath(self._payload[0])
            if not prim.IsValid():
                return

            for attr_name in ('inputs:names', 'inputs:gains', 'inputs:offsets'):
                attr = prim.GetAttribute(attr_name)
                if not notice.AffectedObject(attr):
                    continue
                self._load_mapping()
                break
        finally:
            carb.profiler.end(1)

    def _on_click_reset_gains(self):
        for item in self._tree.selection:
            item.value_model2.set_value(item.value_model4.as_float)

    def _on_click_reset_offsets(self):
        for item in self._tree.selection:
            item.value_model3.set_value(item.value_model5.as_float)

    def _on_click_set_gains(self, val=0.0):
        for item in self._tree.selection:
            item.value_model2.set_value(val)

    def _on_click_set_offsets(self, val=0.0):
        for item in self._tree.selection:
            item.value_model3.set_value(val)

    def _on_click_add_element(self):
        attr = self.prim.GetAttribute('inputs:names')
        if attr.HasValue():
            names = list(attr.Get())
        else:
            names = []
        names += [f'{len(names)}']
        set_property(attr.GetPath(), names)

    def _on_click_remove_element(self):
        names_attr = self.prim.GetAttribute('inputs:names')
        if not names_attr.HasValue():
            # nothing to delete
            return
        items = self._tree.selection
        if len(items) < 1:
            # nothing to delete
            return

        selected = [it.index_model.as_int for it in items]

        value_attributes = [
            'inputs:gains', 'inputs:offsets',
            'state:gain_defaults', 'state:offset_defaults'
        ]
        omni.kit.undo.begin_group()
        old_names = list(names_attr.Get())
        new_names = [x for i, x in enumerate(old_names) if i not in selected]
        set_property(names_attr.GetPath(), new_names)
        for attr_name in value_attributes:
            attr = self.prim.GetAttribute(attr_name)
            if attr.HasValue():
                old_vals = list(attr.Get())
            else:
                old_vals = []
            new_vals = [x for i, x in enumerate(old_vals) if i not in selected]
            set_property(attr.GetPath(), new_vals)
        omni.kit.undo.end_group()

    def _on_bs_preset_save_clicked(self):
        def on_click_save(
            filename: str, dirname: str,
            extension: str = '', selections: List[str] = (),
        ):
            asyncio.ensure_future(self.save_preset(filename, dirname))

        if self._dlg_save_preset is None:
            self._dlg_save_preset = get_file_exporter()

        self._dlg_save_preset.show_window(
            title="Save Float Array Tuner Preset",
            export_button_label="Save",
            export_handler=on_click_save,
            show_only_folders=False,
            enable_filename_input=True,
            file_extension_types=[(".json", ".json Files (*.json)")],
            filename_url=self._cur_dir,
        )

    async def save_preset(self, filename: str, dirname: str):
        """Save preset and show dialog messages.

        Args:
            filename: (str) a file name to save
            dirname: (str) a dir path to save
        """
        import omni.client
        if not filename.lower().endswith('.json'):
            filename = f"{filename}.json"
        filepath = omni.client.combine_urls(dirname + "/", filename)
        try:
            # NOTE: need confirmation dialog?
            result = await fileio.save_tuner_preset(filepath, self.prim_path)
        except fileio.OmniClientError as exc:
            # show dialog for error
            msg = f"Could not save a file.\n{exc}"
            dlg = MessageDialog(
                title="File Save Error",
                message=msg,
                ok_handler=lambda *x: dlg.hide(),
                disable_cancel_button=True,
            )
            dlg.show()
            self._popups.append(dlg)
            raise
        else:
            if result is True or result == omni.client.Result.OK:
                carb.log_info(f'File Saved: {filepath}')
            else:
                msg = f"Could not save a file to the path.\n{filepath}"
                dlg = MessageDialog(
                    title="File Save Failed",
                    message=msg,
                    ok_handler=lambda *x: dlg.hide(),
                    disable_cancel_button=True,
                )
                dlg.show()
                self._popups.append(dlg)
        self._cur_dir = dirname
        return filepath

    def _on_bs_preset_load_clicked(self):
        def on_click_load(
            filename: str, dirname: str,
            extension: str = '', selections: List[str] = (),
        ):
            asyncio.ensure_future(self.load_preset(filename, dirname, extension))

        if self._dlg_load_preset is None:
            self._dlg_load_preset = get_file_exporter()

        self._dlg_load_preset.show_window(
            title="Load Float Array Tuner Preset",
            export_button_label="Load",
            export_handler=on_click_load,
            show_only_folders=False,
            enable_filename_input=True,
            file_extension_types=[(".json", ".json Files (*.json)")],
            filename_url=self._cur_dir,
        )

    async def load_preset(self, filename: str, dirname: str, extension='.json'):
        """Save preset and show dialog messages.

        Args:
            filename: (str) a file name to save
            dirname: (str) a dir path to save
        """
        import omni.client
        filepath = omni.client.combine_urls(dirname + "/", f'{filename}{extension}')
        try:
            result = await fileio.load_tuner_preset(filepath, self.prim_path)
        except fileio.OmniClientError as exc:
            # show dialog for error
            msg = f"Could not load a file.\n{exc}"
            dlg = MessageDialog(
                title="File Load Error",
                message=msg,
                ok_handler=lambda *x: dlg.hide(),
                disable_cancel_button=True,
            )
            dlg.show()
            self._popups.append(dlg)
            raise
        else:
            if result is True or result == omni.client.Result.OK:
                carb.log_info(f'File Loaded: {filepath}')
            else:
                msg = f"Could not load a file from the path.\n{filepath}"
                dlg = MessageDialog(
                    title="File Load Failed",
                    message=msg,
                    ok_handler=lambda *x: dlg.hide(),
                    disable_cancel_button=True,
                )
                dlg.show()
                self._popups.append(dlg)
        self._cur_dir = dirname
        return filepath


class NamedMappingItem(ui.AbstractItem):
    """Single mapping item of the model"""

    def __init__(self, index, text, value1=1.0, value2=0.0, value3=1.0, value4=0.0):
        super().__init__()
        self.index_model = ui.SimpleIntModel(index)
        self.name_model = ui.SimpleStringModel(text)
        self.value_model2 = ui.SimpleFloatModel(value1)
        self.value_model3 = ui.SimpleFloatModel(value2)
        self.value_model4 = ui.SimpleFloatModel(value3)
        self.value_model5 = ui.SimpleFloatModel(value4)

    def __repr__(self):
        msg = (
            f'"{self.index_model.as_string} {self.name_model.as_string}'
            f' {self.value_model2.as_string}(default: {self.value_model4.as_string})'
            f' {self.value_model3.as_string}(default: {self.value_model5.as_string})"'
        )
        return msg


class NamedMappingModel(ui.AbstractItemModel):
    """Represents the model for name-mapping table.

    Examples:
        my_list = ["Hello", 1.0, 0.0, 1.0, 0.0, "World", 0.5, 0.0, 1.0, 0.0]
        model = NamedMappingModel(*my_list)
        ui.TreeView(model)
    """

    def __init__(self, *args):
        super().__init__()
        self._children = []
        self._set_values(args)

    def set_values(self, *args):
        """Define the children based on the new value pairs"""
        # [1, 2, 3, 4] -> [(1, 2), (3, 4)]
        self._set_values(args)

    def _set_values(self, args):
        regrouped = zip(*(iter(args),) * 6)
        self._children = [NamedMappingItem(*t) for t in regrouped]
        self._item_changed(None)

    def get_item_children(self, item):
        """Returns all the children when the widget asks it."""
        if item is not None:
            # Since we are doing a flat list, we return the children of root only.
            # If it's not root we return.
            return []
        return self._children

    def get_item_value_model_count(self, item):
        """The number of (visible) columns"""
        return 4

    def get_item_value_model(self, item, column_id):
        """Return value model.
        """
        if item is None:
            return
        elif column_id == 0:
            return item.index_model
        elif column_id in (2, 3, 4, 5):
            return getattr(item, f'value_model{column_id}')
        else:
            return item.name_model


class EditMappingDelegate(ui.AbstractItemDelegate):
    """Delegate is the representation layer. TreeView calls the methods
    of the delegate to create custom widgets for each item.
    """

    def __init__(self, widget):
        super().__init__()
        self.subscription = None
        self.widget = widget
        self.undo = {}

    def build_branch(self, model, item, column_id, level, expanded):
        """Create a branch widget that opens or closes subtree"""
        pass

    def build_header(self, column_id):
        if column_id == 0:
            ui.Label(" Id", style_type_name_override="TreeView.Header")
        elif column_id == 1:
            ui.Label(" Label", style_type_name_override="TreeView.Header")
        elif column_id == 2:
            ui.Label(" Gain", style_type_name_override="TreeView.Header")
        elif column_id == 3:
            ui.Label(" Offset", style_type_name_override="TreeView.Header")
        else:
            ui.Label("", style_type_name_override="TreeView.Header")

    def build_widget(self, model, item, column_id, level, expanded):
        """Create a widget per column per item"""
        stack = ui.ZStack(height=20)
        with stack:
            value_model = model.get_item_value_model(item, column_id)
            if column_id == 0:
                label = ui.Label(value_model.as_string, style=LABEL_STYLE)
            elif column_id == 1:
                label = ui.Label(value_model.as_string, style=LABEL_STYLE)
                field = ui.StringField(value_model, visible=False)
                stack.set_mouse_double_clicked_fn(
                    lambda x, y, b, m, f=field, l=label, i=item: self.on_double_click(b, f, l, i)
                )
            else:
                field = ui.FloatDrag(value_model, visible=True)
                field.model.add_begin_edit_fn(
                    lambda m, f=field, i=item, c=column_id: self.on_value_changed(m, f, i, c, begin=True)
                )
                field.model.add_value_changed_fn(
                    lambda m, f=field, i=item, c=column_id: self.on_value_changed(m, f, i, c)
                )
                field.model.add_end_edit_fn(
                    lambda m, f=field, i=item, c=column_id: self.on_value_changed(m, f, i, c, final=True)
                )

    def on_value_changed(self, model, field, item, column, final=False, begin=False):
        """Called when the user is editing the item"""
        prim = self.widget.prim
        if column == 2:
            attr = prim.GetAttribute('inputs:gains')
        elif column == 3:
            attr = prim.GetAttribute('inputs:offsets')
        else:
            return

        vals = attr.Get()
        if begin:
            self.undo[model] = [v for v in vals]
            self.widget.pause_reload = True

        idx = item.index_model.as_int
        vals[idx] = model.as_float
        if final:
            self.widget.pause_reload = False
            set_property(attr.GetPath(), vals, prev=self.undo.pop(model))
        else:
            attr.Set(vals)

    def on_double_click(self, button, field, label, item):
        """Called when the user double-clicked the item in TreeView"""
        if button != 0:
            return

        # Make editable field visible when double clicked
        field.visible = True
        field.focus_keyboard()
        # When editing is finished (enter pressed of mouse clicked outside of the viewport)
        self.subscription = field.model.subscribe_end_edit_fn(
            lambda m, f=field, l=label, i=item: self.on_name_changed(m, f, l, i)
        )

    def on_name_changed(self, model, field, label, item):
        """Called when the user finished editing the name"""
        prim = self.widget.prim
        attr = prim.GetAttribute('inputs:names')
        vals = attr.Get()
        idx = item.index_model.as_int
        vals[idx] = model.as_string
        set_property(attr.GetPath(), vals)

        field.visible = False
        label.text = model.as_string
        self.subscription = None
