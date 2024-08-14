import math
import time
from flask import current_app
import logging
from enum import Enum
from random import seed, randint
from hlabandroidpylib.andr_controller import ControllerType
import numpy as np
import json

import os
import threading

from serial.tools import list_ports
import json
import os
import atexit

from apscheduler.schedulers.background import BackgroundScheduler

from hlabandroidpylib.andr_controller import ControllerType
from websockets.sync.client import connect
import pathlib
from dotenv import load_dotenv
import os
import threading

load_dotenv(pathlib.Path(__file__).parent.joinpath('.env').resolve())
POSE_WEBSOCKET = os.environ.get('POSE_WEBSOCKET', None)
UPVIDEOCORNER = os.environ.get('UPVIDEOCORNER', None)
if UPVIDEOCORNER is not None:
    UPVIDEOCORNER = int(UPVIDEOCORNER)
LEFTVIDEOCORNER = os.environ.get('LEFTVIDEOCORNER', None)
if LEFTVIDEOCORNER is not None:
    LEFTVIDEOCORNER = int(LEFTVIDEOCORNER)

IMG_WIDTH = int(os.environ.get('IMG_WIDTH', 1280))
IMG_HEIGHT = int(os.environ.get('IMG_HEIGHT', 720))

def get_usb_ports(current_app):
    connected_usb_port = getattr(current_app, 'connected_usb_port', None)
    if connected_usb_port:
        return [connected_usb_port]
    return [p.device for p in list_ports.comports()]


def get_changed_values(current_app):
    changed_values = getattr(current_app, 'changed_values', None)
    if changed_values:
        return changed_values
    current_app.changed_values = [None for _ in range(len(current_app.controller.actuators))]
    return current_app.changed_values

def load_animations(path):
    animations = []
    for filename in os.scandir(path):
        if filename.is_file():
            with open(filename.path) as file:
                animation = json.load(file)
                a = HlabAnimation(animation['frames'], animation['description'], **animation['header'])
                animations.append(a)
    return animations

def run_animation(app):
    # TODO: send values only if changed? stop scheduler when no animations run?
    with app.app_context():
        lv = app.controller.last_values.copy()
        values = app.anim_scheduler.get_combined_frame(lv)
        _, _ = app.controller.send_values(values)


def setup_scheduling(current_app):
    current_app.scheduler_secs = 0.04 # 25Hertz
    assert getattr(current_app, 'controller', None) is not None
    
    path = './data/animations/head'
    if current_app.controller.controller_type == ControllerType.ANDROID:
        path = './data/animations/android'
    animations = load_animations(path)
    
    if getattr(current_app, 'anim_scheduler', None) is None:
        current_app.anim_scheduler = HlabAnimationScheduler(animations)
    else:
        existing_animation_names = [a.name for a in current_app.anim_scheduler.animations]
        for a in animations:
            if a.name not in existing_animation_names:
                current_app.anim_scheduler.add_or_replace_animation(a)

    scheduler = getattr(current_app, 'scheduler', None)
    if scheduler is None:
        scheduler = BackgroundScheduler()
        scheduler.add_job(run_animation, 'interval', seconds=current_app.scheduler_secs, kwargs={'app': current_app._get_current_object()})
        scheduler.start()
        current_app.scheduler = scheduler
        atexit.register(lambda: scheduler.shutdown(wait=False))


def stop_scheduler(current_app):
    if getattr(current_app, 'scheduler', None) is not None:
        current_app.scheduler.shutdown(wait=False)
        current_app.scheduler = None

def disconnect(current_app):
    assert getattr(current_app, 'controller', None) is not None
    stop_scheduler(current_app)
    current_app.controller.disconnect()
    current_app.controller = None
    current_app.connected_usb_port = None
    return {'connected': False}

def replaceMissingValues(nextFrame, previousFrame):
    values = [v if v is not None else previousFrame[i] for i, v in enumerate(nextFrame)]
    return values

def interpolate(v1, v2, steps):
    v1 = np.asarray(v1, dtype=np.number)
    v2 = np.asarray(v2, dtype=np.number)
    ratios = np.linspace(0, 1, num=steps)
    vectors = list()
    for ratio in ratios:
        v = (1.0 - ratio) * v1 + ratio * v2
        vectors.append([int(val) if np.isfinite(val) else None for val in v])
    return vectors

