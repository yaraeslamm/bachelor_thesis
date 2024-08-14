
import logging
import sys
import argparse
import time

from jetson_inference import poseNet
from jetson_utils import videoSource, videoOutput, Log

import asyncio
from websockets.legacy.protocol import broadcast
from websockets.sync.server import serve
from websockets.exceptions import ConnectionClosedOK
import json

# parse the command line
parser = argparse.ArgumentParser(description="Run pose estimation DNN on a video/image stream.", 
                                 formatter_class=argparse.RawTextHelpFormatter, 
                                 epilog=poseNet.Usage() + videoSource.Usage() + videoOutput.Usage() + Log.Usage())

parser.add_argument("input", type=str, default="", nargs='?', help="URI of the input stream")
parser.add_argument("output", type=str, default="", nargs='?', help="URI of the output stream")
parser.add_argument("--network", type=str, default="resnet18-body", help="pre-trained model to load (see below for options)")
parser.add_argument("--overlay", type=str, default="links,keypoints", help="pose overlay flags (e.g. --overlay=links,keypoints)\nvalid combinations are:  'links', 'keypoints', 'boxes', 'none'")
parser.add_argument("--threshold", type=float, default=0.15, help="minimum detection threshold to use") 

try:
	args = parser.parse_known_args()[0]
except:
	print("")
	parser.print_help()
	sys.exit(0)

# load the pose estimation model
net = poseNet(args.network, sys.argv, args.threshold)

# create video sources & outputs
input = videoSource(args.input, argv=sys.argv)
output = videoOutput(args.output, argv=sys.argv)


def run_loop(ws):
     print('new websocket connection')
     while True:
        # capture the next image
        img = input.Capture()

        if img is None: # timeout
            continue  

        # perform pose estimation (with overlay)
        poses = net.Process(img, overlay=args.overlay)

        # print the pose results
        print("detected {:d} objects in image".format(len(poses)))
        pose_points = [{'id': pose.ID, 'keypoints': [{'id': kp.ID, 'x': kp.x, 'y': kp.y} for kp in pose.Keypoints]} for pose in poses]
        try: 
            ws.send(json.dumps(pose_points))
        except ConnectionClosedOK:
             #logging.exception('exception when sending over websocket')
             print('Connection closed')
             break

        for pose in poses:
            print(pose)
            print(pose.Keypoints)
            print('Links', pose.Links)
        # render the image
        output.Render(img)

        # update the title bar
        #output.SetStatus("{:s} | Network {:.0f} FPS".format(args.network, net.GetNetworkFPS()))

        # print out performance info
        #net.PrintProfilerTimes()
        time.sleep(0.06)
        # exit on input/output EOS
        if not input.IsStreaming():# or not output.IsStreaming()
            break



with serve(run_loop, '', 8001) as server:
    server.serve_forever()