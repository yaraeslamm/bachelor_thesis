# Audio-Based System

## Overview
The Audio-Based System integrates Omniverse integrates Omniverse with Kimi for audio-driven facial expressions

## Installation and Setup
1. Navigate to the `audioBased` directory:
   ```bash
   cd audioBased
    ```
2. Install the required dependencies:
   ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Audio File Configuration (to choose an audio file for Kimi to say):
 1. In the kimiOmniverse folder, open app.py and set the audio_file_path attribute to the path of your desired .wav file.**
 2. In the ARKit_robo folder, open demo_with_wav_file.py in the demo directory and set the test_wav attribute to the same file path.

2. Kimi Setup:
 * Before running the audio processing files, you need to connect to the robotic head (Kimi) with your desired wav_file already in audio_file_path.
 * Run the app.py script located in the kimiRealTime folder:
    ```bash
     cd kimi

     python app.py
     ```

3. Omniverse Setup :
* Ensure Omniverse is running in the background..
* Navigate to the testing_scripts/network directory inside the ARKit_robo folder:

     ```bash
   cd ../ARKit_robo/testing_scripts/network

    python server.py

     ```
<!-- * Ensure that Kimi is connected before running Mediapipe. -->
 ## Notes
 * The audio-based system requires a connection to the robotic head (Kimi) and Omniverse running in the background.

