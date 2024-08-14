from collections import OrderedDict

mediapipe_2_arkit={
'browDownLeft':'BrowDownLeft',
'browDownRight':'BrowDownRight',
'browInnerUp':'BrowInnerUp',
'browOuterUpLeft':'BrowOuterUpLeft',
'browOuterUpRight':'BrowOuterUpRight',
'cheekPuff':'CheekPuff',
'cheekSquintLeft':'CheekSquintLeft',
'cheekSquintRight':'CheekSquintRight',
'eyeBlinkLeft':'EyeBlinkLeft',
'eyeBlinkRight':'EyeBlinkRight',
'eyeLookDownLeft':'EyeLookDownLeft',
'eyeLookDownRight':'EyeLookDownRight',
'eyeLookInLeft':'EyeLookInLeft',
'eyeLookInRight':'EyeLookInRight',
'eyeLookOutLeft':'EyeLookOutLeft',
'eyeLookOutRight':'EyeLookOutRight',
'eyeLookUpLeft':'EyeLookUpLeft',
'eyeLookUpRight':'EyeLookUpRight',
'eyeSquintLeft':'EyeSquintLeft',
'eyeSquintRight':'EyeSquintRight',
'eyeWideLeft':'EyeWideLeft',
'eyeWideRight':'EyeWideRight',
'jawForward':'JawForward',
'jawLeft':'JawLeft',
'jawOpen':'JawOpen',
'jawRight':'JawRight',
'mouthClose':'MouthClose',
'mouthDimpleLeft':'MouthDimpleLeft',
'mouthDimpleRight':'MouthDimpleRight',
'mouthFrownLeft':'MouthFrownLeft',
'mouthFrownRight':'MouthFrownRight',
'mouthFunnel':'MouthFunnel',
'mouthLeft':'MouthLeft',
'mouthLowerDownLeft':'MouthLowerDownLeft',
'mouthLowerDownRight':'MouthLowerDownRight',
'mouthPressLeft':'MouthPressLeft',
'mouthPressRight':'MouthPressRight',
'mouthPucker':'MouthPucker',
'mouthRight':'MouthRight',
'mouthRollLower':'MouthRollLower',
'mouthRollUpper':'MouthRollUpper',
'mouthShrugLower':'MouthShrugLower',
'mouthShrugUpper':'MouthShrugUpper',
'mouthSmileLeft':'MouthSmileLeft',
'mouthSmileRight':'MouthSmileRight',
'mouthStretchLeft':'MouthStretchLeft',
'mouthStretchRight':'MouthStretchRight',
'mouthUpperUpLeft':'MouthUpperUpLeft',
'mouthUpperUpRight':'MouthUpperUpRight',
'noseSneerLeft':'NoseSneerLeft',
'noseSneerRight':'NoseSneerRight'
}
class FaceExpression:
    BASE_VAL=float(0.0)
    # use KEYS for streaming low level animation animation (beware of duplicates: LL-Face animation vs low level animation)
    KEYS=[
        'CTRL_expressions_browDownL', 'CTRL_expressions_browDownR', 'CTRL_expressions_browLateralL', 'CTRL_expressions_browLateralR', 'CTRL_expressions_browRaiseInL', 'CTRL_expressions_browRaiseInR', 'CTRL_expressions_browRaiseOuterL', 'CTRL_expressions_browRaiseOuterR', 'CTRL_expressions_earUpL', 'CTRL_expressions_earUpR', 'CTRL_expressions_eyeBlinkL', 'CTRL_expressions_eyeBlinkR', 'CTRL_expressions_eyeLidPressL', 'CTRL_expressions_eyeLidPressR', 'CTRL_expressions_eyeWidenL', 'CTRL_expressions_eyeWidenR', 'CTRL_expressions_eyeSquintInnerL', 'CTRL_expressions_eyeSquintInnerR', 'CTRL_expressions_eyeCheekRaiseL', 'CTRL_expressions_eyeCheekRaiseR', 'CTRL_expressions_eyeFaceScrunchL', 'CTRL_expressions_eyeFaceScrunchR', 'CTRL_expressions_eyeUpperLidUpL', 'CTRL_expressions_eyeUpperLidUpR', 'CTRL_expressions_eyeRelaxL', 'CTRL_expressions_eyeRelaxR', 'CTRL_expressions_eyeLowerLidUpL', 'CTRL_expressions_eyeLowerLidUpR', 'CTRL_expressions_eyeLowerLidDownL', 'CTRL_expressions_eyeLowerLidDownR', 'CTRL_expressions_eyeLookUpL', 'CTRL_expressions_eyeLookUpR', 'CTRL_expressions_eyeLookDownL', 'CTRL_expressions_eyeLookDownR', 'CTRL_expressions_eyeLookLeftL', 'CTRL_expressions_eyeLookLeftR', 'CTRL_expressions_eyeLookRightL', 'CTRL_expressions_eyeLookRightR', 'CTRL_expressions_eyePupilWideL', 'CTRL_expressions_eyePupilWideR', 'CTRL_expressions_eyePupilNarrowL', 'CTRL_expressions_eyePupilNarrowR', 'CTRL_expressions_eyeParallelLookDirection', 'CTRL_expressions_eyelashesUpINL', 'CTRL_expressions_eyelashesUpINR', 'CTRL_expressions_eyelashesUpOUTL', 'CTRL_expressions_eyelashesUpOUTR', 'CTRL_expressions_eyelashesDownINL', 'CTRL_expressions_eyelashesDownINR', 'CTRL_expressions_eyelashesDownOUTL', 'CTRL_expressions_eyelashesDownOUTR', 'CTRL_expressions_noseWrinkleL', 'CTRL_expressions_noseWrinkleR', 'CTRL_expressions_noseWrinkleUpperL', 'CTRL_expressions_noseWrinkleUpperR', 'CTRL_expressions_noseNostrilDepressL', 'CTRL_expressions_noseNostrilDepressR', 'CTRL_expressions_noseNostrilDilateL', 'CTRL_expressions_noseNostrilDilateR', 'CTRL_expressions_noseNostrilCompressL', 'CTRL_expressions_noseNostrilCompressR', 'CTRL_expressions_noseNasolabialDeepenL', 'CTRL_expressions_noseNasolabialDeepenR', 'CTRL_expressions_mouthCheekSuckL', 'CTRL_expressions_mouthCheekSuckR', 'CTRL_expressions_mouthCheekBlowL', 'CTRL_expressions_mouthCheekBlowR', 'CTRL_expressions_mouthLipsBlowL', 'CTRL_expressions_mouthLipsBlowR', 'CTRL_expressions_mouthLeft', 'CTRL_expressions_mouthRight', 'CTRL_expressions_mouthUp', 'CTRL_expressions_mouthDown', 'CTRL_expressions_mouthUpperLipRaiseL', 'CTRL_expressions_mouthUpperLipRaiseR', 'CTRL_expressions_mouthLowerLipDepressL', 'CTRL_expressions_mouthLowerLipDepressR', 'CTRL_expressions_mouthCornerPullL', 'CTRL_expressions_mouthCornerPullR', 'CTRL_expressions_mouthStretchL', 'CTRL_expressions_mouthStretchR', 'CTRL_expressions_mouthStretchLipsCloseL', 'CTRL_expressions_mouthStretchLipsCloseR', 'CTRL_expressions_mouthDimpleL', 'CTRL_expressions_mouthDimpleR', 'CTRL_expressions_mouthCornerDepressL', 'CTRL_expressions_mouthCornerDepressR', 'CTRL_expressions_mouthPressUL', 'CTRL_expressions_mouthPressUR', 'CTRL_expressions_mouthPressDL', 'CTRL_expressions_mouthPressDR', 'CTRL_expressions_mouthLipsPurseUL', 'CTRL_expressions_mouthLipsPurseUR', 'CTRL_expressions_mouthLipsPurseDL', 'CTRL_expressions_mouthLipsPurseDR', 'CTRL_expressions_mouthLipsTowardsUL', 'CTRL_expressions_mouthLipsTowardsUR', 'CTRL_expressions_mouthLipsTowardsDL', 'CTRL_expressions_mouthLipsTowardsDR', 'CTRL_expressions_mouthFunnelUL', 'CTRL_expressions_mouthFunnelUR', 'CTRL_expressions_mouthFunnelDL', 'CTRL_expressions_mouthFunnelDR', 'CTRL_expressions_mouthLipsTogetherUL', 'CTRL_expressions_mouthLipsTogetherUR', 'CTRL_expressions_mouthLipsTogetherDL', 'CTRL_expressions_mouthLipsTogetherDR', 'CTRL_expressions_mouthUpperLipBiteL', 'CTRL_expressions_mouthUpperLipBiteR', 'CTRL_expressions_mouthLowerLipBiteL', 'CTRL_expressions_mouthLowerLipBiteR', 'CTRL_expressions_mouthLipsTightenUL', 'CTRL_expressions_mouthLipsTightenUR', 'CTRL_expressions_mouthLipsTightenDL', 'CTRL_expressions_mouthLipsTightenDR', 'CTRL_expressions_mouthLipsPressL', 'CTRL_expressions_mouthLipsPressR', 'CTRL_expressions_mouthSharpCornerPullL', 'CTRL_expressions_mouthSharpCornerPullR', 'CTRL_expressions_mouthStickyUC', 'CTRL_expressions_mouthStickyUINL', 'CTRL_expressions_mouthStickyUINR', 'CTRL_expressions_mouthStickyUOUTL', 'CTRL_expressions_mouthStickyUOUTR', 'CTRL_expressions_mouthStickyDC', 'CTRL_expressions_mouthStickyDINL', 'CTRL_expressions_mouthStickyDINR', 'CTRL_expressions_mouthStickyDOUTL', 'CTRL_expressions_mouthStickyDOUTR', 'CTRL_expressions_mouthLipsStickyLPh1', 'CTRL_expressions_mouthLipsStickyLPh2', 'CTRL_expressions_mouthLipsStickyLPh3', 'CTRL_expressions_mouthLipsStickyRPh1', 'CTRL_expressions_mouthLipsStickyRPh2', 'CTRL_expressions_mouthLipsStickyRPh3', 'CTRL_expressions_mouthLipsPushUL', 'CTRL_expressions_mouthLipsPushUR', 'CTRL_expressions_mouthLipsPushDL', 'CTRL_expressions_mouthLipsPushDR', 'CTRL_expressions_mouthLipsPullUL', 'CTRL_expressions_mouthLipsPullUR', 'CTRL_expressions_mouthLipsPullDL', 'CTRL_expressions_mouthLipsPullDR', 'CTRL_expressions_mouthLipsThinUL', 'CTRL_expressions_mouthLipsThinUR', 'CTRL_expressions_mouthLipsThinDL', 'CTRL_expressions_mouthLipsThinDR', 'CTRL_expressions_mouthLipsThickUL', 'CTRL_expressions_mouthLipsThickUR', 'CTRL_expressions_mouthLipsThickDL', 'CTRL_expressions_mouthLipsThickDR', 'CTRL_expressions_mouthCornerSharpenUL', 'CTRL_expressions_mouthCornerSharpenUR', 'CTRL_expressions_mouthCornerSharpenDL', 'CTRL_expressions_mouthCornerSharpenDR', 'CTRL_expressions_mouthCornerRounderUL', 'CTRL_expressions_mouthCornerRounderUR', 'CTRL_expressions_mouthCornerRounderDL', 'CTRL_expressions_mouthCornerRounderDR', 'CTRL_expressions_mouthUpperLipTowardsTeethL', 'CTRL_expressions_mouthUpperLipTowardsTeethR', 'CTRL_expressions_mouthLowerLipTowardsTeethL', 'CTRL_expressions_mouthLowerLipTowardsTeethR', 'CTRL_expressions_mouthUpperLipShiftLeft', 'CTRL_expressions_mouthUpperLipShiftRight', 'CTRL_expressions_mouthLowerLipShiftLeft', 'CTRL_expressions_mouthLowerLipShiftRight', 'CTRL_expressions_mouthUpperLipRollInL', 'CTRL_expressions_mouthUpperLipRollInR', 'CTRL_expressions_mouthUpperLipRollOutL', 'CTRL_expressions_mouthUpperLipRollOutR', 'CTRL_expressions_mouthLowerLipRollInL', 'CTRL_expressions_mouthLowerLipRollInR', 'CTRL_expressions_mouthLowerLipRollOutL', 'CTRL_expressions_mouthLowerLipRollOutR', 'CTRL_expressions_mouthCornerUpL', 'CTRL_expressions_mouthCornerUpR', 'CTRL_expressions_mouthCornerDownL', 'CTRL_expressions_mouthCornerDownR', 'CTRL_expressions_mouthCornerWideL', 'CTRL_expressions_mouthCornerWideR', 'CTRL_expressions_mouthCornerNarrowL', 'CTRL_expressions_mouthCornerNarrowR', 'CTRL_expressions_tongueUp', 'CTRL_expressions_tongueDown', 'CTRL_expressions_tongueLeft', 'CTRL_expressions_tongueRight', 'CTRL_expressions_tongueOut', 'CTRL_expressions_tongueIn', 'CTRL_expressions_tongueRollUp', 'CTRL_expressions_tongueRollDown', 'CTRL_expressions_tongueRollLeft', 'CTRL_expressions_tongueRollRight', 'CTRL_expressions_tongueTipUp', 'CTRL_expressions_tongueTipDown', 'CTRL_expressions_tongueTipLeft', 'CTRL_expressions_tongueTipRight', 'CTRL_expressions_tongueWide', 'CTRL_expressions_tongueNarrow', 'CTRL_expressions_tonguePress', 'CTRL_expressions_jawOpen', 'CTRL_expressions_jawLeft', 'CTRL_expressions_jawRight', 'CTRL_expressions_jawFwd', 'CTRL_expressions_jawBack', 'CTRL_expressions_jawClenchL', 'CTRL_expressions_jawClenchR', 'CTRL_expressions_jawChinRaiseDL', 'CTRL_expressions_jawChinRaiseDR', 'CTRL_expressions_jawChinRaiseUL', 'CTRL_expressions_jawChinRaiseUR', 'CTRL_expressions_jawChinCompressL', 'CTRL_expressions_jawChinCompressR', 'CTRL_expressions_jawOpenExtreme', 'CTRL_expressions_neckStretchL', 'CTRL_expressions_neckStretchR', 'CTRL_expressions_neckSwallowPh1', 'CTRL_expressions_neckSwallowPh2', 'CTRL_expressions_neckSwallowPh3', 'CTRL_expressions_neckSwallowPh4', 'CTRL_expressions_neckMastoidContractL', 'CTRL_expressions_neckMastoidContractR', 'CTRL_expressions_neckThroatDown', 'CTRL_expressions_neckThroatUp', 'CTRL_expressions_neckDigastricDown', 'CTRL_expressions_neckDigastricUp', 'CTRL_expressions_neckThroatExhale', 'CTRL_expressions_neckThroatInhale', 'CTRL_expressions_teethUpU', 'CTRL_expressions_teethUpD', 'CTRL_expressions_teethDownU', 'CTRL_expressions_teethDownD', 'CTRL_expressions_teethLeftU', 'CTRL_expressions_teethLeftD', 'CTRL_expressions_teethRightU', 'CTRL_expressions_teethRightD', 'CTRL_expressions_teethFwdU', 'CTRL_expressions_teethFwdD', 'CTRL_expressions_teethBackU', 'CTRL_expressions_teethBackD', 'CTRL_expressions_skullUnified', 'CTRL_rigLogic_OffOn',
         'CTRL_expressions_headTurnUpU', 'CTRL_expressions_headTurnUpM', 'CTRL_expressions_headTurnUpD', 'CTRL_expressions_headTurnDownU', 'CTRL_expressions_headTurnDownM', 'CTRL_expressions_headTurnDownD', 'CTRL_expressions_headTurnLeftU', 'CTRL_expressions_headTurnLeftM', 'CTRL_expressions_headTurnLeftD', 'CTRL_expressions_headTurnRightU', 'CTRL_expressions_headTurnRightM', 'CTRL_expressions_headTurnRightD', 'CTRL_expressions_headTiltLeftU', 'CTRL_expressions_headTiltLeftM', 'CTRL_expressions_headTiltLeftD', 'CTRL_expressions_headTiltRightU', 'CTRL_expressions_headTiltRightM', 'CTRL_expressions_headTiltRightD','CTRL_expressions_lookAtSwitch', 'HeadYaw', 'HeadPitch', 'HeadRoll', 'LeftEyeYaw', 'LeftEyePitch', 'LeftEyeRoll', 'RightEyeYaw', 'RightEyePitch', 'RightEyeRoll']
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

    JSON_KEYLIST_STR= '[' + (''.join('"' + i+'",' for i in KEYS))[:-1] + ']'   # join all keys to one string, separated by a comma and strip last comma
    #'Pose_0', 'Pose_1', 'Pose_2', 'Pose_3'
    print("")

    def __init__(self, key_idx=0, **kwargs ):
        self.shape_keys = OrderedDict() #ordered dict to preserve order for
        self.key_vals=[]

        if key_idx==0:
            key_list=FaceExpression.KEYS
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