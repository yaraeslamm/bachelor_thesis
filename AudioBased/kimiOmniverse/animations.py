import math
import time
from flask import (
    Blueprint, render_template, current_app, request
)
import logging
from enum import Enum
from random import seed, randint
from hlabandroidpylib.andr_controller import ControllerType

from util import HlabAnimation, HlabLookAtAnimation, setup_scheduling, get_changed_values, get_usb_ports
import json
import numpy as np

import pathlib
from dotenv import load_dotenv
import os



animations_bp = Blueprint('animations', __name__, url_prefix='/animations')
load_dotenv(pathlib.Path(__file__).parent.joinpath('.env').resolve())
POSE_WEBSOCKET = os.environ.get('POSE_WEBSOCKET', None)


@animations_bp.route('/', methods=['GET'])
def show_animations():
    controller = getattr(current_app, 'controller', None)
    connected = False
    anims_by_group = {}
    last_values = []
    changed_values = []
    if controller is not None:
        connected = controller.connected
        last_values = controller.last_values
        setup_scheduling(current_app)
        anim_names = [a.name for a in current_app.anim_scheduler.animations]
        if POSE_WEBSOCKET is not None and 'lookAtDetectedFace' not in anim_names:
            look_at_anim = HlabLookAtAnimation(description='Look at detected faces', name="lookAtDetectedFace", group='interactive')
            current_app.anim_scheduler.add_or_replace_animation(look_at_anim)
        for a in current_app.anim_scheduler.animations:
            if a.group in anims_by_group:
                anims_by_group[a.group].append(a)
            else:
                anims_by_group[a.group] = [a]
        changed_values = get_changed_values(current_app)
    
    usb_ports = get_usb_ports(current_app)
    
    return render_template(
        'animations.html', 
        connected=connected, 
        usb_ports=usb_ports,
        grouped_animations=anims_by_group,
        values=last_values,
        changed_values=changed_values
    )

@animations_bp.route('/toggle', methods=['GET'])
def toggle_animation():
    name = request.args.get('name', '')
    animations = list(filter(lambda a: a.name == name, current_app.anim_scheduler.animations))
    current_app.anim_scheduler.toggleActive(animations)
    return {'toggled': [{'name': a.name, 'active': a.active} for a in animations]}


@animations_bp.route('/run', methods=['POST'])
def run_animation():
    data = request.json
    #print('request.json', request.json)
    a = HlabAnimation(data['frames'], data['description'], **data['header'])
    a.activate()
    current_app.anim_scheduler.add_or_replace_animation(a)
    return {'hell': 'yeah'} # TODO


@animations_bp.route('/save', methods=['POST'])
def save_animation():
    data = request.json
    name = data['header']['name']
    path = './data/animations/head/'+name+'.json'
    if current_app.controller.controller_type == ControllerType.ANDROID:
        path = './data/animations/android/'+name+'.json'
    with open(path, 'x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return {'hell': 'yeah'} # TODO: error handling, file exists, overwrite?

@animations_bp.route('/stop', methods=['GET'])
def stop_animation():
    name = request.args.get('name', '')
    active_names = [a.name for a in current_app.anim_scheduler.animations if a.active]
    if name not in active_names:
        return {'no active animation found': name}
    current_app.anim_scheduler.deleteAnimationByName(name)
    return {'stopped': name}



def register(app):
    app.register_blueprint(animations_bp)


