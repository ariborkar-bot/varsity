import asyncio,sys,math
sys.path.insert(0,'/home/claude/mk')
from cap import *
async def main(which):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        if 'fg' in which:
            p=await newpage(b);r=Rec(p)
            await p.evaluate("()=>{location.hash='#minigames';UI.mtab='fg';render()}");await p.wait_for_timeout(800)
            await p.evaluate("()=>{fgOpen();document.querySelector('.fgx-x').style.display='none';__vt.start()}")
            scores=[]
            async def bot(i):
                if i==25: await p.evaluate("()=>FG.flap()")
                if i>25:
                    await p.evaluate("""()=>{const g=FG;if(!g||g.st!=='play')return;const s=g.s;const nx=g.posts.filter(p=>p.x+40*s>g.x-20*s).sort((a,b)=>a.x-b.x)[0];
                      const target=nx?nx.c+nx.gap*0.12:g.H*.45;if(g.y>target&&g.vy>-1.5*s)g.flap()}""")
                scores.append(await p.evaluate("()=>FG.score"))
            await r.frames('fg_play',450,bot)
            print(await p.evaluate("()=>[FG.st,FG.score,FG.goals]"));open('/home/claude/mk/clips/fg_scores.json','w').write(json.dumps(scores))
            await p.close()
        if 'rc' in which:
            p=await newpage(b);r=Rec(p)
            await p.evaluate("()=>{location.hash='#minigames';UI.mtab='rc';UI.rc=null;render()}");await p.wait_for_timeout(800)
            await p.evaluate("()=>{window.scrollTo(0,0);__vt.start()}")
            async def rc(i):
                if i==15: await p.evaluate("()=>rcStart()")
                if i>15 and i%70==0:
                    await p.evaluate("()=>{const m=UI.rc;if(m&&!m.spinning&&!m.done){const b=document.querySelector('.rc-p');if(b)b.click()}}")
                if i>15: await p.evaluate("()=>{const c=document.querySelector('.rc-card');if(c){const y=c.getBoundingClientRect().top+scrollY-60;window.scrollTo(0,y)}}")
            await r.frames('ring',700,rc)
            print(await p.evaluate("()=>UI.rc&&[UI.rc.done,UI.rc.res,UI.rc.total,UI.rc.aiTotal]"))
            await p.close()
        if 'fc' in which:
            p=await newpage(b);r=Rec(p)
            await p.evaluate("()=>{location.hash='#minigames';UI.mtab='draw';render()}");await p.wait_for_timeout(800)
            await p.evaluate("()=>{const d=document.querySelector('[data-act=fcDeal]');if(d){const y=d.getBoundingClientRect().top+scrollY-120;window.scrollTo(0,y)};__vt.start()}")
            async def fc(i):
                if i==12: await p.evaluate("()=>{const d=document.querySelector('[data-act=fcDeal]');if(d)d.click()}")
                if i>=12: await p.evaluate("()=>{const h=document.querySelector('.fc-hand');if(h){const y=h.getBoundingClientRect().top+scrollY-170;window.scrollTo(0,y)}}")
            await r.frames('fc_deal',170,fc)
            await p.close()
        await b.close()
asyncio.run(main(sys.argv[1:]))
