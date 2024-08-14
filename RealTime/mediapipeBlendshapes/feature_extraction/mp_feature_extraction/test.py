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

BaseOptions = mp.tasks.BaseOptions
FaceLandmarker = mp.tasks.vision.FaceLandmarker
FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
VisionRunningMode = mp.tasks.vision.RunningMode

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_holistic = mp.solutions.holistic



def add_mh_head_rot(face_expr, facial_transform_matrix, head_scale):
    if len(facial_transform_matrix) > 0:
        scaled_matrix = np.dot(facial_transform_matrix, np.diag([head_scale, head_scale, head_scale, 1]))
        rot_matrix_3x3 = scaled_matrix[:3, :3]
        rot = Rotation.from_matrix(rot_matrix_3x3).as_euler('xyz', degrees=False)
        face_expr['HeadYaw'] = rot[1]  # x
        face_expr['HeadRoll'] = rot[2]  # y
        face_expr['HeadPitch'] = rot[0] * -1.0  # z
    return face_expr


# Function to convert normalized landmark coordinates to image coordinates
def get_image_coordinate(landmark, frame_width, frame_height):
    return int(landmark.x * frame_width), int(landmark.y * frame_height)


# Improved function to find the bounding box for the face
def find_passport_bounding_box(lm_body, frame_width, frame_height):
    mp_holistic = mp.solutions.holistic

    key_landmarks = [
        mp_holistic.PoseLandmark.RIGHT_EYE_OUTER,
        mp_holistic.PoseLandmark.LEFT_EYE_OUTER,
        mp_holistic.PoseLandmark.RIGHT_SHOULDER,
        mp_holistic.PoseLandmark.LEFT_SHOULDER,
        mp_holistic.PoseLandmark.NOSE,
        mp_holistic.PoseLandmark.RIGHT_EAR,
        mp_holistic.PoseLandmark.LEFT_EAR,
        mp_holistic.PoseLandmark.MOUTH_LEFT,
        mp_holistic.PoseLandmark.MOUTH_RIGHT
    ]

    image_coords = {landmark: get_image_coordinate(lm_body[landmark], frame_width, frame_height) for landmark in
                    key_landmarks}

    # Get the extreme points
    min_x = min(coord[0] for coord in image_coords.values())
    max_x = max(coord[0] for coord in image_coords.values())
    min_y = min(coord[1] for coord in image_coords.values())
    max_y = max(coord[1] for coord in image_coords.values())

    # Calculate width and height of bounding box
    box_width = max_x - min_x
    box_height = max_y - min_y

    # Apply scaling factors
    width_scaling = 1.2
    height_scaling = 1.5

    scaled_width = int(box_width * width_scaling)
    scaled_height = int(box_height * height_scaling)

    center_x = (min_x + max_x) // 2
    center_y = (min_y + max_y) // 2

    top_left_x = max(0, center_x - scaled_width // 2)
    top_left_y = max(0, center_y - scaled_height // 2)
    bottom_right_x = min(frame_width, center_x + scaled_width // 2)
    bottom_right_y = min(frame_height, center_y + scaled_height // 2)

    return {
        'top_left_bb': (top_left_x, top_left_y),
        'bottom_right_bb': (bottom_right_x, bottom_right_y)
    }


# Function to draw landmarks on the image
def draw_landmarks_on_image(rgb_image, detection_result):
    face_landmarks_list = detection_result.face_landmarks
    annotated_image = np.copy(rgb_image)

    # Loop through the detected faces to visualize
    for idx in range(len(face_landmarks_list)):
        face_landmarks = face_landmarks_list[idx]

        # Draw the face landmarks
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


# Function to plot face blendshapes bar graph
def plot_face_blendshapes_bar_graph(face_blendshapes):
    # Extract the face blendshapes category names and scores
    face_blendshapes_names = [face_blendshapes_category.category_name for face_blendshapes_category in face_blendshapes]
    face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in face_blendshapes]
    # The blendshapes are ordered in decreasing score value
    face_blendshapes_ranks = range(len(face_blendshapes_names))

    fig, ax = plt.subplots(figsize=(12, 12))
    bar = ax.barh(face_blendshapes_ranks, face_blendshapes_scores, label=[str(x) for x in face_blendshapes_ranks])
    ax.set_yticks(face_blendshapes_ranks, face_blendshapes_names)
    ax.invert_yaxis()

    # Label each bar with values
    for score, patch in zip(face_blendshapes_scores, bar.patches):
        plt.text(patch.get_x() + patch.get_width(), patch.get_y(), f"{score:.4f}", va="top")

    ax.set_xlabel('Score')
    ax.set_title("Face Blendshapes")
    plt.tight_layout()
    plt.show()

def pad_image_with_black_pixels(cropped_image,target_width, target_height):
    padding_width = target_width - cropped_image.shape[1]
    padding_height = target_height - cropped_image.shape[0]

    # Create a black canvas of the target size
    padded_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)

    # Paste the cropped image onto the canvas
    padded_image[
        padding_height:padding_height + cropped_image.shape[0],
        padding_width:padding_width + cropped_image.shape[1]
    ] = cropped_image
    return padded_image

# Function to process the video and extract landmarks
def video_to_facial_landmarks(video_in, save_audio, save_video, video_out, video_out_cropped, audio_out):


    options = FaceLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=r'/models/face_landmarker.task'),
                                    output_face_blendshapes=True,
                                    output_facial_transformation_matrixes=True,
                                    running_mode=VisionRunningMode.VIDEO,
                                    num_faces=1)


    with FaceLandmarker.create_from_options(options) as landmarker:
        with mp_holistic.Holistic(
                static_image_mode=False,
                model_complexity=2,
                smooth_landmarks=True,
                refine_face_landmarks=True) as holistic:

            results = []
            vid = cv2.VideoCapture(video_in)
            fps = vid.get(cv2.CAP_PROP_FPS)
            frame_width = int(vid.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(vid.get(cv2.CAP_PROP_FRAME_HEIGHT))

            if save_video:
                out = cv2.VideoWriter(video_out, cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width, frame_height))
                out_cropped = cv2.VideoWriter(video_out_cropped, cv2.VideoWriter_fourcc(*'mp4v'), fps,
                                              (frame_width, frame_height))

            ts = []
            while vid.isOpened():
                ret, frame = vid.read()
                if not ret:
                    break

                ts.append(int(vid.get(cv2.CAP_PROP_POS_FRAMES) * (1000 / fps)))
                lm_body_pred = holistic.process(frame)
                frame_lm = deepcopy(frame)

                mp_drawing.draw_landmarks(
                    frame_lm,
                    lm_body_pred.face_landmarks,
                    mp_holistic.FACEMESH_CONTOURS)
                mp_drawing.draw_landmarks(
                    frame_lm,
                    lm_body_pred.pose_landmarks,
                    mp_holistic.POSE_CONNECTIONS)

                try:
                    bounding_box = find_passport_bounding_box(lm_body_pred.pose_landmarks.landmark, frame_width,
                                                              frame_height)
                    cropped_image = frame[bounding_box['top_left_bb'][1]:bounding_box['bottom_right_bb'][1],
                                    bounding_box['top_left_bb'][0]:bounding_box['bottom_right_bb'][0]]

                    cropped_img_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
                    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cropped_img_rgb)
                    lm_face_pred = landmarker.detect_for_video(mp_image, ts[-1])

                    if lm_face_pred.face_landmarks:
                        cropped_lm_image = draw_landmarks_on_image(cropped_image, lm_face_pred)
                        padded_cropped_lm_img = pad_image_with_black_pixels(cropped_lm_image, frame_width, frame_height)
                    else:
                        padded_cropped_lm_img = frame

                except Exception as e:
                    print('Exception: ' + str(e))
                    continue

                results.append({
                    'ts': ts[-1],
                    'landmarker_face': lm_face_pred,
                    'landmarker_body': lm_body_pred
                })

                if save_video:
                    out_cropped.write(padded_cropped_lm_img)
                    out.write(frame_lm)

            vid.release()
            if save_video:
                out.release()
                out_cropped.release()
                save_videos_with_audio(video_in, [video_out, video_out_cropped])

            if save_audio:
                save_wav(video_in, audio_out)

            return results

