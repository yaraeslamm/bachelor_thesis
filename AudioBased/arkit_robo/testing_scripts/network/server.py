import socket
import chardet
from audio2face.audio2face_streaming_utils import push_audio_track

import json
import zmq
import time

#Initializing kimi's actuator list 
actuators = [0, 127, 0, 0, 0, 0, 0, 0, 0, 0, 0, 127, 127, 127]

import threading
import queue
from demo.demo_with_wav_file import bnQueue


#ZMQ_Setup()
context =zmq.Context()
sockett =context.socket(zmq.PUB)
sockett.bind("tcp://*:5555")


def udp_server():
    ip = '127.0.0.1'
    port = 12030
    buffer_size = 4096

    # Create a UDP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    # Bind the socket to the address and port
    sock.bind((ip, port))

    print("UDP server started, listening on {}:{}".format(ip, port))

    while True:
        # Receive message from client
        data, addr = sock.recvfrom(buffer_size)  # buffer size is 1024 bytes

        # Decode message as UTF-8
        message = data.decode('utf-8')

        # Print received message
        print("Received message from {}: {}".format(addr, message))


#The mapping function, 
#Any multiplications to the blendshapes is weight readjustments
def map_blend_shapes_to_actuators(actuators, blendshapes):


    # Head_Eyes

    if (blendshapes[0] < blendshapes[7]):
        actuators[0] = blendshapes[7]
    else:
        actuators[0] = blendshapes[0]

    if(blendshapes[3]<blendshapes[10]):
        actuators[1]=127-blendshapes[10]
    else:
        actuators[1]=127+blendshapes[3]



    if(blendshapes[4]<0):
        blendshapes[4] = blendshapes[4] * (-1)
    if(blendshapes[11]<0):
        blendshapes[11] = blendshapes[11] * (-1)


    if (blendshapes[4] < blendshapes[11]):
        actuators[2] = blendshapes[11]
    else:
        actuators[2] = blendshapes[4]



    if (blendshapes[5] < blendshapes[12]):
        actuators[3] = blendshapes[12]
    else:
        actuators[3] = blendshapes[5]

        # Head_Brows

    if (blendshapes[41] < blendshapes[42]):
        actuators[4] = blendshapes[42]
    else:
        actuators[4] = blendshapes[41]

    actuators[5] = blendshapes[43]

    # Head_Mouth

    if (blendshapes[23] < blendshapes[24]):
        actuators[6] = blendshapes[24]
    else:
        actuators[6] = blendshapes[23]


    if (blendshapes[27 + 1] < blendshapes[28 + 1]):
        actuators[7] = blendshapes[28 + 1]
    else:
        actuators[7] = blendshapes[27 + 1]

 
    actuators[8] = blendshapes[20]  #

    blendshapes[39] = blendshapes[39] * 2
    blendshapes[40] = blendshapes[40] * 2

    if (blendshapes[39] < blendshapes[40]):
        if (blendshapes[40] < 255):
            actuators[9] = blendshapes[40]
        else:
            actuators[9] = 255
    else:
        if (blendshapes[39] < 255):
            actuators[9] = blendshapes[39]
        else:
            actuators[9] = 255

    

    if(blendshapes[17]>255):
        actuators[10]=255
    else :
        actuators[10] = blendshapes[17]


    blendshapes[54] = 127 + (blendshapes[54] * 127 / 30)
    if (blendshapes[54] > 255):
        actuators[13] = 255
    elif (blendshapes[54] < 0):
        actuators[13] = 0
    else:
        actuators[13] = int(blendshapes[54])

    blendshapes[53] = 127 + (blendshapes[53] * 127 / 20)
    if (blendshapes[53] > 255):
        actuators[12] = 255
    elif (blendshapes[53] < 0):
        actuators[12] = 0
    else:
        actuators[12] = int(blendshapes[53])

    blendshapes[52] = 127 + (blendshapes[52] * 127 / 10)
    if (blendshapes[52] > 255):
        actuators[11] = 255
    elif (blendshapes[52] < 0):
        actuators[11] = 0
    else:
        actuators[11] = int(blendshapes[52])

    
    #The following 2 lines to make sure that kimi's actuator 
