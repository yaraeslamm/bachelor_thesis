from flask import (
    Blueprint, render_template, current_app, Response
)
import logging
import cv2
from hlabandroidpylib.andr_controller import ControllerType

import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import util

from animations import HlabLookAtAnimation
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

import pathlib
from dotenv import load_dotenv
import os

load_dotenv(pathlib.Path(__file__).parent.joinpath('.env').resolve())

CAMINDEX = int(os.environ.get('CAMINDEX', 0))

DEFAULTSENSITIVITY= 0.5


facedetector_bp = Blueprint('facedetector', __name__, url_prefix='/facedetector')

@facedetector_bp.route('/', methods=['GET'])
def show_facedetection():
    controller = getattr(current_app, 'controller', None)
    usb_ports = util.get_usb_ports(current_app)
    connected = False
    if controller is not None:
        connected = controller.connected

    return render_template(
        'facedetector.html',
        usb_ports=usb_ports,
        connected=connected,
    )

@facedetector_bp.route('/video_feed')
def video_feed():
    # return the response generated along with the specific media
    # type (mime type)
    print('video_feed')
    return Response(show_webcam(current_app._get_current_object()),
        mimetype = "multipart/x-mixed-replace; boundary=frame")

@facedetector_bp.route('/video_popup', methods=['GET'])
def video_popup():
    print('video_popup')
    return render_template(
        'img_popup.html'
    )

@facedetector_bp.route('/stop_video', methods=['GET'])
def stop_video():
    print('stop_video')
    webcam = getattr(current_app, 'webcam', None)
    if webcam is None:
        return {'state': 'nothing to stop'}
    else:
        webcam.release()
        return {'state': 'released webcam'}


@facedetector_bp.route('/toggle_facedetection')
def start_face_detection():
    all_img_handlers = getattr(current_app, 'img_handlers', [])
    handlers_without_detect_faces = [ih for ih in all_img_handlers if ih.__name__ != 'detect_faces']
    if len(handlers_without_detect_faces) == len(all_img_handlers):
        model=hub.load('https://tfhub.dev/google/movenet/multipose/lightning/1')
        movenet=model.signatures['serving_default']
        print('start_face_detection model loaded')
        
        def detect_faces(image, framecount, app):
            img = image.copy()
            img=tf.image.resize_with_pad(tf.expand_dims(img,axis=0),480,640)#resize multiple of 32, larger u go cud slow down
            input_img=tf.cast(img,dtype=tf.int32)
            
            #Detection section
            results=movenet(input_img)
            #Apply transformation to only have keypoints with scores
            keypoints_with_scores=results['output_0'].numpy()[:,:,:51].reshape((6,17,3))
            # Render keypoints
            with app.app_context():
                loop_through_people(image, keypoints_with_scores, DEFAULTSENSITIVITY, framecount, current_app._get_current_object())
            return image
        
        img_handlers = getattr(current_app, 'img_handlers', [])
        img_handlers.append(detect_faces)
        current_app.img_handlers = img_handlers
        return {'message': 'added image handler'}
    else:
        current_app.img_handlers = handlers_without_detect_faces
        return {'message': 'removed image handler'}
    

@facedetector_bp.route('/track_faces')
def track_faces():
    anim = HlabLookAtAnimation(description='Look at detected faces', name="lookAtDetectedFace")
    anim.activate()
    current_app.anim_scheduler.add_or_replace_animation(anim)
    #start_polling(current_app, anim)
    return {'polling': True}

def register(app):
    app.register_blueprint(facedetector_bp)

# Function to loop through each person detected and render
def loop_through_people(frame, keypoints_with_scores, confidence_threshold, framecount, app):
    personcount = 0
    allnosepoints = []
    allshapes = []
    for person in keypoints_with_scores:
        y, x, c = frame.shape
        shaped = np.squeeze(np.multiply(person, [y,x,1]))
        similar_person_found = False
        for oldshape in allshapes:
            for kpold in oldshape:
                kyold, kxold, kpold_conf = kpold
                for kp in shaped:
                    ky, kx, kp_conf = kp
                    if kyold == ky and kxold == kx:
                        similar_person_found = True
        if similar_person_found:
            continue
        allshapes.append(shaped)
        count = 0
        nosepoint = None
        
        for kp in shaped:
            ky, kx, kp_conf = kp

            found = False
            for anp in allnosepoints:
                if abs(anp[1][0] - kx) < 4 and abs(anp[1][1] - ky) < 4:
                    found = True
            if not found: # we found a new nosepoint
                if kp_conf > confidence_threshold:
                    if count == 0: # blue nose keypoint(s)
                        cv2.circle(frame, (int(kx), int(ky)), 6, (255,0,0), -1)
                        nosepoint = [int(kx), int(ky)]
                        allnosepoints.append([personcount, nosepoint])
                        personcount += 1
                    else: # all other keypoints in black
                        cv2.circle(frame, (int(kx), int(ky)), 6, (10,10,10), -1)
                    cv2.putText(frame, str(count), (int(kx) + 10, int(ky) + 10), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,255))
                count += 1

    if len(allnosepoints) > 0:
        with app.app_context():
            framedata = getattr(current_app, "framedata", None)
            # print("framedata is not None?")
            if framedata is not None:
                framedata.insert(0, [framecount, allnosepoints])
                framedata = framedata[0:5]
                #logging.warn("framedata in loop_throug_people: {}".format(framedata))
                current_app.framedata = framedata
    cv2.putText(frame, "person count: " + str(personcount), (20, 20), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255))


