import asyncio,sys,json
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
def ART(name):return "[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes(%s))"%json.dumps(name)
def HOLD(expr,off):return "()=>{const e="+expr+";if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-%d)}"%off
NOTOAST="()=>document.querySelectorAll('.toast,.tst,#toast').forEach(e=>e.style.visibility='hidden')"
async def gid_of(p,name):return await p.evaluate("()=>{const c=propCands().find(x=>{const q=pByKey(x.k);return q&&q.name===%s});return gid(c.game)}"%json.dumps(name))
async def props_clip(p,name,player,market,clipname,N,t_over,t_stake,t_lock,off=150,toast=False):
    g=await gid_of(p,player)
    await go(p,"location.hash='#minigames';UI.mtab='props';UI.ppG="+json.dumps(g)+";render()",900)
    A=ART(player)
    await p.evaluate("()=>{const a="+A+";const s=a.querySelector('[data-act=ppSel][data-id$=%s]');s&&s.click()}"%market);await p.wait_for_timeout(300)
    await p.evaluate(HOLD(A,off));await p.evaluate("()=>__vt.on||__vt.start()")
    async def ev(i):
        if i==t_over:await p.evaluate("()=>{const a="+A+";a.querySelector('[data-act=ppSide][data-s=o]').click()}")
        if i==t_stake:await p.evaluate("()=>{const a="+A+";const b=a.querySelector('[data-act=ppStake][data-v=\"25\"]');b&&b.click()}")
        if i==t_lock:await p.evaluate("()=>{const b=document.querySelector('[data-act=ppAll]');b&&b.click()}")
        await p.evaluate(HOLD(A,off))
        if not toast:await p.evaluate(NOTOAST)
    await frames(p,clipname,N,ev)
async def v6(b):
    p=await pageB(b)
    await props_clip(p,'v6','Amaree Maye','passYd','B_props6',150,40,66,96,off=130)
    await p.close()
async def v7(b):
    p=await pageB(b)
    R=await p.evaluate("""()=>{let R,n=0;do{R=wpRoll();n++}while(!(R.r==='l'||R.r==='m'||R.ach)&&n<500);window.__R=R;const q=R.key&&pByKey(R.key);return {n,r:R.r,team:R.team,player:q&&q.name,pos:q&&q.pos,pool:R.pool.length,ach:R.ach||null}}""")
    print('roll',R,flush=True)
    await p.evaluate("()=>{const R=window.__R;window.wpRoll=()=>R;document.querySelectorAll('.toast,.tst').forEach(e=>e.remove());location.hash='#team';render()}");await p.wait_for_timeout(500)
    await p.evaluate("()=>__vt.start()")
    async def ev(i):
        if i==2:await p.evaluate("()=>wpOpen()")
        await p.evaluate(NOTOAST)
    await frames(p,'B_wp',2+int(13.6*30),ev)
    json.dump(R,open('/home/claude/mk/clips/B_wp/roll.json','w'))
    await p.close()
GLOW="""()=>{const u=ME.uid,P=players();const pk=n=>{const q=P.find(x=>x.name===n);return q?'pc:'+q.key:null};
 const cards={};[['Hezekiah Manuel','m'],['Darian Webb','l'],['Paisios Polamalu','l'],['Deandre Eleby','e'],['Seth Fanua','e'],['Malachi Gutierrez','r']].forEach(([n,r])=>{const k=pk(n);if(k)cards[k]={[r]:1}});
 cards['tc:Carlsbad']={l:1};cards['tc:Hoover']={e:1};
 const it={f_gold:1,bn_gold:1,nc_gold:1,cb_gold:1,bu_gold:1};
 S.picks[u]=Object.assign({},S.picks[u],{inv:Object.assign({},invOf(u),{cards,it,eq:{frame:'f_gold',banner:'bn_gold',name:'nc_gold',cback:'cb_gold',bubble:'bu_gold'},wp:Date.now(),wpv:3}),lbt:{w9:600,w10:900,w11:740}});render()}"""
async def still(p,name,N,each=None):
    await p.evaluate("()=>__vt.on||__vt.start()")
    async def ev(i):
        if each:await each(i)
        await p.evaluate(NOTOAST)
    await frames(p,name,N,ev)
