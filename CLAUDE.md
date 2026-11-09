# Varsity: handoff notes for Claude

Varsity is a fantasy-sports PWA for San Diego high school sports. Repo: `ariborkar-bot/varsity` (work on `main`, push every change). It has a football app and a basketball app. The owner is the person you are chatting with. These notes were written at the end of a long earlier chat so a new chat can pick up where it stopped.

## How the repo works
- `index.html` is the football app and the single source of truth. Single file, no build step. Supabase for accounts and leagues.
- `basketball.html` is GENERATED. Never edit it by hand. After any change to `index.html` or `tools/make_basketball.py`, run `python3 tools/make_basketball.py` and commit both files. All basketball-only changes go in `tools/make_basketball.py` (string replacements on the football source, plus data and CSS).
- `tools/data/bb_2526_players.txt`: real 2025-26 San Diego Section boys basketball rosters and season per-game stats from MaxPreps (127 schools). `tools/data/bb_2627_games.txt`: the real 2026-27 schedule (about 1,456 games, Nov 14 2026 to Feb 13 2027, no scores yet).
- `stats.js`: football's MaxPreps box-score stats (`window.MAXPREPS`, about 1 MB), moved out of index.html in v364. **Only open or read it when the owner explicitly asks about player stats/MaxPreps data**; app changes never need it. `tools/fb_boxscores/merge.py` writes it. Basketball still bakes its own stats into basketball.html.
- `games.js`, `logos.js` (school logos), `sw.js` (service worker). **Bump `const CACHE='varsity-vNN'` in `sw.js` and `APP_BUILD` in `index.html` on every change.** Another contributor also pushes, so `git pull --rebase` before pushing; on a conflict keep both people's work and take max+1 for the version.
- Never commit conflict markers: after any rebase run `grep -c "<<<<<<<" basketball.html tools/make_basketball.py sw.js index.html`.
- Tools: `python3 tools/preview/check_syntax.py` (syntax-checks every inline script) and `python3 tools/preview/make_previews.py [out_dir]` (builds the two single-file demo previews).

## Standing preferences from the owner
- After each change: commit and push to `main`. Do NOT send preview files after app changes (owner, Nov 9 2026): only send them (`make_previews.py`, then SendUserFile both `varsity-basketball.html` and `varsity-football.html`) when the owner asks for them.
- The owner also has a private artifact page with both previews: https://claude.ai/artifact/2xj2HfG4M4WiKrj7TnxFmL (slug `0fe0f16f-75c5-4b8c-a206-03dac0615e2b`; the files are `index.html` = basketball, `varsity-basketball.html`, `varsity-football.html`). Republish it with the new preview files after changes if asked to show it in the side panel.
- Short replies. Say what changed in one or two sentences, mention anything the owner should know.
- No approval step (owner, Nov 6 2026): make the change, test it, ship it. (Earlier the owner wanted a picture before each change; that is withdrawn.)
- Test changes in a browser (Playwright with `/usr/bin/google-chrome --no-sandbox`, open a preview file) before shipping.