class AnimationMode(Enum):
    ABSOLUTE = "abs"
    RELATIVE = "rel"
    INHERIT = "inh"  # just for sequences


class HlabAnimation():
    def __init__(self, frames=[], description='', **kwargs):
        self.description = description
        self.name = kwargs.get('name', '')

        self.pause_frames = []  # the pausing frames (random)
        self.pause_frames_min_max = [kwargs.get('minPauseFrames', 0), kwargs.get('maxPauseFrames', 0)]
        assert self.pause_frames_min_max[0] <= self.pause_frames_min_max[1], 'minPauseFrames needs to be smaller than or equal to maxPauseFrames'
        
        self.loop = kwargs.get('loop', 0)  # 0: NO animation(!), > 0: number of loops, < 0: endless loop; i.e. in order to do anything, loop needs to be at least 1
        self.start_with_pause = kwargs.get('start_with_pause', False)
        self.current_frame_index = 0
        self.current_loop_count = 1
        self.prio = kwargs.get('prio', 50)  # should be between 0 (lowest) and 100 (highest) prio
        self.mode = AnimationMode(kwargs.get('mode', 'abs'))  # either absolute or relative (defined as 'abs' or 'rel' in jsons)
        self.group = kwargs.get('group')
        self.active = False
        self.interpolation = kwargs.get('interpolation', None)
        self.steps_to_first_frame = 0
        self.interpolated_to_first_frame = False
        if self.interpolation is not None:
            assert self.mode == AnimationMode.ABSOLUTE, 'only absolute animations can be interpolated'
        
        def default_callback():
            pass
        self.on_completion = kwargs.get('on_completion')
        if self.on_completion is None:
            self.on_completion = default_callback
        self.on_completion_args = kwargs.get('on_completion_args', [])
        
        frame_length = 14
        if current_app.controller.controller_type == ControllerType.ANDROID:
            frame_length = 52
        self.default_frame = [None] * frame_length
        self.frames = []
        if len(frames) <= 0:
            self.frames = [self.default_frame]
        if not self.interpolation:
            last_added_frame = self.default_frame
            last_index = 0
            for f in frames:
                while (last_index+1) < f["frame"]:
                    # if there are gaps inbetween the frame numbers, we will create the missing frames here
                    self.frames.append(last_added_frame)
                    last_index+=1
                last_added_frame = f["values"]
                last_index = f['frame']
                self.frames.append(f["values"])
        else:
            interpolated_frames = []
            if len(frames) == 1:
                interpolated_frames = [frames[0]['values']]
            for i in range(len(frames)):
                if i == 0:
                    self.steps_to_first_frame = frames[i]['frame']
                    # interpolation to first specified frame needs to be done at runtime
                    continue
                start_frame_idx = frames[i-1]['frame']
                end_frame_idx = frames[i]['frame']
                ifs = interpolate(frames[i-1]['values'], frames[i]['values'], end_frame_idx - start_frame_idx + 1)[1:]
                interpolated_frames.extend(ifs)
            self.frames = interpolated_frames



    def activate(self, start_with_pause=False):
        #assert self.active is False
        self.start_with_pause = start_with_pause
        self.active = True

    def deactivate(self):
        #assert self.active is True
        self.active = False
        self.current_frame_index = 0
        self.current_loop_count = 1
        self.clean_up_interpolation()

    def can_be_animated(self):
        can_be_animated = len(self.frames) > 0 and self.loop != 0
        if not can_be_animated:
            logging.error("Animation cannot be animated: frames {}, loop {} Animation={}".format(len(self.frames), self.loop, self.name))
        return can_be_animated

    def hasPause(self):
        return self.pause_frames_min_max[0] > 0

    def pauseHasVariableLength(self):
        return self.pause_frames_min_max[0] != self.pause_frames_min_max[1]

    def finalizeAnimation(self):
        # case: new iteration of animation and pause frames are not set yet
        if self.hasPause() and len(self.pause_frames) == 0 and (self.loop>1 or self.loop<0):
            self.setPauseFrames()

        return True

    def setPauseFrames(self):
        # standardValues = self.animJSONObject["frames"][-1]["values"]  # values of the last frame
        numFrames = self.pause_frames_min_max[0]  # initialize with the value for case of: same number for min and max

        if self.pauseHasVariableLength():  # case: pause has a variable length
            # calculate random number of pause frames between [min, max]
            seed()
            # reset numFrames value
            numFrames = randint(self.pause_frames_min_max[0], self.pause_frames_min_max[1])

        # add pause frames (identical frames to last animation frame), numFrames times
        if numFrames > 0:
            self.pause_frames.extend([self.default_frame] * numFrames)
        # note: creates shallow copies

    def clean_up_interpolation(self):
        if self.interpolation is not None and self.steps_to_first_frame > 1 and self.interpolated_to_first_frame:
            self.frames = self.frames[self.steps_to_first_frame:]
            self.interpolated_to_first_frame = False

    def nextFrame(self, last_values=None):
        if not self.can_be_animated():
            # note: returns also false if loop==0
            return []

        # finalize the animation (adds pause frames if necessary)
        if not self.finalizeAnimation():
            logging.warn("Animation not finalizable -> nextFrame = []")
            return []


        if self.interpolation is not None and self.current_frame_index == 0 and self.steps_to_first_frame > 1:
            ifs = interpolate(last_values, self.frames[0], self.steps_to_first_frame + 1)[:-1]
            ifs.extend(self.frames)
            self.frames = ifs
            self.interpolated_to_first_frame = True

        totalFrames = self.frames + self.pause_frames
        if self.start_with_pause:
            totalFrames = self.pause_frames + self.frames

        nextframe = totalFrames[self.current_frame_index]
                
        if self.current_frame_index < len(totalFrames) - 1:
            self.current_frame_index = self.current_frame_index + 1
        else:  # i.e. the last frame (of the iteration)!
            # reset variables at end of loop:
            self.current_frame_index = 0
            # reset pause frames for next iteration if pause is of variable length
            if self.pauseHasVariableLength():
                # note: pause frames don't need resetting if they are not of variable length
                self.pause_frames.clear()

            # check at which iteration we are and if another iteration follows
            if self.current_loop_count == self.loop:
                # no further iterations
                self.deactivate()
                self.on_completion(*self.on_completion_args)
            else:
                # prepare for next iteration:
                self.current_loop_count += 1
            
            self.clean_up_interpolation()
                
        return nextframe


