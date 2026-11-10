import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b,APPB)
        await p.evaluate("()=>{location.hash='#minigames';UI.mtab='sim';render()}");await p.wait_for_timeout(1000)
        await p.evaluate("()=>window.scrollTo(0,500)");await p.wait_for_timeout(300);await shot(p,'sim1')
        print(await p.evaluate("()=>[...document.querySelectorAll('button,[data-act]')].filter(e=>e.offsetParent).map(e=>(e.dataset.act||e.tagName)+':'+e.innerText.slice(0,25).replace(/\\n/g,' ')).slice(10,50).join(' || ')"))
        await b.close()
asyncio.run(main())
