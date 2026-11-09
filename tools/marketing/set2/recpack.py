import asyncio,sys,json
sys.path.insert(0,'/home/claude/mk')
from rec import *
GOT="[{card:'tc:Mission Hills',r:'u'},{card:'pc:mp1027',r:'r'},{card:'pc:mp299',r:'r'},{id:'cb_gold',r:'l'},{card:'pc:mp29',r:'m'}]"
async def main(pack,name,got,N):
    async with async_playwright() as pw:
        b=await browser(pw);p=await newpage(b)
        await p.evaluate("()=>{location.hash='#shop';render()}");await p.wait_for_timeout(800)
        await p.evaluate("()=>__vt.start()")
        ev=[]
        async def step(i):
            if i==6:await p.evaluate(f"()=>packShow(PACKS.{pack},{got})")
            if i==68:await p.evaluate("()=>document.querySelector('.pko-all').click()");ev.append(['all',i])
            r=await p.evaluate("()=>{const s=document.querySelector('.pks.rdy:not(.out)');if(s){s.click();return 1};return 0}")
            if r:ev.append(['spot',i])
            st=await p.evaluate("()=>[document.querySelector('.pks.rev')?1:0,document.querySelector('.pks')?1:0]")
            if st[0] and (not ev or ev[-1][0]!='rev'):ev.append(['rev',i])
        await frames(p,name,N,step)
        print(ev);json.dump(ev,open(OUT+name+'_ev.json','w'))
        await b.close()
asyncio.run(main(sys.argv[1],sys.argv[2],GOT,int(sys.argv[3])))
