import asyncio,sys
sys.path.insert(0,'/home/claude/mk')
from rec import *
ART="[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes('Zed Hornby'))"
HOLD="()=>{const e="+ART+";if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-%d)}"
async def main(which):
    async with async_playwright() as pw:
        b=await browser(pw)
        if 'lb' in which:
            p=await newpage(b,fake=False)
            await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1000)
            for _ in range(3):
                await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>/show 10 more/i.test(e.innerText));b&&b.click()}");await p.wait_for_timeout(400)
            print('list len',await p.evaluate("()=>document.body.scrollHeight"))
            await p.evaluate("()=>{window.scrollTo(0,560);__vt.start()}")
            # 560 -> 1500 over ~150 frames, pause on the podium, then down the list
            async def sc(i):
                y=560+min(i,60)*9 if i<90 else (1100 if i<120 else 1100+(i-120)*12)
                await p.evaluate(f"()=>window.scrollTo(0,{y})")
            await frames(p,'lb6',300,sc);await p.close()
        if 'props' in which:
            p=await newpage(b,fake=False)
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';location.hash='#minigames';UI.mtab='props';render()}");await p.wait_for_timeout(1000)
            await p.evaluate(HOLD%170);await p.evaluate("()=>__vt.start()")
            async def pp(i):
                if i==16:await p.evaluate("()=>{const a="+ART+";a.querySelector('[data-act=ppSel][data-id$=recYd]').click()}")
                if i==40:await p.evaluate("()=>{const a="+ART+";a.querySelector('[data-act=ppSide][data-s=o]').click()}")
                if i==41:print(await p.evaluate("()=>{const a="+ART+";return [...a.querySelectorAll('[data-act]')].map(e=>e.dataset.act+':'+(e.dataset.v||'')+':'+e.innerText.slice(0,20).replace(/\\n/g,' ')).join(' | ')}"))
                if i==62:await p.evaluate("()=>{const a="+ART+";const b=a.querySelector('[data-act=ppStake][data-v=\"25\"]');b&&b.click()}")
                if i==63:print(await p.evaluate("()=>{const a="+ART+";return [...document.querySelectorAll('[data-act]')].filter(e=>/lock/i.test(e.innerText+e.dataset.act)).map(e=>e.dataset.act+':'+e.innerText.slice(0,30).replace(/\\n/g,' ')).join(' | ')}"))
                if i==84:print('lock',await p.evaluate("()=>{const b=document.querySelector('[data-act=ppAll]');if(b){b.click();return b.innerText}return null}"))
                await p.evaluate(HOLD%170)
            await frames(p,'props6',150,pp);await p.close()
        await b.close()
asyncio.run(main(sys.argv[1:]))
