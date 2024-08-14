from queue import Queue
import io
import speech_recognition as sr
from gtts import gTTS
from pydub import AudioSegment
from scipy.io.wavfile import read
import numpy as np
from audio2face.audio2face_streaming_utils import push_audio_track
import time
import logging
import os
from voicex import TTS, Voices
from concurrent.futures import ThreadPoolExecutor
import librosa
import requests
import threading
from dotenv import load_dotenv
import re
from nltk.tokenize import sent_tokenize

load_dotenv()

# Access the variables
VOICEX_IP = "137.250.24.59"
VOICEX_PORT = ""
#nova-assistant
NOVA_ASSISTANT_IP = "137.250.171.148"
NOVA_ASSISTANT_PORT = 1337
SYSTEM_PROMPT = 'Your name is Lidia. You are having a conversation as a professional assistive agent. When you answer, please remember you have a personality of openness and extroversion. Generate answers short and to the point'
# Constants
A2F_URL = 'localhost:50051'
#SAMPLE_RATE = 22050
EXPECTED_SAMPLE_RATE = 48000
A2F_AVATAR_INSTANCE = '/World/omniverse/PlayerStreaming'


# Basic logger setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

recognizer = sr.Recognizer()
microphone = sr.Microphone()
audio_queue = Queue()
response_queue = Queue()
# Flag to control the listening state
is_listening = True
nova_assistant_url = f"http://{NOVA_ASSISTANT_IP}:{NOVA_ASSISTANT_PORT}"

# ANSI escape sequences for colors are defined in LogColors
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

def clean_response(response):
    # Step 1: Remove asterisk-encapsulated expressions
    text_without_asterisks = re.sub(r'\*[^*]+\*', '', response)

    # Step 2: Remove emojis
    # This regex matches most emojis by focusing on unicode ranges used for emojis
    cleaned_text = re.sub(r'[^\w\s,.?!]', '', text_without_asterisks)
    return cleaned_text

def voicex_tts(text):
    """
    sampleing rate at voiceX is 22050
    """
    tts = TTS(voice=Voices.GABBY, server=f"{VOICEX_IP}")
    wav_data, sample_rate = tts.synthesize(text)
    #tts.write(text, "debug_noice.wav")

    resample_data = librosa.resample(wav_data.astype(np.float32, order='C') / 32768.0, orig_sr=sample_rate, target_sr=EXPECTED_SAMPLE_RATE)
    #write("after_resample.wav", 48000, y_8k)
    return resample_data

def get_tts_data(text: str) -> bytes:
    """
    Generate Text-to-Speech (TTS) audio in mp3 format.

    Parameters:
        text (str): The text to be converted to speech.

    Returns:
        bytes: TTS audio in mp3 format.
    """

    tts_result = io.BytesIO()
    tts = gTTS(text=text, lang='en', slow=False, tld='de')
    tts.write_to_fp(tts_result)
    tts_result.seek(0)

    return tts_result.read()

def tts_to_wav(tts_byte: bytes, framerate: int = 48000) -> np.ndarray:
    """
    Convert TTS audio from mp3 format to WAV format and set the desired frame rate and channels.

    Parameters:
        tts_byte (bytes): TTS audio in mp3 format.
        framerate (int, optional): Desired frame rate for the WAV audio. Defaults to 22050.

    Returns:
        numpy.ndarray: TTS audio in WAV format as a numpy array of float32 values.
    """
    seg = AudioSegment.from_mp3(io.BytesIO(tts_byte))
    seg = seg.set_frame_rate(framerate)
    seg = seg.set_channels(1)
    wavIO = io.BytesIO()

    seg.export(wavIO, format="wav")

    rate, wav = read(io.BytesIO(wavIO.getvalue()))
    return wav


def wav_to_numpy_float32(wav_byte: bytes) -> np.ndarray:
    """
    Convert WAV audio from bytes to a numpy array of float32 values.

    Parameters:
        wav_byte (bytes): WAV audio data.

    Returns:
        numpy.ndarray: WAV audio as a numpy array of float32 values.
    """
    # Convert the WAV audio bytes to a numpy array of float32 values
    return wav_byte.astype(np.float32, order='C') / 32768.0

def get_tts_numpy_audio(text: str) -> np.ndarray:
    """
    Generate Text-to-Speech (TTS) audio in WAV format and convert it to a numpy array of float32 values.

    Parameters:
        text (str): The text to be converted to speech.

    Returns:
        numpy.ndarray: TTS audio as a numpy array of float32 values.
    """
    # Generate TTS audio in mp3 format from the given text
    mp3_byte = get_tts_data(text)
    # Convert the TTS audio in mp3 format to WAV format and a numpy array of float32 values
    wav_byte = tts_to_wav(mp3_byte)
    return wav_to_numpy_float32(wav_byte)

