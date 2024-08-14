# hlabAndroidPyWebapp2.0



## Getting started

Install `requirements.txt`: `pip install -r requirements.txt`.

Install submodule for basic android control software:
`git submodule init` and `git submodule update` and `pip install -r hlabandroidpylib/requirements.txt`

Start app with `flask --app app run` or `python app.py`.

This should be sufficient for basic operations like the `Controls` and `Animations`. Demos might need additional setup steps to be completed.

### Services for speech and chatGPT demo

REST APIs can be provided in our [slurm cluster](https://deeplearn.mi.hdm-stuttgart.de/) or run locally on a capable device like the Nvidia Jetson Orin for **STT**, **TTS** and **Lip-sync**. See the corresponding [readme](./hlab_services/README.md) for instructions on how to start these services. Make sure there is a `.env` file containing the URLs to the services.
The `.env` file should contain following keys:
* `OPENAI_API_KEY` for chatGPT
* `TTS_URL=http://localhost:7223/api/tts`
* `LIPSYNC_URL=http://localhost:7222/lipsync/`
* `STT_URL=http://localhost:9000/asr?task=translate`
    * URLs above are for running local on jetson, using services running on the slurm cluster could look like following
    * `TTS_URL=http://ada.mi.hdm-stuttgart.de:7223/api/tts`
    * `LIPSYNC_URL=http://jarvis.mi.hdm-stuttgart.de:7222/lipsync/`
    * `STT_URL=http://tardis.mi.hdm-stuttgart.de:7224/stt`
    * hostnames e.g. ada, jarvis, tardis, cerebro etc. need to be adjusted according to which node the service was started on
* Additional keys for other functionalities:
    * to replace animations e.g. with a the same animation using the other hand
        * `THINKING_ANIMATION_NAME=think_interpolated_left`
        * `LISTENING_ANIMATION_NAME=listen_left`
    * for person tracking, depending on computer and webcam devices
        * `CAMINDEX=0`
        * webcam-specific, [180, 50] for the microsoft cam and the android head
        * `UPVIDEOCORNER=180` # pixels to ignore from the top
        * `LEFTVIDEOCORNER=50` # pixels to ignore from the left

### Start commands (on jetson):
* Terminal 1 (speech services):
    * `cd hlabandroidpywebapp2.0/hlab_services/docker/`
    * (maybe, when using SD card): `sudo mount /dev/mmcblk1p2 /media/jetson/SDStorage/`
    * `docker compose --file docker-compose.yml up`
* Terminal 2 (pose detection service):
    * `cd hlabandroidpywebapp2.0/hlab_services/docker/`
    * `docker compose --file docker-compose-jetson-inference.yml -p detection up`
    * does not stream the image, use instead:
    * `cd jetson-inference/`
    * `docker/run.sh`
    * `pip3 install websockets`
    * `python3 data/scripts/posenet_socket_copy.py /dev/video0 webrtc://@:8554/my_stream --headless --input-flip=rotate-180`
* Terminal 3 (web app):
    * `conda activate androids`
    * `cd hlabandroidpywebapp2.0/`
    * `python app.py --speech_log=INFO`
    * connect and start animations in webapp
* Terminal 4 (keyboard listener):
    * `conda activate androids`
    * `cd hlabandroidpywebapp2.0/`
    * `sudo /home/jetson/miniconda3/envs/androids/bin/python key_press.py`
        * or on the other jetson: `/home/jetson/.conda/envs/androids/bin/python`
* Terminal 5 (check setup):
    * `pactl list short sinks` or `sources`
    * `pactl set-default-source alsa_input.usb-C-Media_Electronics_Inc._MARANTZ_M4U_20190520-00.mono-fallback`
    * `pactl set-default-sink alsa_output.usb-C-Media_Electronics_Inc._MARANTZ_M4U_20190520-00.analog-stereo`