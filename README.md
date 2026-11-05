# Varsity

San Diego high school fantasy football. Player stats come from public box scores for every San Diego Section team; friends play in snake-draft or budget leagues.

- Live app: https://ariborkar-bot.github.io/varsity/ (install it from the browser's "Add to Home Screen")
- Accounts and leagues: Supabase project `varsity`
- Everything runs from `index.html`; `sw.js` and `manifest.webmanifest` make it installable.

## Basketball

`basketball.html` is generated from `index.html` by `tools/make_basketball.py` (swaps in basketball positions, scoring, lineups, the Simulate court, and placeholder players and games). Run `python3 tools/make_basketball.py` after changing `index.html` and commit both files. The Football / Basketball switch in the header links the two pages. Basketball keeps its own leagues, lineups and picks in `bb_`-prefixed collections; accounts (`profiles`) are shared.

### Basketball data (2025-26)

`tools/data/bb_2526_players.txt` holds the real San Diego Section boys basketball rosters and season stats, copied from each
school's MaxPreps team pages (roster tab for name, grade and position; Player Stats tab for games played and per-game points,
rebounds, assists, steals, blocks, turnovers and 3-pointers made). 127 schools, 88 of them with stats entered.

- MaxPreps has season averages, not box scores, for almost every team, so each finished week carries the per-game average
  (the number of weeks follows games played).
- Many schools list positions as G / F / W or nothing. `assign_positions()` in `make_basketball.py` maps those to PG/SG/SF/PF/C
  (guards by assists, forwards by rebounds, blanks by their own stats, or evenly when there are none).
- Some schools did not enter every stat, so those columns read 0.
- Bishop's and 38 other schools have rosters but no stats entered.
- `tools/data/bb_2627_games.txt` is the real 2026-27 schedule from MaxPreps (about 1,450 games, no scores yet). Weeks 1-4 are
  the pseudo-weeks that carry last season's averages; the first real game week is week 5 (week of Nov 9, 2026).
- Before 20 games have final scores, odds and spreads come from each team's 2025-26 scoring (`window.BB_PRIOR`).
- The playoff bracket is a projection from the same ratings until the real brackets are posted.
- Scores are not read yet: once games are played, the games file and `load_games()` need a score field, then re-run the generator.