class HlabLookAtAnimation(HlabAnimation):
    def __init__(self, frames=[], description='', **kwargs):
        super().__init__(frames, description, **kwargs)

        self.mode = AnimationMode.ABSOLUTE
        self.loop = 1
        self.interpolation_step = 10
        self.target_coordinates = None
        self.previous_target_coordinates = None
        self.updown_index = 12
        self.leftright_index = 13
        self.wait_up = 0
        self.wait_down = 0
        if current_app.controller.controller_type == ControllerType.ANDROID:
            self.updown_index = 17
            self.leftright_index = 18
        if UPVIDEOCORNER is not None:
            self.scaled_upcorner = 1-(UPVIDEOCORNER/IMG_HEIGHT)

        #root@jetson-orin-2:/jetson-inference# python3 data/scripts/posenet_socket.py /dev/video0 webrtc://@:8554/my_stream --headless --input-flip=rotate-180
    
    def poll_poses(self):
        print('poll_poses')
        with connect(POSE_WEBSOCKET) as websocket:
            no_nose_count = 0
            while self.active:
                poses = json.loads(websocket.recv())
                noses = []
                for p in poses:
                    for kp in p['keypoints']:
                        if kp['id'] == 0:
                            no_nose_count = 0
                            noses.append([kp['x'], kp['y']])
                if len(noses) <= 0:
                    no_nose_count += 1
                else:
                    self.target_coordinates = noses[0]
                if no_nose_count >20:
                    self.target_coordinates = None

                time.sleep(0.04) # needs to be less than in the ws server to avoid lag
            #websocket.close()

    def activate(self, start_with_pause=False):
        self.active = True
        poll = threading.Thread(target=self.poll_poses)
        poll.start()

    def nextFrame(self, last_values=None):
        nf = self.default_frame.copy()

        ### New GPU detection ###
        if self.target_coordinates is not None and self.previous_target_coordinates != self.target_coordinates:
            if current_app.controller.controller_type == ControllerType.ANDROID and (UPVIDEOCORNER is None or LEFTVIDEOCORNER is None):
                # Andrea's eyes
                if IMG_WIDTH/2 - self.target_coordinates[0] > 25:
                    nf[self.leftright_index] = last_values[self.leftright_index] + 5
                elif IMG_WIDTH/2 - self.target_coordinates[0] < -25:
                    nf[self.leftright_index] = last_values[self.leftright_index] - 5

                if IMG_HEIGHT/2 - self.target_coordinates[1] > 15 and self.wait_up <= 0:
                    nf[self.updown_index] = last_values[self.updown_index] + math.floor((IMG_HEIGHT/2 - self.target_coordinates[1])/10)
                    self.wait_down = 50
                elif IMG_HEIGHT/2 - self.target_coordinates[1] < -15 and self.wait_down <= 0:
                    nf[self.updown_index] = last_values[self.updown_index] + math.floor((IMG_HEIGHT/2 - self.target_coordinates[1])/10)
                    self.wait_up = 50
            else:
                # External camera
                updown = (1-(self.target_coordinates[1] / IMG_HEIGHT))
                if updown >= self.scaled_upcorner:
                    updown = 1
                updown = updown * 255
                leftright = (1-(self.target_coordinates[0] / IMG_WIDTH)) * 255

                if leftright - last_values[self.leftright_index] > 5:
                    nf[self.leftright_index] = last_values[self.leftright_index] + self.interpolation_step
                elif leftright - last_values[self.leftright_index] < 5:
                    nf[self.leftright_index] = last_values[self.leftright_index] - self.interpolation_step

                if updown - last_values[self.updown_index] > 5:
                    nf[self.updown_index] = last_values[self.updown_index] + self.interpolation_step
                elif updown - last_values[self.updown_index] < 5:
                    nf[self.updown_index] = last_values[self.updown_index] - self.interpolation_step

            self.previous_target_coordinates = self.target_coordinates

            ### Keep eyes straight ###
            if current_app.controller.controller_type == ControllerType.ANDROID:
                nf[2] = nf[3] = 127
            else:
                nf[1] = 127 # eyes straight  
            #logging.warn("self.lv: {}".format(self.lv))

        self.wait_up -= 1
        self.wait_down -= 1
        
        return nf

