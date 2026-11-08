/* Run on any https://www.maxpreps.com page (in the browser pane). Reads every San Diego Section box score from the start of the
   season through Nov 9 and keeps ONLY tackles for loss and passes defensed (the two stats the app added in v301).
   Result: window.__T (text), window.__TL (team labels), window.__TC (checksum). Poll window.__DONE (1 when finished).
   Text format: one line per player: teamIndex(base36)|careerId|entries, entries are 3 chars each: week(base36) tfl(base36) pbu(base36). */
window.__DONE=0;window.__PROG='start';(async()=>{
const CITIES=new Set('san-diego chula-vista escondido oceanside carlsbad el-cajon la-mesa spring-valley santee poway vista san-marcos encinitas del-mar solana-beach national-city imperial-beach coronado ramona valley-center fallbrook bonita lakeside alpine julian borrego-springs campo jamul la-jolla rancho-santa-fe bonsall calexico el-centro brawley imperial holtville calipatria blythe san-ysidro lemon-grove cardiff cardiff-by-the-sea pauma-valley warner-springs pine-valley descanso potrero boulevard ocotillo seeley heber westmorland niland winterhaven'.split(' '));
const START='/ca/san-diego/clairemont-captains/football/';
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const dec=async u=>{const t=await (await fetch(u)).text();let o='';const re=/self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)/g;let m;while(m=re.exec(t)){try{o+=JSON.parse('"'+m[1]+'"')}catch(e){}}return o};
const stats=d=>{const k=d.indexOf('{"teams":[');if(k<0)return null;const ls=d.lastIndexOf('\n',k)+1,le=d.indexOf('\n',k);const line=d.slice(ls,le);return JSON.parse(line.slice(line.indexOf(':')+1))[3]};
const wk=(m,d,y)=>Math.floor((Date.UTC(y,m-1,d)-Date.UTC(2026,7,17))/864e5/7)+1;
const todo=[START],seen=new Set(),games=new Map();
while(todo.length){const team=todo.shift();if(seen.has(team))continue;seen.add(team);
  const doc=new DOMParser().parseFromString(await (await fetch(team+'schedule/')).text(),'text/html');
  for(const tr of doc.querySelectorAll('tr')){const as=[...tr.querySelectorAll('a')],box=as.find(a=>/box score/i.test(a.textContent));
    for(const a of as){const m=(a.getAttribute('href')||'').match(/^(?:https:\/\/www\.maxpreps\.com)?(\/ca\/([^/]+)\/[^/]+\/football\/)$/);if(m&&CITIES.has(m[2])&&!seen.has(m[1])&&!todo.includes(m[1]))todo.push(m[1])}
    if(box){const h=box.getAttribute('href').replace('https://www.maxpreps.com','');const dm=h.match(/\/(\d+)-(\d+)-(20\d\d)\//);if(dm&&+dm[3]===2026&&(+dm[1]<11&&+dm[1]>=8||(+dm[1]===11&&+dm[2]<=9)))games.set(h.split('?c=')[1],[h,wk(+dm[1],+dm[2],+dm[3])])}}
  await sleep(200)}
window.__PROG='teams '+seen.size+' games '+games.size;
const labels=[],P=new Map();let n=0,nos=0;
for(const [c,[h,w]] of games){try{const o=stats(await dec(h+'&tab=Stats'));
  if(!o)nos++;else for(const tm of o.teams){const S=o.statsByTeamId[tm.id];if(!S)continue;
    const lb=tm.label.replace(/\s*\([^)]*\)\s*$/,'');let ti=labels.indexOf(lb);if(ti<0){ti=labels.length;labels.push(lb)}
    for(const grp of S.groups)for(const sg of grp.subgroups){const st=sg.stats;if(!st)continue;const N=st.columns.map(c=>c.name);
      const col=sg.name==='Tackles'?'TacklesForLoss':sg.name==='Defensive Statistics'?'PassesDefensed':null;if(!col)continue;const ci=N.indexOf(col);if(ci<0)continue;
      for(const r of st.rows||[]){const nc=r.columns[N.indexOf('Name')];if(!nc||!nc.href)continue;const m=nc.href.match(/athletes\/[^/]+\/\?careerid=(\w+)/);if(!m)continue;
        const v=parseFloat(r.columns[ci].value)||0;if(!v)continue;
        const key=ti+'|'+m[1],e=P.get(key)||P.set(key,{}).get(key),slot=e[w]||(e[w]=[0,0]);slot[sg.name==='Tackles'?0:1]+=v}}}
  n++}catch(e){console.warn(h,e)}
  window.__PROG='boxes '+n+'/'+games.size;await sleep(200)}
const lines=[];let ck=0;
for(const [key,e] of P){const [ti,car]=key.split('|');let s='';for(const w of Object.keys(e).map(Number).sort((a,b)=>a-b)){const [t,p]=e[w];s+=w.toString(36)+t.toString(36)+p.toString(36);ck+=w*7+t*13+p*17}lines.push((+ti).toString(36)+'|'+car+'|'+s)}
window.__T=lines.join('\n');window.__TL=labels.join('|');window.__TC=[lines.length,ck,nos,games.size].join(',');window.__DONE=1;window.__PROG='done';
})();
