import asyncio,sys,os,json
from common import *
ST='/home/claude/mk/clips/A_still/';os.makedirs(ST,exist_ok=True)
EXPAND="async()=>{for(let i=0;i<3;i++){const b=[...document.querySelectorAll('button')].find(e=>/show 10 more/i.test(e.innerText));if(b){b.click();await new Promise(r=>setTimeout(r,250))}}}"
def ease(k):return k*k*(3-2*k)
async def smooth(p,y0,y1,i,a,n):
    if a<=i<=a+n:
        k=ease((i-a)/n);await p.evaluate(f"()=>window.scrollTo(0,{y0+(y1-y0)*k})")
async def topof(p,sel_js,off=0):
    return await p.evaluate(f"()=>{{const e={sel_js};return e?Math.round(e.getBoundingClientRect().top+scrollY-{off}):null}}")
async def fb(b,which):
    p=await newpage(b)
    await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200)
    await p.evaluate("()=>{const st=document.createElement('style');st.textContent='.pw-card{display:none!important}';document.head.appendChild(st)}")
    await p.evaluate(EXPAND);await p.evaluate(EXPAND);await p.evaluate(EXPAND);await p.wait_for_timeout(500);await zedcheck(p,'stats')
    if 'lb' in which:
        y0=await topof(p,"document.querySelector('.pod.p1')",330)
        await p.evaluate(f"()=>{{window.scrollTo(0,{y0});__vt.start()}}")
        ymax=await topof(p,"[...document.querySelectorAll('.row[data-act=player]')].pop()",900)
        print('lb y0',y0,'ymax',ymax)
        async def sc(i):
            y=min(ymax,y0+(i*i*1.1 if i<30 else 990+(i-30)*70))
            await p.evaluate(f"()=>window.scrollTo(0,{y})")
        await frames(p,'A_lb',70,sc)
        await p.evaluate(f"()=>window.scrollTo(0,{y0})");await p.screenshot(path=ST+'fb_podium.jpg',type='jpeg',quality=94)
    if 'stills' in which:
        for r in range(4,12):
            await p.evaluate(f"()=>{{const e=[...document.querySelectorAll('.row[data-act=player]')].find(e=>e.innerText.trim().startsWith('{r}'));e.scrollIntoView({{block:'center'}})}}");await p.wait_for_timeout(150)
            el=await p.evaluate_handle(f"()=>[...document.querySelectorAll('.row[data-act=player]')].find(e=>e.innerText.trim().startsWith('{r}'))")
            await el.as_element().screenshot(path=ST+f'row{r}.png')
        # rows 6-7 together and 11 context: full-frame shot centred on row 6
        await p.evaluate("()=>{const e=[...document.querySelectorAll('.row[data-act=player]')].find(e=>e.innerText.trim().startsWith('6'));window.scrollTo(0,e.getBoundingClientRect().top+scrollY-700)}");await p.wait_for_timeout(200)
        await p.screenshot(path=ST+'fb_rows6.jpg',type='jpeg',quality=94)
        print('rows6 boxes',await p.evaluate("()=>[6,7,11].map(r=>{const e=[...document.querySelectorAll('.row[data-act=player]')].find(e=>e.innerText.trim().startsWith(String(r)));const b=e.getBoundingClientRect();return [r,b.left,b.top,b.width,b.height]})"))
        for nm,fn in [('Darian Webb','webb'),('Paisios Polamalu','polamalu'),('Hezekiah Manuel','manuel'),('Elisha Robinson','robinson'),('Malachi Gutierrez','gutierrez'),('Timothy Cox','cox')]:
            await p.evaluate(f"()=>{{const q=players().find(x=>x.name==='{nm}'&&!/d$/.test(x.key));openPlayer(q.key)}}");await p.wait_for_timeout(900)
            await p.screenshot(path=ST+f'sheet_{fn}.jpg',type='jpeg',quality=94)
            await p.evaluate("()=>{try{sheetClose()}catch(e){}}");await p.wait_for_timeout(500)
    if 'school' in which:
        await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim()==='Filters');b.click()}");await p.wait_for_timeout(500)
        yq=await topof(p,"document.getElementById('q')",140)
        await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('Filters'));b.click()}");await p.wait_for_timeout(500)
        await p.evaluate(f"()=>{{window.scrollTo(0,{yq});__vt.start()}}")
        ev={}
        async def step(i):
            if i==14:
                await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('Filters'));b.click()}");ev['filters']=i
            if i==30:
                await p.click("input[placeholder='All schools – type to search']");ev['schoolbox']=i
            for k,ch in enumerate('hoover'):
                if i==40+k*3:await p.keyboard.type(ch)
            if i==62:await p.keyboard.press('Enter');ev['pickHoover']=i;await p.evaluate("()=>document.activeElement&&document.activeElement.blur()")
            if i==64:ev['podY']=await topof(p,"document.querySelector('.pod.p1')",300)
            if 'podY' in ev:await smooth(p,yq,ev['podY'],i,64,16)
            if i==128:ev['back']=i
            if i>=128:await smooth(p,ev['podY'],yq,i,128,10)
            if i==144:await p.click("input[placeholder='All schools – type to search']",click_count=3);ev['box2']=i
            for k,ch in enumerate('carlsbad'):
                if i==150+k*3:await p.keyboard.type(ch)
            if i==178:await p.keyboard.press('Enter');ev['pickCarlsbad']=i;await p.evaluate("()=>document.activeElement&&document.activeElement.blur()")
            if i==180:ev['podY2']=await topof(p,"document.querySelector('.pod.p1')",300)
            if i in (100,210):ev['box%d'%i]=await p.evaluate("()=>{const r=document.querySelector('.pod.p1').getBoundingClientRect();return [r.left,r.top,r.width,r.height].map(v=>Math.round(v*1080/392))}")
            if 'podY2' in ev:await smooth(p,yq,ev['podY2'],i,180,16)
            if i==240:
                await p.evaluate("()=>{UI.school='ALL';const b=[...document.querySelectorAll('button')].find(e=>e.innerText.trim().startsWith('Filters'));render()}")
            if i>=240:await smooth(p,ev['podY2'],yq,i,240,12)
            if i==256:await p.click('#q');ev['qfocus']=i
        await frames(p,'A_school',300,step)
        print('school events',ev)
    await zedcheck(p,'end');await p.close()
