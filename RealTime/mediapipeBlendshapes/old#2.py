
import cv2
import numpy as np
from scipy.spatial.transform import Rotation
from copy import deepcopy
from mediapipe.framework.formats import landmark_pb2
import matplotlib.pyplot as plt
import csv
from mediapipe import solutions
import mediapipe as mp
from mediapipe.tasks import python
from moviepy.editor import VideoFileClip
import os
from utils import FaceExpression, mediapipe_2_arkit
import face_alignment
from face_alignment import LandmarksType
import mediapipe.tasks as mp_python


import time
import requests
import json
import zmq


#print(dir(mp_python.vision))







BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

def add_mh_head_rot(face_expr, facial_transform_matrix, head_scale):
    if len(facial_transform_matrix) > 0:
        scaled_matrix = np.dot(facial_transform_matrix, np.diag([head_scale, head_scale, head_scale, 1]))
        rot_matrix_3x3 = scaled_matrix[:3, :3]
        rot = Rotation.from_matrix(rot_matrix_3x3).as_euler('xyz', degrees=False)
        face_expr.shape_keys['HeadYaw'] = rot[1]  # x
        face_expr.shape_keys['HeadRoll'] = rot[2]  # y
        face_expr.shape_keys['HeadPitch'] = rot[0] * -1.0  # z
    return face_expr

def get_image_coordinate(landmark, frame_width, frame_height):
    return int(landmark[0] * frame_width), int(landmark[1] * frame_height)



def get_face_bounding_box(image,face_alignment_model, padding_percentage=0.2):
    detected_faces = face_alignment_model.get_landmarks(image)
    if detected_faces is None or len(detected_faces) == 0:
        print("No face detected.")
        return None
    elif len(detected_faces) > 1:
        print("multiple faces detected, taking the first")

    landmarks = detected_faces[0]
    x_min, y_min = np.min(landmarks, axis=0)
    x_max, y_max = np.max(landmarks, axis=0)

    width = x_max - x_min
    height = y_max - y_min
    padding_x = width * padding_percentage
    padding_y = height * padding_percentage
    x_min = int(max(x_min - padding_x, 0))
    y_min = int(max(y_min - padding_y, 0))
    x_max = int(min(x_max + padding_x, image.shape[1]))
    y_max = int(min(y_max + padding_y, image.shape[0]))
    return (x_min, y_min, x_max, y_max)
def draw_landmarks_on_image(rgb_image, detection_result):
    face_landmarks_list = detection_result.face_landmarks
    annotated_image = np.copy(rgb_image)

    for idx in range(len(face_landmarks_list)):
        face_landmarks = face_landmarks_list[idx]

        face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
        face_landmarks_proto.landmark.extend([
            landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
        ])

        solutions.drawing_utils.draw_landmarks(
            image=annotated_image,
            landmark_list=face_landmarks_proto,
            connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp.solutions.drawing_styles
            .get_default_face_mesh_tesselation_style())
        solutions.drawing_utils.draw_landmarks(
            image=annotated_image,
            landmark_list=face_landmarks_proto,
            connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp.solutions.drawing_styles
            .get_default_face_mesh_contours_style())
        solutions.drawing_utils.draw_landmarks(
            image=annotated_image,
            landmark_list=face_landmarks_proto,
            connections=mp.solutions.face_mesh.FACEMESH_IRISES,
            landmark_drawing_spec=None,
            connection_drawing_spec=mp.solutions.drawing_styles
            .get_default_face_mesh_iris_connections_style())

    return annotated_image

def plot_face_blendshapes_bar_graph(face_blendshapes):
    face_blendshapes_names = [face_blendshapes_category.category_name for face_blendshapes_category in face_blendshapes]
    face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in face_blendshapes]
    face_blendshapes_ranks = range(len(face_blendshapes_names))

    fig, ax = plt.subplots(figsize=(12, 12))
    bar = ax.barh(face_blendshapes_ranks, face_blendshapes_scores, label=[str(x) for x in face_blendshapes_ranks])
    ax.set_yticks(face_blendshapes_ranks, face_blendshapes_names)
    ax.invert_yaxis()

    for score, patch in zip(face_blendshapes_scores, bar.patches):
        plt.text(patch.get_x() + patch.get_width(), patch.get_y(), f"{score:.4f}", va="top")

    ax.set_xlabel('Score')
    ax.set_title("Face Blendshapes")
    plt.tight_layout()
    plt.show()

def pad_image_with_black_pixels(cropped_image, target_width, target_height):
    padding_width = target_width - cropped_image.shape[1]
    padding_height = target_height - cropped_image.shape[0]

    padded_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    padded_image[
        padding_height:padding_height + cropped_image.shape[0],
        padding_width:padding_width + cropped_image.shape[1]
    ] = cropped_image
    return padded_image

detection_results = []


def result_callback(result, output_image, timestamp_ms):
    if isinstance(result.face_landmarks, list) and len(result.face_landmarks) > 0:
        for landmarks in result.face_landmarks:
            if landmarks.HasField('face_blendshapes'):
                blendshapes = landmarks.face_blendshapes
                print(f"Timestamp: {timestamp_ms}, Blendshapes: {blendshapes}")
            else:
                print(f"No blendshapes detected in this face at Timestamp: {timestamp_ms}")
    else:
        print(f"No face landmarks detected at Timestamp: {timestamp_ms}")




