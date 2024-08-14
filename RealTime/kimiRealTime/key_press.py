import requests
import keyboard
import time

# needs to be started as root: sudo /home/jetson/miniconda3/envs/androids/bin/python key_press.py

#VOICE='p225' # Female slow
# VOICE='p374' # Female fast
# VOICE='p228' # Male fast
VOICE='p234' # Male slow

p_was_pressed = False
r_was_pressed = False

print('listening for button press')

while True:
    if keyboard.is_pressed('p') and p_was_pressed == False:
        r = requests.get('http://127.0.0.1:5000/demos/speech/cancel')
        cancelled = r.json()['cancelled']
        print('cancelled running speech animation:', cancelled)
        # start listening
        r = requests.get('http://127.0.0.1:5000/demos/speech/listen')
        p_was_pressed = True
    elif p_was_pressed == True and not keyboard.is_pressed('p'):
        r = requests.get('http://127.0.0.1:5000/demos/speech/cancel')
        # stop listening
        p_was_pressed = False
        r = requests.get('http://127.0.0.1:5000/demos/speech/listen')
        text = r.json()['text']
        print('Transcribed text:', text)
        r = requests.get('http://127.0.0.1:5000/demos/speech/answer?text={}&voice={}'.format(text, VOICE))
        print('ChatGPT answer:', r.json()['answer'])
    elif keyboard.is_pressed('ctrl+alt+r') and r_was_pressed == False:
        r = requests.get('http://127.0.0.1:5000/demos/speech/resetdialog')
        print('Reset dialog')
        r_was_pressed = True
    elif r_was_pressed and not keyboard.is_pressed('ctrl+alt+r'):
        r_was_pressed = False
    time.sleep(0.01)