async def v8(b):
    p=await pageB(b)
    await p.evaluate("()=>{const u=ME.uid;S.picks[u]=Object.assign({},S.picks[u],{inv:Object.assign({},invOf(u),{wp:Date.now(),wpv:3})});render()}")
    await go(p,"location.hash='#locker';render();window.scrollTo(0,0)",800)
    await still(p,'B_lk0',30)
    await p.evaluate("()=>{const b=document.querySelector('[data-act=lkTab][data-v=cards]');b&&b.click()}");await p.wait_for_timeout(500)
    await p.evaluate("()=>{const e=document.querySelector('[data-act=lkTab]');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-110)}")
    await still(p,'B_lk0c',30)
    # after
    await p.evaluate(GLOW);await go(p,"location.hash='#locker';render();window.scrollTo(0,0)",800)
    await p.evaluate("()=>{const b=document.querySelector('[data-act=lkTab][data-v=cos]');b&&b.click();window.scrollTo(0,0)}");await p.wait_for_timeout(400)
    await still(p,'B_lk1',30)
    await p.evaluate("()=>{const b=document.querySelector('[data-act=lkTab][data-v=cards]');b&&b.click()}");await p.wait_for_timeout(500)
    print('cards view',await p.evaluate("()=>document.querySelector('main').innerText.slice(0,900).replace(/\\n+/g,' | ')"))
    await p.evaluate("()=>{const e=[...document.querySelectorAll('main *')].find(x=>x.children.length<4&&/Hezekiah Manuel/i.test(x.innerText||''));if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-260)}")
    await still(p,'B_lkcards',30)
    await p.evaluate("()=>{const b=document.querySelector('[data-act=lkTab][data-v=cos]');b&&b.click()}");await p.wait_for_timeout(400)
    await p.evaluate("()=>{const e=document.querySelector('[data-act=lkK]');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-110)}")
    await still(p,'B_lkcos',30)
    # active picks: lock 2 props + 1 pick through the UI (no recording)
    for pl,mk in [('Amaree Maye','passYd'),('Michael Ogdahl','rushYd')]:
        g=await gid_of(p,pl);await go(p,"location.hash='#minigames';UI.mtab='props';UI.ppG="+json.dumps(g)+";render()",600);A=ART(pl)
        await p.evaluate("()=>{const a="+A+";const s=a.querySelector('[data-act=ppSel][data-id$=%s]');s&&s.click()}"%mk);await p.wait_for_timeout(200)
        await p.evaluate("()=>{const a="+A+";a.querySelector('[data-act=ppSide][data-s=o]').click()}");await p.wait_for_timeout(200)
        await p.evaluate("()=>{const a="+A+";const b=a.querySelector('[data-act=ppStake][data-v=\"50\"]');b&&b.click()}");await p.wait_for_timeout(200)
        await p.evaluate("()=>document.querySelector('[data-act=ppAll]').click()");await p.wait_for_timeout(500)
    await go(p,"location.hash='#minigames';UI.mtab='picks';render()",700)
    await p.evaluate("()=>{const b=[...document.querySelectorAll('[data-act=pkSide]')].find(x=>x.innerText.includes('Carlsbad'));b&&b.click()}");await p.wait_for_timeout(300)
    await p.evaluate("()=>{const b=document.querySelector('[data-act=pkAll]');b&&b.click()}");await p.wait_for_timeout(600)
    await p.evaluate("()=>{const e=document.querySelector('.act-picks');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-110)}")
    await still(p,'B_act8',30)
    await p.evaluate("()=>{const e=document.querySelector('.bt-board');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-260)}")
    await still(p,'B_tok8',60)
    await p.close()
