"""python3 shots.py <tag> <fb.html> <bb.html> <nu.html>: deterministic screenshots of every reachable tab/sub-tab state."""
import sys,os,json,re
from playwright.sync_api import sync_playwright
tag=sys.argv[1];files={'fb':sys.argv[2],'bb':sys.argv[3]};nu=sys.argv[4]
OUT=f'/home/claude/cmp/{tag}';os.makedirs(OUT,exist_ok=True)
INIT="""(()=>{const F=Date.UTC(2026,10,9,18,0,0);const RD=Date;let off=0;
class D extends RD{constructor(...a){if(a.length)super(...a);else super(F+off)}static now(){return F+off}}
D.UTC=RD.UTC;D.parse=RD.parse;window.Date=D;performance.now=()=>off;
let s=12345;Math.random=()=>{s=(s*1103515245+12345)&0x7fffffff;return s/0x7fffffff};
window.__tick=ms=>{off+=ms};history.back=()=>{window.dispatchEvent(new PopStateEvent('popstate',{state:null}))};history.go=()=>{};
const st=document.createElement('style');st.textContent='*,*::before,*::after{animation:none!important;transition:none!important;caret-color:transparent!important}';
document.addEventListener('DOMContentLoaded',()=>document.head.appendChild(st));})();"""
HASH=['me','league','groups','minigames','games','shop','locker','account','simulate','desk','privacy']
TABRE=re.compile(r'tab|Tab|seg|view|mode|sort|filt|pos$|Pos$|side|sub|lb|week|^player$|^team$|Open$|^info$|^more$|^consent$|ntSettings|lgPanel|fcView|cupV|scope|^rank$|^school$|^gschool$|^member$|^group$',re.I)
log={}
def clean(pg):
    pg.evaluate("()=>{document.querySelectorAll('[data-c=\"no\"]').forEach(b=>b.click());document.querySelectorAll('.toast,.tst,#toast').forEach(e=>{e.hidden=true;e.textContent=''})}")
def snap(pg,name,errs):
    clean(pg);pg.wait_for_timeout(250)
    h=pg.evaluate("Math.min(document.documentElement.scrollHeight,5000)")
    pg.set_viewport_size({'width':400,'height':h});pg.wait_for_timeout(120)
    pg.screenshot(path=f'{OUT}/{name}.png',full_page=False)
    pg.set_viewport_size({'width':400,'height':860})
    log[name]=errs[:]
with sync_playwright() as p:
    b=p.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox','--font-render-hinting=none','--disable-lcd-text'])
    for sp,f in files.items():
        for H in HASH:
            errs=[]
            def fresh():
                c=b.new_context(viewport={'width':400,'height':860},device_scale_factor=1);c.add_init_script(INIT)
                c.add_init_script("window.open=()=>null;document.addEventListener('click',e=>{const a=e.target.closest&&e.target.closest('a[href]');if(a&&!a.getAttribute('href').startsWith('#'))e.preventDefault()},true)")
                q=c.new_page();q.set_default_timeout(10000);q.on('pageerror',lambda e:errs.append(str(e)[:200]))
                q.goto('file://'+os.path.abspath(f)+'#'+H);q.wait_for_timeout(2500);clean(q);return c,q
            ctx,pg=fresh()
            pg.evaluate("()=>{try{location.hash='#%s';render()}catch(e){}}"%H);pg.wait_for_timeout(400)
            snap(pg,f'{sp}_{H}_0',errs)
            acts=pg.evaluate("""()=>{const seen=new Set(),o=[];document.querySelectorAll('main [data-act],#app [data-act],body [data-act]').forEach(e=>{const a=e.dataset.act,v=e.dataset.v||'';const k=a+'|'+v;if(seen.has(k))return;seen.add(k);o.push([a,v])});return o}""")
            acts=[x for x in acts if TABRE.search(x[0])]
            seenA={};acts=[x for x in acts if seenA.setdefault(x[0],0)<3 and not seenA.__setitem__(x[0],seenA[x[0]]+1)][:30]
            for i,(a,v) in enumerate(acts):
              try:
                  ok=pg.evaluate("([a,v])=>{const e=[...document.querySelectorAll('[data-act]')].find(x=>x.dataset.act===a&&(x.dataset.v||'')===v);if(!e)return false;e.click();return true}",[a,v])
                  pg.wait_for_timeout(250)
                  if ok:snap(pg,f'{sp}_{H}_{i+1:02d}_{re.sub(r"[^a-zA-Z0-9]","",a+v)[:20]}',errs)
                  pg.evaluate("()=>{document.querySelectorAll('[data-act=close],[data-sh=close],.sheet-x,[aria-label=Close]').forEach(e=>{try{e.click()}catch(_){}});document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))}");pg.wait_for_timeout(150)
              except Exception as ex:
                errs.append('NAV '+str(ex)[:30])
                try:ctx.close()
                except Exception:pass
                ctx,pg=fresh()
            ctx.close()
    # new-user flow
    ctx=b.new_context(viewport={'width':400,'height':860});ctx.add_init_script(INIT);pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.goto('file://'+os.path.abspath(nu));pg.wait_for_timeout(2500);snap(pg,'nu_1_signin',errs)
    pg.click('[data-au="up"]');pg.wait_for_timeout(300);snap(pg,'nu_2_create',errs)
    pg.fill('#au-email','demo@varsity.test');pg.fill('#au-pass','demo1234');pg.click('#au-age');pg.click('#au-form button[type=submit]');pg.wait_for_timeout(2500);snap(pg,'nu_3_role',errs)
    pg.click('[data-nm-role="player"]');pg.wait_for_timeout(300);pg.click('[data-nm-sport="fb"]');pg.wait_for_timeout(300);snap(pg,'nu_4_player',errs)
    pg.click('[data-nm-role="fan"]');pg.wait_for_timeout(300);snap(pg,'nu_5_fan',errs)
    pg.fill('#nm-name','Alex Rivera');pg.evaluate("()=>{const s=document.getElementById('nm-school');s.value=[...s.options].find(o=>o.value).value;s.dispatchEvent(new Event('change',{bubbles:true}))}")
    pg.click('#nm-form button[type=submit]');pg.wait_for_timeout(2500);pg.evaluate("()=>{}");pg.screenshot(path=f'{OUT}/nu_6_welcome.png');log['nu_6_welcome']=errs[:]
    b.close()
json.dump(log,open(f'{OUT}/log.json','w'),indent=0)
print(tag,len(log),'shots; states with errors:',sum(1 for v in log.values() if v))
