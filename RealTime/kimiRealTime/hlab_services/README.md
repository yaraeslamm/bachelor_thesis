# Humanoidlab ML services setup

## Run models on server
To run services in our [slurm cluster](https://deeplearn.mi.hdm-stuttgart.de) they need to be started as `slurm jobs`. See the cluster docs for more general information.

To generate the requried `enroot` containers and start a web server providing a REST API the corresponding `*_server.sh` files from this directory can be used. So you might want to copy this directory to your home on the cluster. To run the scripts e.g. the command `sbatch ./lipsync_server.sh` can be used. This will schedule the job in the background and as soon as it started it will write to a file `hlab_lipsync.out` where you can see if and where (the hostname you need to copy) it's running. Instead of manually starting and checking the files you might also give the `start_all.sh` file a chance though it's not working properly, yet.

When finished with you demo or development, **do not forget to stop the services** again so compute resources are freed for others again.



## Run models (and webapp) local on Jetson Orin

## Start services
* establish `ssh` connection (preferably with VS Code remote plugin as described below)
* or plug in a monitor, usb keyboard and mouse
* in a terminal `cd` into `hlab_services/docker` directory
* start services with `docker compose up`
    * or specifing a specific compose file and project name: `docker compose --file docker-compose-jetson-inference.yml -p detection up`
* make sure URLs are correct (in a [.env](../.env) file located in the root of this project)
* in a new terminal activate (conda) venv (e.g. `conda activate androids`) and start web app
* in case sound in- or output is not working check if the default devices are set correctly as described below

## Initial Setup

### Additional dependencies
* the `sounddevice` library requires `libportaudio2` to be [installed on linux](https://python-sounddevice.readthedocs.io/en/0.4.6/installation.html) systems (on windows and mac this is automatically installed when installing `sounddevice` using `pip`): `sudo apt-get install libportaudio2`
    * if it is missing following error is logged on app startup: `ERROR:root:PortAudio library not found`
* some dependencies seem to have trouble working well together (probably tf or opencv and pygame) and may produce an error like this
    * `import pygame.mixer as mx ImportError: /home/jetson/.conda/envs/androids/lib/python3.10/site-packages/pygame/../pygame.libs/libgomp-d22c30c5.so.1.0.0: cannot allocate memory in static TLS block`
    * as described [here](https://github.com/opencv/opencv/issues/14884) this error can be fixed by importing in a specific order or by setting the `LD_PRELOAD` environment variable to the path mentioned in the error message e.g. run `export LD_PRELOAD=/home/jetson/.conda/envs/androids/lib/python3.10/site-packages/pygame/../pygame.libs/libgomp-d22c30c5.so.1.0.0`
    * to make it permanent create a custom `profile.d` (`sudo vim /etc/profile.d/custom_profile.sh`) and add the above command to it.

### USB Connection rights:
* Serial connection error in `lib` (*permission denied*):
* [multiple possibilities to solve](https://stackoverflow.com/questions/27858041/oserror-errno-13-permission-denied-dev-ttyacm0-using-pyserial-from-pyth)
* choose to add user to `dialout` group as described [here](https://askubuntu.com/questions/133235/how-do-i-allow-non-root-access-to-ttyusb0/133244#133244): `sudo usermod -a -G dialout $USER`
* then restart (or relogin)


### USB Speaker and Mics:
* Also make sure to have the right Jetpack version installed in case [USB-C port is not working](https://forums.developer.nvidia.com/t/jetpack-5-0-2-jetson-agx-orin-developer-kit-one-type-c-not-working/224158/1)
    * `cat /etc/nv_tegra_release` or `sudo apt-cache show nvidia-jetpack` or `dpkg -l | grep -i 'jetpack`
* Give access rights:
    * `sudo vim /etc/udev/rules.d/50-usb-scale.rules`
        * add `SUBSYSTEM=="usb", ATTRS{idVendor}=="2886", ATTRS{idProduct}=="0018", MODE="0666"` for Respeaker Mic array
        * add `SUBSYSTEM=="usb", ATTRS{idVendor}=="045e", ATTRS{idProduct}=="083e", MODE="0666"` for Microsoft Teams USB-C Speaker
        * might require reboot to take effect
    * use `lsusb` to [find idVendor and idProduct](https://kb.synology.com/en-ph/DSM/tutorial/How_do_I_check_the_PID_VID_of_my_USB_device) for other devices
* Set default device:
    * to list devices: `pactl list short sinks` for output speakers or `pactl list short sources` for input mics
    * `pactl set-default-source` (or `sink`)
        * eg: `pactl set-default-source alsa_input.usb-SEEED_ReSpeaker_4_Mic_Array__UAC1.0_-00.multichannel-input`
    * [source](https://how.wtf/how-to-set-default-audio-in-ubuntu.html)

### Firewall allow http on webapp port
* TODO: seems not to work following this tutorial: https://www.digitalocean.com/community/tutorials/iptables-essentials-common-firewall-rules-and-commands
* Workaround: use ssh portforwarding
    * vs code remote code plugin does this automatically for you
    * `ssh jetson@jetson-orin.local -A` with *jetson-orin* as *hostname*
        * it is recomended to use the hostname, there were problems (seemingly with the firewall) when using the ip address

### Docker
* docker is already installed but the user might have to be added to the docker usergroup:
    * `sudo groupadd docker` (should already exist)
    * `sudo usermod -aG docker jetson` (assuming *jetson* as username)
    * reboot `sudo reboot now`
    * from [here](https://www.digitalocean.com/community/questions/how-to-fix-docker-got-permission-denied-while-trying-to-connect-to-the-docker-daemon-socket)

* install [docker compose](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)

* use the [.env file](./docker/.env) in `hlab_services/docker` to adjust variables
    * `MODELS_PATH` sets the path where models are cached `/media/jetson/SDStorage1` can be used with an SD card otherwise e.g. `/home/jetson/Desktop/cached_models` can be used (maybe paths need to exist before starting the containers)
        * when using the SD card it might not be mounted automatically, then `sudo mount /dev/mmcblk1p2 /media/jetson/SDStorage/` mounts it. If the path to the card (`/dev/mmcblk1p2`) is not known: `ls -1 /dev > ~/before.txt` with SD card not plugged in, then `ls -1 /dev > ~/after.txt` with SD card plugged in, finally `diff ~/before.txt ~/after.txt`.
    * `TRANSFORMERS_OFFLINE` needs to be `0` in case there is no internet connection available and needs to be `1` if models are not downloaded to the `MODELS_PATH` yet.
* variables for **pose detection**:
    * `MODELS_PATH` is used as well, should contain `jetson_default_models/networks/models.json` with the content from the [repository](https://github.com/dusty-nv/jetson-inference/blob/master/data/networks/models.json)
    * `SCRIPTS_PATH` should point at the location of [posenet_socket.py](./docker/scripts/posenet_socket.py)
    * `CAMERA_DEVICE` e.g. `/dev/video0`
    * `POSE_DETECTION_ARGS` can be used to flip camera inputs e.g. `--input-flip=rotate-180` as described [here](https://github.com/dusty-nv/jetson-inference/blob/master/docs/aux-streaming.md#command-line-arguments)
    * **NOTE:** the detection currently does not work offline even if models were cached before since `websockets` needs to be installed to the default container on the fly when the container is started.

### Python env
* install miniconda
    * `wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh`
    * `sudo bash Miniconda3-latest-Linux-aarch64.sh -b -u -p /opt/miniconda`
    * `rm Miniconda3-latest-Linux-aarch64.sh`
    * `/opt/miniconda/bin/conda init bash`
* open new terminal, then create and activate env
    * `conda create --name androids python=3.10`
    * `conda activate androids`
    * install requirements as described in [basepath readme](../README.md)