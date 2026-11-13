# Section data pipeline

One JSON file per section at `data/sections/<section>.json` (format in the docstring of `sections_lib.py`). The app does not read these yet (v479 adds that).

- `sync.py <section> --adapter mock|feed` fetches and upserts. `--coverage` reports only, `--dry-run` writes nothing.
- A section that is `off` in `index.html` (`SECTIONS`) is refused unless `--force`.
- The mock adapter makes clearly fake "MOCK ..." data and can only write outside `data/sections/` (for tests).
- Re-runs MERGE by id, so an incremental feed never drops older records. A stat line whose numbers change is a correction: its `v` goes up and it is listed in the report. Use that list to rescore those players.
- Coverage: a section is ready for `beta` when at least 90% of its school-sports have a roster (11 football, 5 basketball), games and stat lines.

## Real feed
`FeedAdapter` in `sections_lib.py` is a placeholder. When the data license is settled, write its `fetch()`: call the provider, map their ids to ours, return the normalized dict. Record the license terms here (what may be stored, shown, cached, and for how long).

## Opening a section
1. Feed written and licensed for that section. 2. `sync.py <section> --adapter feed` until coverage says READY. 3. Set its `status` to `beta` (admins only) in `SECTIONS`, watch one full Friday night of syncing. 4. Set `live`.

## MaxPreps collector (`maxpreps.py`, adapter `maxpreps`)
Reads the JSON that each MaxPreps team page embeds, for schedules and final scores (football and boys basketball, same format). Must run on a computer with normal internet: the cloud workspace's network refuses maxpreps.com.

    python3 tools/sections/test_maxpreps.py                                  offline tests (no network)
    python3 tools/sections/sync.py san-diego --adapter maxpreps --dry-run    look first, writes nothing
    python3 tools/sections/sync.py san-diego --adapter maxpreps              writes data/sections/san-diego.json

- `seeds/<section>.txt` has one team page per sport; the crawl follows opponents inside the section (`seeds/<section>.names.txt`, or for san-diego the app's school list plus `team_aliases.txt`).
- Polite by design: one request at a time, 2 s delay, honest User-Agent (set `VARSITY_CONTACT` to an email or URL), robots.txt respected, 12 h cache, stops at the first 403/429.
- Every game row is checked (ids, date, score vs W/L code, score found in MaxPreps' own summary text). If more than 20% of a page fails, it raises `FormatChanged` instead of writing wrong data. Home/away comes from field 11 (0 home, 1 away); neutral or unset games are listed with `ha: false`.
- Collected so far: schools and games with final scores. NOT yet: rosters and box-score stat lines (each game row has its box-score page url in `url`). Coverage will say "not ready" until they are.
- For a new section: add `seeds/<section>.txt` and `seeds/<section>.names.txt`. MaxPreps' school directory (`/ca/football/schools/`) shows only 200 teams and no section, so section membership still has to come from a names list.

## All of California (`sync.py california`, workflow "Collect section data")
`python3 tools/sections/sync.py california --adapter maxpreps` crawls every California opponent reachable from `seeds/california.txt`, reads each school's section and league from its team page (`teamContext.data.sectionName`), and writes one file per section (`data/sections/<section>.json`) plus `data/sections/index.json` (the list the app reads first). A section name the registry does not know is printed as NOT MATCHED, never dropped silently. Old/cached copies are refused (newest game must be within 150 days).
The GitHub Action `.github/workflows/collect.yml` runs this in GitHub's cloud: run it by hand first with "Dry run" on and a small `max_teams`; it probes MaxPreps first and stops with a clear message if the network is refused or stale. There is no schedule yet: add one after a good run.
NOTE: the repo is public, so committed section data is public too. Check that the MaxPreps permission covers publishing scores this way before turning the schedule on.
