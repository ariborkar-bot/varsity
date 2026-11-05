"""Build the two single-file demo previews (football and basketball) that get sent to the owner after every change.

    python3 tools/preview/make_previews.py [out_dir]      (default out_dir: /tmp/varsity-previews)

Writes out_dir/varsity-football.html and out_dir/varsity-basketball.html. They are self-contained (fonts, logo, logos.js and
games.js inlined), run in demo mode with no Supabase, signed in as a sample player, and the Football/Basketball switch links to
each other by file name. Run tools/make_basketball.py first (this script does it for you) so basketball.html is current."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/varsity-previews'
os.makedirs(OUT, exist_ok=True)
subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'make_basketball.py')], stdout=subprocess.DEVNULL)

A = "if(window.supabase&&window.supabase.createClient){"
B = "JSON.parse(localStorage.getItem('gsd-demo-profile')||'null')"
C = "\nroute();\n"


def build(src, dest, profile, start):
    tmp = os.path.join(OUT, '_base.html')
    subprocess.check_call([sys.executable, '-I', os.path.join(HERE, 'build_preview.py'), ROOT, tmp, src], stdout=subprocess.DEVNULL)
    h = open(tmp, encoding='utf-8').read()
    for x in (A, B, C):
        assert h.count(x) == 1, x
    h = h.replace(A, "if(false){", 1).replace(B, profile, 1).replace(C, "\nif(!location.hash)location.hash='%s';\nroute();\n" % start, 1)
    h = h.replace('</head>', '<style>#tab-admin{display:none!important}</style></head>', 1)
    h = h.replace('href="basketball.html"', 'href="varsity-basketball.html"').replace('href="index.html"', 'href="varsity-football.html"')
    open(os.path.join(OUT, dest), 'w', encoding='utf-8').write(h)
    os.remove(tmp)


build('index.html', 'varsity-football.html',
      '({role:"player",name:"Zed Hornby",school:"Bishop\'s",posLabel:"Wide receiver",pos:"WR",consentAt:Date.now(),v:1})', '#me')
build('basketball.html', 'varsity-basketball.html',
      '({role:"player",name:"Zed Hornby",school:"Bishop\'s",posLabel:"Shooting guard",pos:"SG",consentAt:Date.now(),v:1})', '#league')
print('wrote', os.path.join(OUT, 'varsity-football.html'), 'and', os.path.join(OUT, 'varsity-basketball.html'))
