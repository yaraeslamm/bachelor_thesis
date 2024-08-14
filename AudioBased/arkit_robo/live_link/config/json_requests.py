import json

##############################################################
##########################actual config#######################
##############################################################
from live_link.animation.curves import FaceExpression


SUBJECT_FACE = (
    "mh_face", [
        {"Type": "CharacterSubject",
         "CurveNames": FaceExpression.ARKIT_KEYS
        }
    ]
)


AGENT_MESSAGE_BODY_ANIM = (
    "mh_body",
    [
    {"Type": "CharacterAnimation"}
    # new entries to be appended
    ]
)

AGENT_MESSAGE_FACE_ANIM = (
    "mh_face",
    [
            {"Type": "CharacterAnimation"
            },
            {"CurveValues":[]
            }
    ]
)

#####################################

SUBJECT_STATE = (
    "mh_state", [
        {"Type": "CharacterSubject",
         "CurveNames": ["Listening"]
        }
    ]
)

AGENT_MESSAGE_STATE = (
    "mh_state",
    [
            {"Type": "CharacterAnimation"
            },
            {"CurveValues":[]
            }
    ]
)

