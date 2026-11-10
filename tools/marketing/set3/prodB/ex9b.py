import asyncio,sys
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await pageB(b)
        for t in ['sim','rc']:
            await go(p,f"location.hash='#minigames';UI.mtab='{t}';render()",800)
            print(t,await p.evaluate("()=>[...document.querySelectorAll('main [data-act]')].map(e=>e.dataset.act+':'+(e.dataset.v||'')+':'+e.innerText.slice(0,18).replace(/\\n/g,' ')).slice(5,30).join(' | ')"))
        await b.close()
asyncio.run(main())
