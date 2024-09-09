# Audio-Based System

## Overview
The Audio-Based System integrates NVIDIA Omniverse with the Kimi robot head to generate audio-driven facial expressions.

## Installation and Setup
1. Navigate to the `AudioBased` directory:
   ```bash
   cd AudioBased
    ```
2. Install the required dependencies:
   ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Audio File Configuration 
To choose an audio file for Kimi to say :
     1. In the kimiOmniverse folder, open app.py and set the audio_file_path variable to the path of your desired .wav file.
     2. In the ARKit_robo folder, open demo_with_wav_file.py in the demo directory and set the test_wav attribute to the same audio file path.

2. Kimi Setup:
 * Before running the audio processing files, you need to connect to the robotic head (Kimi) with your desired wav_file already in audio_file_path.
 * Run the app.py script located in the kimiOmniverse folder:
    ```bash
     cd kimiOmniverse

     python app.py
     ```

3. Omniverse Setup :

* Ensure Omniverse is running in the background:
1. Open Omniverse, log in, and navigate to the audio2face folder in ARKit_robo/usd.
2. Open the stream_python_livelink_project file to ensure that the system is prepared to run Audio2Face tasks.

* Navigate to the demo directory inside the ARKit_robo folder:

     ```bash
   cd ../ARKit_robo/demo

    python demo_with_wav_file.py

     ```
<!-- * Ensure that Kimi is connected before running Mediapipe. -->
 ## Notes
 * The audio-based system requires both Kimi and Omniverse to be connected and running.

 * Each folder (kimiOmniverse and ARKit_robo) has its own requirements.txt file specifying dependencies. The main requirements.txt file in the AudioBased folder consolidates both.

 * To change the audio, stop running both scripts (app.py and demo_with_wav_file.py), update the audio paths in both files, and then re-run both files again 

## Troubleshooting
* Ensure you are ran kimi and is connected first before runnig the audio processing scripts . 

* If there is an issue with Kimi, stop running app.py and restart it. Try adjusting any actuator value manually, then re-run demo_with_wav_file.py.

* For issues with Omniverse, ensure the correct module/project is activated. If further errors persist, close and reopen Omniverse.