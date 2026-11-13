#!/usr/bin/env python3
"""Sync one section's data from an adapter into data/sections/<section>.json.

    python3 tools/sections/sync.py southern --adapter mock --out /tmp/sections     test run with fake data
    python3 tools/sections/sync.py southern --adapter feed                         the real run (needs FeedAdapter written)
    python3 tools/sections/sync.py southern --coverage                             coverage report only

Rules:
  - A section whose status in index.html is 'off' is refused unless --force (so a stray run cannot fill a hidden section).
  - The mock adapter may only write outside data/sections/, so fake data can never be committed as real data.
  - Re-running upserts by id. Stat lines that changed are CORRECTIONS (v goes up, listed in the report).
  - --dry-run shows the report and writes nothing.
Exit 0 on success, 2 on refusal or bad input.
"""
import argparse, datetime, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sections_lib as L


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('section')
    ap.add_argument('--adapter', default='feed', choices=sorted(L.ADAPTERS))
    ap.add_argument('--sport', default='both', choices=['fb', 'bb', 'both'])
    ap.add_argument('--out', default=L.DATA_DIR)
    ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--coverage', action='store_true', help='report only, no fetch')
    ap.add_argument('--mock-schools', type=int, default=12)
    ap.add_argument('--mock-correct', type=int, default=0, help='mock only: change N stat lines to test corrections')
    a = ap.parse_args()

    reg = L.registry()
    if a.section not in reg:
        print('unknown section %r; known: %s' % (a.section, ', '.join(reg))); return 2
    path = os.path.join(os.path.abspath(a.out), a.section + '.json')
    old = L.load(path)

    if a.coverage:
        if not old:
            print('no data file at', path); return 2
        data = old
    else:
        if reg[a.section]['status'] == 'off' and not a.force:
            print('section %r is off in index.html; set it to loading/beta first or pass --force' % a.section); return 2
        if a.adapter == 'mock' and os.path.abspath(a.out).startswith(os.path.abspath(L.DATA_DIR)):
            print('refusing: the mock adapter may not write into data/sections (use --out elsewhere)'); return 2
        sports = ['fb', 'bb'] if a.sport == 'both' else [a.sport]
        ad = L.ADAPTERS[a.adapter]() if a.adapter != 'mock' else L.MockAdapter(a.mock_schools, a.mock_correct)
        new = ad.fetch(a.section, sports)
        data, ch = L.upsert(old, new)
        data['synced'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        print('%s: %d schools, %d players, %d games, %d stat lines' % (a.section, len(data['schools']), len(data['players']), len(data['games']), len(data['lines'])))
        print('  new games %d, new stat lines %d, score changes %d, CORRECTED stat lines %d' % (ch['added_games'], ch['added_lines'], len(ch['score_changed']), len(ch['corrected'])))
        for c in ch['corrected'][:10]:
            print('   corrected: %s / %s -> v%d' % (c['game'], c['player'], c['v']))
        if not a.dry_run:
            L.save(path, data)
            print('  wrote', path)

    rows, share, ready = L.coverage(data)
    miss = [r for r in rows if not (r['roster'] and r['games'] and r['stats'])]
    print('coverage: %d of %d school-sports complete (%.0f%%); bar %.0f%% -> %s' % (len(rows) - len(miss), len(rows), share * 100, L.BAR * 100, 'READY for beta' if ready else 'not ready'))
    for r in miss[:15]:
        print('   gap: %s %s  roster=%s games=%s stats=%s' % (r['school'], r['sport'], r['roster'], r['games'], r['stats']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
