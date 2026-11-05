"""Syntax-check every inline <script> in index.html and basketball.html (needs node). Prints OK or the failing script number."""
import os, re, subprocess, sys, json, tempfile
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
bad = 0
for f in ('index.html', 'basketball.html'):
    h = open(os.path.join(ROOT, f), encoding='utf-8').read()
    scripts = [m.group(1) for m in re.finditer(r'<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>', h, re.S)]
    js = "const a=%s;let bad=0;a.forEach((s,i)=>{try{new Function(s)}catch(e){bad++;console.log('ERR',i,e.message)}});console.log(%s+': '+a.length+' scripts, '+(bad?bad+' failed':'ok'))" % (json.dumps(scripts), json.dumps(f))
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as t:
        t.write(js)
    out = subprocess.run(['node', t.name], capture_output=True, text=True).stdout.strip()
    print(out)
    bad += 'failed' in out
sys.exit(1 if bad else 0)
