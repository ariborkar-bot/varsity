# QA review A: videos 01-05 (Nov 9, 2026)

Reviewer: independent QA (I did not make these videos). Files reviewed: `/home/claude/mk2/deliver/01..05*.mp4` and their `_nomusic` twins.
Method: every frame was extracted (`qa/<video>/all/fNNNN.jpg`, 30 fps), with contact sheets every 0.25 s and the TikTok safe area drawn on (`qa/<video>/sheet.jpg`). Full-size frames were checked at every cut and caption. Frame-difference cut detection, OCR on every 6th frame (searched for "Hornby", bet/gamble/cash/payout/wager/odds), ffmpeg ebur128/volumedetect, and per-band RMS energy (30-150 Hz / 150-2k / 2k-12k, plus a "phone speaker" simulation: energy above 200-250 Hz, where phone speakers actually play). Facts were checked against `facts.json` and `varsity/games.js`.

## Verdicts

| # | Video | Verdict |
|---|---|---|
| 01 | comment your school | **FIX** (misleading captions on the key facts) |
| 02 | top 10 walk-in | **FIX** (no hook on frame 0, clipped numerals, cropped cards) |
| 03 | pause and pick | **FIX** (token balance goes UP after a pick; "Wager / ALL IN / paying" on screen) |
| 04 | #6 vs #7 | **FIX (small)**: closest to ready |
| 05 | it's time | **FIX** (the drop gets quieter on phones; "everyone at 0.0" isn't what's on screen; "odds" on screen) |

What passed for all five: 1080x1920, 30 fps, H.264 High, yuv420p. The music and nomusic files are exactly the video's length (12.4 / 15.6 / 16.633 / 20.0 / 13.0 s). Integrated loudness is -13.4 / -14.7 / -13.9 / -14.6 / -13.7 LUFS and true peak is -4.3 / -3.2 / -2.4 / -1.5 / -1.6 dBTP, so nothing is near clipping. The nomusic files have no music (02, 03 and 05 are pure digital silence; 01 has only typing SFX at 3.0-4.2 s and 7.25-7.75 s; 04 has only the stamp hit at 13.25 s). OCR found no "Zed Hornby" in any frame. Every name, school, position, point total and per-game figure I checked matches facts.json. The game Clairemont 28 at Mountain Empire 55 (Fri Nov 6, Division V-AA, week 12) matches games.js.

---

## Cross-cutting issue (all five): the music is mixed for subwoofers, not phones

Spectrum of each full mix (share of energy):
- 01: **85 % of the energy is one sustained ~49 Hz tone** (40-60 Hz band at -0.7 dB relative); everything above 500 Hz is 30+ dB down.
- 02: 20-60 Hz carries most of the energy; 03: same; 05: 20-40 Hz dominates.

Loudness with a phone-speaker simulation (4th-order high-pass at 200 Hz) vs the full mix:
- 01: **-27.0 LUFS** (full mix -13.4). On a phone the bed will be close to inaudible.
- 02: -21.1 · 03: -20.1 · 04: -19.5 · 05: -18.3.

