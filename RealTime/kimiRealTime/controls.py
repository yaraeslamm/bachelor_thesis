from flask import (g,
    Blueprint, render_template, current_app, request
)
from animations import HlabAnimation

import util

controls_bp = Blueprint('controls', __name__, url_prefix='/controls')

# TODO: flask wrapper to check connected?
@controls_bp.route('/', methods=['GET'])
def show_controls():
    controller = getattr(current_app, 'controller', None)
    usb_ports = util.get_usb_ports(current_app)
    changed_values = []
    actuators_by_group = {}
    last_values = []
    if controller is not None:
        changed_values = util.get_changed_values(current_app)
        last_values = controller.last_values
        current_app.slider_animation = SliderAnimation()
        current_app.slider_animation.activate()
        current_app.anim_scheduler.add_or_replace_animation(current_app.slider_animation)
        for a in controller.actuators:
            top, sub = a['group'].split('_')
            if top in actuators_by_group:
                if sub in actuators_by_group[top]:
                    actuators_by_group[top][sub].append(a)
                else:
                    actuators_by_group[top][sub] = [a]
            else:
                    actuators_by_group[top] = {sub: [a]}
    return render_template(
        'controls.html',
        connected=controller is not None and controller.connected,
        usb_ports=usb_ports,
        actuators_by_group=actuators_by_group,
        values=last_values,
        changed_values=changed_values
    )

@controls_bp.route('/update', methods=['GET'])
def update():
    values = [None for _ in current_app.controller.actuators]
    idx = int(request.args.get('idx', ''))
    value = int(request.args.get('value', ''))
    values[idx] = value
    #_, head_response = current_app.controller.send_values(values)
    current_app.slider_animation.values = values
    current_app.changed_values[idx] = value




    return {'values': current_app.controller.last_values, 'changed_values': current_app.changed_values}



@controls_bp.route('/change_actuators', methods=['GET'])
def change_actuators():
    # actuatorlist = [100,0,0,0,0,0,0,0,0,0,255,0,0,0]  # Example values; replace with your actual list
    actuatorlist=getattr(current_app, 'data_list',[] )
    for idx, value in enumerate(actuatorlist):
        current_app.slider_animation.values[idx] = value
        current_app.changed_values[idx] = value


    #current_app.controller.send_values(actuatorlist)





    return {'values': current_app.controller.last_values, 'changed_values': current_app.changed_values}






@controls_bp.route('/resetchangedvalues', methods=['GET'])
def reset_changed_values():
    nones = [None for _ in range(len(current_app.controller.actuators))]
    current_app.changed_values = nones
    return {'changed_values': nones}

@controls_bp.route("/pressureoff")
def pressure_off():
    util.stop_scheduler(current_app)
    current_app.controller.pressure_off()
    return {'pressure': False}


@controls_bp.route("/pressureoffdisconnect")
def pressure_offdisconnect():
    util.stop_scheduler(current_app)
    current_app.controller.pressure_off()
    util.disconnect(current_app)
    return {'pressure': False, 'connected': False}

@controls_bp.route("/pressureon")
def pressure_on():
    current_app.controller.pressure_on()
    return {'pressure': True}

def register(app):
    app.register_blueprint(controls_bp)

class SliderAnimation(HlabAnimation):
    def __init__(self, frames=[], description='', **kwargs):
        super().__init__(frames, description, **kwargs)

        self.loop = 1
        self.prio = 100
        self.name = 'slider'
        self.values = [None for _ in current_app.controller.actuators]

    def nextFrame(self, last_values=None):
        v = self.values.copy()
        self.values = [None for _ in current_app.controller.actuators]
        return v
    








