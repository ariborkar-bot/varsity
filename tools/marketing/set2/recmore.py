import asyncio,sys,json
sys.path.insert(0,'/home/claude/mk')
from rec import *
from cap import LEAGUE
HOLD="()=>{const e=%s;if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-%d)}"
async def main(which):
    async with async_playwright() as pw:
        b=await browser(pw)
        if 'search' in which:
            p=await newpage(b)
            await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(900)
            await p.evaluate("()=>{const i=document.querySelector('input[type=search],input[placeholder*=Search]');window.scrollTo(0,i.getBoundingClientRect().top+scrollY-120);__vt.start()}")
            word='Carlsbad'
            async def ty(i):
                k=(i-15)//4
                if 15<=i<15+4*len(word) and (i-15)%4==0:
                    await p.evaluate("(v)=>{const i=document.querySelector('input[type=search],input[placeholder*=Search]');i.focus();i.value=v;i.dispatchEvent(new Event('input',{bubbles:true}))}",word[:k+1])
            await frames(p,'search',90,ty)
            await p.evaluate("()=>{location.hash='#team/Carlsbad';render()}");await p.wait_for_timeout(900)
            await p.evaluate("()=>window.scrollTo(0,0)")
            end=await p.evaluate("()=>document.body.scrollHeight-innerHeight")
            async def sc(i):await p.evaluate(f"()=>window.scrollTo(0,{min(end,max(0,(i-20)*9))})")
            await frames(p,'team',110,sc);await p.close()
        if 'card' in which:
            p=await newpage(b)
            await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(900);await p.evaluate("()=>__vt.start()")
            async def cd(i):
                if i==8:await p.evaluate("()=>openPlayer('mp29')")
                if i>40:await p.evaluate(f"()=>{{const d=document.querySelector('#drawer');const el=[d,...d.querySelectorAll('*')].find(e=>e.scrollHeight>e.clientHeight+40&&getComputedStyle(e).overflowY!='visible');if(el)el.scrollTop={min(700,(i-40)*8)}}}")
            await frames(p,'card',140,cd);await p.close()
        if 'league' in which:
            p=await newpage(b)
            await p.evaluate("()=>{S.settings.week=11;window.__seed=39}");await p.evaluate(LEAGUE)
            await p.evaluate("()=>{UI.ltab='leagues';location.hash='#groups';render()}");await p.wait_for_timeout(1200)
            pos=await p.evaluate("()=>['.lg-hero','.lg-vs','.lg-tbl'].map(s=>{const e=document.querySelector(s);return e?Math.round(e.getBoundingClientRect().top+scrollY):-1})")
            print('league pos',pos)
            await p.evaluate("()=>{window.scrollTo(0,0);__vt.start()}")
            end=max(pos)-120 if max(pos)>0 else 900
            async def sc(i):await p.evaluate(f"()=>window.scrollTo(0,{min(end,i*8)})")
            await frames(p,'league',int(end/8)+30,sc);await p.close()
        if 'cup' in which:
            p=await newpage(b)
            await p.evaluate("()=>{UI.ltab='cup';location.hash='#groups';render()}");await p.wait_for_timeout(900)
            await p.evaluate("()=>{const e=document.querySelector('.cup-hero,[class*=hero]');window.scrollTo(0,e?e.getBoundingClientRect().top+scrollY-110:200);__vt.start()}")
            async def cs(i):
                if i>60:await p.evaluate(f"()=>window.scrollBy(0,6)")
            await frames(p,'cup',150,cs);await p.close()
        if 'picks' in which:
            p=await newpage(b)
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(1000)
            F="document.querySelectorAll('.bt-g')[0]"
            ok=await p.evaluate("()=>!!"+F+"&&"+F+".innerText.slice(0,80)");print('pick game',ok)
            await p.evaluate(HOLD%(F,200));await p.evaluate("()=>__vt.start()")
            async def pk(i):
                if i==20:await p.evaluate("()=>{const b="+F+".querySelectorAll('[data-act=pkSide]')[0];b&&b.click()}")
                if i==46:await p.evaluate("()=>{const b="+F+".querySelector('[data-act=pkStake][data-v=\"50\"]');b&&b.click()}")
                if i==74:await p.evaluate("()=>{const b=document.querySelector('[data-act=pkAll]');b&&b.click()}")
                await p.evaluate(HOLD%(F,200))
            await frames(p,'picks',130,pk);await p.close()
        await b.close()
asyncio.run(main(sys.argv[1:]))
