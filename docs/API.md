# Varsity API (read-only, v1)

Static JSON served by GitHub Pages next to the app. No keys, no server, CORS open.
Base: `https://ariborkar-bot.github.io/varsity/api/v1/`

| Path | What |
|---|---|
| `index.json` | every section that has data: counts per sport, `partial` flag, links |
| `sections/<section>/<sport>/teams.json` | teams: name, city, league, division, w/l/t, pf, pa |
| `sections/<section>/<sport>/standings.json` | teams grouped by league, best record first |
| `sections/<section>/<sport>/games.json` | every game (`hs`/`as` are null until final) |
| `sections/<section>/<sport>/weeks/<monday>.json` | one week of games, named by that week's Monday (`2026-11-09`) |
| `sections/<section>/<sport>/teams/<id>.json` | one team and its games (`mp:123` becomes `mp-123`) |
| `sections/<section>/<sport>/players.json` | every player with season totals, best fantasy points first (`columns` names each slot) |
| `sections/<section>/<sport>/weekly.json` | every player's line for every game: `[id, name, school, pos, [[date, opponent, [key index, value, ...]], ...]]`, `keys` names the stats |

`<section>` is `san-diego`, `southern`, `la-city`, `central`, `central-coast`, `sac-joaquin`, `oakland`, `san-francisco`, `north-coast` or `northern`. `<sport>` is `fb` or `bb`.
A game: `{id, date, time?, home, away, home_id?, away_id?, hs, as, forfeit?, state?}`.

Example: `fetch('https://ariborkar-bot.github.io/varsity/api/v1/index.json').then(r=>r.json())`

## How it is made
`tools/sections/build_api.py` turns `data/sections/*.json` (written by the collector, see `tools/sections/README.md`) into `api/v1/`. The "Collect section data" workflow runs it after each crawl and commits `api/`. It rebuilds everything each time and is deterministic, so unchanged data gives no diff.
Players come from each played game's box score (`tools/sections/players.py`). Positions are guessed from the stats; grades are not collected.
Data comes from the collector's source (MaxPreps pages today). Check that your permission covers redistributing it before sharing the API URL with others.
