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
import time


from controls import change_actuators#update_actuators


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


    with app.app_context():
        while True:
            data_list = socket.recv_string()
            message = json.loads(data_list)
            change_actuators()
            with current_app.app_context():
              current_app.data_list = message


              #update_actuators()



            print("Received list:", data_list)
            #print("Received message:", message)
        
    




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



