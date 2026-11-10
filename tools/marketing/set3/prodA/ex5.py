import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(1000)
        info=await p.evaluate("""()=>[...document.querySelectorAll('article.gm')].slice(0,12).map(a=>Math.round(a.getBoundingClientRect().top+scrollY)+':'+a.innerText.replace(/\\n/g,' | ').slice(0,120))""");print('\n'.join(info))
        await p.evaluate("()=>{const a=[...document.querySelectorAll('article.gm')].find(a=>a.innerText.includes('Santa Fe Christian'));window.scrollTo(0,a.getBoundingClientRect().top+scrollY-300)}");await p.wait_for_timeout(300);await shot(p,'pick0');await zedcheck(p,'picks')
        print(await p.evaluate("()=>{const a=[...document.querySelectorAll('article.gm')].find(a=>a.innerText.includes('Santa Fe Christian'));return [...a.querySelectorAll('[data-act]')].map(e=>e.dataset.act+':'+(e.dataset.s||'')+':'+e.innerText.slice(0,30).replace(/\\n/g,' ')).join(' || ')}"))
        await b.close()
asyncio.run(main())
