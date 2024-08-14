from pathlib import PureWindowsPath, Path

base_url = 'http://localhost:8011'
#player = '/World/audio2face/Player'

usd_path=str(PureWindowsPath(Path('D:/GIT/github/avatar-chatgpt/audio2face/usd/stream_python_livelink_project.usd')))
ll_streaming_enabled=True
a2f_instance = '/World/audio2face/CoreFullface'
prediction_delay=0.5

emotion_strength=0.6
max_emotions=2
lf_strength=1.3
hf_strength=1.0

emotion_auto_streaming_enabled=False
emotion_keys=[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0 ]
