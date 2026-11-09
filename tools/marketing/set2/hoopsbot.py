import asyncio,sys,json
sys.path.insert(0,'/home/claude/mk')
from rec import *
import os
OFF=float(os.environ.get('OFF','0.18'));VY=float(os.environ.get('VY','0'))
BOT="""()=>{const g=FG;if(!g||g.st!=='play')return [g&&g.st,g&&g.score];const s=g.s;
 const nx=g.posts.filter(p=>p.x+30*s>g.x-14*s).sort((a,b)=>a.x-b.x)[0];
 const c=nx?(nx.amp?nx.c0+nx.amp*Math.sin((g.t+.25)*nx.w+nx.ph):nx.c):g.H*.45;
 const target=c+(nx?nx.gap:150*s)*%s;
 if(g.y>target&&g.vy>=%s*s)g.flap();return [g.st,g.score]}"""%(OFF,VY)
async def main(rec,N,seed):
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b,APPB)
        await p.evaluate(f"()=>{{Math.random=(()=>{{let x={seed};return()=>(x=(x*16807)%2147483647)/2147483647}})();location.hash='#minigames';UI.mtab='fg';render()}}");await p.wait_for_timeout(800)
        await p.evaluate("()=>{fgOpen('free');document.querySelector('.fgx-x').style.display='none';__vt.start()}")
        log=[]
        async def bot(i):
            if i==20:await p.evaluate("()=>FG.flap()")
            if os.environ.get('JUMP'):
                for fi,tt,sc in [(40,57.5,158),(250,87.5,247),(460,127.5,341)]:
                    if i==fi:await p.evaluate(f"()=>{{FG.t0=performance.now()-{tt}*1000;FG.score={sc}}}")
            if i>20:log.append(await p.evaluate(BOT))
        if rec:await frames(p,os.environ.get('NAME','hoops'),N,bot)
        else:
            for i in range(N):
                await bot(i);await p.evaluate("()=>__step(1000/30)")
                if log and log[-1][0]=='over':break
        sc=[x[1] for x in log];print('seed',seed,'frames',len(log),'final',log[-1] if log else None,'score at 10s/20s/40s',[sc[k] if k<len(sc) else None for k in (300,600,1200)])
        if rec:json.dump(log,open(OUT+os.environ.get('NAME','hoops')+'_log.json','w'))
        await b.close()
asyncio.run(main(sys.argv[1]=='rec',int(sys.argv[2]),int(sys.argv[3])))
