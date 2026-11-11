"""School colours for the player cards (v434). Reads logos.js, takes the two most common saturated colours of each logo
(ignoring white, black and grey), and prints the `SCH_COL` line for index.html: {school: [main, second]}.
Usage: python3 tools/cards/school_colors.py   (paste the output over the `const SCH_COL=` line, then fix any school by hand)."""
import re, base64, io, json, os, colorsys
from PIL import Image
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
s = open(os.path.join(ROOT, 'logos.js')).read()
out = {}
for name, b in re.findall(r'"([^"]+)":"data:image/webp;base64,([^"]+)"', s):
    im = Image.open(io.BytesIO(base64.b64decode(b))).convert('RGBA').resize((64, 64))
    bk = {}
    for r, g, bl, a in im.getdata():
        mx, mn = max(r, g, bl), min(r, g, bl)
        if a < 200 or mn > 215 or mx < 45 or mx - mn < 50: continue
        k = (r >> 5, g >> 5, bl >> 5); v = bk.setdefault(k, [0, 0, 0, 0]); v[0] += r; v[1] += g; v[2] += bl; v[3] += 1
    L = [tuple(round(v[i] / v[3]) for i in range(3)) for v in sorted(bk.values(), key=lambda v: -v[3]) if v[3] >= 12]
    if not L: continue                      # black / white / grey logo: the card keeps its rarity colour
    c1 = L[0]
    c2 = next((c for c in L[1:] if sum(abs(c[i] - c1[i]) for i in range(3)) > 150), None)
    def fix(c):                             # keep the main colour dark enough for white text
        h, l, sat = colorsys.rgb_to_hls(*[x / 255 for x in c]); l = min(l, .42); sat = max(sat, .45)
        return '#%02x%02x%02x' % tuple(round(x * 255) for x in colorsys.hls_to_rgb(h, l, sat))
    out[name] = [fix(c1), ('#%02x%02x%02x' % c2) if c2 else '#ffffff']
print('const SCH_COL=' + json.dumps(out, separators=(',', ':')) + ';')
