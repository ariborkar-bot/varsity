"""Shared recorder for the Nov 8 video set: true 9:16 phone (392x697 css @ 1080x1920), iPhone safe areas, virtual clock, made-up names."""
import asyncio,os,shutil,json,sys
sys.path.insert(0,'/home/claude/mk')
from cap import FAKE
from playwright.async_api import async_playwright
APPF='file:///home/claude/mk/app/varsity-football.html';APPB='file:///home/claude/mk/app/varsity-basketball.html'
OUT='/home/claude/mk/clips/';W,H,DPR=392,697,1080/392
SAFE="""()=>{document.querySelectorAll('style').forEach(s=>{const t=s.textContent;if(t.includes('safe-area-inset'))s.textContent=t.replace(/env\\(safe-area-inset-top(?:,\\s*[^)]*)?\\)/g,'50px').replace(/env\\(safe-area-inset-bottom(?:,\\s*[^)]*)?\\)/g,'26px')})}"""
async def browser(pw):return await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
async def newpage(b,app=APPF,fake=None):
    if fake is None: fake=os.environ.get('REAL')!='1'
    ctx=await b.new_context(viewport={'width':W,'height':H},device_scale_factor=DPR,is_mobile=True,has_touch=True)
    await ctx.add_init_script(path='/home/claude/mk/vt.js')
    p=await ctx.new_page();p.on('pageerror',lambda e:print('ERR',e))
    await p.goto(app);await p.wait_for_timeout(2400);await p.evaluate(SAFE)
    if fake:await p.evaluate(FAKE)
    await p.evaluate("()=>{try{const pr=S.profiles[ME.uid];if(pr)pr.name='Jordan Reyes'}catch(e){};document.querySelectorAll('.toast,.tst').forEach(e=>e.remove());render()}");await p.wait_for_timeout(300)
    return p
async def frames(p,name,n,each=None,ms=1000/30):
    d=OUT+name;shutil.rmtree(d,ignore_errors=True);os.makedirs(d)
    for i in range(n):
        if each:await each(i)
        await p.evaluate(f"()=>__step({ms})")
        await p.screenshot(path=f'{d}/f{i:04d}.jpg',type='jpeg',quality=92)
    print(name,n,'frames',flush=True)
async def shot(p,name):await p.screenshot(path=f'/home/claude/mk/shots/{name}.jpg',type='jpeg',quality=80)
