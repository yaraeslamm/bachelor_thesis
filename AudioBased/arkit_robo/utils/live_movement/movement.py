from live_link.animation.curves import FaceExpression
from live_link.config.settings import mediapipe_2_arkit, arkit_scaling_min_max
import numpy as np
from scipy.spatial.transform import Rotation
from copy import deepcopy

min_max_dict=deepcopy(arkit_scaling_min_max)

def mediapipe_min_max_from_bs(blendshapes):
    global min_max_dict
    frame_keys={}#
    if len(blendshapes)>0:
        for blendshape in blendshapes:
            if blendshape.category_name=='_neutral':
                continue
            arkit_name = mediapipe_2_arkit[blendshape.category_name]
            frame_keys[arkit_name] = blendshape.score
            min_max_dict[arkit_name][0]=min(min_max_dict[arkit_name][0], blendshape.score)
            min_max_dict[arkit_name][1]=max(min_max_dict[arkit_name][1], blendshape.score)
        #print(min_max_dict)

def mediapipe_bs_to_face_expr(blendshapes, arkit_scaler):
    frame_keys={}#
    if len(blendshapes) >0:
        for blendshape in blendshapes:
            if blendshape.category_name=='_neutral':
                continue
            arkit_name = mediapipe_2_arkit[blendshape.category_name]
            #scale bs value from an interval [min, max] --> [0,1]
            frame_keys[arkit_name] = (blendshape.score - arkit_scaler[arkit_name][0]) / (arkit_scaler[arkit_name][1] - arkit_scaler[arkit_name][0])

    face_expr = FaceExpression(1, **frame_keys)
    return face_expr

"""
facial_transformation_matrix: assumes, that an result-object from medipipes prediction is passed: "results.facial_transformation_matrixes[0]"
"""
def add_mh_head_rot(face_expr, facial_transform_matrix, head_scale):
    # 'HeadYaw'
    # 'HeadPitch'
    # 'HeadRoll'
    if (len(facial_transform_matrix) > 0):
        scaled_matrix = np.dot(facial_transform_matrix, np.diag([head_scale,head_scale,head_scale, 1]))
        rot_matrix_3x3 = scaled_matrix[:3, :3]
        # rot_matrix to euler angles in radians

        rot=Rotation.from_matrix(rot_matrix_3x3).as_euler('xyz', degrees=False)
        face_expr.shape_keys['HeadYaw']= rot[1]      #x
        face_expr.shape_keys['HeadRoll'] = rot[2]  #y
        face_expr.shape_keys['HeadPitch'] = rot[0]  *(-1.0)  #z

    return face_expr


def get_mh_body_angles(result):
    pass