The **drops get quieter on a phone**, because all the energy added at the drop is sub-bass. Here is the energy above 250 Hz before vs after each drop:
- 02 at 6.0 s: **-2.8 dB** (and the 2-12 kHz band falls from -30 to -42 dB, so the "filter opens" in the plan doesn't happen).
- 04 at 13.3 s: **-5.6 dB**.
- 05 at 3.2 s: **-10.5 dB** (mids fall from about -15 to -28 dB; the "hard hip-hop beat" is all sub). On an iPhone speaker the season-switch drop, which is the whole joke of video 5, will sound like the music cut out.

**Fix (in musicA.py, then re-mux):** high-pass or low-shelf everything below about 60 Hz by 8-12 dB. Add harmonics to the 808 and bass (saturation, or a layer an octave up at 100-200 Hz). Put the drop's energy into the mids and highs: snare/clap at 1-3 kHz, hats at 6-10 kHz, chord stabs at 300 Hz-2 kHz. For 05, make the recorded dribble and sneaker squeak loud, since they live in the mids. Re-normalize to -14 LUFS / -1.5 dBTP. **Acceptance test:** with HPF 200 Hz, the mix should be no more than about 5 LU below the full mix, and the energy above 250 Hz should rise by at least +4 dB at each drop (02 at 6.0, 04 at 13.3, 05 at 3.2).

---

## 01 comment your school: FIX

1. **5.30-7.17 s: "#1 in all of san diego." points at the wrong player.** The caption sits at y≈600-705, right between "1 Dean... (Morse) 74.4" and "2 Wesley Dill" in the *Players of the Week* panel (which ignores the school filter). It also covers Wesley Dill's stat line. Hezekiah Manuel's card is lower, at y≈1050-1570. A viewer reads "#1" as Deandre Eleby or Wesley Dill. *Fix:* scroll or crop so the POTW panel is off screen and the Hoover podium is centred (Hezekiah card around y 500-1100). Put the caption directly above or below his card, for example "hezekiah manuel. #1 in all of sd."
2. **8.30-9.77 s: "carlsbad has #3." contradicts the screen.** The only "3" badges visible are Cash Redman's school-rank badge (112.4) and Caleb McNickle's POTW rank. Darian Webb's card shows a **"1"** badge (school rank), and no "#3 overall" appears anywhere. *Fix:* use "darian webb. #3 in all of sd." placed on Webb's card, or cut to the overall leaderboard row that shows rank 3. Crop the POTW panel out as in issue 1.
3. **11.10-12.40 s: the end card is only 1.3 s** (the rule is 2.0-2.4 s), and the tagline is only fully readable for about 0.8 s (it fades in until about 11.35 s and the 0.25 s audio/visual fade starts at 12.15 s). *Fix:* start the end card at about 10.0 s (trim the 9.77-11.1 hold) or extend the video to about 13 s.
4. **11.10 s: hard cut from the dark app to a pure-white end card (mean luma 252).** This is a full-screen white flash and the only white frame in the series. It looks harsh and off-look. *Fix:* use a dark end card that matches the app navy, or a short (4-6 frame) dip.
5. **End card tagline crosses the right safe line:** "find your name on the leaderboard" spans x≈42-958 (limit 940), so TikTok's right rail will sit on "leaderboard". *Fix:* make the font about 8 % smaller or break it into two lines.
6. **9.77-9.90 s: the background jumps.** The filtered Carlsbad results snap to the unfiltered list ("First Team All-Varsity", the Polamalu/Manuel/Webb podium) and scroll for 4 frames while "carlsbad has #3." is still on screen. *Fix:* cut on 9.77 straight to the cleared search bar, with no visible re-render.
7. **0-1.33 s: the hook (7 words plus the counter) is on screen only 1.33 s.** It can't be read twice. *Fix:* hold it to about 1.9 s (shift the later beats by one beat, 0.652 s) or shorten it to "every sd football player. ranked."
8. **1.17-1.33 s: the scroll overshoots to the bottom of the Stats page.** The "Compare" panel ("Pick any two players...") is behind the hook for about 5 frames. At the top, "SHOW 10 MORE (3748 LEFT)" is half-hidden by the header; that number disagrees with the 3,597 counter if anyone reads it. *Fix:* stop the scroll inside the list.
9. **Audio sync, 7.6-7.83 s:** the music stops and hits on the beat at 7.83 s, but the Carlsbad results zoom lands at about 8.07-8.20 s, roughly 0.3 s late. (Hoover lines up: stop at 5.1, hit at 5.2, zoom at 5.0-5.3.) *Fix:* finish typing "carlsbad" by 7.7 s so the zoom lands at 7.83 s.
10. **Audio:** see the cross-cutting section. Above 250 Hz the bed is at -34 dB RMS, so it is basically silent on phones. The kick "coming in at 5.2 s" changes the phone-audible level by only +2.5 dB.
11. Minor: in the zoomed result shots the header logo is cut at x=0, and Webb's "416.7" (y≈1490) sits below the y=1450 safe line, where TikTok's caption can cover it. Raise the podium about 150 px.

## 02 top 10 walk-in: FIX

1. **0.00-0.23 s: frame 0 is pure black, with no hook.** "san diego's" fades in from 0.25 s, and the full line "san diego's top 10 walking into playoff week:" is complete only at about 1.5 s and gone at about 1.9 s, so the whole hook is readable for about 0.4 s. Frame 0 is also TikTok's default cover. *Fix:* show the full line at full opacity on frame 0 (the type-in can be a highlight sweep instead), and hold it until 2.4 s (one bar).
2. **1.8-6.0 s: the big rank numerals are clipped and hidden.** The outline numerals sit at x≈850-1010, half behind the cards. They cross the x=940 safe line, and the "9" at 2.5 s is cut off by the frame edge. The plan put the numeral on the left. *Fix:* put the numeral left of the rows (or above the newest row) on a layer in front of the cards, fully inside x<940.
3. **6.0-13.2 s: the player cards are cropped badly.** The "SEASON PTS" tile is cut at the card's left edge (the "4" of 416.7 touches the border), "BEST WEEK" is cut on the right, and there is a visible darker panel seam behind the big "3". "Carlsbad, 10 / games" (and "St. Augustine, 10 / games", "Hoover, 11 / games") wraps with an orphan word. *Fix:* capture the whole profile header with padding (or widen the viewport before capture) so all three tiles have full rounded borders. Don't let the school line wrap ("Carlsbad · 10 games").
4. **11.4-13.2 s: the redundant, contradictory count-up.** "167.8 pts... 343.1 pts" counts up under a card that already says SEASON PTS **464.1**. *Fix:* either blank the 464.1 tile until the count-up finishes, or drop the count-up.
5. **13.2-15.6 s: the end card line breaks badly:** "who's walking in next / week? / find your rank." leaves an orphan "week?". *Fix:* "who's walking in / next week?" then "find your rank." on its own line. Also, the first 0.3 s of the end card is nearly blank (text fades in 13.2-13.5); start it at about 60 % opacity.
6. **6.0 s: the drop.** The visual flash and card are on time (white flash at f181), but on phones the drop gets 2.8 dB quieter and the highs fall (see cross-cutting). The "filter opens + hats" doesn't happen in the audio.
7. **Look:** every card fills only y≈450-1230. The bottom 40 % of the frame is empty black with a blurred background, which reads as unfinished rather than "letterboxed". *Fix:* scale the cards up about 15 % and centre them on y≈850, or add the faint leaderboard behind them.
8. Minor: "DEANDRE E..." is truncated by the app (the POTW chip steals the space). Hide the chip for the capture so the full name shows. These are real players walking into playoff week, and their name is the payoff.

## 03 pause and pick: FIX

1. **13.93 s (f419): the token balance jumps 210 → 240 the instant the pick locks**, right after "Locked in: Carlsbad for 5 tokens". It should go *down* (205). Anyone watching closely will call it fake. *Fix:* re-record so the header shows the real post-pick balance, or crop the header out of the 12.9-14.8 s shot. If the +30 is a real bonus (first pick, daily, etc.), show the app's own toast explaining it.
2. **12.9-14.8 s: gambling words on screen.** The app UI shows **"Wager"**, **"ALL IN"** and "Locked in: Carlsbad for 5 tokens, **paying** 10 tokens" (OCR confirmed). The brief bans bet/gamble/payout-type wording, and an "ALL IN" button in an ad aimed at 14-year-olds is a real platform-review risk. *Fix:* crop to the two team tiles plus the "Your pick" chip and "Locked in" (zoom about 130 % on y≈650-1150), so the wager row, ALL IN and "paying" text are out of frame. Longer term the app copy could say "pick for 5 tokens · win 10".
3. **Throughout: the cards show sportsbook-style multipliers** (1.73x / 2.01x, 2.11x / 1.66x...). With the % they imply about 7 % margin, which looks like a betting line. The plan asked for "seeds and % to win". *Fix:* the owner should decide. If they stay, keep the small print (it's there). Otherwise crop to "% to win".
4. **0.0-1.85 s and 12.9-14.8 s: the captions cross the right safe line.** "PAUSE ON EVERY GAME." box runs to x≈1010 and "PICKS LOCK AT KICKOFF." box to x≈975. *Fix:* cap caption boxes at x=920.
5. **Caption style breaks the series rule.** Hook, "picks lock at kickoff." and the end card are ALL CAPS ("on-screen text is lowercase and casual"). *Fix:* use lowercase in the same condensed italic, or get the owner's sign-off on caps for this look.
6. **12.9-14.8 s: a messy layer behind the caption.** "PICKS LOCK AT KICKOFF." sits on half-visible text of the top card ("Vincent Memorial / Palo Verde Valley", a game that isn't in the 6), cut by the app header. The caption box is also about 40 % empty on the right. *Fix:* scroll so the Santa Fe Christian card is at the top of the viewport, and size the box to the text.
7. **12.9-14.8 s: the video picks a side (Carlsbad) in the 1/6 game**, while the pinned-comment plan says the post doesn't take a side. *Fix:* demonstrate the lock-in on a game that isn't in the six (for example Holtville at Poway).
8. **Frame 0 has no text** (the hook slides in; line 1 is readable at 0.10 s and all three lines at 0.33 s). That meets the 0.3 s target, but frame 0 is the default cover. *Fix:* have line 1 already in place on frame 0.
9. **14.8-16.63 s: the end card is 1.83 s** (rule 2.0-2.4 s), and the audio there is the *loudest* part of the track (-7 dB RMS, a sustained sub boom) rather than the "full break" in the plan. *Fix:* start the end card at 14.6 s or extend to 16.9 s, and make it a real break (drop the drums, let one stab ring).
10. **nomusic file is complete silence:** the "real tap" SFX at lock-in (plan, 12.9-14.8 s) is missing, so if the owner uses the trend sound in-app there is no tap at all. *Fix:* put the tap SFX in m3_sfx.wav.
11. Not verifiable from here: whether 54 %/46 %, 1.73x/2.01x etc. match what the app shows today. The plan says to use only recorded app numbers. They look like real captures, but re-check them on posting day, because odds can move.

## 04 #6 and #7: FIX (small)

Facts all check out: #6 Malachi Gutierrez (Clairemont WR, 338.7, 30.8/g, 11 games), #7 Elisha Robinson (Mountain Empire RB, 320.3, 35.6/g, 9 games), #11 Timothy Cox (289.3), and Mountain Empire 55 Clairemont 28, Fri Nov 6, Division V-AA. The cuts land on the bars (3.33 / 11.73 / 16.67 / 18.0 s), and the FINAL stamp lands at 13.37 s against the audio hit at 13.33 s. Good.

1. **13.33-13.37 s (f401, f402): the "paper shake" shows black bars**: 10 px of black at the top on f401 and 4 px at the bottom on f402. *Fix:* scale the page to 102 % during the shake (overscan), or clamp the offset.
2. **File size / bitrate: 102 MB at 40.7 Mbit/s for 20 s** (the others are 6-10 Mbit/s), driven by full-frame paper grain. It may exceed in-app upload limits on some phones, and TikTok/IG will recompress the grain into blocky mush. *Fix:* re-encode with CRF 20-22 and `-maxrate 12M -bufsize 24M`, and lower or soften the grain (or animate it at 12 fps).
3. **13.3 s: the trap drop gets 5.6 dB quieter on phones** (cross-cutting); the drop energy is all sub.
4. **6.7-13.3 s: the same card-crop problems as 02:** "Mountain Empire, 9 / games" and "Clairemont, 11 / games" wrap, and the stat tiles are cut at the card edges. There is also a small stray vertical gold glint at the card's top right (x≈640, y≈470) on both cards. *Fix:* same as 02 item 3; remove the glint.
5. **11.73-13.3 s: the Timothy Cox row is tiny.** The row is about 875x200 px, the name about 30 px tall and the stat line about 20 px, so it is unreadable on a phone. *Fix:* scale the row to full width (about 1.3x) and keep the red circle.
6. **End card says "The VARSITY"** in the serif. The brand wordmark is "VARSITY". The masthead pun works, but the end card is the brand moment. *Fix:* "VARSITY" alone (the serif is fine), or the app wordmark.
7. **0.0 s: frame 0 shows only the masthead**, and the headline types in from 0.25 s. *Fix:* start with "#6 and #7" already printed.
8. Minor: the masthead "The Varsity" (y≈200-300) overlaps TikTok's top "Following / For You" bar; lower the whole layout about 60 px. The thin "#" glyph next to the heavy numerals looks like a font fallback; use the bold weight's "#" or a hand-set number sign.
9. Minor: the audio sits at -29 to -35 dB RMS from 2.0-2.9 s and 8.5-9.9 s (the piano decays). That is intended, but 2.0-2.9 s is still the hook window. Consider a soft pad under it.

## 05 it's time: FIX

Facts check out: 890 players; podium #1 Tristan Anderson (Olympian PG), #2 Josiah Roy (Horizon Prep C), #3 Brewster Gale (St. Joseph Academy PF); #4 Tavid Johnson, #5 Zach Baker as in bbTop10; Westview at La Jolla, Sat Nov 14; 7 spots PG SG SF PF C G PF/C. The Hoops zone change at clock 15.0 s (Home Gym → Sunset Blacktop) is consistent with `FG_ZONES` (time-based, at:15), so the gameplay is genuine.

1. **3.2 s: the drop is the concept, and on a phone it gets 10.5 dB quieter** (music box at -16.7 dB above 250 Hz → beat at -27.2 dB). See cross-cutting. Highest-priority fix in this video.
2. **4.8-6.4 s: "EVERYONE AT 0.0" vs the screen.** Every card and tile in view shows **"—"** (a dash), not 0.0. 0.0 appears only in the small "0.0 per game" text on the rows. The plan says to zoom on the 0.0. *Fix:* zoom onto a row's "0 pts · 0 reb · 0 ast / 0.0 per game", or change the caption to "890 players. nobody's scored yet."
3. **6.4-8.0 s: "odds set by Varsity"** (OCR) in the Week 1 Pick 'em header, plus 1.73x/2.01x multipliers. That is betting language in a video with **no "tokens only · no real money"** small print. *Fix:* crop the header line out, and add the small print to the end card, since the video shows a pick screen with multipliers.
4. **8.0-9.6 s: "BUILD YOUR 7." is pasted over the "BEST TEAMS · POINTS PER GAME" heading.** The cut-off heading peeks out above and around the box ("B[...]GAME"). At 9.0-9.5 s the shot is shifted so "82-0" is cut at the left edge and reads as "2-0" / "12-0". *Fix:* move the caption onto the empty area below the card (y≈1250), and keep "82-0" fully in frame.
5. **8.0-9.6 s: no draft screen is shown.** The plan called for "Draft screen with 7 spots", and the screen shown says "Build your team opens once the season is underway (it starts Nov 14) and players have at least 2 games of stats". "draft your 7" right after "tips off saturday" implies you can draft Saturday. *Fix:* show the real 7-spot layout if the app can render it in demo mode. Otherwise change the caption to "82-0: your best 7." and crop out the "opens once..." sentence.
6. **0.0-3.2 s: the frost is a full-screen cracked-ice / scratch texture** (white crack lines over everything). The plan says "a soft white vignette, not snowflakes". This reads as a stock overlay and is the most "cheap/AI" look in the batch. *Fix:* soft white radial vignette from the edges plus slight desaturation and blur, with no line texture.
7. **3.2-4.8 s: busy caption plate.** "BASKETBALL / IS HERE." sits over the blue TOTAL pill and the position chips, with the pill poking out both sides of the "IS HERE." box (f121). At f129, "PF" / "C" chips and fragments of "FIRST TEAM ALL-VARSITY" peek around it. The header court (the visual hero of the drop) is visible for only about 0.8 s and is washed out by the white flash at 3.2 s. *Fix:* hold the header court un-zoomed and un-flashed for 2 beats (3.2-4.0 s) with the caption over the court, then move to the leaderboard.
8. **6.4-8.0 s: "TIPS OFF SATURDAY." covers "Hoover"** on the second card (Hoover at Morse), leaving a half-hidden card. *Fix:* scroll so only the Westview at La Jolla card is in frame, and put the caption below it.
9. **9.6-11.0 s: the Hoops HUD** (clock 0:14.9, ZONE tag) is at y≈230, inside TikTok's top bar, and the school banner on the pole runs off the top edge. *Fix:* shift the gameplay capture down about 80 px.
10. **nomusic file is complete silence:** the plan's recorded dribble (kick) and sneaker squeak (snare) live only in the music file. If the owner uses Mariah in-app, the drop has no hit at all. *Fix:* put one dribble plus squeak hit at 3.2 s in m5_sfx.wav.
11. Minor: the Westview at La Jolla numbers (1.73x / 54 %, 2.01x / 46 %) are identical to Santa Fe Christian at Carlsbad in video 03. That suggests a default home/away line rather than BB_PRIOR. It is not a video defect, but if both videos run the same week someone may notice. Worth checking in the app.

---

## Priority list for the producer
1. Remix all five tracks for phone speakers (cross-cutting). This matters most in 05 and 01.
2. 03: the 210→240 balance jump, and crop out Wager / ALL IN / paying.
3. 01: re-place "#1 in all of san diego" and "carlsbad has #3" so they point at Hezekiah Manuel and Darian Webb, and crop out the POTW panel.
4. 05: fix "everyone at 0.0" (screen shows "—"), crop "odds set by Varsity", add the small print, and fix the "BUILD YOUR 7." overlap.
5. 02: show the hook on frame 0 and hold it 2.4 s; fix the numeral placement and the card crops.
6. 04: overscan the shake, re-encode at about 12 Mbit/s, and use the "VARSITY" end card.
7. Safe-area and end-card length clean-up: 01 end card 1.3 s and tagline to x=958; 03 end card 1.83 s and captions to x≈1010.