## Basketball decisions already made (do not undo without asking)
- Scoring: point +1, rebound +1.2, assist +1.5, steal +3, block +3, turnover -2, no 3-pointer bonus.
- Basketball says "Week N" again (v311, owner): `gameify()` was removed, so basketball uses the same word as football. The data is bucketed by calendar week; a team that plays twice in a week counts as one "game" in the per-week stats. (Per-game stats were added in v312.)
- 2025-26 seniors (grade 4) are removed (graduated). Everyone else moved up one grade for 2026-27 (Nov 6, v219, in `make_basketball.py` where players are built): 446 Sr, 243 Jr, 116 So, no Fr (new freshmen are not in last year's rosters), 31 unknown.
- Last year's stats are hidden: `SHOW_LAST_YEAR = False`. Everyone shows 0.0. While nobody has a real stat line, `PRE()` makes every player count as one 0.0 game, and the leaderboard order and TOP 10 tags follow a hidden ranking from last season (`window.BB_RANK`, `window.BB_TOP10`). Last season's team scoring still drives preseason odds (`window.BB_PRIOR`) and the projected playoff bracket.
- The 2025-26 stats banner was removed from every tab. "Show more" on the Stats leaderboard reveals 10 players at a time.
- The header court is one centered full court (cream lines, blue lane, wood floor) drawn in `_court_uri()`. The other contributor's navy and gold branded court is still used on the Simulate tab's court (`COURT_JS`).
- Basketball's 10-0 is called 82-0 (v228; every '10-0' label is swapped in make_basketball.py). Teams have 7 spots: PG, SG, SF, PF, C, G (PG or SG) and PF/C (SF, PF or C); rules version `SIM_V=3`, so older 5-player bests don't count. The season is the school's whole real regular-season schedule (no 10-game cap or filler like football).
- Hoops (basketball's Field Goal game, v229): obstacles are hoops on their side (`fgRim`): back half of the rim + trailing net + pole drawn before the ball, front half after it, so the ball flies through the ring; the hit box under the gap is the rim's width. The ball is a spinning basketball (gradient, pebbles `FG_PEB`, seams, shine). Wording: 'Tap to tip off', 'Brick!'.
- Field Goal / Hoops always possible (v230-231): each new opening is kept within what the ball can climb (~3 px·s per frame, steady taps) or drop (60% of free fall) in the frames between goals at the current speed (`g.sp`, minus 110·s for the goals' width). A tap bot survived 3 minutes at top speed in 47 of 48 runs on two phone sizes. Hit areas match the drawings: the banner has a pointed bottom; in Hoops only the bottom of the rim and the pole are solid (the old flat bar under the rim failed you in empty space).
- Geometry Dash-style zones (v231): `FG_ZONES` (fb: Day Game, Golden Hour, Friday Night Lights, Snow Bowl, Neon Turf, Space Bowl; bb: Home Gym, Sunset Blacktop, Arena Lights, Ice Court, Neon Streetball, Zero Gravity) start at scores 0/8/18/30/45/65. Colours fade over 0.9 s (`fgMix`), effects in `fgFx` (sky tint, sun, stadium lights, stars, snow, neon glow), a ZONE title card (shrunk to fit) and a ZONE n tag under the clock.
- Field Goal uprights are shorter (v232, `fgUp` = 60% of the opening, max 115·s). Flying over their tops is NO GOOD: no points, red NO GOOD flash, the run continues (`p.miss`). Hoops is unaffected.
- Positions: MaxPreps gives PG/SG/SF/PF/C, G, F, W or blank; `assign_positions()` infers the rest from stats.
- 11 small schools have no roster at all in the 2025-26 data; 24 have fewer than 5 players.

## Daily score update
- A Claude scheduled task ("Varsity daily scores", 5:41 am Pacific every day) is ON (re-created Nov 5 2026 at the owner's request). it finds final scores in news scoreboards (High School On SI, local papers) and adds them with `tools/add_scores.py`. It does not scrape MaxPreps: from the cloud MaxPreps pages come back about a year stale, and automated scraping breaks their terms.
- `tools/add_scores.py` (read its docstring): input lines `fb|YYYY-MM-DD|home|hs|away|as|source`; fills scores for scheduled games, adds unscheduled games that involve a San Diego Section school, reports CONFLICT/SKIPPED and never guesses. `--pending` lists played games with no score, `--names fb|bb` lists team names, `--dry-run` previews. Other spellings go in `tools/data/team_aliases.txt`.
- Football scores live in `games.js`; basketball scores are a trailing `64-58` (home first) on a line of `tools/data/bb_2627_games.txt`, read by `load_games()` and passed through to `basketball.html`.
- Player stats are not updated automatically (news sources rarely publish full box scores). The owner is asking MaxPreps/PlayOn for a data license and ScoreStream for an API quote; the owner wants to expand the app to the whole U.S. The app is free, with no purchases and no gambling (tokens have no cash value; real-money packs show 'Coming soon').

## Getting MaxPreps data (if needed again)
Use Claude in Chrome. `javascript_tool` output is cut off at about 1 KB and blocks query-string URLs, so write results into the page DOM and read them with `get_page_text`. Verify hand-transcribed data with a checksum computed in the browser and in Python.


## Marketing
- Six TikTok/Reels videos (Nov 5) and the tools that made them are on branch `marketing-videos` (`tools/marketing/`, read its README). Player names in videos 1-6 are made up; video 7 ("6 ways to play", Nov 6) uses real players at the owner's request (Darian Webb, Hezekiah Manuel, top 5 Card Draw hand); the owner was told California needs consent (a parent's for minors) to use names in ads. Music is synthesized.



## Where the details are
- `docs/HISTORY.md` has everything that used to live here: phone behaviour notes, open items, and one note per version from v236 to now (what each feature does and the function names). **grep it before changing a feature, and append new version notes there, not here.**

## Rules to keep (owner decisions that are easy to break)
- Declined for now (do not do without asking): hiding "Admin sign in", intro shown once ever, bigger tap targets, 12 px minimum text, shorter Minigames tab labels, Simulate leaderboard wording, "VARSITY 05" yard numbers, Stats list loading more at once.
- Wagers are final once saved (no Remove); All in asks once to confirm. Tokens have no cash value; real-money prices show 'Coming soon' (no purchases, no gambling). Pay-for-tokens was NOT built.
- Signed-out visitors only see the sign-in screen on the real site (previews run in demo mode). 13+ box at sign-up.
- Two-way football players: each card scores only its own side. Football defense scoring: tackle 1.25, TFL 2, sack 3, INT 5, PBU 2, FF 4, FR 3, def TD 6.
- Stats tab On the rise / Cooling off show exactly 5 people each.
- Field Goal / Hoops: the daily course must be identical for everyone (everything random is seeded per goal). Pack card backs never glow; Epic+ cards get the full-screen reveal.
- `games.js` was filled from MaxPreps schedule pages on Nov 8 (v335); `Castle` = `Castle Park` in team_aliases.txt is wrong for MaxPreps' 'Castle'.

## Things only the owner can do (still open as of Nov 8)
- Supabase SQL editor: run `tools/sql/push.sql`, `owner_brief.sql`, `league_cap_32.sql`, `ring_chaser_online.sql`, `mocks_policies.sql`.
- GitHub secrets for the push sender: SUPABASE_URL, SUPABASE_SERVICE_KEY, VAPID_PRIVATE_KEY, then run the workflow once as a dry run.
- Fill the `[contact email]` placeholder on the privacy page; allow host urdkamhsdjhzhrjwzyoq.supabase.co in claude.ai network settings (owner brief).
