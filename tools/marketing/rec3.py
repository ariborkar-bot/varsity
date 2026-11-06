import asyncio,sys,math,base64
sys.path.insert(0,'/home/claude/mk')
from cap import *
ST='/home/claude/mk/stills/'
async def main():
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        p=await newpage(b)
        # pick a strong non-two-way WR and RB for cards
        info=await p.evaluate("""()=>{const L=players().filter(x=>x.mp&&!x.tw).sort((a,b)=>agg(b,'season').v-agg(a,'season').v);const wr=L.find(x=>x.pos==='WR'),rb=L.find(x=>x.pos==='RB'),qb=L.find(x=>x.pos==='QB');window.__wr=wr.key;window.__rb=rb.key;return [wr.name,wr.school,agg(wr,'season').v,rb.name,qb.name]}""")
        print(info)
        for key,nm in [('__wr','card_wr'),('__rb','card_rb')]:
            await p.evaluate(f"()=>openPlayer(window.{key})");await p.wait_for_timeout(1400)
            await p.evaluate("()=>{const d=document.querySelector('#drawer');d.style.position='static';d.style.height='auto';d.querySelectorAll('*').forEach(e=>{const c=getComputedStyle(e);if(c.overflowY==='auto'||c.overflowY==='scroll'){e.style.overflow='visible';e.style.maxHeight='none';e.style.height='auto'}});const dp=d.querySelector('.dp');dp.style.position='static';dp.style.transform='none';dp.style.maxHeight='none'}")
            await p.evaluate("()=>{[...document.querySelectorAll('body *')].forEach(e=>{if(getComputedStyle(e).position==='fixed'&&!e.closest('#drawer'))e.style.display='none'})}")
            await p.wait_for_timeout(300)
            await (await p.query_selector('#drawer .dp')).screenshot(path=ST+nm+'.png')
            await p.goto(APP);await p.wait_for_timeout(2000);await p.evaluate(FAKE);await p.wait_for_timeout(300)
            await p.evaluate("""()=>{const L=players().filter(x=>x.mp&&!x.tw).sort((a,b)=>agg(b,'season').v-agg(a,'season').v);window.__wr=L.find(x=>x.pos==='WR').key;window.__rb=L.find(x=>x.pos==='RB').key}""")
        # share card image
        data=await p.evaluate("""async()=>{const p=pByKey(window.__wr);const b=await playerCardBlob(p);const r=new FileReader();return await new Promise(res=>{r.onload=()=>res(r.result);r.readAsDataURL(b)})}""")
        open(ST+'share_wr.png','wb').write(base64.b64decode(data.split(',')[1]))
        # full pages
        for h,nm,extra in [('#league','stats',''),('#groups','leagues',''),('#minigames','pickem',"UI.mtab='picks';"),('#games','games',''),('#minigames','sim',"UI.mtab='sim';")]:
            await p.evaluate(f"()=>{{location.hash='{h}';{extra}render()}}");await p.wait_for_timeout(1200);await p.evaluate("()=>{window.scrollTo(0,0);[...document.querySelectorAll('body *')].forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.visibility='hidden'})}")
            await p.screenshot(path=ST+nm+'.png',full_page=True);await p.evaluate("()=>[...document.querySelectorAll('body *')].forEach(e=>{e.style.visibility=''})")
        await b.close()
asyncio.run(main())
