import asyncio,sys,math
sys.path.insert(0,'/home/claude/mk')
from cap import *
ease=lambda x:0.5-0.5*math.cos(math.pi*min(1,max(0,x)))
async def main(which):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        if 'stats' in which:
            p=await newpage(b);r=Rec(p)
            await p.evaluate("()=>{location.hash='#league'}");await p.wait_for_timeout(900);await p.evaluate("()=>{_tickRev=-1;render();__vt.start()}")
            H=await p.evaluate("()=>Math.min(2600,document.documentElement.scrollHeight-innerHeight)")
            async def sc(i): 
                y=H*ease((i-15)/120);await p.evaluate(f"()=>window.scrollTo(0,{y})")
            await r.frames('stats_scroll',150,sc)
            await p.close()
        if 'card' in which:
            p=await newpage(b);r=Rec(p)
            await p.evaluate("()=>{location.hash='#league'}");await p.wait_for_timeout(900)
            await p.evaluate("()=>{const t=players().filter(x=>x.mp&&x.pos!=='DEF').sort((a,b)=>agg(b,'season').v-agg(a,'season').v)[0];window.__k=t.key;openPlayer(t.key)}")
            await p.wait_for_timeout(1500);await p.evaluate("()=>{window.__sc=[...document.querySelectorAll('#drawer,#drawer *')].find(e=>e.scrollHeight>e.clientHeight+50&&getComputedStyle(e).overflowY!='visible');__vt.start()}")
            async def op(i):
                if i>20:
                    await p.evaluate(f"()=>{{if(window.__sc)window.__sc.scrollTop={1500*ease((i-25)/120)}}}")
            await r.frames('player_card',165,op)
            await p.close()
        if 'search' in which:
            p=await newpage(b);r=Rec(p)
            await p.evaluate("()=>{location.hash='#league'}");await p.wait_for_timeout(900)
            name=await p.evaluate("()=>players().filter(x=>x.mp&&x.pos==='WR').sort((a,b)=>agg(b,'season').v-agg(a,'season').v)[0].name")
            await p.click('input[type=search]');await p.evaluate("()=>__vt.start()")
            typed=['']
            async def ty(i):
                k=(i-12)//4
                if 0<=k<len(name) and (i-12)%4==0:
                    await p.keyboard.type(name[k])
                if i==12+4*len(name)+25:
                    await p.evaluate("()=>{const b=document.querySelector('#main [data-act=player]');if(b)b.click()}")
            await r.frames('search',12+4*len(name)+75,ty)
            print('searched',name)
            await p.close()
        await b.close()
asyncio.run(main(sys.argv[1:]))
