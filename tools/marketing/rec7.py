import asyncio,sys,math,json
sys.path.insert(0,'/home/claude/mk')
from cap import *
ease=lambda x:0.5-0.5*math.cos(math.pi*min(1,max(0,x)))
ST='/home/claude/mk/stills/'
TAPS={}
async def tap(p,name,i,sel,idx=0):
    r=await p.evaluate(f"()=>{{const e=document.querySelectorAll({json.dumps(sel)})[{idx}];if(!e)return null;const b=e.getBoundingClientRect();e.click();return [b.left+b.width/2,b.top+b.height/2]}}")
    TAPS.setdefault(name,[]).append([i]+(r or [0,0]));print(name,i,sel,r)
async def hide_fixed(p,on=True):
    await p.evaluate("()=>{[...document.querySelectorAll('#mastMini,.tabbar,nav.tabs,#tabs')].forEach(e=>{})}")
async def main(which):
    async with async_playwright() as pw:
        b=await pw.chromium.launch(executable_path='/usr/bin/google-chrome',args=['--no-sandbox'])
        if 'card' in which:
            p=await newpage(b,fake=False);r=Rec(p)
            await p.evaluate("()=>{location.hash='#league'}");await p.wait_for_timeout(900)
            nm=await p.evaluate("()=>{const t=players().filter(x=>x.mp&&!x.tw&&x.pos!=='DEF').sort((a,b)=>agg(b,'season').v-agg(a,'season').v)[0];openPlayer(t.key);return [t.name,t.school,t.pos,agg(t,'season').v]}")
            print(nm)
            await p.wait_for_timeout(1500);await p.evaluate("()=>{window.__sc=[...document.querySelectorAll('#drawer,#drawer *')].find(e=>e.scrollHeight>e.clientHeight+50&&getComputedStyle(e).overflowY!='visible');__vt.start()}")
            async def op(i):
                if i>20: await p.evaluate(f"()=>{{if(window.__sc)window.__sc.scrollTop={1400*ease((i-25)/110)}}}")
            await r.frames('card7',150,op);await p.close()
        if 'picks' in which:
            p=await newpage(b,fake=False);r=Rec(p)
            await p.evaluate("()=>{UI.bf.dv='Division II';location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(1000)
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';const e=[...document.querySelectorAll('.bt-g')][3];window.__hz=e;window.scrollTo(0,e.getBoundingClientRect().top+scrollY-180);__vt.start()}")
            async def pk(i):
                await p.evaluate("()=>{if(!document.contains(window.__hz))window.__hz=[...document.querySelectorAll('.bt-g')].find(a=>a.innerText.includes('Mater Dei'))}")
                if i==20: await tap(p,'picks7',i,'.bt-g [data-act=pkSide]',6)
                if i==46: await tap(p,'picks7',i,'.bt-g [data-act=pkStake][data-v="50"]',0)
                if i==74: await tap(p,'picks7',i,'[data-act=pkAll]',0)
                await p.evaluate("()=>{const e=[...document.querySelectorAll('.bt-g')].find(a=>a.innerText.includes('Mater Dei'));if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-180)}")
            await r.frames('picks7',130,pk);await p.close()
        if 'props' in which:
            p=await newpage(b,fake=False);r=Rec(p)
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';UI.bf.sc='Hoover';location.hash='#minigames';UI.mtab='props';render()}");await p.wait_for_timeout(1000)
            print(await p.evaluate("()=>[...document.querySelectorAll('[data-act=ppSide]')].slice(0,4).map(e=>e.closest('article').innerText.split('\\n').slice(0,4).join(' / '))"))
            await p.evaluate("()=>{document.body.style.paddingBottom='1200px';const e=[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes('Hezekiah Manuel'));window.__hz=e;window.scrollTo(0,e.getBoundingClientRect().top+scrollY-180);__vt.start()}")
            async def pp(i):
                await p.evaluate("()=>{if(!document.contains(window.__hz))window.__hz=[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes('Hezekiah Manuel'))}")
                if i==20: await tap(p,'props7',i,'[data-act=ppSide]',await p.evaluate("()=>[...document.querySelectorAll('[data-act=ppSide]')].indexOf(window.__hz.querySelector('[data-act=ppSide]'))"))
                if i==46: await tap(p,'props7',i,'[data-act=ppStake][data-v="25"]',0)
                if i==74: await tap(p,'props7',i,'[data-act=ppAll]',0)
                await p.evaluate("()=>{const e=[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes('Hezekiah Manuel'));if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-180)}")
            await r.frames('props7',130,pp);await p.close()
        if 'fc' in which:
            p=await newpage(b,fake=False);r=Rec(p)
            await p.evaluate("()=>{location.hash='#minigames';UI.mtab='draw';render()}");await p.wait_for_timeout(800)
            print(await p.evaluate("""()=>{const pool=fcPool(new Set());const by={};pool.slice().sort((a,b)=>agg(b,'season').v-agg(a,'season').v).forEach(p=>{if(!by[p.pos])by[p.pos]=p});
              const want=['QB','RB','WR','DEF','TE','K'].map(k=>by[k]).filter(Boolean).slice(0,FC_SIZE).map(p=>p.key);const arr=pool.slice(),q=[];for(const k of want){const i=arr.findIndex(p=>p.key===k);q.push(i);arr.splice(i,1)}
              const orig=crypto.getRandomValues.bind(crypto);crypto.getRandomValues=x=>{if(q.length&&x.length===1){x[0]=q.shift();return x}return orig(x)};return want.map(k=>pByKey(k).name+' '+pByKey(k).school)}"""))
            await p.evaluate("()=>{const d=document.querySelector('[data-act=fcDeal]');if(d){const y=d.getBoundingClientRect().top+scrollY-120;window.scrollTo(0,y)};__vt.start()}")
            async def fc(i):
                if i==12: await p.evaluate("()=>{const d=document.querySelector('[data-act=fcDeal]');if(d)d.click()}")
                if i>=12: await p.evaluate("()=>{const h=document.querySelector('.fc-hand');if(h){const y=h.getBoundingClientRect().top+scrollY-170;window.scrollTo(0,y)}}")
            await r.frames('fc7',170,fc)
            print(await p.evaluate("()=>[...document.querySelectorAll('.fc-hand b, .fc-hand .nm')].map(e=>e.innerText).join(', ')"))
            await p.close()
        if 'still' in which:
            p=await newpage(b,fake=False)
            await p.evaluate("()=>{S.settings.week=11;window.__seed=39}");await p.evaluate(LEAGUE);await p.evaluate("()=>{location.hash='#groups';render()}");await p.wait_for_timeout(1200);await p.evaluate("()=>__step(1500)")
            print(await p.evaluate("()=>standingsOf(S.groups.lgdemo).map(x=>nm(x.uid)+' '+x.rec.w+'-'+x.rec.l).join(' | ')"))
            await p.evaluate("()=>{window.scrollTo(0,0);[...document.querySelectorAll('body *')].forEach(e=>{if(getComputedStyle(e).position==='fixed')e.style.visibility='hidden'})}")
            await p.screenshot(path=ST+'league7.png',full_page=True)
            await p.goto(APP);await p.wait_for_timeout(2000);await p.evaluate("()=>{try{S.profiles[ME.uid].name='Jordan Reyes'}catch(e){}}")
            await p.evaluate("()=>{location.hash='#minigames';UI.mtab='picks';render()}");await p.wait_for_timeout(800)
            await p.evaluate("()=>document.querySelector('[data-act=tokOpen]').click()");await p.wait_for_timeout(600)
            await p.screenshot(path=ST+'tok7.png')
            await p.close()
        await b.close()
    old={}
    try: old=json.load(open('/home/claude/mk/clips/taps7.json'))
    except: pass
    old.update(TAPS);json.dump(old,open('/home/claude/mk/clips/taps7.json','w'))
asyncio.run(main(sys.argv[1:]))
