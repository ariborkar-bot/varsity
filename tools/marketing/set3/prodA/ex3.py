import asyncio
from common import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200)
        btn=await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='Filters');return b?b.dataset.act:null}");print('filters act',btn)
        await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='Filters');b.click()}");await p.wait_for_timeout(500)
        await p.evaluate("()=>window.scrollTo(0,document.getElementById('q').getBoundingClientRect().top+scrollY-140)");await shot(p,'filters')
        print(await p.evaluate("()=>[...document.querySelectorAll('input,select')].filter(e=>e.offsetParent).map(e=>e.tagName+'#'+e.id+'|'+(e.placeholder||'')+'|'+(e.dataset.act||'')+'|'+Math.round(e.getBoundingClientRect().top)).join('\\n')"))
        await p.evaluate("()=>{UI.school='Hoover';render()}");await p.wait_for_timeout(500)
        print(await p.evaluate("()=>[...document.querySelectorAll('[data-act=player]')].slice(0,5).map(e=>e.className+':'+e.innerText.replace(/\\n/g,' ').slice(0,70))"))
        await p.evaluate("()=>window.scrollTo(0,document.getElementById('q').getBoundingClientRect().top+scrollY-140)");await shot(p,'school_hoover')
        await b.close()
asyncio.run(main())
