import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200);await shot(p,'stats0');await zedcheck(p,'stats')
        print(await p.evaluate("()=>document.querySelector('main, #app, body').innerText.slice(0,900)"))
        print(await p.evaluate("()=>[...document.querySelectorAll('input')].map(i=>i.id+'|'+i.placeholder+'|'+i.type).join('\\n')"))
        await p.evaluate("()=>window.scrollTo(0,600)");await shot(p,'stats1')
        await b.close()
asyncio.run(main())
