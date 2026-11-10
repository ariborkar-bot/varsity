#!/bin/bash
# mux.sh video.mp4 music.wav sfx.wav out_base   -> out_base.mp4 (music) + out_base_nomusic.mp4 (sfx only)
set -e
V=$1;M=$2;S=$3;O=$4
D=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $V)
ffmpeg -y -v error -i $V -i $M -map 0:v -map 1:a -c:v copy -af "apad,atrim=0:$D,afade=t=out:st=$(python3 -c "print(max(0,$D-0.25))"):d=0.25,loudnorm=I=-14:TP=-1.5:LRA=11" -ar 48000 -c:a aac -b:a 192k -t $D -movflags +faststart ${O}.part.mp4 && mv ${O}.part.mp4 ${O}.mp4
ffmpeg -y -v error -i $V -i $S -map 0:v -map 1:a -c:v copy -af "apad,atrim=0:$D,volume=0.8" -ar 48000 -c:a aac -b:a 160k -t $D -movflags +faststart ${O}_nomusic.part.mp4 && mv ${O}_nomusic.part.mp4 ${O}_nomusic.mp4
echo done $O $D
