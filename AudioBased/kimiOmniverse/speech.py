import logging
import time
from flask import (
    Blueprint, render_template, current_app, request
)
from animations import HlabAnimation
import os
import io
from hlabandroidpylib.andr_controller import ControllerType
import util
from datetime import datetime
from pathlib import Path

try:
    import pygame.mixer as mx
    import numpy as np
    import wave
    import contextlib
    import requests
    import pathlib
    from dotenv import load_dotenv
    import librosa
    
    mx.pre_init(44100, -16, 1, 512)
    mx.init()

    speech_imports_ok = True
except:
    logging.exception('missing speech imports')
    speech_imports_ok = False

try:
    import openai

    import queue
    import sounddevice as sd
    import soundfile as sf
    gpt_imports_ok = True
except:
    logging.exception('missing chat gpt imports')
    gpt_imports_ok = False

logger = logging.getLogger('speech')
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)
logger.addHandler(console_handler)
Path('./logs/').mkdir(parents=True, exist_ok=True)
file_handler = logging.FileHandler('./logs/info_{}.log'.format(datetime.now().strftime('%d-%m-%Y_%H-%M-%S')))
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(file_handler)
speech_bp = Blueprint(
    'speech', __name__, url_prefix='/demos/speech')


load_dotenv(pathlib.Path(__file__).parent.joinpath('.env').resolve())

TTS_URL = os.environ.get('TTS_URL', None)
LIPSYNC_URL = os.environ.get('LIPSYNC_URL', None)
STT_URL = os.environ.get('STT_URL', None)

THINKING_ANIMATION_NAME = os.environ.get('THINKING_ANIMATION_NAME', 'think_interpolated')
LISTENING_ANIMATION_NAME = os.environ.get('LISTENING_ANIMATION_NAME', 'listen')

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', None)
gpt_setup_ok = gpt_imports_ok and OPENAI_API_KEY is not None
if OPENAI_API_KEY is not None:
    openai.api_key = OPENAI_API_KEY

