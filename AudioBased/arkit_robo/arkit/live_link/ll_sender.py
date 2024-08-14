from live_link.config.json_requests import *
import socket
from live_link.config.settings import *

# Metahuman setup
FaceExpression.BASE_VAL = 0.0
scale_blendshapes = 1.0
SUBJECT_FACE[1][0]["CurveNames"] = FaceExpression.ARKIT_KEYS
SUBJECTS_DICT = { SUBJECT_FACE[0]: SUBJECT_FACE[1],
                  SUBJECT_STATE[0]: SUBJECT_STATE[1]
                  }
JSON_SUBJECTS = json.dumps(SUBJECTS_DICT)

BUILD_SUBJECTS_REQUEST = JSON_SUBJECTS.encode('utf-8')

# send subject msg
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((TCP_IP, TCP_PORT))
s.send(BUILD_SUBJECTS_REQUEST)

# build animation request
ANIMATION_REQUEST = {"mh_face": AGENT_MESSAGE_FACE_ANIM[1]}

ANIMATION_STATE = {"mh_state": AGENT_MESSAGE_STATE[1]}

print("ll sending subjects setup")


# media pipe and opencv setup



def send_face_to_metahuman(face_expr):
    #send facial expression to meta-human
    ANIMATION_REQUEST["mh_face"][1]["CurveValues"] = list(face_expr.shape_keys.values())
    ANIM_REQU = json.dumps(ANIMATION_REQUEST)
    ANIM_REQ_BYTES = ANIM_REQU.encode('utf-8')
    s.send(ANIM_REQ_BYTES)

def send_state_to_metahuman(listening):
    #send facial expression to meta-human
    ANIMATION_STATE["mh_state"][1]["CurveValues"] = [float(listening)]
    ANIM_REQU = json.dumps(ANIMATION_STATE)
    ANIM_REQ_BYTES = ANIM_REQU.encode('utf-8')
    s.send(ANIM_REQ_BYTES)
