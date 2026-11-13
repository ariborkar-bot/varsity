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