async def picks(b):
    p=await newpage(b)
    await p.evaluate("()=>{location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(1000)
    games=[('Santa Fe Christian','Carlsbad'),('Mission Hills','Cathedral Catholic'),('Torrey Pines','Helix'),('San Marcos','Granite Hills'),('Lincoln','Oceanside'),('Rancho Bernardo','La Costa Canyon')]
    for i,(a,h) in enumerate(games):
        js=f"[...document.querySelectorAll('article.gm')].find(x=>x.innerText.includes({json.dumps(a)})&&x.innerText.includes({json.dumps(h)}))"
        await p.evaluate(f"()=>{js}.scrollIntoView({{block:'center'}})");await p.wait_for_timeout(250)
        el=await p.evaluate_handle(f"()=>{js}");await el.as_element().screenshot(path=ST+f'game{i+1}.png')
    js="[...document.querySelectorAll('article.gm')].find(x=>x.innerText.includes('Santa Fe Christian')&&x.innerText.includes('Carlsbad'))"
    await p.evaluate(f"()=>{js}.scrollIntoView({{block:'center'}})");await p.wait_for_timeout(300)
    y=await topof(p,js,230);await p.evaluate(f"()=>{{window.scrollTo(0,{y});__vt.start()}}")
    ev={}
    async def step(i):
        if i==12:await p.evaluate(f"()=>{js}.querySelector('[data-act=pkSide][data-s=h]').click()");ev['tap']=i
        if i==13:ev['after']=await p.evaluate("()=>document.body.innerText.match(/(\\d+) pick[s]? ready|Lock in[^\\n]*/g)")
        if i==40:
            r=await p.evaluate("()=>{const b=document.querySelector('[data-act=pkAll]');if(b){b.click();return b.innerText}return null}");ev['lock']=(i,r)
        if i>12:await p.evaluate(f"()=>{{const e={js};window.scrollTo(0,e.getBoundingClientRect().top+scrollY-230)}}")
    await frames(p,'A_pick',90,step)
    ev['card']=await p.evaluate(f"()=>{js}.innerText.replace(/\\n/g,' | ')")
    print('pick events',ev)
    await p.screenshot(path=ST+'pick_locked.jpg',type='jpeg',quality=94)
    await p.close()
async def bb(b):
    p=await newpage(b,APPB)
    await p.evaluate("()=>{location.hash='#stats';render()}");await p.wait_for_timeout(1200);await zedcheck(p,'bb')
    await p.screenshot(path=ST+'bb_top.jpg',type='jpeg',quality=94)
    y1=await topof(p,"document.querySelector('.pod.p1')",330)
    await p.evaluate("()=>{window.scrollTo(0,0);__vt.start()}")
    async def sc(i):await smooth(p,0,y1,i,6,40)
    await frames(p,'A_bblb',60,sc)
    await p.screenshot(path=ST+'bb_podium.jpg',type='jpeg',quality=94)
    print('bb podium',await p.evaluate("()=>[...document.querySelectorAll('.pod,.row[data-act=player]')].slice(0,6).map(e=>e.innerText.replace(/\\n/g,' ').slice(0,60))"))
    await p.evaluate("()=>{location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(800)
    js="[...document.querySelectorAll('article.gm')].find(x=>x.innerText.includes('Westview')&&x.innerText.includes('La Jolla'))"
    await p.evaluate(f"()=>{js}.scrollIntoView({{block:'center'}})");await p.wait_for_timeout(300)
    await p.screenshot(path=ST+'bb_pick.jpg',type='jpeg',quality=94)
    el=await p.evaluate_handle(f"()=>{js}");await el.as_element().screenshot(path=ST+'bb_game.png')
    await p.evaluate("()=>{location.hash='#groups';UI.ltab='mock';render()}");await p.wait_for_timeout(800)
    await p.evaluate("()=>{const b=document.querySelector('[data-act=mkSolo]');b&&b.click()}");await p.wait_for_timeout(1500)
    await p.screenshot(path=ST+'bb_mock1.jpg',type='jpeg',quality=94)
    print('mock text',await p.evaluate("()=>document.body.innerText.slice(0,600).replace(/\\n/g,' | ')"))
    await p.close()
async def main(which):
    async with async_playwright() as pw:
        b=await browser(pw)
        if set(which)&{'lb','stills','school'}:await fb(b,which)
        if 'picks' in which:await picks(b)
        if 'bb' in which:await bb(b)
        await b.close()
asyncio.run(main(sys.argv[1:]))