class HlabAnimationScheduler:
    def __init__(self, animations) -> None:
        names = [a.name for a in animations]
        duplicates = [n for n in names if names.count(n) > 1]
        if len(duplicates) > 0:
            logging.error('found duplicate names in predefined animations: {}'.format(duplicates))
        self.animations = animations
        self.animations.sort(key=lambda anim: anim.prio)

    def get_animation_by_name(self, name):
        for a in self.animations:
            if a.name == name:
                return a
        return None

    def setGroupActive(self, groupname, active):
        for anim in self.animations:
            if anim.group == groupname:
                anim.active = active

    def toggleActive(self, anims):
        for anim in anims:
            if anim.active:
                anim.deactivate()
            else:
                anim.activate()

    def toggle_by_name(self, names):
        anims = [a for a in self.animations if a.name in names]
        self.toggleActive(anims)

    def activate_by_name(self, names, start_with_pause=False):
        for a in self.animations:
            if a.name in names:
                a.activate(start_with_pause)

    def deactivate_by_name(self, names):
        for a in self.animations:
            if a.name in names:
                a.deactivate()
        

    def add_or_replace_animation(self, animation):
        if animation.name in [a.name for a in self.animations]:
            self.deleteAnimationByName(animation.name)
        self.animations.append(animation)
        self.animations.sort(key=lambda anim: anim.prio)

    def deleteAnimationByName(self, name):
        self.animations = [a for a in self.animations if a.name != name]

    def get_combined_frame(self, initialFrame):
        for anim in self.animations:
            if anim.active:
                nf = anim.nextFrame(initialFrame)
                for index, value in enumerate(nf):
                    if value is not None:
                        if anim.mode == AnimationMode.ABSOLUTE:
                            # Note: animations are sorted by prio
                            initialFrame[index] = value
                        elif anim.mode == AnimationMode.RELATIVE:
                            initialFrame[index] = max(min(initialFrame[index] + value, 255), 0)
        return initialFrame

