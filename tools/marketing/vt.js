(()=>{const rNow=performance.now.bind(performance),rDate=Date.now,rRAF=requestAnimationFrame.bind(window),rST=setTimeout.bind(window),rSI=setInterval.bind(window);
let on=false,vt=0,base=0,dbase=0,q=[],tq=[],tid=1e6;
window.__vt={get on(){return on},start(){vt=rNow();base=vt;dbase=rDate();on=true;document.getAnimations().forEach(a=>{try{a.pause()}catch(e){}})}};
performance.now=()=>on?vt:rNow();
Date.now=()=>on?dbase+(vt-base):rDate();
window.requestAnimationFrame=cb=>{if(!on)return rRAF(cb);q.push(cb);return q.length};
window.setTimeout=(f,ms,...a)=>{if(!on)return rST(f,ms,...a);const id=++tid;tq.push({id,due:vt+(+ms||0),f,a});return id};
const rCT=clearTimeout.bind(window);window.clearTimeout=id=>{tq=tq.filter(x=>x.id!==id);rCT(id)};
window.__step=ms=>{vt+=ms;
  for(let guard=0;guard<50;guard++){const due=tq.filter(x=>x.due<=vt).sort((a,b)=>a.due-b.due);if(!due.length)break;tq=tq.filter(x=>x.due>vt);due.forEach(x=>{try{typeof x.f==='function'?x.f(...x.a):eval(x.f)}catch(e){console.error(e)}})}
  const cbs=q.splice(0);cbs.forEach(cb=>{try{cb(vt)}catch(e){console.error(e)}});
  document.getAnimations().forEach(a=>{try{if(a.playState!=='paused')a.pause();const d=a.effect&&a.effect.getComputedTiming();a.currentTime=(a.currentTime||0)+ms}catch(e){}});
};
})();
