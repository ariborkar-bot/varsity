# QA review B: videos 6-10

Reviewer B, Nov 9 2026. Files: `/home/claude/mk2/deliver/06..10*.mp4`. All frames were extracted to `/home/claude/mk2/qa/<video>/f/` (every frame, 30 fps). Contact sheets are `sheet.jpg` in each folder.

**Verdicts: 06 FIX · 07 FIX · 08 FIX · 09 FIX · 10 FIX.** No video ships as it is. The audio master fails on all five. #7 is closest: fix the audio and three small visual items and it can ship.

These checks pass on all five videos:
- 1080x1920, 30 fps.
- Music and nomusic files have the same length as the video, and the video stream is bit-identical across each pair.
- Nomusic files contain no music. In #6 they contain two taps at 4.40 and 6.00 s. #7 to #10 are pure digital silence, which is allowed.
- No browser UI, no demo or preview badge, no black frames before the end cards, and "Zed Hornby" never appears.
- Every name, school, point total, line and game checked matches facts.json, games.js and the app data:
  - Amaree Maye passing yards 115.5, Michael Ogdahl rushing yards 70.5, Mission Bay at Bishop's Nov 13, Division IV.
  - Santa Fe Christian at Carlsbad, Open Division.
  - Top 5: 464.1 / 428.0 / 416.7 / 399.7 / 365.1.
  - Welcome odds 49/33/17/1.
  - Hudson Quinn is a Fallbrook WR. Dane Johnson, Amelio Hernandez, Rhys Sixt and Trayshawn McNair exist in the data.
  - 86 schools.

---

## Applies to all five: audio master (severity: HIGH)

| file | integrated | true peak | clipped samples (decoded) |
|---|---|---|---|
| 06 | -12.0 LUFS | +2.7 dBTP | 3,071 |
| 07 | -10.5 LUFS | +1.9 dBTP | 8,618 |
| 08 | -11.5 LUFS | +1.1 dBTP | 6,888 |
| 09 | -10.5 LUFS | +1.6 dBTP | 7,093 |
| 10 | -11.2 LUFS | +2.9 dBTP | 9,570 |

- **What's wrong:** every file is 1.5 to 3.5 LU too loud against the -14 LUFS target. Every file has a true peak above 0 dBTP, so it will clip and distort on phone speakers. `musicB.py finish()` targets -10.5 to -13 LUFS and only limits sample peaks to -1.0 dBFS. Intersample peaks plus the AAC encode push the result past 0 dBTP.
- **Fix:** master every track to -14 LUFS with a true-peak limiter at -1.5 dBTP (oversampled) **before** the AAC encode. For example, run a two-pass `loudnorm=I=-14:TP=-1.5:LRA=11` on each `audio/vN.wav`, or set `lufs=-14` in `finish()` and add a TP limiter. Then re-run `mux.sh`. Re-measure with `ebur128=peak=true` after muxing: the true peak must be below -1.0 dBTP.
- **Also:** the nomusic tap in #6 peaks at -3.3 dBFS. That is not "soft". Bring the sfx bus down by about 8 dB.

---

## 06 "why would i deceive you?": FIX

1. **6.00-7.00 s: token balance goes UP after the wager.** The header reads 210 before the lock and **220** right after a 25-token pick is locked in (frames 181+). To a viewer this looks broken or like free money. It also looks like an app bug. `bank()` subtracts the stake, so even with a +10 starter reward the balance should read 195.
   - **Fix:** re-record, or crop or cover the header token pill for 6.0-7.0.
   - **Report to the owner:** the balance shown after locking a prop.
2. **6.00-7.00 s: "paying 54 tokens" is on screen and readable.** The in-app line is "Locked in: Over 115.5 for 25 tokens, paying 54 tokens." (y≈1310, 30 px+). "Paying" is payout language, which the rules ban. The sportsbook-style "2.17x / 1.63x" multipliers add to it.
   - **Fix (for this video):** mask that line during 6.0-7.0, or end the clip before the footer updates.
   - **Fix (app, owner decision):** change the app copy in `index.html` lines 4827/5087/5195 to "win 54 tokens".
