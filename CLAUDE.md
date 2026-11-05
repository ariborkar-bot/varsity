# Varsity: handoff notes for Claude

Varsity is a fantasy-sports PWA for San Diego high school sports. Repo: `ariborkar-bot/varsity` (work on `main`, push every change). It has a football app and a basketball app. The owner is the person you are chatting with. These notes were written at the end of a long earlier chat so a new chat can pick up where it stopped.

## How the repo works
- `index.html` is the football app and the single source of truth. Single file, no build step. Supabase for accounts and leagues.
- `basketball.html` is GENERATED. Never edit it by hand. After any change to `index.html` or `tools/make_basketball.py`, run `python3 tools/make_basketball.py` and commit both files. All basketball-only changes go in `tools/make_basketball.py` (string replacements on the football source, plus data and CSS).
- `tools/data/bb_2526_players.txt`: real 2025-26 San Diego Section boys basketball rosters and season per-game stats from MaxPreps (127 schools). `tools/data/bb_2627_games.txt`: the real 2026-27 schedule (about 1,456 games, Nov 14 2026 to Feb 13 2027, no scores yet).
- `games.js`, `logos.js` (school logos), `sw.js` (service worker). **Bump `const CACHE='varsity-vNN'` in `sw.js` and `APP_BUILD` in `index.html` on every change.** Another contributor also pushes, so `git pull --rebase` before pushing; on a conflict keep both people's work and take max+1 for the version.
- Never commit conflict markers: after any rebase run `grep -c "<<<<<<<" basketball.html tools/make_basketball.py sw.js index.html`.
- Tools: `python3 tools/preview/check_syntax.py` (syntax-checks every inline script) and `python3 tools/preview/make_previews.py [out_dir]` (builds the two single-file demo previews).

## Standing preferences from the owner
- After each change: commit, push to `main`, and send the owner fresh preview files (`make_previews.py`, then SendUserFile both `varsity-basketball.html` and `varsity-football.html`).
- The owner also has a private artifact page with both previews: https://claude.ai/artifact/2xj2HfG4M4WiKrj7TnxFmL (slug `0fe0f16f-75c5-4b8c-a206-03dac0615e2b`; the files are `index.html` = basketball, `varsity-basketball.html`, `varsity-football.html`). Republish it with the new preview files after changes if asked to show it in the side panel.
- Short replies. Say what changed in one or two sentences, mention anything the owner should know.
- Test changes in a browser (Playwright with `/usr/bin/google-chrome --no-sandbox`, open a preview file) before shipping.

## Basketball decisions already made (do not undo without asking)
- Scoring: point +1, rebound +1.2, assist +1.5, steal +3, block +3, turnover -2, no 3-pointer bonus.
- The word "week" is replaced by "game" everywhere visible in basketball (`gameify()` in `make_basketball.py`). The data is still bucketed by calendar week, so "Game 5" is really all of a team's games that week. A true per-game model was offered and not started.
- 2025-26 seniors (grade 4) are removed (graduated). Remaining players still show their 2025-26 grade; moving everyone up a grade was offered and not done.
- Last year's stats are hidden: `SHOW_LAST_YEAR = False`. Everyone shows 0.0. While nobody has a real stat line, `PRE()` makes every player count as one 0.0 game, and the leaderboard order and TOP 10 tags follow a hidden ranking from last season (`window.BB_RANK`, `window.BB_TOP10`). Last season's team scoring still drives preseason odds (`window.BB_PRIOR`) and the projected playoff bracket.
- The 2025-26 stats banner was removed from every tab. "Show more" on the Stats leaderboard reveals 10 players at a time.
- The header court is one centered full court (cream lines, blue lane, wood floor) drawn in `_court_uri()`. The other contributor's navy and gold branded court is still used on the Simulate tab's court (`COURT_JS`).
- Positions: MaxPreps gives PG/SG/SF/PF/C, G, F, W or blank; `assign_positions()` infers the rest from stats.
- 11 small schools now have empty rosters (all seniors); 24 have fewer than 5 players.

## Open items and ideas
- Scores are not read yet. When games are played, `tools/data/bb_2627_games.txt` and `load_games()` need a score field. A daily update was discussed: either a Claude scheduled task (needs a paid plan in the session) or a GitHub Actions cron job that pulls scores from MaxPreps and pushes. MaxPreps rarely has real per-game box scores, so player stats would stay season averages for most schools. Automated scraping may break MaxPreps' terms and may get blocked; tell the owner this.
- Supabase: basketball uses `bb_`-prefixed collections. Row-level security for them is unverified.
- Home/away follows MaxPreps entry order and is unverified.
- Bishop's and 38 other schools have no stats on MaxPreps.

## Getting MaxPreps data (if needed again)
Use Claude in Chrome. `javascript_tool` output is cut off at about 1 KB and blocks query-string URLs, so write results into the page DOM and read them with `get_page_text`. Verify hand-transcribed data with a checksum computed in the browser and in Python.