# values doesnt exceed 255 and doesn't go lower than 0 
    actuators = [0 if x < 0 else x for x in actuators]
    actuators=[255 if x>255 else x for x in actuators]



    return actuators


def tcp_server(port):
    ip = '127.0.0.1'
    #port = 12030
    buffer_size = 4096

    min_interval = 1.0 / 24



    # Create a TCP socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Bind the socket to the address and port
    sock.bind((ip, port))

    # Start listening for incoming connections
    sock.listen(1)

    print("TCP server started, listening on {}:{}".format(ip, port))

    while True:
        # Accept incoming connection
        conn, addr = sock.accept()
        counter = 0
        last_sent_time = time.time()

        print("Connected to client at {}".format(addr))

        while True:
            # Receive message from client
            data = conn.recv(buffer_size)

            message = data.decode('ISO-8859-1')
            print(port)


            if not data:
                break

            print("hello tcp server")
            try:
                counter += 1
                json_str = message.strip()[32:]

                json_str = json_str[:-12]
                
                dataa = json.loads(json_str)

                names = dataa['Names']
                weights = dataa['Weights']

                name_weight_dict = {names[i]: weights[i] for i in range(len(names))}

                
                #the weight 17 :JawOpen is for the mouth 
                #intensify by the factor of ic 
                #mouth openeing threshold was calibrated with trial error 

                ic = 2
                mouth_opening_threshold=0.11
                if(weights[17]>mouth_opening_threshold):
                    weights[17] = weights[17] * ic

                face_blendshapesAfterAdjustingRange = [int(float((value)) * 255) for value in weights]

               #Manual blinking
                if counter==100 or counter==101 or counter==101 :

                   face_blendshapesAfterAdjustingRange[0]=220
                   face_blendshapesAfterAdjustingRange[5] = 30
                   newActuator = map_blend_shapes_to_actuators(actuators, face_blendshapesAfterAdjustingRange)
                else:
                    if counter%50==0 and counter !=0 :
                        face_blendshapesAfterAdjustingRange[0] = 200
                        face_blendshapesAfterAdjustingRange[5] = 20
                        newActuator = map_blend_shapes_to_actuators(actuators, face_blendshapesAfterAdjustingRange)
                    else:
                        newActuator = map_blend_shapes_to_actuators(actuators, face_blendshapesAfterAdjustingRange)

                
                
                
                
                nQueue.put(face_blendshapesAfterAdjustingRange)


                current_time = time.time()
                elapsed_time = current_time - last_sent_time

                if elapsed_time >= min_interval:
                    messagee = json.dumps(newActuator)
                    sockett.send_string(messagee)
                    last_sent_time = current_time
                    print(f"Message sent at {current_time} with actuators: {newActuator}")
                else:
                    print(f"Message skipped at {current_time} due to rate limiting")

                
                print(counter)
                print(name_weight_dict)



                '''
                result = chardet.detect(data)
                encoding = result['encoding']
                confidence = result['confidence']
                print("encoding: " + str(encoding) + " confidence: " + str(confidence))
                '''
            except Exception:
                print("determining decoding failed")

            print("")
            try:
                # Decode message as UTF-8
                #data.decode('ascii')
                #data.decode('utf-8')
                print('x')



                # Print received message
                #print("Received message from {}: {}".format(addr, message))
            except Exception:
                print("something went wrong when decoding")



        # Close the connection
        conn.close()

