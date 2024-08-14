import mediapipe as mp
from mediapipe.tasks import python
import cv2
from mediapipe.tasks.python.vision import FaceLandmarkerResult
from utils.live_movement.movement import mediapipe_bs_to_face_expr, add_mh_head_rot, mediapipe_min_max_from_bs
from live_link.config.settings import arkit_scaling_min_max, arkit_scaling_generic, headscale
from pathlib import Path
from live_link.ll_sender import send_face_to_metahuman, send_state_to_metahuman


#@title Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# Create a face landmarker instance with the live stream mode:
def sendToMetaHuman(result: FaceLandmarkerResult, output_image: mp.Image, timestamp_ms: int):
    global results
    #print('face landmarker result: {}'.format(result))
    results=result

results=None

# Mediapipe setup
BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
FaceLandmarkerResult = mp.tasks.vision.FaceLandmarkerResult
VisionRunningMode = mp.tasks.vision.RunningMode
model_path = Path('D:/GIT/unreal_agent123123/python_client/models/mediapipe/face_landmarker.task')
results = None

options = FaceLandmarkerOptions(
    base_options=BaseOptions(model_asset_path=model_path),
    running_mode=VisionRunningMode.LIVE_STREAM,
    result_callback=sendToMetaHuman,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=True,
    num_faces=1
)




# define a video capture object


#vid.set(3, 1920)
#vid.set(4, 1080)


from datetime import datetime

def mirror_user(mirroring):
    vid = cv2.VideoCapture(0)
    with FaceLandmarker.create_from_options(options) as landmarker:
        # Use OpenCV’s VideoCapture to start capturing from the webcam.
        # Create a loop to read the latest frame from the camera using #
        # VideoCapture#read()

        start=datetime.now()
        while (mirroring()):

            # Capture the video frame
            # by frame
            ret, frame = vid.read()

            if not ret:
                #print("Error: Failed to capture image")
                continue

            if frame is None or frame.size == 0:
                #print("Warning: Captured an empty frame")
                continue

            # Display the resulting frame
            cv2.imshow('frame', frame)

            #print('fps: ')

            # the 'q' button is set as the
            # quitting button you may use any
            # desired button of your choice
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

            # Convert the frame received from OpenCV to a MediaPipe’s Image object.
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame)

            # Send live image data to perform face landmarking.
            # The results are accessible via the `result_callback` provided in the `FaceLandmarkerOptions` object.
            # The face landmarker must be created with the live stream mode.
            ts= int(vid.get(cv2.CAP_PROP_POS_MSEC))
            #print(ts)
            landmarker.detect_async(mp_image, ts)

            # translate face expression from mediapipe to meta-human
            frame_keys = {}
            if not results is None and len(results.face_blendshapes)>0:
                face_expr = mediapipe_bs_to_face_expr(results.face_blendshapes[0], arkit_scaling_generic)
                mediapipe_min_max_from_bs(results.face_blendshapes[0])

                f_transf_mat=results.facial_transformation_matrixes[0] if len(results.facial_transformation_matrixes)>0 else results.facial_transformation_matrixes
                face_expr = add_mh_head_rot(face_expr, f_transf_mat, headscale)

                send_face_to_metahuman(face_expr)

        print("false mirroring")
        # After the loop release the cap object
        vid.release()
        # Destroy all the windows
        cv2.destroyAllWindows()




    print("End of listening thread")

def mirror():
    return True
if __name__=="__main__":
    send_state_to_metahuman(0.0)
    mirror_user(mirror)