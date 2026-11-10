import asyncio,sys
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await pageB(b)
        await go(p,"location.hash='#stats';render()",900)
        print(await p.evaluate("()=>[document.querySelector('main').innerText.slice(0,500).replace(/\\n+/g,' | '),[...document.querySelectorAll('input')].map(i=>i.id+':'+i.placeholder).join(',')]"))
        await p.evaluate("()=>window.scrollTo(0,500)");await p.screenshot(path='e10_1.jpg',type='jpeg',quality=60)
        await p.evaluate("()=>openPlayer(players().find(x=>x.name==='Darian Webb').key)");await p.wait_for_timeout(900)
        await p.screenshot(path='e10_2.jpg',type='jpeg',quality=60)
        print(await p.evaluate("()=>{const s=document.querySelector('.sheet,#sheet,[role=dialog]');return s?s.innerText.slice(0,500).replace(/\\n+/g,' | '):'nosheet'}"))
        await p.evaluate("()=>{const s=document.querySelector('.sheet .sh-b,.sheet,#sheet');const sc=[...document.querySelectorAll('*')].filter(e=>e.scrollHeight>e.clientHeight+50&&getComputedStyle(e).overflowY!='visible');window.__sc=sc.map(e=>e.className).join(',')}")
        print(await p.evaluate("()=>window.__sc"))
        await b.close()
asyncio.run(main())
