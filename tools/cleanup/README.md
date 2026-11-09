# Dead-code cleanup (v365)
- `cssdead.py [--apply]`: CSS declarations redefined later by the exact same selector, rules whose class/id appears nowhere in the app or the build tools, unused @keyframes. Skips anything make_basketball.py / preview tools look for.
- `jsdead.js` (needs `npm i acorn acorn-walk`): top-level functions/constants in index.html that nothing references (writes a plan; removal was done by hand-checked script).
- `shots.py <tag> <fb.html> <bb.html> <newuser.html>` + `diff.py <a> <b>`: deterministic screenshots of ~130 screens (fixed clock, seeded random, no animations) and a pixel diff. Run on previews before and after a cleanup; the only expected difference is the welcome-pack team reel (random).
