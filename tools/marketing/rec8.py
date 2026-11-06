import asyncio,sys,math,json,os,shutil
sys.path.insert(0,'/home/claude/mk')
from cap import APP,LEAGUE
from playwright.async_api import async_playwright
OUT='/home/claude/mk/clips/'
W,H,DPR=392,697,1080/392
SAFE="""()=>{document.querySelectorAll('style').forEach(s=>{const t=s.textContent;if(t.includes('safe-area-inset'))s.textContent=t.replace(/env\\(safe-area-inset-top(?:,\\s*[^)]*)?\\)/g,'50px').replace(/env\\(safe-area-inset-bottom(?:,\\s*[^)]*)?\\)/g,'26px')})}"""
TAPS={}
async def newpage(b):
    ctx=await b.new_context(viewport={'width':W,'height':H},device_scale_factor=DPR,is_mobile=True,has_touch=True)
    await ctx.add_init_script(path='/home/claude/mk/vt.js')
    p=await ctx.new_page();p.on('pageerror',lambda e:print('ERR',e))
    await p.goto(APP);await p.wait_for_timeout(2200)
    await p.evaluate(SAFE)
    await p.evaluate("()=>{try{const pr=S.profiles[ME.uid];if(pr)pr.name='Jordan Reyes'}catch(e){};render()}");await p.wait_for_timeout(300)
    return p
async def frames(p,name,n,each):
    d=OUT+name;shutil.rmtree(d,ignore_errors=True);os.makedirs(d)
    for i in range(n):
        await each(i)
        await p.evaluate("()=>__step(1000/30)")
        await p.screenshot(path=f'{d}/f{i:04d}.jpg',type='jpeg',quality=92)
    print(name,n)
async def tap(p,name,i,js):
    r=await p.evaluate("()=>{const e=("+js+");if(!e)return null;const b=e.getBoundingClientRect();e.click();return [b.left+b.width/2,b.top+b.height/2]}")
    TAPS.setdefault(name,[]).append([i]+(r or [0,0]));print(name,i,r)
HOLD="()=>{const e=%s;if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-%d)}"
async def main(which):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        if 'league' in which:
            p=await newpage(b)
            await p.evaluate("()=>{S.settings.week=11;window.__seed=39}");await p.evaluate(LEAGUE)
            await p.evaluate("()=>{location.hash='#groups';render()}");await p.wait_for_timeout(1200)
            pos=await p.evaluate("()=>['.lg-hero','.lg-vs','.lg-tbl'].map(s=>{const e=document.querySelector(s);return Math.round(e.getBoundingClientRect().top+scrollY)})")
            print('league positions',pos);json.dump(pos,open(OUT+'league8_pos.json','w'))
            await p.evaluate("()=>{window.scrollTo(0,0);__vt.start()}")
            end=pos[2]-150;STEP=7;n=int(end/STEP)+20
            async def sc(i): await p.evaluate(f"()=>window.scrollTo(0,{min(end,i*STEP)})")
            await frames(p,'league8',n,sc);await p.close()
        if 'picks' in which:
            p=await newpage(b)
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';UI.bf.dv='Division II';location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(1000)
            F="[...document.querySelectorAll('.bt-g')].find(a=>a.innerText.includes('Mater Dei'))"
            await p.evaluate(HOLD%(F,200));await p.evaluate("()=>__vt.start()")
            async def pk(i):
                if i==20: await tap(p,'picks8',i,F+".querySelectorAll('[data-act=pkSide]')[0]")
                if i==46: await tap(p,'picks8',i,F+".querySelector('[data-act=pkStake][data-v=\"50\"]')")
                if i==74: await tap(p,'picks8',i,"document.querySelector('[data-act=pkAll]')")
                await p.evaluate(HOLD%(F,200))
            await frames(p,'picks8',130,pk);await p.close()
        if 'props' in which:
            p=await newpage(b)
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';UI.bf.sc='Hoover';location.hash='#minigames';UI.mtab='props';render()}");await p.wait_for_timeout(1000)
            F="[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes('Hezekiah Manuel'))"
            await p.evaluate(HOLD%(F,200));await p.evaluate("()=>__vt.start()")
            async def pp(i):
                if i==20: await tap(p,'props8',i,F+".querySelector('[data-act=ppSide]')")
                if i==46: await tap(p,'props8',i,F+".querySelector('[data-act=ppStake][data-v=\"25\"]')")
                if i==74: await tap(p,'props8',i,"document.querySelector('[data-act=ppAll]')")
                await p.evaluate(HOLD%(F,200))
            await frames(p,'props8',130,pp);await p.close()
        await b.close()
    old={}
    try: old=json.load(open(OUT+'taps8.json'))
    except: pass
    old.update(TAPS);json.dump(old,open(OUT+'taps8.json','w'))
asyncio.run(main(sys.argv[1:]))
