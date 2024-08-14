from collections import OrderedDict

class FaceExpression:
    BASE_VAL=float(0.0)
    # use KEYS for streaming low level animation animation (beware of duplicates: LL-Face animation vs low level animation)
    # use ARKIT_KEYS for streaming mediapipe data
    ARKIT_KEYS = [
        'BrowDownLeft', 'BrowDownRight', 'BrowInnerUp', 'BrowOuterUpLeft', 'BrowOuterUpRight', 'CheekPuff', 'CheekSquintLeft', 'CheekSquintRight',
        'EyeBlinkLeft','EyeBlinkRight','EyeLookDownLeft','EyeLookDownRight', 'EyeLookInLeft','EyeLookInRight','EyeLookOutLeft', 'EyeLookOutRight',
        'EyeLookUpLeft','EyeLookUpRight', 'EyeSquintLeft','EyeSquintRight','EyeWideLeft','EyeWideRight',
        'JawForward', 'JawLeft', 'JawOpen', 'JawRight', 'MouthClose', 'MouthDimpleLeft', 'MouthDimpleRight','MouthFrownLeft','MouthFrownRight', 'MouthFunnel',
        'MouthLeft','MouthLowerDownLeft', 'MouthLowerDownRight','MouthPressLeft', 'MouthPressRight','MouthPucker',  'MouthRight','MouthRollLower', 'MouthRollUpper',
        'MouthShrugLower', 'MouthShrugUpper', 'MouthSmileLeft', 'MouthSmileRight','MouthStretchLeft', 'MouthStretchRight','MouthUpperUpLeft', 'MouthUpperUpRight',
        'NoseSneerLeft', 'NoseSneerRight', 'TongueOut',
        'HeadYaw', 'HeadPitch', 'HeadRoll', 'LeftEyeYaw', 'LeftEyePitch', 'LeftEyeRoll', 'RightEyeYaw', 'RightEyePitch', 'RightEyeRoll'
    ]
    #use ARKIT_ANIM_KEYS for streaming LL-FACE data
    ARKIT_ANIM_KEYS =[
    'EyeBlinkLeft',
    'EyeLookDownLeft',
    'EyeLookInLeft',
    'EyeLookOutLeft',
    'EyeLookUpLeft',
    'EyeSquintLeft',
    'EyeWideLeft',
    'EyeBlinkRight',
    'EyeLookDownRight',
    'EyeLookInRight',
    'EyeLookOutRight',
    'EyeLookUpRight',
    'EyeSquintRight',
    'EyeWideRight',
    'JawForward',
    'JawRight',
    'JawLeft',
    'JawOpen',
    'MouthClose',
    'MouthFunnel',
    'MouthPucker',
    'MouthRight',
    'MouthLeft',
    'MouthSmileLeft',
    'MouthSmileRight',
    'MouthFrownLeft',
    'MouthFrownRight',
    'MouthDimpleLeft',
    'MouthDimpleRight',
    'MouthStretchLeft',
    'MouthStretchRight',
    'MouthRollLower',
    'MouthRollUpper',
    'MouthShrugLower',
    'MouthShrugUpper',
    'MouthPressLeft',
    'MouthPressRight',
    'MouthLowerDownLeft',
    'MouthLowerDownRight',
    'MouthUpperUpLeft',
    'MouthUpperUpRight',
    'BrowDownLeft',
    'BrowDownRight',
    'BrowInnerUp',
    'BrowOuterUpLeft',
    'BrowOuterUpRight',
    'CheekPuff',
    'CheekSquintLeft',
    'CheekSquintRight',
    'NoseSneerLeft',
    'NoseSneerRight',
    'TongueOut',
    'HeadYaw',
    'HeadPitch',
    'HeadRoll',
    'LeftEyeYaw',
    'LeftEyePitch',
    'LeftEyeRoll',
    'RightEyeYaw',
    'RightEyePitch',
    'RightEyeRoll'
    ]

    #JSON_KEYLIST_STR= '[' + (''.join('"' + i+'",' for i in KEYS))[:-1] + ']'   # join all keys to one string, separated by a comma and strip last comma
    #'Pose_0', 'Pose_1', 'Pose_2', 'Pose_3'
    print("")

    def __init__(self, key_idx=0, **kwargs ):
        self.shape_keys = OrderedDict() #ordered dict to preserve order for
        self.key_vals=[]

        if key_idx==0:
            raise Exception("dump")
        elif key_idx==1:
            key_list=FaceExpression.ARKIT_KEYS
        elif key_idx==2:
            key_list=FaceExpression.ARKIT_ANIM_KEYS

        for key in key_list:
            self.shape_keys[key]=FaceExpression.BASE_VAL

        for k,v in kwargs.items():
            self.shape_keys[k]=float(v)

        self.json_vlist_str= '[' + self.get_val_str() + ']'

    def get_val_str(self):
        val_str=''
        for v in self.shape_keys.values():
            val_str+=  '' + str(v) + ','
        return val_str[:-1]


#
# for i in FaceExpression.KEYS:
#     print(i)