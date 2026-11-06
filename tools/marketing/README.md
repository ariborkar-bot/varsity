# Marketing video tools (Nov 5 2026)

How the six TikTok/Reels videos were made, so they can be remade with new players and numbers.

1. `python3 tools/preview/make_previews.py /home/claude/mk/app` (demo app copy).
2. `cap.py` + `rec1.py`/`rec2.py`/`rec3.py`: record the real app at phone size (390x844 @2.5x) with a virtual clock (`vt.js`), so animations and the Field Goal game are captured frame by frame. Every player name is swapped for a made-up one (`FAKE` in cap.py). Clips go to `/home/claude/mk/clips/<name>/fNNNN.jpg`, stills to `/home/claude/mk/stills/`.
3. `v/v1.html` … `v/v6.html`: each video is a page with `render(t)`; `lib.js`/`lib.css`/`end.js` are shared (phone frame, grain, captions, end card).
4. `mkaudio.py <v>` makes the beat + sound effects (`audio.py`, all synthesized, no licensed music).
5. `render.py video v/vN.html out.mp4 <seconds> audio/vN.wav` renders 1080x1920 30 fps H.264 + AAC. `render.py stills ...` draws single frames to check.

## Video 7: "6 ways to play" (Nov 6)
Uses REAL player names (owner's call): `REAL=1` env or `newpage(b,fake=False)`. `rec7.py card picks props fc still` records Darian Webb's card, Pick 'em on Mount Miguel vs Mater Dei Catholic, props on Hezekiah Manuel, a 5 Card Draw hand of the top player at each position, and a sample league (`LEAGUE` in cap.py, `__seed=39`, week set to 11). `REAL=1 SUF=_r python3 rec2.py rc` records Ring Chaser.

## Video 8: "group chat" (Nov 6) — the native-style one
Built to look like a real phone screen recording, not a mockup: an iMessage group chat hook ("when the group chat finds out there's fantasy for OUR high school"), then full-screen app footage with velocity edits (beat zoom punches, whip pans, zoom-through), TikTok white-box captions, and a muffled-to-drop phonk beat.
- `rec8.py league picks props`: records the app at 392x697 (true 9:16, 1080x1920 frames) with iPhone safe-area spacing patched in. League clip = one frame per 7 px of scroll, so the page can speed-ramp.
- `audio8.py audio8_v8.json`: 140 BPM synthesized beat + iMessage dings/swoosh, taps, coin, lock. Cuts sit on beats (drop = beat 8).
- `render.py video v/v8.html out.mp4 20.571 audio/v8.wav`.