3. **5.80 / 5.67 / 6.00 s: the "locked in" beat is out of sync.**
   - The beat hit (kick + 808) lands at 5.667.
   - The caption switches to "locked in." and the snap zoom starts at 5.80.
   - The app only shows the locked state at 6.00, when the tap sfx plays.
   - For 6 frames the caption says "locked in." over the still-open wager panel ("Win 54 tokens", ALL IN).
   - **Fix:** retime the clip so the source lock frame lands on 5.667, and move caption, zoom and tap there. Or move caption and zoom to exactly 6.00 and shift the 808 from H+4b to 6.0.
4. **5.20-5.55 s: hole in the music.** The level drops to -73/-81 dB RMS for about 0.35 s because the first 808 tail ends before the next hit. On a phone it sounds like a dropout.
   - **Fix:** lengthen the first `k808` to about 2.7 s, or add the hats at 5.33/5.50 at full velocity.
5. **4.40 and 5.20 s: no visible tap.** Over turns selected in one frame, and the 25 chip turns blue with nothing showing a finger. The plan asked for a real tap ripple.
   - **Fix:** add a small touch indicator (soft white circle, 0.25 s) at the Over card (about 300,975) at 4.40 and at the 25 chip (about 557,1288) at 5.20.
6. **3.00-4.40 s: cluttered captions.** The "the line is 115.5." box sits on top of the next card's header ("FRI, NOV 1…VISION IV"). From 4.40 to 5.80 the "over." box covers the bottom of the 25 wager chip.
   - **Fix:** shift `#cam` so a plain card area sits behind y 1340-1450. Or keep the caption and darken the area behind it with a 40% scrim strip.
7. **6.00 s: the bottom nav bar pops in** (ME / STATS / ... appear when the app re-renders). It reads as a half-loaded frame.
   - **Fix:** re-record with the nav already visible, or crop the clip so the nav is out of frame for the whole shot.
8. **5.83-6.05 s: the snap zoom crops** the VARSITY logo and the "FRI, NOV 13" header at the left edge. Minor.
   - **Fix:** set the transform origin to about x=600 so the zoom stays centered on the Over card.

---

## 07 "1% chance it's immortal.": FIX (closest to shipping)

1. **Audio master:** see the table above (-10.5 LUFS, +1.9 dBTP).
2. **7.90 and 8.00 s: double white flash.** The carousel's landing flash (7.90) and the card-reveal flash (8.00) are only 3 frames apart, because MAP `[7.9,340],[8.0,346]` squeezes them together. It reads as flicker right on the drop.
   - **Fix:** end the carousel at source frame about 336 at 7.9 and jump to 346 at 8.0, so only the reveal flash plays. Or slow 7.6-8.0 so the two flashes are at least 0.3 s apart.
3. **10.0-12.0 s: end card goes outside the safe area.** The "WHAT'D YOU PULL? 👇" line runs from x=55 to 1015. The emoji (x≈925-1015) sits under TikTok's right-hand buttons.
   - **Fix:** set `#end .q` to 100 px and the emoji to 80 px, or break the line ("what'd you pull?" / 👇 on its own line).
4. **8.10-8.13 s: mirrored card text.** During the card spin, the front of the card shows reversed ("NIUQ NOSDUH") for 2 frames. The app's flip has no card back (backface visibility).
   - **Fix:** skip those 2 source frames (about 354-355) in MAP.
   - **App:** add `backface-visibility:hidden` and a card back to the reveal spin.
5. **0.0-3.5 s: hook overlaps app UI.** The hook block sits on the app's TEAM/RARITY/PLAYER chips: their outlines and the "…" chip show through at y≈370-450, beside and under "GETS A FREE CARD." From 3.40 to 3.57 the fading hook and the fading-in "YOUR FREE PLAYER" title are on screen together (double text).
   - **Fix:** make `#topband` fully opaque down to y≈640 (gradient end at 700). Fade the hook out over 3.15-3.35, before the title appears.
6. **0.00-0.20 s: the first 200 ms of audio are digital silence** (the first stab is at 0.25). Minor.
   - **Fix:** start the stab pattern at 0, or add the kick on frame 1.
7. **Low:** the planned `team: [school]` caption at the landing was dropped. The app's Team chip covers it. OK as is.

---

## 08 "day 1 vs week 11": FIX

1. **6.80-8.50 s: "1 you (you)".** On the token leaderboard the demo name "you" plus the app's own "(you)" marker reads as a typo, and it is the final payoff shot.
   - **Fix:** give the demo profile a plausible handle (for example `sdfan27`). It is not a real player's name, so it is safe. Or hide the "(you)" suffix with CSS while recording.
