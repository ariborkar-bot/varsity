import asyncio,sys
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await pageB(b)
        await go(p,"location.hash='#minigames';UI.mtab='draw';render()",800)
        print(await p.evaluate("async()=>{const w=fcCur();const r=[w,fcOpen(w),!!fcHand(ME.uid,w),ME.mode];window.__s=[];const os=say;say=m=>{window.__s.push(m);os(m)};await fcDeal();return r.concat([window.__s,!!fcHand(ME.uid,w),typeof _fcBusy!=='undefined'&&_fcBusy])}"))
        await p.wait_for_timeout(3000)
        print(await p.evaluate("()=>[!!fcHand(ME.uid,fcCur()),document.querySelector('.fc-hand')?document.querySelector('.fc-hand').innerText.slice(0,200):'no hand']"))
        await b.close()
asyncio.run(main())
