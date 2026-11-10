import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200)
        k=await p.evaluate("()=>{const q=players().find(x=>x.name==='Hezekiah Manuel');openPlayer(q.key);return q.key}");await p.wait_for_timeout(900);await shot(p,'sheet_hm')
        print(await p.evaluate("()=>{const s=document.querySelector('.sheet, #sheet, [role=dialog]:not([hidden])');return s?s.className+' '+s.innerText.slice(0,500):'none'}"))
        await p.mouse.wheel(0,600);await p.wait_for_timeout(400);await shot(p,'sheet_hm2')
        await b.close()
asyncio.run(main())
