#!/bin/bash
#SBATCH --job-name tts_server
#SBATCH --partition gpu
#SBATCH --gpus 1
#SBATCH --output hlab_tts.out
#SBATCH --time 4:00:00

# Print some node information
echo "$(date)"
echo "TTS Sever Hostname: $(hostname)"
echo "Available CPUs: $(taskset -c -p $$) (logical CPU ids)"
echo "Available GPUs: $(nvidia-smi)"

# Create the enroot container if necessary
if enroot list | grep -q -w "^tts_container$"; then 
	echo "Found container: tts_container";
elif [ -f "/home/ma/h/heisler/hlab_images/tts_container.sqsh" ]; then
	echo "Found image: tts_container.sqsh";
	enroot create /home/ma/h/heisler/hlab_images/tts_container.sqsh; 
else 
	echo "Can't find tts_container.sqsh image in /home/ma/heisler/images/."
	exit
fi


enroot start -w tts_container bash -c "source ~/.bashrc && conda activate tts && export NUMBA_CACHE_DIR=/tmp/ && tts-server --model_name tts_models/en/vctk/vits --port 7223 --use_cuda True"
