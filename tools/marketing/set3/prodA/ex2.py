import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200)
        print(await p.evaluate("""()=>{const r=e=>e?Math.round(e.getBoundingClientRect().top+scrollY):null;
          const q=document.getElementById('q');const rows=[...document.querySelectorAll('[data-act=player]')].slice(0,14).map(e=>r(e)+':'+e.className+':'+e.innerText.replace(/\\n/g,' ').slice(0,60));
          return {q:r(q),h:document.body.scrollHeight,rows}}"""))
        # type a search
        await p.click('#q');await p.keyboard.type('hoover',delay=30);await p.wait_for_timeout(600)
        print(await p.evaluate("()=>[...document.querySelectorAll('[data-act=player]')].slice(0,6).map(e=>Math.round(e.getBoundingClientRect().top+scrollY)+':'+e.innerText.replace(/\\n/g,' ').slice(0,70))"))
        await p.evaluate("()=>window.scrollTo(0,document.getElementById('q').getBoundingClientRect().top+scrollY-140)");await p.wait_for_timeout(200);await shot(p,'search_hoover')
        await b.close()
asyncio.run(main())