def process_sentence(sentence):
    """
    Process a single sentence through voicex_tts and return the audio data.
    """
    return voicex_tts(sentence)
    #return get_tts_numpy_audio(sentence)

def make_avatar_speaks_parallel_ordered_optimized(text: str) -> None:
    """
    Optimally make the avatar speak the given text by processing each sentence through TTS
    in parallel, ensuring playback in the correct order.

    Parameters:
        text (str): The text to be spoken by the avatar.
    """
    global A2F_URL, EXPECTED_SAMPLE_RATE, A2F_AVATAR_INSTANCE, logger, is_listening
    is_listening = False
    # Split the text into sentences
    sentences = sent_tokenize(text)

    # Process sentences in parallel and collect results in order
    with ThreadPoolExecutor() as executor:
        # Map the process_sentence function across all sentences
        # The results will be in the order of the sentences
        processed_audio_data = list(executor.map(process_sentence, sentences))

    # Sequentially push the audio data to the A2F instance in the correct order
    for audio_data in processed_audio_data:
        push_audio_track(A2F_URL, audio_data, EXPECTED_SAMPLE_RATE, A2F_AVATAR_INSTANCE, logger=logger)
    logger.info(colorize("Done pushback return back to listening", LogColors.WHITE))

def listen_in_background(audio_queue):
    global is_listening
    logger.debug(colorize("Listening thread started", LogColors.GREEN))
    while True:
        with microphone as source:
            if is_listening:
                logger.info(colorize("Microphone listening, you may speak now", LogColors.CYAN))
                audio = recognizer.listen(source)
                audio_queue.put(audio)
            else:
                time.sleep(0.1)

def recognize_speech(audio_queue, response_queue):
    global is_listening
    logger.debug(colorize("Recognition thread started", LogColors.GREEN))
    while True:

        audio = audio_queue.get()
        if is_listening:
            try:
                logger.info(colorize("Recognizing speech...", LogColors.BLUE))
                text = recognizer.recognize_google(audio)
                logger.info(colorize(f"Recognized speech: {text}", LogColors.MAGENTA))
                response_queue.put(text)
            except sr.UnknownValueError:
                logger.warning(colorize("Failed to understand audio", LogColors.YELLOW))

            except sr.RequestError as e:
                logger.error(colorize(f"Recognition service error: {e}", LogColors.RED))




def post_stream_nova_assistant(api_url, request_data):
    # if not start_event.is_set():
    #     start_event.set()
    s = requests.Session()
    answer = ""
    with s.post(api_url + '/assist', json=request_data, stream=True) as resp:
        for line in resp.iter_lines():
            if line:
                word = line.decode()
                answer += word

    return answer



def chat_with_nova_assistant(user_input: str, history: list, api_url: str) -> str:
    """Chat with Nova Assistant using the new request format."""
    request = {
        'model': 'gemma',
        'provider': 'ollama_chat',
        'message': user_input,
        'system_prompt': SYSTEM_PROMPT,
        'data_desc': "",
        'data': "",
        'stream': True,
        'top_k': 50,
        'top_p': 0.95,
        'temperature': 0.8,
        'history': history
    }

    response = post_stream_nova_assistant(api_url, request)
    cln_response = clean_response(response)
    history.append([user_input, response])

    return cln_response

def process_responses(response_queue, conversation_history):
    global is_listening
    logger.info(colorize(f"System prompt: {SYSTEM_PROMPT}", LogColors.GREEN))
    while True:
        user_input = response_queue.get()
        if user_input:
            is_listening = False
            logger.debug(colorize(f"Processing input: {user_input}", LogColors.BLUE))
            avatar_response = chat_with_nova_assistant(user_input, conversation_history, nova_assistant_url)
            logger.info(colorize(f"Avatar response: {avatar_response}", LogColors.YELLOW))
            make_avatar_speaks_parallel_ordered_optimized(avatar_response)
            is_listening = True
            logger.info(colorize("Ready to listen again", LogColors.GREEN))

# post_stream_nova_assistant and chat_with_nova_assistant remain unchanged

def main():
    # Threads setup
    conversation_history = []
    listening_thread = threading.Thread(target=listen_in_background, args=(audio_queue,))
    recognition_thread = threading.Thread(target=recognize_speech, args=(audio_queue, response_queue))
    processing_thread = threading.Thread(target=process_responses, args=(response_queue, conversation_history))

    # Threads start
    listening_thread.start()
    recognition_thread.start()
    processing_thread.start()

    # Wait for threads to complete
    listening_thread.join()
    recognition_thread.join()
    processing_thread.join()

if __name__ == "__main__":
    main()
