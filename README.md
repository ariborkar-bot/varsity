# Varsity

San Diego high school fantasy football. Player stats come from public box scores for every San Diego Section team; friends play in snake-draft or budget leagues.

- Live app: https://ariborkar-bot.github.io/varsity/ (install it from the browser's "Add to Home Screen")
- Accounts and leagues: Supabase project `varsity`
- Everything runs from `index.html`; `sw.js` and `manifest.webmanifest` make it installable.

## Basketball

`basketball.html` is generated from `index.html` by `tools/make_basketball.py` (swaps in basketball positions, scoring, lineups, the Simulate court, and placeholder players and games). Run `python3 tools/make_basketball.py` after changing `index.html` and commit both files. The Football / Basketball switch in the header links the two pages. Basketball keeps its own leagues, lineups and picks in `bb_`-prefixed collections; accounts (`profiles`) are shared.