def show_webcam(app):
    # loop over frames from the output stream
    webcam = cv2.VideoCapture(CAMINDEX)
    if not webcam.isOpened():
        logging.error(f'Cannot open camera at index {CAMINDEX}')
        return
    
    framecount = 0
    with app.app_context():
        framedata = getattr(current_app, "framedata", None)
        if framedata is None:
            current_app.framedata = []
        current_app.webcam = webcam
    while webcam.isOpened():
        ret, image = webcam.read()
        if not ret or image is None:
            logging.warn('no image')
            return
        
        with app.app_context():
            img_handlers = getattr(current_app, 'img_handlers', [])
            for handler_fn in img_handlers:
                image = handler_fn(image, framecount=framecount, app=current_app)

        (_, encodedImage) = cv2.imencode(".jpg", image)
        yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')

        framecount = (framecount + 1) % 1000000


def update_detection_values(app, anim):
    with app.app_context():
        if len(app.framedata) == 0:
            return
        fd = app.framedata.copy()
        lastvalues = app.controller.last_values.copy()

        # TODO: some logic to get coordinates from framedata
        # choosing some of the first values from framedata now to check if they are updated and propagated to the animation
        ########
        # fd might look like this:
        # [
        #     [956, [[0, [358, 256]], [1, [358, 256]], [2, [358, 256]]]],
        #     [956, [[0, [355, 246]], [1, [355, 246]], [2, [355, 246]], [3, [355, 246]]]],
        #     [
        #         955,
        #         [
        #             [0, [360, 253]],
        #             [1, [298, 237]],
        #             [2, [360, 253]],
        #             [3, [360, 251]],
        #             [4, [360, 253]],
        #         ],
        #     ],
        #     [955, [[0, [356, 247]], [1, [356, 247]], [2, [356, 246]], [3, [356, 247]]]],
        #     [954, [[0, [172, 87]], [1, [359, 253]], [2, [359, 253]], [3, [360, 252]]]],
        #     [954, [[0, [170, 95]], [1, [355, 247]], [2, [355, 247]]]],
        #     [953, [[0, [359, 260]], [1, [360, 255]], [2, [381, 226]], [3, [382, 226]]]],
        #     [953, [[0, [355, 245]], [1, [355, 245]], [2, [355, 248]]]],
        #     [952, [[0, [171, 97]], [1, [359, 260]]]],
        # ]
        # '956' = keyframe number; [[0, [358,256]], ..] = nosepoint(s)-number and x/y coords
        # same keyframe number is a little strange, though
        # IDEA: reduce outer list to those frames with most nosepoints (in inner list) 
        fd.sort(reverse=True)
        # logging.warn('update_detection_values: {}'.format(fd))
        filtered_fd = []
        keyframenumber = -1
        keyframe = []
        for frame in fd:
            # print("index: ", index, ", len(fd): ", len(fd))
            if keyframenumber == -1:
                keyframenumber = frame[0]
                keyframe = frame
                continue
            if frame[0] == keyframenumber and len(keyframe[1]) < len(frame[1]):
                keyframe = frame
                continue
            if frame[0] != keyframenumber:
                filtered_fd.append(keyframe)
                keyframe = frame
                keyframenumber = frame[0]
                continue

        # logging.warn("filtered fd: {}".format(filtered_fd))
        nosepoint_counts = []
        if (len(filtered_fd) > 0):
            nosepoint_counts = [[1, x] for x in filtered_fd[0] if isinstance(x, list)][0][1] # use the noisepoints of the first frame
            for index in range(1, len(filtered_fd)): # check all subsequent frames
                # print("next frame: ", filtered_fd[index])
                for npc in nosepoint_counts:
                    for frame_np in filtered_fd[index][1]: # loop through all nosepoints in the current frame
                        if abs(frame_np[1][0] - npc[1][0]) < 3 and abs(frame_np[1][1] - npc[1][1]) < 3:
                            npc[0] = npc[0] + 1
                            continue
        nosepoint_counts.sort(reverse=True)
        logging.warn("nosepoint_counts: {}".format(nosepoint_counts)) 
        anim.target_coordinates = nosepoint_counts
        
        
def start_polling(current_app, anim):
    current_app.polling_secs = 0.1
    assert getattr(current_app, 'controller', None) is not None

    scheduler = getattr(current_app, 'scheduler', None)
    if scheduler is None:
        print('no scheduler exists')
        scheduler = BackgroundScheduler()
        scheduler.add_job(update_detection_values, 'interval', seconds=current_app.polling_secs, kwargs={'app': current_app._get_current_object(), 'anim': anim})
        scheduler.start()
        current_app.scheduler = scheduler
        atexit.register(lambda: current_app.scheduler.shutdown(wait=False))
    else:
        print('scheduler exists adding job')
        scheduler.add_job(update_detection_values, 'interval', seconds=current_app.polling_secs, kwargs={'app': current_app._get_current_object(), 'anim': anim})