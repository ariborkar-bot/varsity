import asyncio, os, json, random, shutil, sys
from playwright.async_api import async_playwright
APP='file:///home/claude/mk/app/varsity-football.html'
OUT='/home/claude/mk/clips'
FIRST=['Ty','Cole','Zane','Reggie','Bryson','Jayce','Kellen','Amari','Desmond','Rocco','Luca','Ashton','Darius','Emmett','Grady','Hayden','Jett','Keon','Landon','Marco','Nate','Otis','Pablo','Reid','Sawyer','Tanner','Uriel','Vince','Wes','Yusuf','Brayden','Chase','Deacon','Easton','Finn','Gage','Holden','Ivan','Jonah','Kian','Jalen','Marcus','Tyler','Isaiah','Bryce','Cameron','Elijah','Jaylen','Mason','Gavin','Xavier','Dominic','Caden','Logan','Andre','Mateo','Josiah','Kai','Trey','Nico','Jordan','Malik','Carter','Brody','Damian','Roman','Tristan','Zion','Owen','Diego','Hudson','Ezra','Miles','Jace','Aiden','Rylan','Kobe','Quinn','Devin','Santi']
LAST=['Kerr','Lyons','Maddox','Nash','Oliver','Pratt','Quintero','Rowe','Stokes','Tate','Underwood','Vance','Walsh','York','Zamora','Abbott','Baird','Conley','Drake','Ellis','Frost','Gallo','Hale','Ingram','Jordan','Keane','Lowe','Mercer','Noble','Ochoa','Payne','Rhodes','Sharp','Tobin','Upton','Valdez','Ware','Young','Zeller','Archer','Brooks','Reyes','Carter','Hayes','Morales','Bennett','Coleman','Ortiz','Sullivan','Price','Jenkins','Ramos','Foster','Vega','Hughes','Delgado','Wallace','Navarro','Griffin','Castillo','Porter','Mendoza','Russell','Flores','Holland','Cruz','Barnes','Silva','Webb','Rios','Pierce','Torres','Dixon','Salazar','Grant','Molina','Harper','Lopez','Wade','Fields']
FAKE="""()=>{const F=%s,L=%s;let h=s=>{let x=7;for(const c of s)x=(x*31+c.charCodeAt(0))>>>0;return x};
 const seen=new Set();for(const p of players()){if(!p.mp)continue;let k=h(p.key.replace(/x$/,'').replace(/[od]$/,'')),n;let i=0;const base=p.key.replace(/x$/,'').replace(/[od]$/,'');if(!window.__nm)window.__nm={};if(window.__nm[base]){p.name=window.__nm[base];continue}do{n=F[(k+i*13)%%F.length]+' '+L[(Math.floor(k/97)+i*7)%%L.length];i++}while(seen.has(n)&&i<400);seen.add(n);window.__nm[base]=n;p.name=n}
 try{const pr=S.profiles[ME.uid];if(pr)pr.name='Jordan Reyes'}catch(e){}; if(typeof T10S!=='undefined')T10S=null;try{POTW_C=null}catch(e){};try{_tickRev=-1}catch(e){}; render()}""" % (json.dumps(FIRST),json.dumps(LAST))
class Rec:
    def __init__(s,page): s.p=page
    async def frames(s,name,n,each=None,ms=1000/30):
        d=os.path.join(OUT,name); shutil.rmtree(d,ignore_errors=True); os.makedirs(d)
        for i in range(n):
            if each: await each(i)
            await s.p.evaluate(f"()=>__step({ms})")
            await s.p.screenshot(path=f'{d}/f{i:04d}.jpg',type='jpeg',quality=92)
        print(name,n,'frames')
async def newpage(b,w=390,h=844):
    ctx=await b.new_context(viewport={'width':w,'height':h},device_scale_factor=2.5,has_touch=False)
    await ctx.add_init_script(path='/home/claude/mk/vt.js')
    p=await ctx.new_page(); p.on('pageerror',lambda e:print('ERR',e))
    await p.goto(APP); await p.wait_for_timeout(2200)
    await p.evaluate(FAKE); await p.wait_for_timeout(300)
    return p