async def v9(b):
    p=await pageB(b)
    await p.evaluate("()=>{const u=ME.uid;S.picks[u]=Object.assign({},S.picks[u],{inv:Object.assign({},invOf(u),{wp:Date.now(),wpv:3})});render()}")
    await go(p,"location.hash='#minigames';UI.mtab='draw';render();window.scrollTo(0,0)",800)
    await p.evaluate("()=>{try{dlyPend=''}catch(e){};const u=ME.uid;S.picks[u]=Object.assign({},S.picks[u],{dly:{}})}")
    await p.evaluate("()=>__vt.start()")
    async def d1(i):
        if i==8:await p.evaluate("()=>dlyClaim()")
    await frames(p,'B_daily',50,d1)
    await go(p,"location.hash='#minigames';UI.mtab='sim';render()",600)
    await p.evaluate("()=>{const e=document.querySelector('[data-act=simStart]');if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-360)}")
    async def d2(i):
        if i==4:await p.evaluate("()=>{const e=document.querySelector('[data-act=simStart]');e&&e.click()}")
        if i==6:await p.evaluate("()=>{const e=document.querySelector('main .head');if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY+330)}")
        await p.evaluate(NOTOAST)
    await frames(p,'B_sim',60,d2)
    await props_clip(p,'v9','Michael Ogdahl','rushYd','B_ogdahl',50,16,26,40,off=150)
    # Field goal
    await go(p,"location.hash='#minigames';UI.mtab='fg';render()",600)
    await p.evaluate("()=>{fgOpen('free');const x=document.querySelector('.fgx-x');if(x)x.style.display='none'}");await p.wait_for_timeout(300)
    BOT="""()=>{const g=FG;if(!g||g.st!=='play')return [g&&g.st,g&&g.score];const s=g.s;
     const nx=g.posts.filter(p=>p.x+30*s>g.x-14*s).sort((a,b)=>a.x-b.x)[0];
     const c=nx?(nx.amp?nx.c0+nx.amp*Math.sin((g.t+.25)*nx.w+nx.ph):nx.c):g.H*.45;
     const target=c+(nx?nx.gap:150*s)*0.18;if(g.y>target&&g.vy>=0)g.flap();return [g.st,g.score]}"""
    async def fg(i):
        if i==2:await p.evaluate("()=>FG.flap()")
        if i==3:await p.evaluate("()=>{FG.t0=performance.now()-14*1000;FG.score=Math.max(FG.score,9)}")
        if i>3:await p.evaluate(BOT)
    await frames(p,'B_fg',70,fg)
    await p.evaluate("()=>{try{fgClose&&fgClose()}catch(e){};document.querySelectorAll('.fgx,.fg-ov').forEach(e=>e.remove())}")
    await go(p,"location.hash='#minigames';UI.mtab='picks';render()",700)
    SFC="[...document.querySelectorAll('[data-act=pkSide]')].find(x=>x.innerText.includes('Carlsbad')).closest('article')"
    await p.evaluate(HOLD(SFC,170))
    async def pk(i):
        if i==14:await p.evaluate("()=>{const b=[...document.querySelectorAll('[data-act=pkSide]')].find(x=>x.innerText.includes('Carlsbad'));b&&b.click()}")
        if i==30:await p.evaluate("()=>{const b=document.querySelector('[data-act=pkAll]');b&&b.click()}")
        await p.evaluate(HOLD(SFC,170));await p.evaluate(NOTOAST)
    await frames(p,'B_pick',50,pk)
    # lock Amaree too, so active picks has 3
    g=await gid_of(p,'Amaree Maye');await go(p,"location.hash='#minigames';UI.mtab='props';UI.ppG="+json.dumps(g)+";render()",600);A=ART('Amaree Maye')
    await p.evaluate("()=>{const a="+A+";a.querySelector('[data-act=ppSide][data-s=o]').click()}");await p.wait_for_timeout(200)
    await p.evaluate("()=>document.querySelector('[data-act=ppAll]').click()");await p.wait_for_timeout(500)
    await p.evaluate("()=>{const e=document.querySelector('.act-picks');window.scrollTo(0,e.getBoundingClientRect().top+scrollY-110)}")
    await still(p,'B_act9',50)
    await go(p,"location.hash='#games';render();window.scrollTo(0,0)",800)
    await p.evaluate("()=>{const e=document.querySelector('.gotw');if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-200)}")
    await still(p,'B_gotw',50)
    await go(p,"location.hash='#stats';render();window.scrollTo(0,0)",800)
    y0=await p.evaluate("()=>{const e=document.querySelector('[data-act=player]');return e?e.getBoundingClientRect().top+scrollY-250:600}")
    async def sc(i):
        k=min(1,i/22);e=1-(1-k)**3
        await p.evaluate(f"()=>window.scrollTo(0,{y0+1500*(1-e)})")
    await still(p,'B_stats9',50,sc)
    await go(p,"location.hash='#shop';render();window.scrollTo(0,0)",700)
    got=await p.evaluate("""()=>{const u=ME.uid,v0=JSON.parse(JSON.stringify(invOf(u)));let best=null,tries=0;
      const real=Math.random;
      return 'ok'}""")
    await p.evaluate("()=>__vt.on||__vt.start()")
    pev=[]
    async def pkk(i):
        if i==4:await p.evaluate("()=>packOpen('rookie','tok')")
        if i==112:
            await p.evaluate("()=>{const b=document.querySelector('.pko-all');b&&b.click()}");pev.append(i)
        await p.evaluate(NOTOAST)
    await frames(p,'B_pack9',200,pkk)
    print('pack flips',pev,await p.evaluate("()=>[...document.querySelectorAll('.pks')].map(e=>e.className).join(' / ')"))
    await p.close()
