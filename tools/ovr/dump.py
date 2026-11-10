"""Dump players() from the two previews into <dir>/fb.json and <dir>/bb.json for make_ovr.py.
usage: python3 tools/preview/make_previews.py /tmp/pv && python3 tools/ovr/dump.py /tmp/pv /tmp/ovr
fb.json rows also carry 'st' = this season's total of every box-score stat."""
import sys, json, os
from playwright.sync_api import sync_playwright
PV, OUT = sys.argv[1], sys.argv[2]; os.makedirs(OUT, exist_ok=True)
with sync_playwright() as p:
    b = p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--no-sandbox'])
    pg = b.new_page(); pg.goto('file://%s/varsity-football.html' % PV); pg.wait_for_timeout(3000)
    d = pg.evaluate("""()=>players().filter(p=>p.key!=='me'&&!p.sample).map(p=>{const g=(p.games||[]).filter(x=>x&&x.stat),st={};
      g.forEach(x=>{for(const k in x.stat)st[k]=(st[k]||0)+(+x.stat[k]||0)});
      return {key:p.key,name:p.name,school:p.school,pos:p.pos,sub:p.sub||p.pos,gr:p.gr,gp:g.length,tot:g.reduce((a,x)=>a+pts(x.stat),0),st,inj:!!injOf(p)}})""")
    json.dump(d, open(os.path.join(OUT, 'fb.json'), 'w'))
    pg = b.new_page(); pg.goto('file://%s/varsity-basketball.html' % PV); pg.wait_for_timeout(3000)
    d2 = pg.evaluate("""()=>players().filter(p=>p.key!=='me'&&!p.sample).map(p=>({key:p.key,name:p.name,school:p.school,pos:p.pos,gr:p.gr}))""")
    json.dump(d2, open(os.path.join(OUT, 'bb.json'), 'w')); print(len(d), len(d2)); b.close()