def result_callback(result, output_image, timestamp_ms):
    # Process the result here, e.g., print blendshapes or display the output_image
    # if result.face_landmarks:
    #     print(f"Timestamp: {timestamp_ms}, Face Landmarks: {result.face_landmarks}")
      return
def video_to_facial_landmarks(video_out, video_out_cropped, audio_out):
    options = FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=r'/home/yara/Downloads/face_landmarker.task'),
        output_face_blendshapes=True,
        output_facial_transformation_matrixes=True,
        running_mode=VisionRunningMode.LIVE_STREAM,
        num_faces=1,
        result_callback=result_callback  # Add this line
    )

    face_alignment_model = face_alignment.FaceAlignment(
        LandmarksType.TWO_D, device='cpu', face_detector='blazeface', face_detector_kwargs={'back_model': True}
    )

    with FaceLandmarker.create_from_options(options) as landmarker:
        vid = cv2.VideoCapture(0)  # Use webcam
        frame_width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

        previous_ts = 0
        while True:
            ret, frame = vid.read()
            if not ret:
                break

            current_ts = int(time.time() * 1000)  # Current time in milliseconds
            if current_ts <= previous_ts:
                current_ts = previous_ts + 1
            previous_ts = current_ts

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            try:
                bounding_box = get_face_bounding_box(frame_rgb, face_alignment_model, padding_percentage=0.2)
                if bounding_box is not None:
                    x_min, y_min, x_max, y_max = bounding_box
                    cropped_image = frame[y_min:y_max, x_min:x_max]
                else:
                    cropped_image = frame

                cropped_img_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cropped_img_rgb)
                landmarker.detect_async(mp_image, current_ts)  # Pass the timestamp here

            except Exception as e:
                print('Exception: ' + str(e))

        
                    # Display the frame
            cv2.imshow('Webcam Feed', frame)

            # Break the loop on 'q' key press
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        vid.release()




def mediapipe_bs_to_face_expr(blendshapes, arkit_scaler=0):
    frame_keys = {}
    if len(blendshapes) > 0:
        for blendshape in blendshapes:
            if blendshape.category_name == '_neutral':
                continue
            arkit_name = mediapipe_2_arkit[blendshape.category_name]
            frame_keys[arkit_name] = blendshape.score

    face_expr = FaceExpression(1, **frame_keys)
    return face_expr

#map_blend_shapes_to_actuators(result['landmarker_face'].face_blendshapes[0])

def map_blend_shapes_to_actuators(blendshapes):
    actuators = [255] * 14
    # actuators[1]= result['landmarker_face'].face_blendshapes[0]
    #actuators[0] = blendshapes.get('browDownLe', 0) - blendshapes.get('browInnerUp', 0)  # browUD
    #actuators[0]= 255*blendshapes[1]
    return actuators


def main(video_out,video_out_cropped, audio_out, head_scale):
  print('whyyyyyyyyy')
    # ZMQ Setup
  context = zmq.Context()
  socket = context.socket(zmq.PUB)
  socket.bind("tcp://*:5555")
  time.sleep(2) 
  data_list = map_blend_shapes_to_actuators(0)
  print(data_list)
  message = json.dumps(data_list)
  socket.send_string(message)
  time.sleep(1) 
  print('abokeda')

  print(data_list)
  results = video_to_facial_landmarks( video_out=video_out,
  video_out_cropped=video_out_cropped, audio_out=audio_out)
  print('yl3anabokeda')
#   message = json.dumps(generated_list)
#   socket.send_string(message)
#   print(f"Sent: {message}")




  
  data = []
  all_blendshapes=set()
 
  for result in results:

      if len(result['landmarker_face'].face_blendshapes):
          #print(result['landmarker_face'].face_blendshapes[:])
          face_blendshapes=result['landmarker_face'].face_blendshapes[0]
          face_expr = mediapipe_bs_to_face_expr(result['landmarker_face'].face_blendshapes[0])
          f_transf_mat = result['landmarker_face'].facial_transformation_matrixes[0] if len(
            result['landmarker_face'].facial_transformation_matrixes) > 0 else result[
            'landmarker_face'].facial_transformation_matrixes
          face_expr = add_mh_head_rot(face_expr, f_transf_mat, head_scale)
          data.append(face_expr)
          all_blendshapes.update([blendshape.category_name for blendshape in face_blendshapes])
          
  print("all blendshapes categorz names:")
  print(all_blendshapes)

  with open('output.csv', 'w', newline='') as csvfile:
       fieldnames = ['ts', 'HeadYaw', 'HeadPitch', 'HeadRoll'] + list(data[0].shape_keys.keys())
       writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

       writer.writeheader()
       for idx, row in enumerate(data):
           row_dict = row.shape_keys
           row_dict['ts'] = results[idx]['ts']
           writer.writerow(row_dict)
         
if __name__ == "__main__":
# video_in = r'/Users/funnyflea7/Desktop/bachelor/sara_thesis/data/test.avi'
    video_out = r'/home/yara/Downloads/sara_thesis/data/test_output_video.mp4'
    video_out_cropped = r'/home/yara/Downloads/sara_thesis/data/test_video_cropped.mp4'
    audio_out = r'/home/yara/Downloads/sara_thesis/data/output_audio.wav'
    head_scale = 1.0          
main( video_out,video_out_cropped, audio_out, head_scale)