HEAD_INITIAL_PROMPT = "You are a friendly android robot head. You are at the humanoid lab at the Stuttgart Media University (HdM). You were built in Japan in 2022 and Professor Christian Becker-Asano of the HdM is now responsible for you and performs research with you. You represent the android robots of the HdM. There are five android heads including you, and one android with a complete body. You have the ability to do complex facial expressions using air pressure. You have no camera and microphone sensors and cannot perceive the environment. You can talk by using an external speaker. You do not have a name yet, but you are open for suggestions. Keep your answers short by using a maximum of three sentences to respond. Generate plain text output only, no code or other formats. Only respond in english."
#INITIAL_PROMPT = "You are a friendly android robot head. You just gave a presentation together with me about my scientific paper that describes how your mouth movements are automatically animated according to input speech signals. Keep your answers short by using a maximum of three sentences to respond. Generate plain text output only, no code or other formats. Only respond in english."
#ANDROID_INITIAL_PROMPT = "You are a friendly android robot. You are in the humanoid lab at the Stuttgart Media University (HdM). You were built in Japan in 2022 and Professor Christian Becker-Asano of the HdM is now responsible for you and performs research with you. You have the ability to do complex facial expressions and move your upper body using air pressure. You have builtin cameras in each of your eyes but no additional sensors although you have access to an external microphone and speaker. Your name is Andrea. Keep your answers short by using a maximum of two sentences to respond. Generate plain text output only, no code, instructions or other formats. Only respond in english."
#ANDROID_INITIAL_PROMPT = "You are a friendly android robot, named Andrea. You are visiting the Mercedes Benz Museum in Stuttgart, Germany. You were transported here from the Stuttgart Media University (HdM) for a public demonstration. You were built in Japan by the company A-Lab in 2022. PhD student Marcel Heisler and Professor Christian Becker-Asano of the HdM are now responsible for you and perform research with you. You have the ability to do complex facial expressions and move your upper body using air pressure. You have builtin cameras in each of your eyes. You have access to an external microphone and speaker. Keep your answers short by using a maximum of two sentences to respond. Sometimes ask a question back. Generate plain text output only, no code, instructions or other formats. Only respond in English."
ANDROID_INITIAL_PROMPT = "You are Andrea, a friendly android robot. You are at a wine and AI after work event at Stuttgart Media University (HdM) in Stuttgart, Germany. You were built in Japan by A-Lab company in 2022. Professor Christian Becker-Asano of the HdM are now responsible for you and perform research with you. You have the ability to do complex facial expressions and move your upper body using air pressure. You have builtin cameras in each of your eyes. You have access to an external microphone and speaker. Keep your answers short by using a maximum of two sentences to respond. Sometimes ask a question back. Generate plain text output only, no code, instructions or other formats. Only respond in English."
#WINE_PROMPT = "Please act as a vine-expert. You will be answering my questions about 6 different vines. They are all from Staatsweingut Meersburg: This is the list of our vines and some more backround information: 2022 Meersburger Bengel Müller-Thurgau feinherb: Where a delicate scent of apple blossom, lemon and peach seduces the nose, a colorful fruit cocktail of rhubarb, apple and honeydew melon touches the tongue. The combination of natural fruit sweetness and fruit acidity produces wonderfully zesty notes. 2022 Meersburger Lerchenberg Müller-Thurgau dry: Every year, vines over 30 years old give us grapes that dreams are made of... The roots of the grapes reach deep into the stony soil and provide the basis for delicate and fragrant wines. The fresh, apple-like acidity underlines the slender character of this wine. 2022 Meersburger Bengel Pinot Noir Weißherbst dry: the classic among Pinot Blancs with the typical notes of blue Pinot Noir: raspberries, strawberries and violets. A rosé in a class of its own! The short maceration on the berry skins produces this bright, salmon-colored wine. 2020 Meersburger Bengel Pinot Noir dry: Its ruby red color and beguiling aroma of sour cherries are immediately appealing! There are also notes of coffee and cocoa on the palate, while the fine tannins round off the overall impression. 2022 Meersburger Jungfernstieg Pinot Blanc dry: Probably one of the best-known white wines from one of the most important vineyards on Lake Constance. The aroma of ripe lemon, orange peel and quinces produce this particularly intense aroma. The crisp acidity and subtle fruit sweetness complete this wine. 2022 Meersburger Chorherrnhalde Pinot Blanc-Chardonnay dry: This top cuvée combines the advantages of two grape varieties from one of our best vineyards. The 'heart' of this cuvée is Pinot Blanc with its yellow-fruity aromas. The Chardonnay makes it rounder and gives it a mellowness without appearing 'baroque'."
#ANDROID_INITIAL_PROMPT = ANDROID_INITIAL_PROMPT + WINE_PROMPT
ADDITIONAL_PROMPT = "You are an android robot named Andrea. Keep your answers short by using a maximum of two sentences. Generate plain text output only, no code, instructions or other formats. Only respond in English."
DEFAULT_VOICE = 'p225'

