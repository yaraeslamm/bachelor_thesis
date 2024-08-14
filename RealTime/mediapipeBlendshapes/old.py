
# import cv2
# import numpy as np
# from scipy.spatial.transform import Rotation
# from copy import deepcopy
# from mediapipe.framework.formats import landmark_pb2
# import matplotlib.pyplot as plt
# import csv
# from mediapipe import solutions
# import mediapipe as mp
# from mediapipe.tasks import python
# from moviepy.editor import VideoFileClip
# from utils import FaceExpression, mediapipe_2_arkit
# import face_alignment
# from face_alignment import LandmarksType
# #import mediapipe.tasks as mp_python
# import time
# import json
# import zmq
# import statistics




# BaseOptions = mp.tasks.BaseOptions
# FaceLandmarker = mp.tasks.vision.FaceLandmarker
# FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
# VisionRunningMode = mp.tasks.vision.RunningMode

# mp_drawing = mp.solutions.drawing_utils
# mp_drawing_styles = mp.solutions.drawing_styles


# # Face Alignment model
# face_alignment_model = face_alignment.FaceAlignment(
#     LandmarksType.TWO_D, device='cpu', face_detector='blazeface', face_detector_kwargs={'back_model': True}
# )

# # ZMQ Setup
# context = zmq.Context()
# socket = context.socket(zmq.PUB)
# socket.bind("tcp://*:5555")

# actuators = [0, 127, 0, 0, 0, 0, 0, 0, 0, 0, 0, 127, 127, 127]

# def add_mh_head_rot(face_expr, facial_transform_matrix, head_scale):
#     if len(facial_transform_matrix) > 0:
#         scaled_matrix = np.dot(facial_transform_matrix, np.diag([head_scale, head_scale, head_scale, 1]))
#         rot_matrix_3x3 = scaled_matrix[:3, :3]
#         rot = Rotation.from_matrix(rot_matrix_3x3).as_euler('xyz', degrees=False)
#         face_expr.shape_keys['HeadYaw'] = rot[1]  # x
#         face_expr.shape_keys['HeadRoll'] = rot[2]  # y
#         face_expr.shape_keys['HeadPitch'] = rot[0] * -1.0  # z
#     return face_expr

# def get_image_coordinate(landmark, frame_width, frame_height):
#     return int(landmark[0] * frame_width), int(landmark[1] * frame_height)


# def get_face_bounding_box(image,face_alignment_model, padding_percentage=0.2):
#     detected_faces = face_alignment_model.get_landmarks(image)
#     if detected_faces is None or len(detected_faces) == 0:
#         print("No face detected.")
#         return None
#     elif len(detected_faces) > 1:
#         print("multiple faces detected, taking the first")

#     landmarks = detected_faces[0]
#     x_min, y_min = np.min(landmarks, axis=0)
#     x_max, y_max = np.max(landmarks, axis=0)

#     width = x_max - x_min
#     height = y_max - y_min
#     padding_x = width * padding_percentage
#     padding_y = height * padding_percentage
#     x_min = int(max(x_min - padding_x, 0))
#     y_min = int(max(y_min - padding_y, 0))
#     x_max = int(min(x_max + padding_x, image.shape[1]))
#     y_max = int(min(y_max + padding_y, image.shape[0]))
#     return (x_min, y_min, x_max, y_max)
# def draw_landmarks_on_image(rgb_image, detection_result):
#     face_landmarks_list = detection_result.face_landmarks
#     annotated_image = np.copy(rgb_image)

#     for idx in range(len(face_landmarks_list)):
#         face_landmarks = face_landmarks_list[idx]

#         face_landmarks_proto = landmark_pb2.NormalizedLandmarkList()
#         face_landmarks_proto.landmark.extend([
#             landmark_pb2.NormalizedLandmark(x=landmark.x, y=landmark.y, z=landmark.z) for landmark in face_landmarks
#         ])

