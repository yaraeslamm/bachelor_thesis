import queue

from audio2face.audio2face_streaming_utils import push_audio_track
import logging
import librosa

from dotenv import load_dotenv
import zmq

import requests
import json

load_dotenv()



# Constants
A2F_URL = 'localhost:50051'
#SAMPLE_RATE = 22050
EXPECTED_SAMPLE_RATE = 8000#48000
A2F_AVATAR_INSTANCE = '/World/audio2face/PlayerStreaming'


# Basic logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LogColors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    RESET = '\033[0m'
# Helper function to colorize messages
def colorize(message, color):
    return f"{color}{message}{LogColors.RESET}"



def get_tts_numpy_audio(self, wav_path):
    """
    """
    import numpy as np

    # Load output file
    y, sr = librosa.load(wav_path)

    # Resample the audio to 22500 Hz
    resample_data = librosa.resample(y, orig_sr=sr, target_sr=EXPECTED_SAMPLE_RATE)

    # Convert to numpy array
    # y_resampled_array = np.array(y_resampled)

    return resample_data


def push_wav_to_a2f(wav_path) -> None:
    """
    Optimally make the avatar speak the given text by processing each sentence through TTS
    in parallel, ensuring playback in the correct order.

    Parameters:
        text (str): The text to be spoken by the avatar.
    """

    audio_data=get_tts_numpy_audio(EXPECTED_SAMPLE_RATE,wav_path)

    push_audio_track(A2F_URL, audio_data, EXPECTED_SAMPLE_RATE, A2F_AVATAR_INSTANCE, logger=logger)
    #logger.info(colorize("Done pushback return back to listening", LogColors.WHITE))







# post_stream_nova_assistant and chat_with_nova_assistant remain unchanged



#def audio_thread_func():
   # while True:
        #if not audio_queue.empty():
        #    audio_data = audio_queue.get()
         #   push_audio_track(A2F_URL, audio_data, EXPECTED_SAMPLE_RATE, A2F_AVATAR_INSTANCE, logger=logger)
         #   time.sleep(1)  # Add appropriate sleep time if needed

#def blendshapes_thread_func():
    #while True:
        #if not blendshapes_queue.empty():
            #blendshapes = blendshapes_queue.get()
            # Process blendshapes here (e.g., send them to the avatar)
            #print(f"Processed blendshapes: {blendshapes}")
            #time.sleep(1)  # Add appropriate sleep time if needed


global bnQueue
bnQueue= queue.Queue()
global adQueue
adQueue= queue.Queue()
import time

def audio_thread_func():
    while True:
        if not adQueue.empty():
            audio_data = adQueue.get()
            push_audio_track(A2F_URL, audio_data, EXPECTED_SAMPLE_RATE, A2F_AVATAR_INSTANCE, logger=logger)
            time.sleep(1)

def blendshapes_thread_func():
    while True:
        if not bnQueue.empty():
            blendshapes = bnQueue.get()
            print(f"Processed blendshapes: {blendshapes}")
            time.sleep(1)


def main():
    from pathlib import Path
    import threading
    from testing_scripts.network.server import tcp_server

    #listening_thread = threading.Thread(target=tcp_server, args=())
   # bn_thread = threading.Thread(target=tcp_server, args=())

    bn_thread = threading.Thread(target=tcp_server, args=(12030,))

    ad_thread = threading.Thread(target=tcp_server, args=(12031,))

    # Threads start
    #listening_thread.start()
    bn_thread.start()
    ad_thread.start()




    #test_wav=Path(r'C:\Users\kimi\Downloads\Andrea-Stimmen\Andrea-Stimmen\Andrea_HarvardSentence_list1-sentence10.wav')
    #test_wav=Path(r'C:\Users\kimi\Desktop\robotHead-main\robotHead-main\data\speech\audio\hello.wav')
    test_wav = Path(r'C:\Users\kimi\Desktop\robotHead-main\robotHead-main\data\speech\audio\mesh_test.wav')
    #test_wav = Path(r'C:\Users\kimi\Downloads\Andrea-Stimmen\Andrea-Stimmen\Andrea_HarvardSentence_list1-sentence10sslowed.wav')
    #test_wav = Path(r'C:\Users\kimi\Downloads\Andrea-Stimmen\Andrea-Stimmen\Andrea_HarvardSentence_list2-sentence1.wav')

    #test_wav = Path(r'C:\Users\kimi\Desktop\robotHead-main\robotHead-main\data\speech\audio\genderneutral.wav')

    #test_wav=Path(r'C:\Users\kimi\Desktop\mesh_testt.wav')
    #test_wav = Path(r'C:\Users\kimi\Downloads\neutralized_Jauwairia_humming.wav')


    push_wav_to_a2f( str(test_wav) )
    adQueue.put(get_tts_numpy_audio(EXPECTED_SAMPLE_RATE,str(test_wav)))

   # push_audio_track(A2F_URL, audio_data, EXPECTED_SAMPLE_RATE, A2F_AVATAR_INSTANCE, logger=logger)





if __name__ == "__main__":
    main()

