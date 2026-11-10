const S=document.getElementById('stage');
const cl=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const E={lin:x=>x,out:x=>1-Math.pow(1-x,3),in:x=>x*x*x,io:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,back:x=>{const c1=2.2,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)},el:x=>x===0||x===1?x:Math.pow(2,-10*x)*Math.sin((x*10-.75)*2.094)+1};
const seg=(t,a,b,e='out')=>E[e](cl((t-a)/(b-a)));
const lerp=(a,b,k)=>a+(b-a)*k;
function el(html,cls='abs',parent=S){const d=document.createElement('div');d.className=cls;d.innerHTML=html;parent.appendChild(d);return d}
function tf(e,{x=0,y=0,s=1,r=0,o=1,blur=0,sx=null,sy=null}={}){e.style.transform=`translate(${x}px,${y}px) rotate(${r}deg) scale(${sx??s},${sy??s})`;e.style.opacity=o;e.style.filter=blur?`blur(${blur}px)`:'none'}
async function setImg(img,src){if(img.dataset.src!==src){img.src=src;img.dataset.src=src;try{await img.decode()}catch(e){}}}
const clip=(name,i)=>`/home/claude/mk/clips/${name}/f${String(Math.max(0,Math.round(i))).padStart(4,'0')}.jpg`;
/* piecewise time -> frame map: [[t,frame],...] */
function fmap(t,pts){if(t<=pts[0][0])return pts[0][1];for(let i=1;i<pts.length;i++){const[a,fa]=pts[i-1],[b,fb]=pts[i];if(t<=b)return fa+(fb-fa)*(t-a)/(b-a)}return pts[pts.length-1][1]}
/* grain */
const G=document.createElement('canvas');G.id='grain';G.width=540;G.height=960;S.appendChild(G);const gx=G.getContext('2d');const GT=[];
for(let k=0;k<6;k++){const d=gx.createImageData(540,960);for(let i=0;i<d.data.length;i+=4){const v=Math.random()*255;d.data[i]=d.data[i+1]=d.data[i+2]=v;d.data[i+3]=255}GT.push(d)}
function grain(t){gx.putImageData(GT[Math.floor(t*30)%GT.length],0,0)}
/* handheld drift (phone held in a hand), impact shake, beat punch */
const hand=(t,a=1)=>({x:(Math.sin(t*1.7)*7+Math.sin(t*4.3+1)*2.5)*a,y:(Math.cos(t*1.3)*6+Math.sin(t*3.1)*2)*a,r:(Math.sin(t*.9)*.4+Math.sin(t*2.3)*.12)*a});
const hit=(t,at,amp=22,dur=.4)=>{const k=t-at;if(k<0||k>dur)return{x:0,y:0,r:0};const f=Math.pow(1-k/dur,2);return{x:Math.sin(k*95)*amp*f,y:Math.cos(k*73)*amp*f,r:Math.sin(k*60)*amp*.04*f}};
const punch=(t,beats,amt=.05,dur=.22)=>{let s=0;for(const b of beats){const k=t-b;if(k>=0&&k<dur)s=Math.max(s,amt*Math.pow(1-k/dur,2))}return s};
const flashAt=(t,list,dur=.18)=>{let o=0;for(const[a,amt]of list){const k=t-a;if(k>=0&&k<dur)o=Math.max(o,amt*(1-k/dur))}return o};
const FL=el('','');FL.id='flash';
window.__ready=document.fonts.ready.then(()=>Promise.all([...document.images].map(i=>i.decode().catch(()=>0))));