#         solutions.drawing_utils.draw_landmarks(
#             image=annotated_image,
#             landmark_list=face_landmarks_proto,
#             connections=mp.solutions.face_mesh.FACEMESH_TESSELATION,
#             landmark_drawing_spec=None,
#             connection_drawing_spec=mp.solutions.drawing_styles
#             .get_default_face_mesh_tesselation_style())
#         solutions.drawing_utils.draw_landmarks(
#             image=annotated_image,
#             landmark_list=face_landmarks_proto,
#             connections=mp.solutions.face_mesh.FACEMESH_CONTOURS,
#             landmark_drawing_spec=None,
#             connection_drawing_spec=mp.solutions.drawing_styles
#             .get_default_face_mesh_contours_style())
#         solutions.drawing_utils.draw_landmarks(
#             image=annotated_image,
#             landmark_list=face_landmarks_proto,
#             connections=mp.solutions.face_mesh.FACEMESH_IRISES,
#             landmark_drawing_spec=None,
#             connection_drawing_spec=mp.solutions.drawing_styles
#             .get_default_face_mesh_iris_connections_style())

#     return annotated_image

# def plot_face_blendshapes_bar_graph(face_blendshapes):
#     face_blendshapes_names = [face_blendshapes_category.category_name for face_blendshapes_category in face_blendshapes]
#     face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in face_blendshapes]
#     face_blendshapes_ranks = range(len(face_blendshapes_names))

#     fig, ax = plt.subplots(figsize=(12, 12))
#     bar = ax.barh(face_blendshapes_ranks, face_blendshapes_scores, label=[str(x) for x in face_blendshapes_ranks])
#     ax.set_yticks(face_blendshapes_ranks, face_blendshapes_names)
#     ax.invert_yaxis()

#     for score, patch in zip(face_blendshapes_scores, bar.patches):
#         plt.text(patch.get_x() + patch.get_width(), patch.get_y(), f"{score:.4f}", va="top")

#     ax.set_xlabel('Score')
#     ax.set_title("Face Blendshapes")
#     plt.tight_layout()
#     plt.show()

# def pad_image_with_black_pixels(cropped_image, target_width, target_height):
#     padding_width = target_width - cropped_image.shape[1]
#     padding_height = target_height - cropped_image.shape[0]

#     padded_image = np.zeros((target_height, target_width, 3), dtype=np.uint8)

#     padded_image[
#         padding_height:padding_height + cropped_image.shape[0],
#         padding_width:padding_width + cropped_image.shape[1]
#     ] = cropped_image
#     return padded_image




# def result_callback(result, csv_writer, header_written):
#     if result.face_blendshapes:
#         face_expr = mediapipe_bs_to_face_expr(result.face_blendshapes[0])
#         f_transf_mat = result.facial_transformation_matrixes[0] if result.facial_transformation_matrixes else []
#         face_expr = add_mh_head_rot(face_expr, f_transf_mat, 1.0)

#         # Write header only once
#         if not header_written[0]:
#             csv_writer.writerow(list(face_expr.shape_keys.keys()))
#             header_written[0] = True
        
#         # Extract blendshape names and values
#         #blendshape_names = list(face_expr.shape_keys.keys())
#         blendshapes_values = list(face_expr.shape_keys.values())
#         formatted_blendshapes_values = [f"{value:.2f}" for value in blendshapes_values]
#         #print(formatted_blendshapes_values)

#         int_blendshapes_values = [int(float((value)) * 255) for value in formatted_blendshapes_values]
#         print("Integer blendshapes (after multiplying by 255):", int_blendshapes_values)

#         # print("borwsouterL",int_blendshapes_values[3])
#         # print("browsouterR",int_blendshapes_values[4])
#         # print("dimpleL",int_blendshapes_values[27])
#         # print("dimpleR",int_blendshapes_values[28])
#         # print("stretchL",int_blendshapes_values[45])
#         # print("stretchR",int_blendshapes_values[46])
#         # print("upperL",formatted_blendshapes_values[47])
#         # print("upperR",formatted_blendshapes_values[48])
#         # print("lowerL",formatted_blendshapes_values[33])
#         # print("lowerR",formatted_blendshapes_values[34])

#         #print("mouthL",formatted_blendshapes_values[32])
#         #print("mouthR",formatted_blendshapes_values[38])

        






#         #print("smileR",int_blendshapes_values[44])

#         new_actuators_values =map_blend_shapes_to_actuators(actuators,int_blendshapes_values )
#         #new_actuators_values=actuators      
#         message = json.dumps(new_actuators_values)
#         socket.send_string(message)

#         # Write blendshapes to CSV
#         csv_writer.writerow([f"{value:.6f}" for value in blendshapes_values])
#         #print(face_expr.shape_keys)
#         time.sleep(1)