2. **6.80-8.50 s: the token leaderboard has exactly one row** (rank 1 of 1). "all gold everything." over a one-person leaderboard looks fake or empty, and implies a rank-1 claim the producer meant to drop.
   - **Fix:** end on a different "after" screen: the Locker summary, the equipped banner, or the Mythical card detail. Or record against a leaderboard with real accounts.
3. **0.0-3.4 s: contradicts video #7.** The text says "day 1:" / "cards: none." while #7 says "every new account gets a free card." Posted in the same week, viewers will notice.
   - **Fix:** change the second caption to "cards: 0." under a "before:" framing, or (better) show the day-1 welcome card (an Epic) as the plain "before".
4. **3.40-5.95 vs 5.95-8.50 s: the balance changes inside the "after".** The header reads 2,450 for the first three after-shots, then 2,390 for the last two (it is a different recording).
   - **Fix:** record all after-shots from the same state, or re-record active picks and the leaderboard after setting the balance to 2,450.
5. **4.25-5.10 s: no hero card.** The "Mythical card, glowing" beat is a list row (Hezekiah Manuel, red outline), shown for 0.85 s. Nothing reads as a glowing card at phone size.
   - **Fix:** use the card detail or full-screen view of the Hezekiah Manuel Mythical card for this beat.
6. **4.25-5.10 s: app glitch on screen.** The "PLAYER" label on each mini card thumbnail is clipped at the bottom ("PLAYEᴿ").
   - **Fix:** this is an app CSS bug (the label overflows its thumbnail). Fix it before re-recording, or crop it out.
7. **1.70-3.40 s: app copy looks wrong.** Immortal card copy: "Top 25 +125%, Top 50 +200%, Player of the Week +300%, Top 10 +400%". Top 50 boosting more than Top 25 looks like a typo.
   - **Fix:** ask the owner to confirm. If it is wrong, fix `index.html` before re-recording. Few will read it in 1.7 s.
8. **8.51-10.2 s: end card breaks the series rule.** It lasts 1.69 s (rule: 2.0-2.4 s; the plan itself said 8.5-10.2) and the logo pulses on every beat (rule: holds still).
   - **Fix:** remove the per-beat `punch` on the logo, and give the end card 2.0 s (start it at 8.2, or extend the video to 10.5).
9. **Low:**
   - The "week 11:" label sits on picks for Fri Nov 13, which games.js and the app's own week tabs call Wk 13.
   - The planned post caption "200 tokens to top of the leaderboard" doesn't match the 210 shown, and "top" is the rank claim that was dropped.
   - **Fix:** caption "210 tokens to all gold everything. it's free btw."
10. **Audio master:** see the table above. The timing is good: drop at 3.40, cuts on 4.26/5.11/5.96/6.81, end at 8.51.

---

## 09 "playoff friday, timestamped": FIX

1. **1.56-3.12 s (7:40 am, 10-0 sim): broken-image icons on screen.** The end-zone banner above the field shows two missing-image icons (top right at about 810,1035 and behind the OFFENSE badge at the top left). See `qa/09_playoff_friday_timestamped/crop_sim.jpg`. This is a half-loaded asset in a marketing video.
   - **Fix:** re-record after the end-zone images load (wait for `img.complete`), or fix the image paths in the preview build.
2. **0.0-1.56 s: the hook's proof sits under TikTok's UI.**
   - The "+25 tokens · daily bonus" toast sits at y≈1570-1690, below the 1450 safe line.
   - The phone mockup (y 570-1914) puts the lower third of every app shot under TikTok's caption and buttons.
   - The phone's bottom bezel is cut at the frame edge.
   - **Fix:** scale the phone to about 0.6 and move it up (top ≈540, bottom ≤1600). Make sure the toast and each tapped control sit above y=1450.
3. **Every shot: the app is a mockup.** Rule: "Record real app screens in true 9:16 ... not a mockup". The app sits in a drawn phone frame at 70% scale, so in-app text is about 20-25 px effective and hard to read in 1.56 s.
   - **Fix:** accept it as this video's look (the owner's call), but enlarge the phone as in item 2. Or drop the frame and run the screens full-bleed under a white top band holding the clock.
