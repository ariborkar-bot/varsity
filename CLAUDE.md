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

## Daily score update
- A Claude scheduled task ("Varsity daily scores", 5:41 am Pacific every day) is ON (re-created Nov 5 2026 at the owner's request). it finds final scores in news scoreboards (High School On SI, local papers) and adds them with `tools/add_scores.py`. It does not scrape MaxPreps: from the cloud MaxPreps pages come back about a year stale, and automated scraping breaks their terms.
- `tools/add_scores.py` (read its docstring): input lines `fb|YYYY-MM-DD|home|hs|away|as|source`; fills scores for scheduled games, adds unscheduled games that involve a San Diego Section school, reports CONFLICT/SKIPPED and never guesses. `--pending` lists played games with no score, `--names fb|bb` lists team names, `--dry-run` previews. Other spellings go in `tools/data/team_aliases.txt`.
- Football scores live in `games.js`; basketball scores are a trailing `64-58` (home first) on a line of `tools/data/bb_2627_games.txt`, read by `load_games()` and passed through to `basketball.html`.
- Player stats are not updated automatically (news sources rarely publish full box scores). The owner is asking MaxPreps/PlayOn for a data license and ScoreStream for an API quote; the owner wants to expand the app to the whole U.S. The app is free, with no purchases and no gambling.

## Phone behaviour (Nov 5 mobile audit, owner approved)
- Back button: tabs use `history.pushState`, so the phone's Back goes to the previous tab. Opening a player card or notifications calls `sheetPush()`; Back (popstate) closes the sheet. User closes go through `sheetClose()`.
- Phones (< 760 px): the big banner scrolls away and `#mastMini` (logo, week, settings via `#gear2`) slides in at the top.
- Login server: the real site has `NEEDS_SERVER=true`. If the Supabase library cannot load (jsDelivr, then unpkg as backup), `ME.mode='offline'`: an Offline banner with Try again, `act()` refuses to save, sign-in says it can't connect. Previews set `NEEDS_SERVER=false` and run in demo mode. Hosting supabase.min.js in the repo was approved but not done: package downloads were blocked in that session.
- Pick 'em draws one week of games at a time (`pkWeeksHTML`, Show more adds a week): a basketball season is ~1,400 games.
- Over/Under player names open the player card. Join forms start with no position and require one for players.
- Basketball preseason: `PRE()` still counts everyone as one 0.0 game for ranking, but game counts show 0; Simulate says when it opens instead of "Not enough players".
- Declined for now (do not do without asking): hiding "Admin sign in", intro shown once ever, bigger tap targets, 12 px minimum text, shorter Minigames tab labels, Simulate leaderboard wording, "VARSITY 05" yard numbers, Stats list loading more at once.
- Football `games.js` is missing many weeks 1-11 results (most teams show 6-9 games, not 10). Cloud search could only find 2 more; the rest needs SI or MaxPreps pages read through the owner's Chrome.

## Open items and ideas
- Database rules: only `tools/sql/mocks_policies.sql` is in the repo. Its "update mock" policy lets any signed-in user change any mock draft. (`merge_doc` runs as the caller, so table policies apply.)
- Supabase (Nov 5 2026, migration `league_security_and_account_delete`, copy in tools/sql/): only a league's owner/members/admins can update it; joining by code goes through the `join_league` RPC; `bb_` collections have the same rules as football; `delete_my_account()` RPC backs Settings → Delete my account. Multiplayer mock drafts still need tools/sql/mocks_policies.sql.
- Privacy policy page is `#privacy` (viewPrivacy). It has a `[contact email]` placeholder the owner must fill in.
- Navigation: 5 bottom tabs (Simulate lives in Minigames). Minigames = Predict (Game winners / Player over-under), 5 Card Draw, Mock Draft, Simulate. Page descriptions sit behind an "i" button (infoIcons). Scoring rules live in each league's League settings. Player of the Week podium + POTW tag, Game of the Week, player Share card (playerCardBlob), token "+" opens Get tokens (watch a sponsor). The owner asked for a pay-for-tokens option; it was NOT built (free/no-purchases promise, minors, Apple in-app purchase rules) pending the owner's confirmation.
- Home/away follows MaxPreps entry order and is unverified.
- Bishop's and 38 other schools have no stats on MaxPreps.

## Getting MaxPreps data (if needed again)
Use Claude in Chrome. `javascript_tool` output is cut off at about 1 KB and blocks query-string URLs, so write results into the page DOM and read them with `get_page_text`. Verify hand-transcribed data with a checksum computed in the browser and in Python.