async def v10(b):
    p=await pageB(b)
    await p.evaluate("()=>{const u=ME.uid;S.picks[u]=Object.assign({},S.picks[u],{inv:Object.assign({},invOf(u),{wp:Date.now(),wpv:3})});render()}")
    await go(p,"location.hash='#stats';render();window.scrollTo(0,0)",800)
    top=await p.evaluate("()=>{const e=document.querySelector('[data-act=player]');return e?e.getBoundingClientRect().top+scrollY:700}")
    async def s1(i):await p.evaluate(f"()=>window.scrollTo(0,{top-220+i*2.2})")
    await still(p,'B_lb10',95,s1)
    await p.evaluate("()=>openPlayer(players().find(x=>x.name==='Darian Webb').key)");await p.wait_for_timeout(700)
    await p.evaluate("()=>{const d=document.querySelector('.dp');const w=[...d.querySelectorAll('*')].find(x=>/^W1$/.test(x.textContent.trim()));if(w)d.scrollTop=Math.max(0,w.getBoundingClientRect().top-d.getBoundingClientRect().top+d.scrollTop-330)}")
    await still(p,'B_pl10',95)
    await p.evaluate("()=>{try{sheetClose()}catch(e){};document.querySelectorAll('.dp').forEach(e=>e.remove())}")
    await go(p,"location.hash='#stats';render();window.scrollTo(0,0)",700)
    await p.evaluate("()=>{const q=document.getElementById('q');window.scrollTo(0,q.getBoundingClientRect().top+scrollY-140)}")
    word='darian webb'
    async def s3(i):
        k=(i-10)//3
        if 10<=i and (i-10)%3==0 and k<len(word):
            await p.evaluate("(w)=>{const q=document.getElementById('q');q.focus();q.value=w;q.dispatchEvent(new Event('input',{bubbles:true}))}",word[:k+1])
            await p.evaluate("()=>{const q=document.getElementById('q');window.scrollTo(0,q.getBoundingClientRect().top+scrollY-140)}")
    await still(p,'B_search10',95,s3)
    await p.evaluate("()=>{const q=document.getElementById('q');q.value='';q.dispatchEvent(new Event('input',{bubbles:true}));q.blur()}");await p.wait_for_timeout(400)
    await p.evaluate("()=>window.scrollTo(0,0)")
    await still(p,'B_lbw10',95)
    await go(p,"location.hash='#minigames';UI.mtab='picks';render()",700)
    await p.evaluate("()=>{const e=[...document.querySelectorAll('.bt-g')][0];if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-200)}")
    async def s5(i):await p.evaluate("()=>{const e=[...document.querySelectorAll('.bt-g')][0];if(e)window.scrollTo(0,e.getBoundingClientRect().top+scrollY-200+%f)}"%(i*1.6))
    await still(p,'B_pk10',95,s5)
    await p.close()
async def v10s(b):
    p=await pageB(b)
    await go(p,"location.hash='#stats';render();window.scrollTo(0,0)",700)
    await p.evaluate("()=>{const q=document.getElementById('q');window.scrollTo(0,q.getBoundingClientRect().top+scrollY-140)}")
    word='darian webb'
    async def s3(i):
        k=(i-10)//3
        if 10<=i and (i-10)%3==0 and k<len(word):
            await p.evaluate("(w)=>{const q=document.getElementById('q');q.focus();q.value=w;q.dispatchEvent(new Event('input',{bubbles:true}))}",word[:k+1])
            await p.evaluate("()=>{const q=document.getElementById('q');window.scrollTo(0,q.getBoundingClientRect().top+scrollY-140)}")
    await still(p,'B_search10',95,s3)
    await p.close()
async def main(which):
    async with async_playwright() as pw:
        b=await browser(pw)
        for w in which:await globals()[w](b)
        await b.close()
asyncio.run(main(sys.argv[1:]))
