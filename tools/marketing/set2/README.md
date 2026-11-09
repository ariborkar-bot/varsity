# Video set 2 (Nov 8 2026): five new TikTok/Reels videos

Owner feedback on set 1: "they all have the same sound, all look the same AI look". Set 2 has five different genres and five different looks,
real app footage at true 9:16, real player names (owner's call, Nov 8) and only gold cosmetics.

| Video | Look | Music (all synthesized here, no samples or licensed music) |
|---|---|---|
| v1 pack opening (12.8 s) | raw screen recording, TikTok outline captions, handheld drift, RGB split on the pull | rage, 150 BPM, F# minor, drop on the Mythical reveal |
| v2 is your school on here? (12 s) | gold/black editorial, Anton, wall of school logos, zoom into Carlsbad, team page | jersey club, 140 BPM, vocal chops |
| v3 Hoops: can you make it to zone 6? (15 s) | arcade HUD (Rubik Mono One), zone progress bar, synthwave end card | chiptune trap, 160 BPM, layer added each zone |
| v4 POV meme (13.5 s) | white meme caption box, red hand-drawn circle, A+ slam | drill, 142 BPM, sliding 808s, choir |
| v5 rivalry week (12 s) | letterman-jacket red/cream, Dela Gothic One, split-screen rivalries | marching drumline + brass + 808, 120 BPM |

Each video also has a `_no_music` version (sound effects only, about -18 LUFS) for adding a trending sound in TikTok/Instagram.

## Remake
1. `python3 tools/preview/make_previews.py /home/claude/mk/app`; copy `vt.js` and `cap.py` (set 1) to `/home/claude/mk/`, and this folder's files there too.
2. Footage (REAL=1 = real names): `REAL=1 python3 recpack.py player pack 480` (pack: `GOT` = Mission Hills team card, Deshaun Hille, Courtney Miller-Thompson, Gold foil card back, Darian Webb Mythical),
   `REAL=1 python3 recmore.py search card league cup picks`, `OFF=0.18 VY=0 python3 hoopsbot.py rec 1500 11` (zones 1-3) and
   `JUMP=1 NAME=hoops2 OFF=0.18 VY=0 python3 hoopsbot.py rec 700 11` (zones 4-6: zones change by time played, so the game clock is moved forward).
3. `python3 music.py v1 v2 v3 v4 v5` -> `audio/vN.wav` and `audio/vN_sfx.wav`.
4. `python3 render.py video v/vN.html out/name.mp4 <seconds> audio/vN.wav` (stills: `render.py stills v/vN.html prefix t1 t2 ...`).
Notes: the pack recording flickers the last cards (virtual clock); v1 holds frame 402 for the final grid. Hoops search by school name does not exist (search matches player names), so v2 uses the team page.