'''
subject_json={
    "Audio2Face":{
        "Facial":{
            "Names":["EyeBlinkLeft","EyeLookDownLeft","EyeLookInLeft","EyeLookOutLeft","EyeLookUpLeft","EyeSquintLeft","EyeWideLeft","EyeBlinkRight","EyeLookDownRight","EyeLookInRight","EyeLookOutRight","EyeLookUpRight","EyeSquintRight","EyeWideRight","JawForward","JawLeft","JawRight","JawOpen","MouthClose","MouthFunnel","MouthPucker","MouthLeft","MouthRight","MouthSmileLeft","MouthSmileRight","MouthFrownLeft","MouthFrownRight","MouthDimpleLeft","MouthDimpleRight","MouthStretchLeft","MouthStretchRight","MouthRollLower","MouthRollUpper","MouthShrugLower","MouthShrugUpper","MouthPressLeft","MouthPressRight","MouthLowerDownLeft","MouthLowerDownRight","MouthUpperUpLeft","MouthUpperUpRight","BrowDownLeft","BrowDownRight","BrowInnerUp","BrowOuterUpLeft","BrowOuterUpRight","CheekPuff","CheekSquintLeft","CheekSquintRight","NoseSneerLeft","NoseSneerRight","TongueOut","HeadRoll","HeadPitch","HeadYaw"],
            
            "Weights":[0.0,0.05309253772056348,-0.04475094961675552,0.04475094961675552,-0.05309253772056348,0.0,0.03837311267852783,0.0,0.01971977095783558,0.05998443712180037,-0.05998443712180037,-0.01971977095783558,0.0,0.17286939918994904,0.0,0.0,0.021557575091719627,0.07040295004844666,0.0,0.0,0.05714983493089676,0.00786587130278349,0.0,0.11883703619241714,0.10429675877094269,0.0,0.0,0.0644637867808342,0.10441923886537552,0.0,0.0,0.0,0.04704050347208977,0.20964589715003967,0.047867417335510254,0.0,0.015957597643136978,0.0,0.0,0.0,0.0,0.0,0.0,0.2583494186401367,0.08639302849769592,0.12205315381288528,0.0,0.0,0.0,0.0,0.0,0.0,0.007533327994508994,-0.0219596400787704,-0.025713169406232]
        },
        "Body":{}
    }
}
'''

'''
data_json={
    "Audio2Face":{
        "Facial":{
            "Names":["EyeBlinkLeft","EyeLookDownLeft","EyeLookInLeft","EyeLookOutLeft","EyeLookUpLeft","EyeSquintLeft","EyeWideLeft","EyeBlinkRight","EyeLookDownRight","EyeLookInRight","EyeLookOutRight","EyeLookUpRight","EyeSquintRight","EyeWideRight","JawForward","JawLeft","JawRight","JawOpen","MouthClose","MouthFunnel","MouthPucker","MouthLeft","MouthRight","MouthSmileLeft","MouthSmileRight","MouthFrownLeft","MouthFrownRight","MouthDimpleLeft","MouthDimpleRight","MouthStretchLeft","MouthStretchRight","MouthRollLower","MouthRollUpper","MouthShrugLower","MouthShrugUpper","MouthPressLeft","MouthPressRight","MouthLowerDownLeft","MouthLowerDownRight","MouthUpperUpLeft","MouthUpperUpRight","BrowDownLeft","BrowDownRight","BrowInnerUp","BrowOuterUpLeft","BrowOuterUpRight","CheekPuff","CheekSquintLeft","CheekSquintRight","NoseSneerLeft","NoseSneerRight","TongueOut","HeadRoll","HeadPitch","HeadYaw"],
            
            "Weights":[0.0,0.08062668872922577,-0.026837027974793592,0.026837027974793592,-0.08062668872922577,0.0,0.14188571274280548,0.0,0.047678891873417284,0.04199190872761519,-0.04199190872761519,-0.047678891873417284,0.0,0.27075275778770447,0.0,0.0,0.019798647612333298,0.10171862691640854,0.0,0.0,0.0038354170974344015,0.012296776287257671,0.004639990162104368,0.1241246685385704,0.11364983022212982,0.0,0.0,0.03339442238211632,0.07433165609836578,0.0,0.0,0.0,0.01779118739068508,0.3607620894908905,0.05136699229478836,0.0,0.036317188292741776,0.0,0.0,0.0,0.0,0.0,0.0,0.28838422894477844,0.0790630429983139,0.11218994855880737,0.0,0.0,0.0,0.0,0.0,0.0,-0.00041391739456307235,-0.0043913444425807534,-0.00033519579396451305]
        },
        "Body":{}
    }
}
'''






