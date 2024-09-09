import cv2

from scipy.spatial.transform import Rotation

import mediapipe as mp

from mediapipe.tasks import python

from mediapipe.tasks.python import vision

from mediapipe import solutions

from mediapipe.framework.formats import landmark_pb2

import numpy as np

import matplotlib.pyplot as plt

import argparse

import zmq 
import json
import time



mp_drawing = mp.solutions.drawing_utils

mp_drawing_styles = mp.solutions.drawing_styles


# ZMQ Setup
context = zmq.Context()
socket = context.socket(zmq.PUB)
socket.bind("tcp://*:5555")

#initial values of kimi's actuators
actuators = [0, 127, 0, 0, 0, 0, 0, 0, 0, 0, 0, 127, 127, 127]





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





def add_mh_head_rot(facial_transform_matrix, head_scale=1.0):

    scaled_matrix = np.dot(facial_transform_matrix, np.diag([head_scale, head_scale, head_scale, 1]))

    rot_matrix_3x3 = scaled_matrix[:3, :3]

    rot = Rotation.from_matrix(rot_matrix_3x3).as_euler('xyz', degrees=True)

    yaw = rot[1]

    roll = rot[2]

    pitch = -rot[0]

    return yaw, roll, pitch





def plot_blendshapes(blendshapes):

    names = [f'Blendshape {i}' for i in range(len(blendshapes))]

    scores = [blendshape for blendshape in blendshapes]

    plt.barh(names, scores)

    plt.xlabel('Score')

    plt.title('Face Blendshapes')

    plt.show()


# The mapping function 

def map_blend_shapes_to_actuators(actuators,blendshapes,yaw ,pitch,roll):
#Head_rotations
    yaw=127+(yaw*127/30)
    if(yaw>255):
        actuators[13]=255
    elif (yaw<0):
        actuators[13]=0
    else :
        actuators[13]=int(yaw)

    

    pitch=127+(pitch*127/20)
    if(pitch>255):
        actuators[12]=255
    elif (pitch<0):
        actuators[12]=0
    else :
        actuators[12]=int(pitch)


    roll=127+(roll*127/10)
    if(roll>255):
        actuators[11]=255
    elif (roll<0):
        actuators[11]=0
    else :
        actuators[11]=int(roll)


    


    #Head_Eyes

    if (blendshapes[8+1]<blendshapes[9+1]):
        actuators[0]= blendshapes[9+1] 
    else :
        actuators[0]= blendshapes[8+1]


    eyeL=blendshapes[12+1]/255
    eyeR=blendshapes[13+1]/255



    if(abs(eyeL-eyeR)<0.2):
        actuators[1]=actuators[1]
    else:
        
        eyeL=int(float((eyeL)) * 128)
        eyeR=int(float((eyeR)) * 128)
        if(eyeL>eyeR):
            actuators[1]=eyeL
        else:
            actuators[1]=eyeR+127



    if (blendshapes[16+1]<blendshapes[17+1]):
        actuators[2]= blendshapes[17+1] 
    else :
        actuators[2]= blendshapes[16+1]    


    if (blendshapes[18+1]<blendshapes[19+1]):
        actuators[3]= blendshapes[19+1] 
    else :
        actuators[3]= blendshapes[18+1]    

    #Head_Brows

    if (blendshapes[4+1]<blendshapes[3+1]):
        actuators[4]= blendshapes[3+1] 
    else :
        actuators[4]= blendshapes[4+1]
        

    actuators[5]= blendshapes[2+1]


    #Head_Mouth

    if (blendshapes[43+1]<blendshapes[44+1]):
        actuators[6]= blendshapes[44+1] 
    else :
        actuators[6]= blendshapes[43+1]   


    if (blendshapes[27+1]<blendshapes[28+1]):
        actuators[7]= blendshapes[28+1] 
    else :
        actuators[7]= blendshapes[27+1]

    
    actuators[8]=blendshapes[37+1]#
    

    blendshapes[47+1]=blendshapes[47+1]*2
    blendshapes[48+1]=blendshapes[48+1]*2

    if (blendshapes[47+1]<blendshapes[48+1]):
        if(blendshapes[48+1]<255):
          actuators[9]= blendshapes[48+1]
        else :
            actuators[9]=255 
    else :
        if(blendshapes[47]<255):
          actuators[9]= blendshapes[47+1]
        else :
            actuators[9]=255 

   
    actuators[10]=blendshapes[24+1]

