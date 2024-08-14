#!/bin/bash

rm -f hlab_tts.out
rm -f hlab_lipsync.out

sbatch ./lipsync_server.sh
sbatch ./tts_server.sh
sbatch ./stt_server.sh


all_up=false

tts_status="Waiting for tts job to be scheduled."
tts_up=false
lipsync_status="Waiting for lipsync job to be scheduled."
lipsync_up=false
stt_status="Waiting for stt job to be scheduled."
stt_up=false
while [ "$all_up" = false ]; do
    if [[ -f hlab_tts.out ]]; then 
        tts_host=$(cat hlab_tts.out | grep "TTS Sever Hostname:")
        if [ ! -z "$tts_host" ]; then
            running=$(cat hlab_tts.out | grep " Running on ")
            if [ ! -z "$running" ]; then
                tts_up=true
                tts_status="TTS server up and running"
            else
                tts_status="Waiting for tts webserver to startup"
                err=$(cat hlab_tts.out | grep "Address already in use")
                if [ ! -z "$err" ]; then
                    echo "${err}" "A server seems to be running on the requested port already."
                    exit 1
                fi
            fi
        else
            tts_status="Waiting for TTS Sever Hostname: to appear in hlab_tts.out"
        fi
    else 
      tts_status="Waiting for tts job to be scheduled, the file hlab_tts.out cannot be found."
    fi
    echo "${tts_status}" 
    
    if [[ -f hlab_lipsync.out ]]; then 
        lipsync_host=$(cat hlab_lipsync.out | grep "Lipsync Sever Hostname:")
        if [ ! -z "$lipsync_host" ]; then
            running=$(cat hlab_lipsync.out | grep " Running on ")
            if [ ! -z "$running" ]; then
                lipsync_up=true
                lipsync_status="Lipsync server up and running"
            else
                lipsync_status="Waiting for lipsync webserver to startup"
                err=$(cat hlab_tts.out | grep "Address already in use")
                if [ ! -z "$err" ]; then
                    echo "${err}" "A server seems to be running on the requested port already."
                    exit 1
                fi
            fi
        else
            lipsync_status="Waiting for Lipsync Sever Hostname: to appear in hlab_lipsync.out"
        fi
    else 
      lipsync_status="Waiting for lipsync job to be scheduled, the file hlab_lipsync.out cannot be found."
    fi
    echo "${lipsync_status}" 
    
    if [[ -f hlab_stt.out ]]; then 
        stt_host=$(cat hlab_stt.out | grep "STT Sever Hostname:")
        if [ ! -z "$stt_host" ]; then
            running=$(cat hlab_stt.out | grep " Running on ")
            if [ ! -z "$running" ]; then
                stt_up=true
                stt_status="STT server up and running"
            else
                stt_status="Waiting for STT webserver to startup"
                err=$(cat hlab_stt.out | grep "Address already in use")
                if [ ! -z "$err" ]; then
                    echo "${err}" "A server seems to be running on the requested port already."
                    exit 1
                fi
            fi
        else
            stt_status="Waiting for STT Sever Hostname: to appear in hlab_stt.out"
        fi
    else 
      stt_status="Waiting for stt job to be scheduled, the file hlab_stt.out cannot be found."
    fi
    echo "${stt_status}" 
    
    all_up = (tts_up && lipsync_up && stt_up)
   sleep 2
done


echo "${tts_host}" 
echo "${lipsync_host}" 
echo "${stt_host}" 