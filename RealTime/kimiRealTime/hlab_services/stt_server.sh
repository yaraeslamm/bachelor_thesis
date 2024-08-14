#!/bin/bash
#SBATCH --job-name stt_server
#SBATCH --partition gpu
#SBATCH --gpus 1
#SBATCH --output hlab_stt.out
#SBATCH --time 4:00:00

# Print some node information
echo "$(date)"
echo "STT Sever Hostname: $(hostname)"
echo "Available CPUs: $(taskset -c -p $$) (logical CPU ids)"
echo "Available GPUs: $(nvidia-smi)"

# Create the enroot container if necessary
if enroot list | grep -q -w "^tts_container$"; then 
	echo "Found container: stt_container";
elif [ -f "/home/ma/h/heisler/hlab_images/stt_container.sqsh" ]; then
	echo "Found image: stt_container.sqsh";
	enroot create /home/ma/h/heisler/hlab_images/stt_container.sqsh; 
else 
	echo "Can't find stt_container.sqsh image in /home/ma/heisler/hlab_images/."
	exit
fi

enroot start -w stt_container /opt/miniconda3/envs/stt/bin/python ~/STT/hf_whisper.py