def save_wav(video_in, audio_out):
    video_clip = VideoFileClip(video_in)
    audio=video_clip.audio
    audio.write_audiofile(audio_out, codec='pcm_s16le')

def save_videos_with_audio (video_in, videos_to_combine):
    original_video_clip = VideoFileClip(video_in)
    for video in videos_to_combine:
        modified_video_clip = VideoFileClip(video)
        final_video_clip = modified_video_clip.set_audio(original_video_clip.audio)
        final_video_clip.write_videofile(video[:-4] + '_va.mp4', codec='libx264')
        os.remove(video)

def mediapipe_bs_to_face_expr(blendshapes, arkit_scaler=0):
    frame_keys={}#
    if len(blendshapes) >0:
        for blendshape in blendshapes:
            if blendshape.category_name=='_neutral':
                continue
            arkit_name = mediapipe_2_arkit[blendshape.category_name]
            #scale bs value from an interval [min, max] --> [0,1]
            #frame_keys[arkit_name] = (blendshape.score - arkit_scaler[arkit_name][0]) / (arkit_scaler[arkit_name][1] - arkit_scaler[arkit_name][0])
            frame_keys[arkit_name] = blendshape.score

    face_expr = FaceExpression(1, **frame_keys)
    return face_expr
def main(video_in, video_out, video_out_cropped, audio_out, head_scale):
    results = video_to_facial_landmarks(video_in, save_audio=True, save_video=True, video_out=video_out,
                                        video_out_cropped=video_out_cropped, audio_out=audio_out)

    data = []
    for result in results:
        face_expr = mediapipe_bs_to_face_expr(result['landmarker_face'].face_blendshapes[0])
        f_transf_mat = result['landmarker_face'].facial_transformation_matrixes[0] if len(
            result['landmarker_face'].facial_transformation_matrixes) > 0 else result[
            'landmarker_face'].facial_transformation_matrixes
        face_expr = add_mh_head_rot(face_expr, f_transf_mat, head_scale)
        data.append(face_expr)

    with open('output.csv', 'w', newline='') as csvfile:
        fieldnames = ['ts', 'HeadYaw', 'HeadPitch', 'HeadRoll'] + list(data[0].keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for idx, row in enumerate(data):
            row['ts'] = results[idx]['ts']
            writer.writerow(row)


if __name__ == "__main__":
    video_in = r'D:\GitHub\sara_thesis\data\test.avi'
    video_out = r'D:\GitHub\sara_thesis\data\test_output_video.mp4'
    video_out_cropped = r'D:\GitHub\sara_thesis\data\test_video_cropped.mp4'
    audio_out = r'D:\GitHub\sara_thesis\data\output_audio.wav'
    head_scale = 1.0

    main(video_in, video_out, video_out_cropped, audio_out, head_scale)
