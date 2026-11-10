import asyncio,sys
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await pageB(b)
        print(await p.evaluate("()=>[players().filter(x=>/Hornby|^you$/.test(x.name)).map(x=>x.name+' '+x.school),ME.uid,JSON.stringify(S.profiles[ME.uid]),bank(ME.uid)]"))
        for nm,js in [('props',"location.hash='#minigames';UI.mtab='props';render()"),('picks',"location.hash='#minigames';UI.mtab='picks';render()"),('me',"location.hash='#me';render()"),('stats',"location.hash='#stats';render()"),('home',"location.hash='#team';render()"),('locker',"location.hash='#locker';render()"),('shop',"location.hash='#shop';render()"),('draw',"location.hash='#minigames';UI.mtab='draw';render()"),('fg',"location.hash='#minigames';UI.mtab='fg';render()"),('acct',"location.hash='#account';render()")]:
            await go(p,js,900);await p.screenshot(path=f'/home/claude/mk2/prodB/x_{nm}.jpg',type='jpeg',quality=60,full_page=False)
            print(nm,(await p.evaluate("()=>document.body.innerText.replace(/\\n+/g,' | ').slice(0,300)")))
        await b.close()
asyncio.run(main())
