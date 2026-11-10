import asyncio,sys
sys.path.insert(0,'/home/claude/mk2/prodB')
from recB import *
ART="[...document.querySelectorAll('[data-act=ppSide]')].map(x=>x.closest('article')).find(a=>a.innerText.includes('Amaree Maye'))"
async def main():
    async with async_playwright() as pw:
        b=await browser(pw);p=await pageB(b)
        gid=await p.evaluate("()=>{const c=propCands().find(x=>{const q=pByKey(x.k);return q&&q.name==='Amaree Maye'});return gid(c.game)}")
        await go(p,"location.hash='#minigames';UI.mtab='props';UI.ppG="+json.dumps(gid)+";render()",900)
        print(await p.evaluate("()=>{const a="+ART+";return a?[...a.querySelectorAll('[data-act]')].map(e=>e.dataset.act+':'+(e.dataset.id||'')+':'+(e.dataset.s||e.dataset.v||'')+':'+e.innerText.slice(0,25).replace(/\\n/g,' ')).join(' | '):'none'}"))
        await p.evaluate("()=>{const a="+ART+";a.scrollIntoView({block:'center'})}");await p.wait_for_timeout(300)
        await p.screenshot(path='e6_1.jpg',type='jpeg',quality=60)
        await p.evaluate("()=>{const a="+ART+";const s=a.querySelector('[data-act=ppSel][data-id$=passYd]');s&&s.click()}");await p.wait_for_timeout(300)
        await p.evaluate("()=>{const a="+ART+";a.scrollIntoView({block:'center'});a.querySelector('[data-act=ppSide][data-s=o]').click()}");await p.wait_for_timeout(300)
        await p.evaluate("()=>{const a="+ART+";a.scrollIntoView({block:'center'})}");await p.screenshot(path='e6_2.jpg',type='jpeg',quality=60)
        print(await p.evaluate("()=>{const a="+ART+";return [...a.querySelectorAll('[data-act]')].map(e=>e.dataset.act+':'+(e.dataset.v||'')+':'+e.innerText.slice(0,20).replace(/\\n/g,' ')).join(' | ')}"))
        await p.evaluate("()=>{const a="+ART+";const b=a.querySelector('[data-act=ppStake][data-v=\"25\"]');b&&b.click()}");await p.wait_for_timeout(300)
        await p.evaluate("()=>{const a="+ART+";a.scrollIntoView({block:'center'})}");await p.screenshot(path='e6_3.jpg',type='jpeg',quality=60)
        print('lock',await p.evaluate("()=>{const b=document.querySelector('[data-act=ppAll]');if(b){const r=b.getBoundingClientRect();b.click();return b.innerText+' y='+r.top}return null}"))
        await p.wait_for_timeout(600)
        await p.evaluate("()=>{const a="+ART+";a.scrollIntoView({block:'center'})}");await p.screenshot(path='e6_4.jpg',type='jpeg',quality=60)
        await p.evaluate("()=>window.scrollTo(0,0)");await p.screenshot(path='e6_5.jpg',type='jpeg',quality=60)
        await b.close()
asyncio.run(main())