4. **10.9-12.5 s: "9:45 pm · checking the leaderboard" implies the board updates the same night.** Player stats are not updated automatically. Per CLAUDE.md they come from MaxPreps or the owner, not live.
   - **Fix:** relabel (for example "9:45 pm · top 10 check") or move the stamp to Saturday morning. Or get the owner to confirm that a same-night update is real.
5. **14.03-15.6 s: end card is 1.57 s** (rule 2.0-2.4 s).
   - **Fix:** shorten one middle shot by 2 beats (0.78 s), or extend the video to 16.0 s.
6. **Clock styling.** "6 : 58   AM" in Mono1 has a wide colon and a double-width gap before AM. "FRIDAY · PLAYOFFS" is uppercase, while the rule says on-screen text is lowercase.
   - **Fix:** use "6:58 am" (a single space, or narrower letter-spacing) and "friday · playoffs".
7. **Low:** "Locked in: Carlsbad for 5 tokens, paying 10 tokens." is readable at 6.23-7.79. Same "paying" issue as #6.
   - **Fix:** blur that line or fix the app copy.
8. **Low, 12.5-14.0 s: weak final beat.** The 10:30 pm Rookie pack pulls three Uncommons, an anticlimax for the day's last beat. The third card overlaps the bottom of the first row (app layout).
   - **Fix:** use a natural pull with a Rare or better, or end on the reveal of a single card.
9. **Low, 1.56-3.12 s: weak lineup.** The 10-0 lineup shows QB "R. Sixt 0.0 PPG".
   - **Fix:** auto-fill the lineup with players who have stats before recording.
10. **Audio master:** see the table above. Timing is good: 1-beat stop at 8.9-9.3, toms, drop at 9.35, end hit at 14.03.

---

## 10 "some of these guys play their last game friday.": FIX

1. **0.00-0.70 s: the hook is not on screen at the start.** The text is invisible on frames 1-7. At 0.33 s it is half-transparent and overlaps the app's player names and points (ghosted double text). It is fully readable only at about 0.7 s. Brief: hook visible within about 0.3 s.
   - **Fix:** for the first segment, set `#txt` opacity to 1 from t=0 with no rise. Keep the fade-in only for later segments.
2. **6.1-9.1 s: singles out one named minor in a "last game" tribute.** The search types "darian webb" and the result shows his "Sr" chip. The hook frames also show "Sr" chips on Paisios Polamalu and Darian Webb. The plan said: show no individual player as a senior, keep it general.
   - Putting a named minor under "the last high school game they ever play" is sensitive.
   - It becomes false if Carlsbad wins on Friday.
   - It is a likely consent issue if the video is boosted.
   - **Fix:** type a school playing Friday, as planned (for example "helix"), so a list appears, not one player. Or use the leaderboard without the search.
3. **12.15-15.2 s: odds in a tribute, with no small print.** "go make it count." sits over the Pick 'em list with multipliers and win percentages ("3.22x / 29% to win", "3.77x", ...).
   - Betting-style odds in a senior tribute are off-tone.
   - The screen shows token wagers, so the end card needs "tokens only · no real money", and this one has none.
   - **Fix:** use a screen without multipliers (Game of the Week, or Friday's schedule or playoff bracket). Or keep this screen and add `tokens only · no real money` to the end card.
4. **6.1-9.1 s: the typing is nearly invisible.** The search bar is at y≈360-500, under `#topdim` (86-92% black). The typed "dari… darian webb", the action of the shot, is dark grey on black.
   - **Fix:** cut `#topdim` to about 560 px tall, or zoom or position the clip so the search bar sits below about y=600.
5. **3.0-6.1 s: the caption doesn't match the chart.** "every friday since august." sits over a chart with a BYE in W6 and "No game" or TBD in W12.
   - **Fix:** "since august." or "11 weeks." (the original plan wording).
6. **Low, 0-3.0 s: player count doesn't match.** "SHOW 10 MORE (3776 LEFT)" implies 3,781 players. That conflicts with the 3,597 used in marketing and with "PLAYERS 6/3599" in #8.
   - **Fix:** scroll so the button is out of frame, or crop it.
7. **Low, 6.1 s: floor tom barely audible.** The planned floor-tom entry raises the level only about 2-3 dB. The planned build doesn't come through on phone speakers.
   - **Fix:** raise the tom bus by about 4 dB.
8. **Audio master:** see the table above (+2.9 dBTP is the worst of the five). Timing is good: band at 12.15, ringing chord at 15.2, fade to black by 18.2.