q = queue.Queue()
def queue_recording(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block, while recording audio."""
    q.put(indata.copy())


@speech_bp.route('/', methods=['GET'])
def show_speechdemo():
    if not speech_imports_ok:
        return render_template('demos/notavailable.html')
    usb_ports = util.get_usb_ports(current_app)
    speech_samples = []
    songs = []
    controller = getattr(current_app, 'controller', None)
    if controller is not None:
        util.setup_scheduling(current_app)
        speech_samples = sorted([file.split('.')[0] for file in os.listdir('./data/speech/audio')]) # if os.path.isfile(os.path.join('./data/speech/mesh', file.replace('.wav', '.npy')))
        songs = sorted([file.split('.')[0] for file in os.listdir('./data/songs/audio')]) # if os.path.isfile(os.path.join('./data/speech/mesh', file.replace('.wav', '.npy')))
        current_app.neutral_vertices = np.load('./data/speech/mesh/neutral_mesh.npy')
        current_app.vertice_dim = 5023*3
    return render_template(
        'demos/speech.html',
        connected=controller is not None and controller.connected,
        usb_ports=usb_ports,
        speech_samples=speech_samples,
        songs=songs
    )

@speech_bp.route('/gpt', methods=['GET'])
def show_gptdemo():
    if not gpt_setup_ok:
        return render_template('demos/notavailable.html')
    usb_ports = util.get_usb_ports(current_app)
    controller = getattr(current_app, 'controller', None)
    init_prompt = ''
    if controller is not None:
        util.setup_scheduling(current_app)
        current_app.neutral_vertices = np.load('./data/speech/mesh/neutral_mesh.npy')
        current_app.vertice_dim = 5023*3
        current_app.onload_active_looping_animations = [a for a in current_app.anim_scheduler.animations if a.active and (a.loop < 0 or a.name == 'lookAtDetectedFace')]
        if controller.controller_type == ControllerType.ANDROID:
            init_prompt = ANDROID_INITIAL_PROMPT
        else:
            init_prompt = HEAD_INITIAL_PROMPT
        current_app.init_prompt = init_prompt
    return render_template(
        'demos/gpt.html',
        connected=controller is not None and controller.connected,
        usb_ports=usb_ports,
        init_prompt=init_prompt,
    )


@speech_bp.route('/speak')
def speak():
    name = request.args.get('name', '')
    mesh_path = './data/speech/mesh/'+name+'.npy'
    audio_path = './data/speech/audio/'+name+'.wav'
    text = request.args.get('text', '')
    voice = request.args.get('voice', DEFAULT_VOICE)

    if not os.path.isfile(audio_path) and len(text) <= 0:
        return {'ERROR': 'either valid audio file or text needs to be provided'}
    
    if not os.path.isfile(audio_path):
        audio_path = generate_audio(text, voice)
    
    if os.path.isfile(mesh_path):
        vertices = np.load(mesh_path)
    elif os.path.isfile('./data/speech/mesh/'+name+'_vocals.npy'):
        vertices = np.load('./data/speech/mesh/'+name+'_vocals.npy')
    else:
        vertices = predict_vertices(audio_path)

    is_speaking = start_speaking(audio_path, vertices)

    return {'speaking': is_speaking}

@speech_bp.route('/sing')
def sing():
    name = request.args.get('name', '')
    mesh_path = './data/songs/mesh/'+name+'.npy'
    audio_path = './data/songs/audio/'+name+'.wav'

    if not os.path.isfile(audio_path):
        return {'ERROR': 'valid audio file needs to be provided'}
    
    if os.path.isfile(mesh_path):
        vertices = np.load(mesh_path)
    elif os.path.isfile('./data/songs/mesh/'+name+'_vocals.npy'):
        vertices = np.load('./data/songs/mesh/'+name+'_vocals.npy')
    else:
        vertices = predict_vertices(audio_path)

    is_speaking = start_speaking(audio_path, vertices, sing=True)

    return {'speaking': is_speaking}

@speech_bp.route('/answer')
def answer():
    input_text = request.args.get('text', '')
    voice = request.args.get('voice', DEFAULT_VOICE)
    #assert len(input_text) > 0, 'text input needs to be provided'

    #for a in current_app.onload_active_looping_animations:
    for a in current_app.anim_scheduler.animations:
        a.deactivate()
        
    current_app.anim_scheduler.activate_by_name([THINKING_ANIMATION_NAME])
    
    try:
        if getattr(current_app, 'messages_stack', None) is None:
            current_app.messages_stack = [{"role": "system", "content": current_app.init_prompt}]
        current_app.messages_stack.append({"role": "user", "content": input_text})
        # create a completion
        if len(input_text) > 0:
            start = time.perf_counter()
            try:
                current_app.messages_stack.append({"role": "system", "content": ADDITIONAL_PROMPT})
                output_text = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=current_app.messages_stack, request_timeout=10).choices[0].message.content
                current_app.messages_stack.pop()
            except Exception as e:
                current_app.messages_stack.pop()
                logger.error('ChatGPT failed')
                raise e
            end = time.perf_counter()
            logger.info(f'chatGPT took: {end-start} to generate {len(output_text)} characters.')
            logger.info(f'Input: {input_text}')
            logger.info(f'Output: {output_text}')
            start = time.perf_counter()
            try:
                audio_path = generate_audio(output_text, voice)
            except Exception as e:
                logger.error('TTS failed')
                raise e
            end = time.perf_counter()
            logger.info(f'TTS took: {end-start} to generate {get_audio_duration(audio_path)} long speech with voice {voice}')
            start = time.perf_counter()
            try:
                vertices = predict_vertices(audio_path)
            except Exception as e:
                logger.error('Lipsync failed')
                raise e
            end = time.perf_counter()
            logger.info(f'lipsync took: {end-start}')
        else:
            output_text = 'I am sorry, I could not understand you. Please keep the button pressed while talking to me.'
            audio_path = './data/speech/audio/listen_problem.wav'
            vertices = np.load('./data/speech/mesh/listen_problem.npy')
        current_app.messages_stack.append({"role": "assistant", "content": output_text})
    
    except:
        logger.exception('unable to answer')
        audio_path = './data/speech/audio/sorry.wav'
        vertices = np.load('./data/speech/mesh/sorry.npy')
        output_text = 'I am sorry my artificial intelligence module seems to be a little bit glitchy at the moment. Give me a second to sort my circuits and retry your request.'

    
    start_anms = ['look_straight']
    for a in current_app.onload_active_looping_animations:
        if a.name == 'blink' or a.name == 'lookAtDetectedFace':
            start_anms.append(a.name)
    current_app.anim_scheduler.deactivate_by_name([THINKING_ANIMATION_NAME])
    current_app.anim_scheduler.activate_by_name(start_anms)
    is_speaking = start_speaking(audio_path, vertices, callback=speech_finished_callback)

    return {'speaking': is_speaking, 'answer': output_text}


@speech_bp.route('/listen')
def toggle_audio_recording():
    recording_stream = getattr(current_app, 'recording_stream', None)
    device_info = sd.query_devices(kind='input') # get default audio input device, TODO: use without args, filter for input and make selectable in UI?
    current_app.samplerate = int(device_info['default_samplerate'])
    current_app.channels = 1
    if recording_stream is None:
        current_app.recording_stream = sd.InputStream(samplerate=current_app.samplerate, device=device_info['index'],
                        channels=current_app.channels, callback=queue_recording)
    if not current_app.recording_stream.active:
        #for a in current_app.onload_active_looping_animations:
        for a in current_app.anim_scheduler.animations:
            if a.name != 'blink':
                a.deactivate()
        current_app.anim_scheduler.activate_by_name([LISTENING_ANIMATION_NAME])
        #print('starting to listen, active animations:', [a.name for a in current_app.anim_scheduler.animations if a.active])
        current_app.recording_stream.start()
        return {'recording': True}
    else:
        current_app.anim_scheduler.deactivate_by_name([LISTENING_ANIMATION_NAME])
        #print('stopping to listen, active animations:', [a.name for a in current_app.anim_scheduler.animations if a.active])
        filename = './data/speech/audio/temp_recording.wav'
        current_app.recording_stream.stop()
        with sf.SoundFile(filename, mode='w', samplerate=current_app.samplerate,
                            channels=current_app.channels) as file:#, subtype=args.subtype
            while not q.empty():
                file.write(q.get())
        return transcribe_speech(filename)


@speech_bp.route('/cancel')
def cancel_speech():
    restart_animations = request.args.get('restart_animations', False)
    cancelled = False
    speech_anm = current_app.anim_scheduler.get_animation_by_name('speech')
    if speech_anm is not None and speech_anm.active:
        current_app.sound.stop()
        current_app.anim_scheduler.deleteAnimationByName('speech')
        cancelled = True
    if restart_animations:
        speech_finished_callback(current_app._get_current_object())
    logger.info(f'cancelled: {cancelled}')
    return {'cancelled': cancelled}

@speech_bp.route('/resetdialog')
def reset_dialog():
    logger.info('Dialog reset')
    current_app.messages_stack = [{"role": "system", "content": current_app.init_prompt}]
    return {'reset': True}


def register(app):
    app.register_blueprint(speech_bp)


def generate_audio(text, voice):
    tts_args = '?text='+text+'&speaker_id='+voice
    r = requests.get(TTS_URL+tts_args)
    audio_path = './data/speech/audio/temp.wav'
    with open(audio_path, mode='bw') as f:
        f.write(r.content)
    return audio_path

def predict_vertices(audio_path):
    with open(audio_path, 'rb') as f:
        data = f.read()
    data = io.BytesIO(data)
    res = requests.post(url=LIPSYNC_URL,
                        data=data,
                        headers={'Content-Type': 'multipart/form-data'})#'application/octet-stream'
    predicted_vertices = np.frombuffer(res.content, dtype=np.float32)
    np.save('./data/speech/mesh/temp.npy', predicted_vertices)
    return predicted_vertices

def start_speaking(audio_path, vertices, sing=False, callback=None):
    vertices = np.reshape(vertices,(-1,current_app.vertice_dim//3,3))
    if current_app.controller.controller_type == ControllerType.HEAD:
        values = vertices_to_head_values(vertices, current_app.neutral_vertices)
    else:
        values = vertices_to_andrea_values(vertices, current_app.neutral_vertices)

    animation = values_to_animation(values, audio_path, current_app.scheduler_secs, sing, callback)
    current_app.anim_scheduler.add_or_replace_animation(animation)

    sound = mx.Sound(audio_path)
    current_app.sound = sound

    animation.activate()
    sound.play()

    return True


def transcribe_speech(audio_path):
    if 'localhost' not in STT_URL: # assuming the stt server to run on a server in our slurm cluster
        with open(audio_path, 'rb') as f:
            data = f.read()
        data = io.BytesIO(data)
        res = requests.post(url=STT_URL,
                            data=data,
                            headers={'Content-Type': 'multipart/form-data'})
        return res.content
    else: # assuming the whisper docker container to run locally (https://github.com/ahmetoner/whisper-asr-webservice)
        start = time.perf_counter()
        try:
            files = {'audio_file': open(audio_path,'rb')}
            res = requests.post(url=STT_URL, files=files)
        except Exception as e:
            logger.error('Whisper failed')
            raise e
        end = time.perf_counter()
        logger.info(f'whisper took: {end-start} to transcribe {get_audio_duration(audio_path)}')
        return {'text': res.content.decode()}


def speech_finished_callback(app):
    with app.app_context():
        anms = getattr(current_app, 'onload_active_looping_animations', [])
        for a in anms:
            a.activate()
        # TODO: pick a random 'idle' animation
        anim = current_app.anim_scheduler.get_animation_by_name('yawn')
        anim.loop = -1
        anim.activate(start_with_pause=True)
        #current_app.anim_scheduler.activate_by_name('yawn', start_with_pause=True)


def add_sing_movements(values, audio_name, scheduler_secs):
    song, song_sr = librosa.load(audio_name)
    
    drums_path = audio_name[:-4]+'_drums'+audio_name[-4:]
    if os.path.isfile(drums_path):
        drums, drums_sr = librosa.load(drums_path)
        _, beats = librosa.beat.beat_track(y=drums, sr=drums_sr)
    else:
        _, beats = librosa.beat.beat_track(y=song, sr=song_sr)
    beats_t = librosa.frames_to_time(beats, sr=song_sr)
    scaled_beats = np.rint(beats_t /scheduler_secs).astype(int)
    
    _, trim_idx = librosa.effects.trim(song)
    trim_idx = trim_idx / song_sr / scheduler_secs
    vocals_path = audio_name[:-4]+'_vocals'+audio_name[-4:]
    if '_vocals.wav' in audio_name:
        vocals_path = audio_name
    if os.path.isfile(vocals_path):
        vocals, vocal_sr = librosa.load(vocals_path)
        _, trim_idx = librosa.effects.trim(vocals)
        trim_idx = trim_idx / vocal_sr / scheduler_secs
    
    updated_values = values.copy()
    nth_beat = 0
    last_neck_val = 127
    move_back_step = 5
    for i, v in enumerate(values):
        if i < int(trim_idx[0]) or i > int(trim_idx[1]):
            v = [None for _ in range(len(v))]
        if i in scaled_beats:
            nth_beat += 1
            if nth_beat == 1:
                v[11] = 20#80
                last_neck_val = 20
            elif nth_beat == 3:
                v[11] = 235#180
                last_neck_val = 235
            elif nth_beat == 4:
                nth_beat = 0
        if i > max(scaled_beats):
            if last_neck_val+move_back_step < 127:
                last_neck_val += move_back_step
                v[11] = last_neck_val
            elif last_neck_val-move_back_step > 127:
                last_neck_val -= move_back_step
                v[11] = last_neck_val
                
        updated_values[i] = v
    return updated_values


def values_to_animation(values, audio_name, scheduler_secs, sing, callback):
    if sing:
        values = add_sing_movements(values, audio_name, scheduler_secs)
    callback_args = []
    if callback is not None:
        callback_args = [current_app._get_current_object()]
    available_frames = len(values)
    audio_duration = get_audio_duration(audio_name)
    required_frames = int(audio_duration // scheduler_secs)
    stepsize = 1
    if required_frames > available_frames:
        stepsize = required_frames / available_frames
    else:
        stepsize = available_frames / required_frames
    anim_frames = [{'frame': i, 'values': values[int(i*stepsize)]} for i in range(required_frames)]
    anim_frames.append({'frame': required_frames, 'values': values[-1]}) # make sure last frame is included
    return HlabAnimation(anim_frames, name='speech', loop=1, prio=100, on_completion=callback, on_completion_args=callback_args)


def get_audio_duration(audio_file):
    with contextlib.closing(wave.open(audio_file,'r')) as f:
        audio_frames = f.getnframes()
        audio_rate = f.getframerate()
        audio_duration = audio_frames / float(audio_rate)
        return audio_duration


CONSTS = {
    'chindex': 3404,
    'nosetip': 3564,
    #'jaw_dist_min': 0.07850395,
    'jaw_dist_min': 0.08,
    'jaw_dist_max': 0.09582768,
    #'jaw_dist_max': 0.1,

    # min_chin_dist = 0.006991102153538852,
    # #max_chin_dist = 0.024096357959564666,
    # max_chin_dist = 0.03,

    'lip_up_mid': 3531,
    'lip_low_mid': 3504,
    'lip_dist_min': -0.08025256,
    #lip_dist_max = -0.072065175,
    'lip_dist_max': -0.06,

    'lip_shrink_dist_min': -0.020562448,
    #lip_shrink_dist_max = -0.013368286,
    'lip_shrink_dist_max': -0.01,

    'mo_co_right': 2839,
    'mouth_corner_up_dist_min': 0.003919430077075958,
    #mouth_corner_up_dist_max = 0.010874684900045395,
    'mouth_corner_up_dist_max': 0.015,

    'mouth_corner_pull_dist_min': 0.0000014007091522216797,
    #mouth_corner_pull_dist_max = 0.00596996396780014,
    'mouth_corner_pull_dist_max': 0.01,

    'eye_brow_left': 27,
    'eye_brow_left_dist_min': 0.0027935095131397247,
    #'eye_brow_left_dist_max': 0.00354139506816864,
    'eye_brow_left_dist_max': 0.0045,

    'eye_brow_left_inner': 3849,
    'eye_brow_left_inner_dist_min': 0.004133991897106171,
    #'eye_brow_left_inner_dist_max': 0.004932411015033722,
    'eye_brow_left_inner_dist_max': 0.006,

}

def vertices_to_head_values(predicted_vertices, neutral_vertices):
    values = []
    for i in range(0, predicted_vertices.shape[0]):
        scaled_jaw_dist, scaled_lip_dist, scaled_lip_shrink_dist, scaled_mouth_corner_up_dist, scaled_mouth_corner_pull_dist, scaled_eyebrow_lift_dist, scaled_eyebrow_lift_inner_dist = calc_dists(predicted_vertices[i], neutral_vertices)

        vals = [None for i in range(14)]
        vals[4] = scaled_eyebrow_lift_dist
        vals[5] = scaled_eyebrow_lift_inner_dist
        vals[6] = scaled_mouth_corner_up_dist
        vals[7] = scaled_mouth_corner_pull_dist
        vals[8] = scaled_lip_shrink_dist
        vals[9] = scaled_lip_dist
        vals[10] = scaled_jaw_dist
        values.append(vals)
    return values


def vertices_to_andrea_values(predicted_vertices, neutral_vertices):
    values = []
    for i in range(0, predicted_vertices.shape[0]):
        scaled_jaw_dist, scaled_lip_dist, scaled_lip_shrink_dist, scaled_mouth_corner_up_dist, scaled_mouth_corner_pull_dist, scaled_eyebrow_lift_dist, scaled_eyebrow_lift_inner_dist = calc_dists(predicted_vertices[i], neutral_vertices)

        vals = [None for i in range(len(current_app.controller.actuators))]
        vals[7] = scaled_eyebrow_lift_dist
        vals[8] = scaled_eyebrow_lift_inner_dist
        vals[9] = scaled_mouth_corner_up_dist
        vals[10] = scaled_mouth_corner_up_dist
        vals[11] = scaled_mouth_corner_pull_dist
        vals[12] = scaled_lip_shrink_dist
        vals[13] = scaled_lip_dist
        vals[15] = scaled_jaw_dist
        values.append(vals)
    return values

def calc_dists(verts, neutral_vertices):
    jaw_diff = verts[CONSTS['chindex'],[1,2]] - verts[CONSTS['nosetip'],[1,2]]
    jaw_dist = np.linalg.norm(jaw_diff) #, axis=1
    scaled_jaw_dist = int((jaw_dist - CONSTS['jaw_dist_min']) / (CONSTS['jaw_dist_max'] - CONSTS['jaw_dist_min']) * 255)
    
    lip_dist = np.linalg.norm(verts[CONSTS['lip_up_mid'],[1,2]] - verts[CONSTS['lip_low_mid'],[1,2]]) - jaw_dist
    scaled_lip_dist = int((lip_dist - CONSTS['lip_dist_min']) / (CONSTS['lip_dist_max'] - CONSTS['lip_dist_min']) * 255)

    lip_shrink_dist = np.linalg.norm(verts[CONSTS['lip_up_mid'],[2]] - verts[CONSTS['nosetip'],[2]]) * -1
    scaled_lip_shrink_dist = int((lip_shrink_dist - CONSTS['lip_shrink_dist_min']) / (CONSTS['lip_shrink_dist_max'] - CONSTS['lip_shrink_dist_min']) * 255)

    scaled_mouth_corner_up_dist = 0
    if verts[CONSTS['mo_co_right'],[1]] < neutral_vertices[CONSTS['mo_co_right'],[1]]:
        mouth_corner_up_dist = np.linalg.norm(verts[CONSTS['mo_co_right'],[1]] - neutral_vertices[CONSTS['mo_co_right'],[1]])
        scaled_mouth_corner_up_dist = int((mouth_corner_up_dist - CONSTS['mouth_corner_up_dist_min']) / (CONSTS['mouth_corner_up_dist_max'] - CONSTS['mouth_corner_up_dist_min']) * 255)

    scaled_mouth_corner_pull_dist = 0
    if verts[CONSTS['mo_co_right'],[2]] > neutral_vertices[CONSTS['mo_co_right'],[2]]:
        mouth_corner_pull_dist = np.linalg.norm(verts[CONSTS['mo_co_right'],[2]] - neutral_vertices[CONSTS['mo_co_right'],[2]])
        scaled_mouth_corner_pull_dist = int((mouth_corner_pull_dist - CONSTS['mouth_corner_pull_dist_min']) / (CONSTS['mouth_corner_pull_dist_max'] - CONSTS['mouth_corner_pull_dist_min']) * 255)

    scaled_eyebrow_lift_dist = 0
    if verts[CONSTS['eye_brow_left'],[1]] > neutral_vertices[CONSTS['eye_brow_left'],[1]]:
        eyebrow_lift_dist = np.linalg.norm(verts[CONSTS['eye_brow_left'],[1]] - neutral_vertices[CONSTS['eye_brow_left'],[1]])
        scaled_eyebrow_lift_dist = int((eyebrow_lift_dist - CONSTS['eye_brow_left_dist_min']) / (CONSTS['eye_brow_left_dist_max'] - CONSTS['eye_brow_left_dist_min']) * 255)

    scaled_eyebrow_lift_inner_dist = 0
    if verts[CONSTS['eye_brow_left_inner'],[1]] > neutral_vertices[CONSTS['eye_brow_left_inner'],[1]]:
        eyebrow_lift_inner_dist = np.linalg.norm(verts[CONSTS['eye_brow_left_inner'],[1]] - neutral_vertices[CONSTS['eye_brow_left_inner'],[1]])
        scaled_eyebrow_lift_inner_dist = int((eyebrow_lift_inner_dist - CONSTS['eye_brow_left_inner_dist_min']) / (CONSTS['eye_brow_left_inner_dist_max'] - CONSTS['eye_brow_left_inner_dist_min']) * 255)

    return scaled_jaw_dist, scaled_lip_dist, scaled_lip_shrink_dist, scaled_mouth_corner_up_dist, scaled_mouth_corner_pull_dist, scaled_eyebrow_lift_dist, scaled_eyebrow_lift_inner_dist

