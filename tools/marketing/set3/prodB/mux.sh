#!/bin/bash
# mux.sh video.mp4 music.wav sfx.wav dur out_base
set -e
ffmpeg -y -v error -i "$1" -i "$2" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -t "$4" -movflags +faststart "$5.part.mp4" && mv "$5.part.mp4" "$5.mp4"
ffmpeg -y -v error -i "$1" -i "$3" -map 0:v -map 1:a -c:v copy -c:a aac -b:a 192k -t "$4" -movflags +faststart "$5_nomusic.part.mp4" && mv "$5_nomusic.part.mp4" "$5_nomusic.mp4"
