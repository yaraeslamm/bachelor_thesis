from flask import Flask, g,render_template, request, current_app,jsonify
from hlabandroidpylib.andr_controller import AndrController, ControllerType, FakeAndrController
import animations
import controls
import speech
import util
import logging
import argparse


import json
import zmq
import threading

from controls import change_actuators

import pygame

# Initialize pygame mixer for audio playback
pygame.mixer.init()

# Load the specific audio file
#audio_file_path = r'C:\Users\kimi\Downloads\Andrea-Stimmen\Andrea-Stimmen\Andrea_HarvardSentence_list1-sentence10.wav'
#audio_file_path =r'C:\Users\kimi\Desktop\robotHead-main\robotHead-main\data\speech\audio\hello.wav'
audio_file_path =r'C:\Users\kimi\Desktop\robotHead-main\robotHead-main\data\speech\audio\mesh_test.wav'
#audio_file_path =r'C:\Users\kimi\Downloads\Andrea-Stimmen\Andrea-Stimmen\Andrea_HarvardSentence_list1-sentence10sslowed.wav'
#audio_file_path =r'C:\Users\kimi\Downloads\Andrea-Stimmen\Andrea-Stimmen\Andrea_HarvardSentence_list2-sentence1.wav'

#audio_file_path =r'C:\Users\kimi\Desktop\robotHead-main\robotHead-main\data\speech\audio\genderneutral.wav'


#audio_file_path =r'C:\Users\kimi\Desktop\mesh_testt.wav'

#audio_file_path =r'C:\Users\kimi\Downloads\neutralized_Jauwairia_humming.wav'

audio = pygame.mixer.Sound(audio_file_path)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=5000)
    parser.add_argument('--speech_log', default='WARNING')

    args = parser.parse_args()
    return args


def create_app():
    app = Flask(__name__)

    @app.route("/")
    def index():
        connected = False
        controller = getattr(current_app, 'controller', None)
        if controller is not None:
            connected = controller.connected
        current_app.controller = controller
        usb_ports = util.get_usb_ports(current_app)
        return render_template(
            'base.html',
            connected=connected,
            usb_ports=usb_ports,
        )

    @app.route("/connect")
    def connect():
        port = request.args.get('port')
        device = request.args.get('device')
        #spec='./hlabandroidpylib/head_spec.txt'
        controller_type = ControllerType.HEAD
        if device.lower() == 'andrea':
            controller_type = ControllerType.ANDROID
            #spec='./hlabandroidpylib/android_spec.txt'
        if port == 'fake':
            current_app.controller = FakeAndrController(port, controller_type=controller_type)# spec=spec
        else:
            current_app.controller = AndrController(port, controller_type=controller_type)# spec=spec
        connected = current_app.controller.connect()
        if connected:
            current_app.connected_usb_port = port
        util.setup_scheduling(current_app)
        return {'connected': connected}

    @app.route("/disconnect")
    def disconnect():
        return util.disconnect(app)

    
    controls.register(app)
    animations.register(app)
    speech.register(app)



    return app



def zmq_receiver():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "")
   # played_audio = False

    played_audio = False  # To track if audio has already been played
    audio_channel = None  # Channel on which the audio is played

    with app.app_context():
        while True:
            data_list = socket.recv_string()
            change_actuators()
            message = json.loads(data_list)
            with current_app.app_context():
              current_app.data_list = message
            print("Received list:", data_list)
            #print("Received message:", message)
            # Check if audio has not been played yet
            if not played_audio:
              #  # Play the audio and get the channel
                audio_channel = audio.play()
                played_audio = True

            # Check if audio is still playing
            if played_audio and audio_channel is not None and not pygame.mixer.get_busy():
                # Reset the flag after audio completes
                played_audio = False
                audio_channel = None
        
    




if __name__ == '__main__':
    args = parse_args()
    numeric_level = getattr(logging, args.speech_log.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError('Invalid log level: %s' % args.speech_log)
    logging.getLogger('speech').setLevel(numeric_level)
    app = create_app()


#######################
    zmq_thread = threading.Thread(target=zmq_receiver, daemon=True)
    zmq_thread.start()



    app.run(host=args.host, port=int(args.port))



