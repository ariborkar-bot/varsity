const S=document.getElementById('stage');
const cl=(x,a=0,b=1)=>Math.max(a,Math.min(b,x));
const E={lin:x=>x,out:x=>1-Math.pow(1-x,3),in:x=>x*x*x,io:x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2,back:x=>{const c1=1.9,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)},el:x=>x===0||x===1?x:Math.pow(2,-10*x)*Math.sin((x*10-.75)*2.094)+1};
const seg=(t,a,b,e='out')=>E[e](cl((t-a)/(b-a)));
const lerp=(a,b,k)=>a+(b-a)*k;
function el(html,cls='abs',parent=S){const d=document.createElement('div');d.className=cls;d.innerHTML=html;parent.appendChild(d);return d}
function st(e,o){for(const k in o)e.style[k]=o[k]}
function tf(e,{x=0,y=0,s=1,r=0,o=1,blur=0,sx=null,sy=null}={}){e.style.transform=`translate(${x}px,${y}px) rotate(${r}deg) scale(${sx??s},${sy??s})`;e.style.opacity=o;e.style.filter=blur?`blur(${blur}px)`:'none'}
/* phone with a screen image (clip frames or a tall still) */
function phone(){const p=el('<div class="island"></div><div class="scr"><img></div>','phone');p.img=p.querySelector('img');p.scr=p.querySelector('.scr');return p}
const IMC={};function pre(src){if(!IMC[src]){const i=new Image();i.src=src;IMC[src]=i}return IMC[src]}
async function setImg(img,src){if(img.dataset.src!==src){img.src=src;img.dataset.src=src;try{await img.decode()}catch(e){}}}
const clip=(name,i)=>`/home/claude/mk/clips/${name}/f${String(Math.max(0,i)).padStart(4,'0')}.jpg`;
/* grain */
const G=document.createElement('canvas');G.id='grain';G.width=540;G.height=960;S.appendChild(G);const gx=G.getContext('2d');const GT=[];
for(let k=0;k<6;k++){const d=gx.createImageData(540,960);for(let i=0;i<d.data.length;i+=4){const v=Math.random()*255;d.data[i]=d.data[i+1]=d.data[i+2]=v;d.data[i+3]=255}GT.push(d)}
function grain(t){gx.putImageData(GT[Math.floor(t*30)%GT.length],0,0)}
/* handheld camera drift */
const shake=(t,a=1)=>({x:Math.sin(t*1.7)*6*a+Math.sin(t*4.3)*2*a,y:Math.cos(t*1.3)*5*a+Math.sin(t*3.1)*2*a,r:Math.sin(t*.9)*.35*a});
/* impact shake that decays */
const kick=(t,at,amp=18,dur=.35)=>{const k=t-at;if(k<0||k>dur)return{x:0,y:0};const f=1-k/dur;return{x:Math.sin(k*90)*amp*f,y:Math.cos(k*70)*amp*f}};
/* word-by-word caption: words appear on their times */
function words(e,t,list){e.innerHTML=list.map(([w,at,c])=>{const k=cl((t-at)/.12);return `<span style="display:inline-block;opacity:${k>0?1:0};transform:scale(${k>0?lerp(1.35,1,E.out(k)):1});${c?`color:${c}`:''}">${w}</span>`}).join(' ')}
window.__ready=document.fonts.ready;
