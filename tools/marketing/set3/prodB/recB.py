import asyncio,os,sys,json
sys.path.insert(0,'/home/claude/mk')
os.environ['REAL']='1'
from rec import *
SETUP="""async()=>{const u=ME.uid;const pr={name:'you',role:'fan',school:'',v:2,joinedAt:Date.now()-86400000*70};try{await setDoc('profiles/'+u,pr)}catch(e){};try{localStorage.setItem('gsd-demo-profile',JSON.stringify(pr))}catch(e){};S.profiles[u]=Object.assign({id:u},pr);
 try{if(typeof _plCache!=='undefined')_plCache=null}catch(e){}
 document.querySelectorAll('.toast,.tst').forEach(e=>e.remove());const c=document.querySelector('#cfm');if(c)c.hidden=true;render()}"""
async def pageB(b,app=APPF):
    p=await newpage(b,app=app,fake=False)
    await p.evaluate(SETUP);await p.wait_for_timeout(400)
    return p
async def go(p,js,wait=700):
    await p.evaluate("()=>{"+js+"}");await p.wait_for_timeout(wait)