# def video_to_facial_landmarks():
#     options = FaceLandmarkerOptions(
#         base_options=python.BaseOptions(model_asset_path=r'/home/yara/Downloads/face_landmarker.task'),
#         output_face_blendshapes=True,
#         output_facial_transformation_matrixes=True,
#         running_mode=VisionRunningMode.LIVE_STREAM,
#         num_faces=1,
#         result_callback=lambda result, image, timestamp: result_callback(result, csv_writer,header_written) 
#     )

#     # face_alignment_model = face_alignment.FaceAlignment(
#     #     LandmarksType.TWO_D, device='cpu', face_detector='blazeface', face_detector_kwargs={'back_model': True}
#     # )

#     with FaceLandmarker.create_from_options(options) as landmarker:
#         #results = []
#         cap = cv2.VideoCapture(0) ##### changed this from video_in to 0 for webcam
        
#         cap.set(cv2.CAP_PROP_FPS, 30)  # Set higher FPS
#         cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set lower resolution for faster processing
#         cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
#         # fps = cap.get(cv2.CAP_PROP_FPS)
#         # frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
#         # frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

#            # Initialize CSV writer
#         csv_file = open('blendshapes.csv', mode='w', newline='')
#         csv_writer = csv.writer(csv_file)

#         header_written = [False] 


#         previous_ts = 0
#         while True:
#             ret, frame = cap.read()
#             if not ret:
#                 break

#             current_ts = int(time.time() * 1000)  # Current time in milliseconds
#             if current_ts <= previous_ts:
#                 current_ts = previous_ts + 1
#             previous_ts = current_ts

#             frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

#             frame_lm = deepcopy(frame)

#             try:
#                 bounding_box = get_face_bounding_box(frame_rgb, face_alignment_model, padding_percentage=0.2)
#                 if bounding_box is not None:
#                     x_min, y_min, x_max, y_max = bounding_box
#                     cropped_image = frame[y_min:y_max, x_min:x_max]
#                 else:
#                     cropped_image = frame

#                 cropped_img_rgb = cv2.cvtColor(cropped_image, cv2.COLOR_BGR2RGB)
#                 mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cropped_img_rgb)
#                 # lm_face_pred = landmarker.detect_for_video(mp_image, ts[-1])
#                 # lm_face_pred =
#                 landmarker.detect_async(mp_image, current_ts)

#                 # if lm_face_pred.face_landmarks:
#                 #     cropped_lm_image = draw_landmarks_on_image(cropped_image, lm_face_pred)
#                 #     padded_cropped_lm_img = pad_image_with_black_pixels(cropped_lm_image, frame_width, frame_height)

#                     # Visualize the processed frames for debugging
#                 cv2.imshow('Original Frame', frame)
#                     # cv2.imshow('Cropped Landmark Frame', cropped_lm_image)
#                 if cv2.waitKey(1) & 0xFF == ord('q'):
#                     break


#                 else:
#                     padded_cropped_lm_img = frame

#             except Exception as e:
#                 print('Exception: ' + str(e))
#                 padded_cropped_lm_img = frame



#         cap.release()

#         cv2.destroyAllWindows()


#         csv_file.close()

#         #return results


# def save_wav(video_in, audio_out):
#     video_clip = VideoFileClip(video_in)
#     audio = video_clip.audio
#     audio.write_audiofile(audio_out, codec='pcm_s16le')


# def mediapipe_bs_to_face_expr(blendshapes, arkit_scaler=0):
#     frame_keys = {}
#     if len(blendshapes) > 0:
#         for blendshape in blendshapes:
#             if blendshape.category_name == '_neutral':
#                 continue
#             arkit_name = mediapipe_2_arkit[blendshape.category_name]
#             frame_keys[arkit_name] = blendshape.score

#     face_expr = FaceExpression(1, **frame_keys)
#     return face_expr


# def map_blend_shapes_to_actuators(actuators,blendshapes):


#     #Head_Eyes

#     if (blendshapes[8]<blendshapes[9]):
#         actuators[0]= blendshapes[9] 
#     else :
#         actuators[0]= blendshapes[8]


#     if (blendshapes[16]<blendshapes[17]):
#         actuators[2]= blendshapes[17] 
#     else :
#         actuators[2]= blendshapes[16]    


#     if (blendshapes[18]<blendshapes[19]):
#         actuators[3]= blendshapes[19] 
#     else :
#         actuators[3]= blendshapes[18]    

#     #Head_Brows

#     if (blendshapes[4]<blendshapes[3]):
#         actuators[4]= blendshapes[3] 
#     else :
#         actuators[4]= blendshapes[4]
        

