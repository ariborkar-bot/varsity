import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b,APPB)
        await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200);await shot(p,'bb_stats0');await zedcheck(p,'bbstats')
        await p.evaluate("()=>window.scrollTo(0,1150)");await p.wait_for_timeout(200);await shot(p,'bb_stats1')
        await p.evaluate("()=>{location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(800)
        await p.evaluate("()=>{const a=[...document.querySelectorAll('article.gm')].find(a=>a.innerText.includes('Westview'));window.scrollTo(0,a.getBoundingClientRect().top+scrollY-300)}");await p.wait_for_timeout(300);await shot(p,'bb_pick')
        await p.evaluate("()=>{location.hash='#groups';UI.ltab='mock';render()}");await p.wait_for_timeout(800);await shot(p,'bb_mock0')
        print(await p.evaluate("()=>[...document.querySelectorAll('[data-act]')].filter(e=>e.offsetParent&&/mk/i.test(e.dataset.act)).map(e=>e.dataset.act+':'+(e.dataset.v||'')+':'+e.innerText.slice(0,25).replace(/\\n/g,' ')).join(' || ')"))
        await b.close()
asyncio.run(main())
