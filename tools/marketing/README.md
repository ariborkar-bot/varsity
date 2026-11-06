# Marketing video tools (Nov 5 2026)

How the six TikTok/Reels videos were made, so they can be remade with new players and numbers.

1. `python3 tools/preview/make_previews.py /home/claude/mk/app` (demo app copy).
2. `cap.py` + `rec1.py`/`rec2.py`/`rec3.py`: record the real app at phone size (390x844 @2.5x) with a virtual clock (`vt.js`), so animations and the Field Goal game are captured frame by frame. Every player name is swapped for a made-up one (`FAKE` in cap.py). Clips go to `/home/claude/mk/clips/<name>/fNNNN.jpg`, stills to `/home/claude/mk/stills/`.
3. `v/v1.html` … `v/v6.html`: each video is a page with `render(t)`; `lib.js`/`lib.css`/`end.js` are shared (phone frame, grain, captions, end card).
4. `mkaudio.py <v>` makes the beat + sound effects (`audio.py`, all synthesized, no licensed music).
5. `render.py video v/vN.html out.mp4 <seconds> audio/vN.wav` renders 1080x1920 30 fps H.264 + AAC. `render.py stills ...` draws single frames to check.