#     actuators[5]= blendshapes[2]


#     #Head_Mouth

#     if (blendshapes[43]<blendshapes[44]):
#         actuators[6]= blendshapes[44] 
#     else :
#         actuators[6]= blendshapes[43]   

#     #actuators[6]=statistics.mean(blendshapes[43],blendshapes[44])       



#     if (blendshapes[27]<blendshapes[28]):
#         actuators[7]= blendshapes[28] 
#     else :
#         actuators[7]= blendshapes[27]

#     #actuators[7]=statistics.mean(blendshapes[43],blendshapes[44]) 

    
#     actuators[8]=blendshapes[37]#
    

#     blendshapes[47]=blendshapes[47]*2
#     blendshapes[48]=blendshapes[48]*2

#     if (blendshapes[47]<blendshapes[48]):
#         if(blendshapes[48]<255):
#           actuators[9]= blendshapes[48]
#         else :
#             actuators[9]=255 
#     else :
#         if(blendshapes[47]<255):
#           actuators[9]= blendshapes[47]
#         else :
#             actuators[9]=255 





    
#     actuators[10]= blendshapes[24]

   
#    # actuators[4]=int((blendshapes[2]+blendshapes[3]+blendshapes[4]-blendshapes[0]-blendshapes[1])/5)


#         # Head_Eyes
#     # actuators[0] = blendshapes[8] - blendshapes[9]  # upper eyelid open close: EyeBlinkLeft - EyeBlinkRight
#     # actuators[1] = (blendshapes[14] - blendshapes[12] + blendshapes[15] - blendshapes[13]) / 2  # eyeball left right
#     # actuators[2] = (blendshapes[16] - blendshapes[10] + blendshapes[17] - blendshapes[11]) / 2  # eyeball up down
#     # actuators[3] = blendshapes[18] - blendshapes[19]  # lower eyelid open close: EyeSquintLeft - EyeSquintRight
#     # actuators[4] = (blendshapes[3] + blendshapes[4] - blendshapes[0] - blendshapes[1]) / 2  # eyebrow up down
#     # actuators[5] = blendshapes[2]  # eyebrow shrink (inner up)

#     #     # Head_Mouth
#     # actuators[6] = (blendshapes[43] - blendshapes[29] + blendshapes[44] - blendshapes[30]) / 2  # mouth corner up down

#     return actuators

    


# # ZMQ Setup
# # context = zmq.Context()
# # socket = context.socket(zmq.PUB)
# # socket.bind("tcp://*:5555")

# # actuators = [0, 127, 0, 0, 0, 0, 0, 0, 0, 0, 0, 127, 127, 127]


# #def main( head_scale):
#     # ZMQ Setup
# #   context = zmq.Context()
# #   socket = context.socket(zmq.PUB)
# #   socket.bind("tcp://*:5555")
# #   time.sleep(2) 
# #   actuators = [100] * 14
# #   data_list = map_blend_shapes_to_actuators(actuators,0)
# #   print(data_list)
# #   message = json.dumps(data_list)
# #   socket.send_string(message)
# #   time.sleep(1) 
# #  print('abokeda')

# #   print(data_list)
#   #results = video_to_facial_landmarks( )
#   #print('yl3anabokeda')

# #   data = []
 
# #   for result in results:

# #       if len(result['landmarker_face'].face_blendshapes):
# #           print(result['landmarker_face'].face_blendshapes[:])
# #           face_expr = mediapipe_bs_to_face_expr(result['landmarker_face'].face_blendshapes[0])
# #           f_transf_mat = result['landmarker_face'].facial_transformation_matrixes[0] if len(
# #             result['landmarker_face'].facial_transformation_matrixes) > 0 else result[
# #             'landmarker_face'].facial_transformation_matrixes
# #           face_expr = add_mh_head_rot(face_expr, f_transf_mat, head_scale)
# #           data.append(face_expr)
          

# if __name__ == "__main__":
#     video_to_facial_landmarks( )
#  #save_video=False
#  #video_in = r'/home/yara/Downloads/sara_thesis/data/data/test.avi'
#  #video_out = r'/home/yara/Downloads/sara_thesis/data/test_output_video.mp4'
#  #video_out_cropped = r'/home/yara/Downloads/sara_thesis/data/test_video_cropped.mp4'
#  #audio_out = r'/home/yara/Downloads/sara_thesis/data/output_audio.wav'
#  #head_scale = 1.0          
# #main( head_scale)

