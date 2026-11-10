import asyncio
from common import *
ST='/home/claude/mk/clips/A_still/'
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200)
        await p.evaluate("async()=>{for(let i=0;i<3;i++){const b=[...document.querySelectorAll('button')].find(e=>/show 10 more/i.test(e.innerText));if(b){b.click();await new Promise(r=>setTimeout(r,250))}}}");await p.wait_for_timeout(400)
        await p.evaluate("()=>{const e=[...document.querySelectorAll('.row[data-act=player]')].find(e=>e.innerText.trim().startsWith('6'));window.scrollTo(0,e.getBoundingClientRect().top+scrollY-250)}");await p.wait_for_timeout(300)
        await p.screenshot(path=ST+'fb_rows6.jpg',type='jpeg',quality=94)
        print('rows',await p.evaluate("()=>[5,6,7,8,11].map(r=>{const e=[...document.querySelectorAll('.row[data-act=player]')].find(e=>e.innerText.trim().startsWith(String(r)));const b=e.getBoundingClientRect();return [r,Math.round(b.top),Math.round(b.height)]})"))
        await p.close()
        p=await newpage(b,APPB)
        await p.evaluate("()=>{location.hash='#groups';UI.ltab='mock';render()}");await p.wait_for_timeout(800)
        await p.evaluate("()=>{const b=document.querySelector('[data-act=mkSolo]');b&&b.click()}");await p.wait_for_timeout(1500)
        for y in (300,700,1100):
            await p.evaluate(f"()=>window.scrollTo(0,{y})");await p.wait_for_timeout(300);await p.screenshot(path=f'shots/mock_{y}.jpg',type='jpeg',quality=80)
        print(await p.evaluate("()=>document.body.innerText.slice(600,1800).replace(/\\n/g,' | ')"))
        await b.close()
asyncio.run(main())
