"""Support for simplified access to data on nodes of type omni.avatar.FloatArrayTuner

Manage a custom tuner array with gain and offset. Output array has the same length as names.
"""

import numpy
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class FloatArrayTunerNodeDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.avatar.FloatArrayTuner

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.array
            inputs.gains
            inputs.names
            inputs.offsets
        Outputs:
            outputs.array
        State:
            state.gain_defaults
            state.offset_defaults
    """

    # Imprint the generator and target ABI versions in the file for JIT generation
    GENERATOR_VERSION = (1, 31, 1)
    TARGET_VERSION = (2, 107, 4)

    # This is an internal object that provides per-class storage of a per-node data dictionary
    PER_NODE_DATA = {}

    # This is an internal object that describes unchanging attributes in a generic way
    # The values in this list are in no particular order, as a per-attribute tuple
    #     Name, Type, ExtendedTypeIndex, UiName, Description, Metadata,
    #     Is_Required, DefaultValue, Is_Deprecated, DeprecationMsg
    # You should not need to access any of this data directly, use the defined database interfaces
    INTERFACE = og.Database._get_interface([
        ('inputs:array', 'float[]', 0, 'Array', 'Input array', {}, True, [], False, ''),
        ('inputs:gains', 'float[]', 0, 'Gains', 'Scale weights', {ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('inputs:names', 'token[]', 0, 'Names', 'Element names. Defines the output size.', {ogn.MetadataKeys.HIDDEN: 'True', ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('inputs:offsets', 'float[]', 0, 'Offsets', 'Offset weights after scale', {ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('outputs:array', 'float[]', 0, 'Array', 'Output array', {}, True, None, False, ''),
        ('state:gain_defaults', 'float[]', 0, 'Gain Defaults', 'Gain default values', {ogn.MetadataKeys.HIDDEN: 'True', ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('state:offset_defaults', 'float[]', 0, 'Offset Defaults', 'Offset default values', {ogn.MetadataKeys.HIDDEN: 'True', ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
    ])

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = { }
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = []
            self._batchedReadValues = []

        @property
        def array(self):
            data_view = og.AttributeValueHelper(self._attributes.array)
            return data_view.get()

        @array.setter
        def array(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.array)
            data_view = og.AttributeValueHelper(self._attributes.array)
            data_view.set(value)
            self.array_size = data_view.get_array_size()

        @property
        def gains(self):
            data_view = og.AttributeValueHelper(self._attributes.gains)
            return data_view.get()

        @gains.setter
        def gains(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.gains)
            data_view = og.AttributeValueHelper(self._attributes.gains)
            data_view.set(value)
            self.gains_size = data_view.get_array_size()

        @property
        def names(self):
            data_view = og.AttributeValueHelper(self._attributes.names)
            return data_view.get()

        @names.setter
        def names(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.names)
            data_view = og.AttributeValueHelper(self._attributes.names)
            data_view.set(value)
            self.names_size = data_view.get_array_size()

        @property
        def offsets(self):
            data_view = og.AttributeValueHelper(self._attributes.offsets)
            return data_view.get()

        @offsets.setter
        def offsets(self, value):
            if self._setting_locked:
                raise og.ReadOnlyError(self._attributes.offsets)
            data_view = og.AttributeValueHelper(self._attributes.offsets)
            data_view.set(value)
            self.offsets_size = data_view.get_array_size()

        def _prefetch(self):
            readAttributes = self._batchedReadAttributes
            newValues = _og._prefetch_input_attributes_data(readAttributes)
            if len(readAttributes) == len(newValues):
                self._batchedReadValues = newValues

    class ValuesForOutputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = { }
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.array_size = None
            self._batchedWriteValues = { }

        @property
        def array(self):
            data_view = og.AttributeValueHelper(self._attributes.array)
            return data_view.get(reserved_element_count=self.array_size)

        @array.setter
        def array(self, value):
            data_view = og.AttributeValueHelper(self._attributes.array)
            data_view.set(value)
            self.array_size = data_view.get_array_size()

        def _commit(self):
            _og._commit_output_attributes_data(self._batchedWriteValues)
            self._batchedWriteValues = { }

    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.gain_defaults_size = 0
            self.offset_defaults_size = 0

        @property
        def gain_defaults(self):
            data_view = og.AttributeValueHelper(self._attributes.gain_defaults)
            self.gain_defaults_size = data_view.get_array_size()
            return data_view.get()

        @gain_defaults.setter
        def gain_defaults(self, value):
            data_view = og.AttributeValueHelper(self._attributes.gain_defaults)
            data_view.set(value)
            self.gain_defaults_size = data_view.get_array_size()

        @property
        def offset_defaults(self):
            data_view = og.AttributeValueHelper(self._attributes.offset_defaults)
            self.offset_defaults_size = data_view.get_array_size()
            return data_view.get()

        @offset_defaults.setter
        def offset_defaults(self, value):
            data_view = og.AttributeValueHelper(self._attributes.offset_defaults)
            data_view.set(value)
            self.offset_defaults_size = data_view.get_array_size()

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = FloatArrayTunerNodeDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = FloatArrayTunerNodeDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = FloatArrayTunerNodeDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):
                return get_node_type_function()
            return 'omni.avatar.FloatArrayTuner'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = FloatArrayTunerNodeDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = FloatArrayTunerNodeDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = FloatArrayTunerNodeDatabase(node)

            try:
                compute_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            FloatArrayTunerNodeDatabase._initialize_per_node_data(node)
            initialize_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):
                initialize_function(context, node)

        @staticmethod
        def release(node):
            release_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):
                release_function(node)
            FloatArrayTunerNodeDatabase._release_per_node_data(node)

        @staticmethod
        def release_instance(node, target):
            FloatArrayTunerNodeDatabase._release_per_node_instance_data(node, target)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.avatar.livelink")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Float Array Tuner")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Manage a custom tuner array with gain and offset. Output array has the same length as names.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                FloatArrayTunerNodeDatabase.INTERFACE.add_to_node_type(node_type)
                node_type.set_has_state(True)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        FloatArrayTunerNodeDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(FloatArrayTunerNodeDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.avatar.FloatArrayTuner")