#The following 2 lines to make sure that kimi's actuator 
# values doesnt exceed 255 and doesn't go lower than 0 
    actuators=[0 if x<0 else x for x in actuators]
    actuators=[255 if x>255 else x for x in actuators]

    return actuators



def main(args):
    lists_sent = 0
    start_time = time.time()
#Write the model path after downloading it on your local PC in the model_asset_path attribute
    base_options = python.BaseOptions(model_asset_path=r'/home/yara/Downloads/face_landmarker.task')

    options = vision.FaceLandmarkerOptions(base_options=base_options,

                                           output_face_blendshapes=True,

                                           output_facial_transformation_matrixes=True,

                                           num_faces=1)

    detector = vision.FaceLandmarker.create_from_options(options)



    cap = cv2.VideoCapture(0)

    try:

        while cap.isOpened():

            success, frame = cap.read()

            if not success:

                print("Ignoring empty camera frame.")

                continue



            # Convert the frame to the format required by MediaPipe

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=frame_rgb)



            # Detect face landmarks

            detection_result = detector.detect(mp_image)



            # Draw landmarks

            annotated_image = draw_landmarks_on_image(frame, detection_result)



            if detection_result.facial_transformation_matrixes:

                facial_transform_matrix = detection_result.facial_transformation_matrixes[0]

                face_blendshapes = detection_result.face_blendshapes[0]

                yaw, roll, pitch = add_mh_head_rot(facial_transform_matrix)



                # Display head rotation

                cv2.putText(annotated_image, f'Yaw: {yaw:.2f}', (10, 30),

                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                cv2.putText(annotated_image, f'Roll: {roll:.2f}', (10, 60),

                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)

                cv2.putText(annotated_image, f'Pitch: {pitch:.2f}', (10, 90),

                            cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)







                face_blendshapes_names = [face_blendshapes_category.category_name for face_blendshapes_category in

                                          face_blendshapes]

                face_blendshapes_scores = [face_blendshapes_category.score for face_blendshapes_category in

                                           face_blendshapes]
                

                face_blendshapesAfterAdjustingRange=[int(float((value)) * 255) for value in face_blendshapes_scores]
                new_actuators_values =map_blend_shapes_to_actuators(actuators,face_blendshapesAfterAdjustingRange,yaw,pitch,roll )
                     
                message = json.dumps(new_actuators_values)
                lists_sent += 1
                if(lists_sent<25):
                    socket.send_string(message)
               
                elapsed_time = time.time() - start_time
    
    # If one second has passed, print the number of lists sent and reset
    # this is a checker that kimi doesnt take more than 25 lists/sec (kimi's limit)
                if elapsed_time >= 1.0:
                     print(f"Lists sent in the last second: {lists_sent}")
                     lists_sent = 0
                     start_time = time.time()
                




            cv2.putText(annotated_image, "Press 'Q' to quit", (10, frame.shape[0] - 10),

                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)



            cv2.imshow('MediaPipe Face Mesh', annotated_image)



            if cv2.waitKey(5) & 0xFF == ord('q'):

                break

    except KeyboardInterrupt:

        print("Keyboard Interrupt: Exiting...")

    finally:

        cap.release()

        cv2.destroyAllWindows()





if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Facial Landmarks and Blendshapes Detection')

    #parser.add_argument('model_path', type=str, help='Path to the face landmark model', default=r'/home/yara/Downloads/face_landmarker.task')

    #parser.add_argument('--video_path', type=str, help='Path to the video file (optional)', default=None)



    args = parser.parse_args()

    main(args)
