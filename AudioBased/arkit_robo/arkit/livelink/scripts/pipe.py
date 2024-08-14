import os

import carb
import omni.graph.core as og
import omni.kit.commands
import omni.kit.undo
import omni.usd
from omni.audio2face.common import GRAPH_TYPE, get_prim_io
from pxr import Sdf, Usd

NODE_TYPE_RECEIVE_LIVELINK = 'omni.avatar.ReceiveLivelink'
NODE_TYPE_WRITE_PRIM = "omni.graph.nodes.WritePrimAttribute"
NODE_TYPE_READ_TIME = "omni.graph.nodes.ReadTime"


def add_blendshape_receive_pipe(driven: str, graph_name: str = 'avatar_stream'):
    """Create ReceiveLivelink node and SkelAnimation for a blendshape
    """
    stage = omni.usd.get_context().get_stage()

    if not is_valid_prim_path(driven, prim_type='Mesh', stage=stage):
        carb.log_error(f'Please specify a valid Driven Mesh instead of "{driven}"')
        return False

    driven_path = og.ObjectLookup.prim_path(driven)

    # TODO: remove this check or revive with a proper definition of duplication
    # check if there is receive node already
    # for prim in stage.Traverse():
    #     if prim.GetAttribute("node:type").Get() == NODE_TYPE_RECEIVE_LIVELINK:
    #         # TODO: check the target is driven
    #         log_warn(f"There is already omni.avatar.ReceiveLivelink for {driven}")
    #         return True

    # start building prims and nodes
    driven_prim = og.ObjectLookup.prim(driven_path)
    skel_path = driven_prim.GetRelationship("skel:skeleton").GetTargets()[0]
    skel_prim = stage.GetPrimAtPath(skel_path)

    # create a new skelAnimation prim and connect it
    skel_blendshape_names = driven_prim.GetAttribute("skel:blendShapes").Get()

    new_anim_path = omni.usd.get_stage_next_free_path(stage, f"{skel_path}/bs_anim", False)
    omni.kit.commands.execute(
        "CreatePrimCommand",
        prim_path=new_anim_path,
        prim_type="SkelAnimation",
        select_new_prim=True,
        attributes={},
        create_default_xform=False,
    )

    new_anim_prim = stage.GetPrimAtPath(new_anim_path)
    attr_bs = new_anim_prim.CreateAttribute(
        "blendShapes", Sdf.ValueTypeNames.TokenArray, False)
    attr_bs.Set(skel_blendshape_names)
    new_anim_prim.CreateAttribute(
        "blendShapeWeights", Sdf.ValueTypeNames.FloatArray, False)

    rel = skel_prim.GetRelationship("skel:animationSource")
    targets = rel.GetTargets()
    if targets:
        for target in targets:
            omni.kit.commands.execute("RemoveRelationshipTargetCommand", relationship=rel, target=target)
    omni.kit.commands.execute("AddRelationshipTargetCommand", relationship=rel, target=new_anim_path)

    # make sure that there is a lazy graph to start with
    graph = get_or_create_graph(graph_name, graph_type="LazyGraph")

    # create write prim node
    anim_write_node = get_prim_io(
        graph_name, new_anim_prim, NODE_TYPE_WRITE_PRIM, force=True)
    og.Controller(anim_write_node.get_attribute("inputs:name")).set("blendShapeWeights", update_usd=True)

    # create bs receive node
    bs_receive_node = create_node(graph_name, NODE_TYPE_RECEIVE_LIVELINK)
    og.Controller.evaluate_sync()

    # create read time node
    read_time_node = create_node(graph_name, NODE_TYPE_READ_TIME)

    # connect receive to write prim
    og.Controller.connect(
        bs_receive_node.get_attribute("outputs:face_weights"),
        anim_write_node.get_attribute("inputs:value"),
    )

    # connect receive to write prim
    og.Controller.connect(
        read_time_node.get_attribute("outputs:timeSinceStart"),
        bs_receive_node.get_attribute("inputs:time"),
    )

    return bs_receive_node


def set_attribute(prop_path, value):
    result = omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=f'{prop_path}',
        value=value,
        prev=None,
    )
    return result


def create_node(graph_name: str, node_type: str, name="", stage=None):
    """Create node with next available path in the graph

    Args:
        graph_name: (str) name of the omni graph
        node_type: (str) node type name

    Keywords:
        name: (str) name of the node. Default: ""
        stage: (Usd.Stage): Usd Stage object. Default: None

    Returns:
        (omni.graph.Node) The create OmniGraph Node
    """
    if stage is None:
        stage = omni.usd.get_context().get_stage()

    graph = get_or_create_graph(graph_name)
    graph_path = graph.get_path_to_graph()

    if not name:
        name = node_type.split('.')[-1]

    node_path = omni.usd.get_stage_next_free_path(stage, f"{graph_path}/{name}", False)
    result = omni.kit.commands.execute(
        'CreateNodeCommand',
        graph=graph, node_path=node_path, node_type=node_type, create_usd=True,
    )

    node = og.ObjectLookup.node(node_path)
    return node


def get_or_create_graph(graph_name, graph_type="PushGraph"):
    """Return the graph path from default scene root if found or create and return a new graph

    Args:
        graph_name: name of the graph

    Keywords:
        graph_type: (str) graph type name. Default: "PushGraph"

    Returns:
        (omni.graph.Graph) The create OmniGraph
    """
    stage = omni.usd.get_context().get_stage()
    if stage is None:
        raise RuntimeError("Unable to get or create graph: no stage")

    root_path = ""
    world = stage.GetDefaultPrim()
    if world:
        root_path = world.GetPath()

    prefix = os.path.commonprefix([str(root_path), str(graph_name)])
    graph_name = graph_name[len(prefix):].lstrip('/')

    # find graph under default prim with the right type
    graph_path = f'{root_path}/{graph_name}'

    graph = og.get_graph_by_path(graph_path)

    if not graph:
        free_path = omni.usd.get_stage_next_free_path(stage, graph_path, False)
        # create time node on a brand new graph which force create the graph as well
        (graph, nodes, _, _) = og.Controller.edit(
            {"graph_path": free_path, "evaluator_name": GRAPH_TYPE[graph_type]}, {}
        )

    return graph


def is_valid_prim_path(prim_path: str, prim_type: str = '', stage: Usd.Stage = None):
    """Validate the prim path.

    Args:
        prim_path: (str) A prim path to validate
        prim_type: (str) A prim type to validate

    Keywords:
        stage: (Usd.Stage or None) A stage to check the path. Default to None and it uses the current stage.

    Returns:
        (bool) True if the prim path is a valid path.
    """
    if not isinstance(prim_path, str):
        return False

    if stage is None:
        context = omni.usd.get_context()
        stage = context.get_stage()

    prim = stage.GetPrimAtPath(prim_path)

    if not prim.IsValid():
        return False

    if prim_type and prim.GetTypeName() != prim_type:
        return False

    return True


def set_property(prop_path, value, prev=None):
    """Set property values through commands (undoable)

    Args:
        prop_path: (str) a property path
        value: (any) value to set property
    """
    result = omni.kit.commands.execute(
        "ChangeProperty",
        prop_path=f'{prop_path}',
        value=value,
        prev=prev,
    )
    return result
