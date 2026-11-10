import asyncio,sys
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
GLOW="""()=>{const u=ME.uid,P=players();const pk=n=>{const q=P.find(x=>x.name===n);return q?'pc:'+q.key:null};
 const cards={};[['Hezekiah Manuel','m'],['Darian Webb','l'],['Paisios Polamalu','l'],['Deandre Eleby','e'],['Seth Fanua','e'],['Malachi Gutierrez','r']].forEach(([n,r])=>{const k=pk(n);if(k)cards[k]={[r]:1}});
 cards['tc:Carlsbad']={l:1};cards['tc:Hoover']={e:1};
 const it={f_gold:1,bn_gold:1,nc_gold:1,cb_gold:1,bu_gold:1};
 S.picks[u]=Object.assign({},S.picks[u],{inv:Object.assign({},invOf(u),{cards,it,eq:{frame:'f_gold',banner:'bn_gold',name:'nc_gold',cback:'cb_gold',bubble:'bu_gold'},wp:Date.now(),wpv:3}),lbt:{w9:600,w10:900,w11:740}});render()}"""
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await pageB(b)
        await go(p,"location.hash='#locker';render()",900);await p.screenshot(path='e8_0.jpg',type='jpeg',quality=60)
        await p.evaluate(GLOW);await p.wait_for_timeout(600)
        print(await p.evaluate("()=>[bank(ME.uid),earned(ME.uid),document.querySelector('main')?document.querySelector('main').innerText.slice(0,600).replace(/\\n+/g,' | '):'']"))
        await p.screenshot(path='e8_1.jpg',type='jpeg',quality=60)
        print(await p.evaluate("()=>[...document.querySelectorAll('[data-act]')].map(e=>e.dataset.act+':'+(e.dataset.v||e.dataset.k||'')).filter((v,i,a)=>a.indexOf(v)===i).join(' ')"))
        await p.evaluate("()=>{const b=[...document.querySelectorAll('button')].find(e=>/^cards/i.test(e.innerText.trim()));b&&b.click()}");await p.wait_for_timeout(600)
        await p.evaluate("()=>window.scrollTo(0,300)");await p.screenshot(path='e8_2.jpg',type='jpeg',quality=60)
        await go(p,"location.hash='#minigames';UI.mtab='picks';render()",800);await p.evaluate("()=>{const e=document.querySelector('.bt-board');e&&window.scrollTo(0,e.getBoundingClientRect().top+scrollY-110)}");await p.screenshot(path='e8_3.jpg',type='jpeg',quality=60)
        await b.close()
asyncio.run(main())
