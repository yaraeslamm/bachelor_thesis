#!/bin/bash
#SBATCH --job-name lipsync_server
#SBATCH --partition gpu
#SBATCH --gpus 1
#SBATCH --output hlab_lipsync.out
#SBATCH --time 4:00:00
#SBATCH --exclude tardis

# Print some node information
echo "$(date)"
echo "Lipsync Sever Hostname: $(hostname)"
echo "Available CPUs: $(taskset -c -p $$) (logical CPU ids)"
echo "Available GPUs: $(nvidia-smi)"

# Create the enroot container if necessary
if enroot list | grep -q -w "^faceformer$"; then 
	echo "Found container: faceformer";
elif [ -f "/home/ma/h/heisler/hlab_images/faceformer.sqsh" ]; then
	echo "Found image: faceformer.sqsh";
	enroot create /home/ma/h/heisler/hlab_images/faceformer.sqsh; 
else 
	echo "Can't find faceformer.sqsh image in /home/ma/heisler/halb_images/."
	exit
fi

enroot start -w faceformer bash -c "cd ~/faceanimation/FaceFormer && /opt/miniconda3/envs/faceformer/bin/python ~/faceanimation/FaceFormer/server.py"