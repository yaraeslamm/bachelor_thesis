"""Support for simplified access to data on nodes of type omni.avatar.ReceiveAudioStream

Receive audio through network connection.
"""

import numpy
import sys
import traceback

import omni.graph.core as og
import omni.graph.core._omni_graph_core as _og
import omni.graph.tools.ogn as ogn



class ReceiveAudioStreamNodeDatabase(og.Database):
    """Helper class providing simplified access to data on nodes of type omni.avatar.ReceiveAudioStream

    Class Members:
        node: Node being evaluated

    Attribute Value Properties:
        Inputs:
            inputs.activate
            inputs.host
            inputs.port
            inputs.time
            inputs.timeout
        Outputs:
            outputs.address
            outputs.buffer
            outputs.connected
            outputs.playing
            outputs.time
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
        ('inputs:activate', 'bool', 0, 'Activate', 'activate livelink connection', {ogn.MetadataKeys.DEFAULT: 'false'}, True, False, False, ''),
        ('inputs:host', 'string', 0, 'Host Name', 'livelink server host name', {ogn.MetadataKeys.DEFAULT: '"0.0.0.0"'}, True, "0.0.0.0", False, ''),
        ('inputs:port', 'uint', 0, 'Port Number', 'livelink server port number', {ogn.MetadataKeys.DEFAULT: '12031'}, True, 12031, False, ''),
        ('inputs:time', 'float', 0, None, 'Reference time in seconds', {}, True, 0.0, False, ''),
        ('inputs:timeout', 'float', 0, 'Timeout', 'server timeout seconds', {ogn.MetadataKeys.DEFAULT: '0'}, True, 0, False, ''),
        ('outputs:address', 'string', 0, 'Address', 'activated server address', {ogn.MetadataKeys.DEFAULT: '""'}, True, "", False, ''),
        ('outputs:buffer', 'float[]', 0, 'Buffer', 'receiving audio buffer', {ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('outputs:connected', 'token[]', 0, 'Connected', 'hostnames of connected clients', {ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('outputs:playing', 'token[]', 0, 'Playing', 'hostnames of clients playing audio buffer.', {ogn.MetadataKeys.DEFAULT: '[]'}, True, [], False, ''),
        ('outputs:time', 'float', 0, None, 'Track time in seconds', {}, True, None, False, ''),
    ])

    @classmethod
    def _populate_role_data(cls):
        """Populate a role structure with the non-default roles on this node type"""
        role_data = super()._populate_role_data()
        role_data.inputs.host = og.AttributeRole.TEXT
        role_data.outputs.address = og.AttributeRole.TEXT
        return role_data

    class ValuesForInputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"activate", "host", "port", "time", "timeout", "_setting_locked", "_batchedReadAttributes", "_batchedReadValues"}
        """Helper class that creates natural hierarchical access to input attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self._batchedReadAttributes = [self._attributes.activate, self._attributes.host, self._attributes.port, self._attributes.time, self._attributes.timeout]
            self._batchedReadValues = [False, "0.0.0.0", 12031, 0.0, 0]

        @property
        def activate(self):
            return self._batchedReadValues[0]

        @activate.setter
        def activate(self, value):
            self._batchedReadValues[0] = value

        @property
        def host(self):
            return self._batchedReadValues[1]

        @host.setter
        def host(self, value):
            self._batchedReadValues[1] = value

        @property
        def port(self):
            return self._batchedReadValues[2]

        @port.setter
        def port(self, value):
            self._batchedReadValues[2] = value

        @property
        def time(self):
            return self._batchedReadValues[3]

        @time.setter
        def time(self, value):
            self._batchedReadValues[3] = value

        @property
        def timeout(self):
            return self._batchedReadValues[4]

        @timeout.setter
        def timeout(self, value):
            self._batchedReadValues[4] = value

        def __getattr__(self, item: str):
            if item in self.LOCAL_PROPERTY_NAMES:
                return object.__getattribute__(self, item)
            else:
                return super().__getattr__(item)

        def __setattr__(self, item: str, new_value):
            if item in self.LOCAL_PROPERTY_NAMES:
                object.__setattr__(self, item, new_value)
            else:
                super().__setattr__(item, new_value)

        def _prefetch(self):
            readAttributes = self._batchedReadAttributes
            newValues = _og._prefetch_input_attributes_data(readAttributes)
            if len(readAttributes) == len(newValues):
                self._batchedReadValues = newValues

    class ValuesForOutputs(og.DynamicAttributeAccess):
        LOCAL_PROPERTY_NAMES = {"address", "time", "_batchedWriteValues"}
        """Helper class that creates natural hierarchical access to output attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)
            self.address_size = 0
            self.buffer_size = 0
            self.connected_size = 0
            self.playing_size = 0
            self._batchedWriteValues = { }

        @property
        def buffer(self):
            data_view = og.AttributeValueHelper(self._attributes.buffer)
            return data_view.get(reserved_element_count=self.buffer_size)

        @buffer.setter
        def buffer(self, value):
            data_view = og.AttributeValueHelper(self._attributes.buffer)
            data_view.set(value)
            self.buffer_size = data_view.get_array_size()

        @property
        def connected(self):
            data_view = og.AttributeValueHelper(self._attributes.connected)
            return data_view.get(reserved_element_count=self.connected_size)

        @connected.setter
        def connected(self, value):
            data_view = og.AttributeValueHelper(self._attributes.connected)
            data_view.set(value)
            self.connected_size = data_view.get_array_size()

        @property
        def playing(self):
            data_view = og.AttributeValueHelper(self._attributes.playing)
            return data_view.get(reserved_element_count=self.playing_size)

        @playing.setter
        def playing(self, value):
            data_view = og.AttributeValueHelper(self._attributes.playing)
            data_view.set(value)
            self.playing_size = data_view.get_array_size()

        @property
        def address(self):
            value = self._batchedWriteValues.get(self._attributes.address)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.address)
                return data_view.get()

        @address.setter
        def address(self, value):
            self._batchedWriteValues[self._attributes.address] = value

        @property
        def time(self):
            value = self._batchedWriteValues.get(self._attributes.time)
            if value:
                return value
            else:
                data_view = og.AttributeValueHelper(self._attributes.time)
                return data_view.get()

        @time.setter
        def time(self, value):
            self._batchedWriteValues[self._attributes.time] = value

        def __getattr__(self, item: str):
            if item in self.LOCAL_PROPERTY_NAMES:
                return object.__getattribute__(self, item)
            else:
                return super().__getattr__(item)

        def __setattr__(self, item: str, new_value):
            if item in self.LOCAL_PROPERTY_NAMES:
                object.__setattr__(self, item, new_value)
            else:
                super().__setattr__(item, new_value)

        def _commit(self):
            _og._commit_output_attributes_data(self._batchedWriteValues)
            self._batchedWriteValues = { }

    class ValuesForState(og.DynamicAttributeAccess):
        """Helper class that creates natural hierarchical access to state attributes"""
        def __init__(self, node: og.Node, attributes, dynamic_attributes: og.DynamicAttributeInterface):
            """Initialize simplified access for the attribute data"""
            context = node.get_graph().get_default_graph_context()
            super().__init__(context, node, attributes, dynamic_attributes)

    def __init__(self, node):
        super().__init__(node)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_INPUT)
        self.inputs = ReceiveAudioStreamNodeDatabase.ValuesForInputs(node, self.attributes.inputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_OUTPUT)
        self.outputs = ReceiveAudioStreamNodeDatabase.ValuesForOutputs(node, self.attributes.outputs, dynamic_attributes)
        dynamic_attributes = self.dynamic_attribute_data(node, og.AttributePortType.ATTRIBUTE_PORT_TYPE_STATE)
        self.state = ReceiveAudioStreamNodeDatabase.ValuesForState(node, self.attributes.state, dynamic_attributes)

    class abi:
        """Class defining the ABI interface for the node type"""

        @staticmethod
        def get_node_type():
            get_node_type_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'get_node_type', None)
            if callable(get_node_type_function):
                return get_node_type_function()
            return 'omni.avatar.ReceiveAudioStream'

        @staticmethod
        def compute(context, node):
            def database_valid():
                return True
            try:
                per_node_data = ReceiveAudioStreamNodeDatabase.PER_NODE_DATA[node.node_id()]
                db = per_node_data.get('_db')
                if db is None:
                    db = ReceiveAudioStreamNodeDatabase(node)
                    per_node_data['_db'] = db
                if not database_valid():
                    per_node_data['_db'] = None
                    return False
            except:
                db = ReceiveAudioStreamNodeDatabase(node)

            try:
                compute_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'compute', None)
                if callable(compute_function) and compute_function.__code__.co_argcount > 1:
                    return compute_function(context, node)

                db.inputs._prefetch()
                db.inputs._setting_locked = True
                with og.in_compute():
                    return ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS.compute(db)
            except Exception as error:
                stack_trace = "".join(traceback.format_tb(sys.exc_info()[2].tb_next))
                db.log_error(f'Assertion raised in compute - {error}\n{stack_trace}', add_context=False)
            finally:
                db.inputs._setting_locked = False
                db.outputs._commit()
            return False

        @staticmethod
        def initialize(context, node):
            ReceiveAudioStreamNodeDatabase._initialize_per_node_data(node)
            initialize_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'initialize', None)
            if callable(initialize_function):
                initialize_function(context, node)

        @staticmethod
        def release(node):
            release_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'release', None)
            if callable(release_function):
                release_function(node)
            ReceiveAudioStreamNodeDatabase._release_per_node_data(node)

        @staticmethod
        def release_instance(node, target):
            ReceiveAudioStreamNodeDatabase._release_per_node_instance_data(node, target)

        @staticmethod
        def update_node_version(context, node, old_version, new_version):
            update_node_version_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'update_node_version', None)
            if callable(update_node_version_function):
                return update_node_version_function(context, node, old_version, new_version)
            return False

        @staticmethod
        def initialize_type(node_type):
            initialize_type_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'initialize_type', None)
            needs_initializing = True
            if callable(initialize_type_function):
                needs_initializing = initialize_type_function(node_type)
            if needs_initializing:
                node_type.set_metadata(ogn.MetadataKeys.EXTENSION, "omni.avatar.livelink")
                node_type.set_metadata(ogn.MetadataKeys.UI_NAME, "Receive Audio Stream")
                node_type.set_metadata(ogn.MetadataKeys.DESCRIPTION, "Receive audio through network connection.")
                node_type.set_metadata(ogn.MetadataKeys.EXCLUSIONS, "tests")
                node_type.set_metadata(ogn.MetadataKeys.LANGUAGE, "Python")
                ReceiveAudioStreamNodeDatabase.INTERFACE.add_to_node_type(node_type)

        @staticmethod
        def on_connection_type_resolve(node):
            on_connection_type_resolve_function = getattr(ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS, 'on_connection_type_resolve', None)
            if callable(on_connection_type_resolve_function):
                on_connection_type_resolve_function(node)

    NODE_TYPE_CLASS = None

    @staticmethod
    def register(node_type_class):
        ReceiveAudioStreamNodeDatabase.NODE_TYPE_CLASS = node_type_class
        og.register_node_type(ReceiveAudioStreamNodeDatabase.abi, 1)

    @staticmethod
    def deregister():
        og.deregister_node_type("omni.avatar.ReceiveAudioStream")
