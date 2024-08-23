# Real-time System

## Overview
The Real-time System is designed for real-time processing using Mediapipe and Kimi, a robotic head. 

## Installation and Setup
1. Navigate to the `realtime system` directory:
   ```bash
   cd realtime
    ```
2. Install the required dependencies:
   ```bash
    pip install -r requirements.txt
    ```

## Usage
1. Kimi Setup:
 * Before running the Mediapipe module, you need to connect to the robotic head (Kimi).
 * Run the app.py script located in the kimiRealTime folder:
    ```bash
     cd kimi
     python app.py
     ```

* Open the website appeared in the terminal to connect to the head via the local website.

2. Mediapipe Setup :
* Ensure a camera is plugged in.
* Navigate to the feature_extraction directory inside the mediapipeBlendshapes folder:

     ```bash
   cd ../mediapipeBlendshapes/feature_extraction/mediapipe_feature
     python mediapipe_feature.py
     ```
* Ensure that Kimi is connected before running Mediapipe.
 ## Notes
 * The real-time system requires a camera and a connection to the robotic head (Kimi) before running Mediapipe.

