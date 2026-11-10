import asyncio,os,sys,shutil
sys.path.insert(0,'/home/claude/mk')
os.environ['REAL']='1'
from rec import browser,newpage as _np,frames as _frames,APPF,APPB,W,H,DPR
from playwright.async_api import async_playwright
CL='/home/claude/mk/clips/'
ME_FAN="()=>{try{const u=ME.uid;S.profiles[u]={name:'you',role:'fan',v:2,joinedAt:Date.now()-864e5*30};}catch(e){};document.querySelectorAll('.toast,.tst').forEach(e=>e.remove());const c=document.getElementById('cfm');if(c)c.hidden=true;const st=document.createElement('style');st.textContent='#toast{display:none!important}';document.head.appendChild(st);render()}"
async def newpage(b,app=APPF):
    p=await _np(b,app=app,fake=False)
    await p.evaluate(ME_FAN);await p.wait_for_timeout(300)
    return p
async def frames(p,name,n,each=None):
    assert name.startswith('A_')
    await _frames(p,name,n,each)
async def shot(p,name):await p.screenshot(path=f'/home/claude/mk2/prodA/shots/{name}.jpg',type='jpeg',quality=80)
async def zedcheck(p,label=''):
    z=await p.evaluate("()=>document.body.innerText.includes('Zed Hornby')")
    if z:print('!!! Zed Hornby visible',label)
