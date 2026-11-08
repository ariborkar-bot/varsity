/* Run on any https://www.maxpreps.com page. See merge.py for the whole process.
   Polite: one request at a time, 250 ms apart (about 10 minutes for a season). */
window.__DONE=0;(async()=>{
const CITIES=new Set('san-diego chula-vista escondido oceanside carlsbad el-cajon la-mesa spring-valley santee poway vista san-marcos encinitas del-mar solana-beach national-city imperial-beach coronado ramona valley-center fallbrook bonita lakeside alpine julian borrego-springs campo jamul la-jolla rancho-santa-fe bonsall calexico el-centro brawley imperial holtville calipatria blythe san-ysidro lemon-grove cardiff cardiff-by-the-sea pauma-valley warner-springs pine-valley descanso potrero boulevard ocotillo seeley heber westmorland niland winterhaven'.split(' '));
const START='/ca/san-diego/clairemont-captains/football/', LAST={m:10,d:31};   // last date of the regular season to read
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const dec=async u=>{const t=await (await fetch(u)).text();let o='';const re=/self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)/g;let m;while(m=re.exec(t)){try{o+=JSON.parse('"'+m[1]+'"')}catch(e){}}return o};
const stats=d=>{const k=d.indexOf('{"teams":[');if(k<0)return null;const ls=d.lastIndexOf('\n',k)+1,le=d.indexOf('\n',k);const line=d.slice(ls,le);return JSON.parse(line.slice(line.indexOf(':')+1))[3]};
const gz=async obj=>{const s=new Blob([JSON.stringify(obj)]).stream().pipeThrough(new CompressionStream('gzip'));const b=new Uint8Array(await new Response(s).arrayBuffer());let bin='';for(let i=0;i<b.length;i+=8192)bin+=String.fromCharCode(...b.subarray(i,i+8192));return btoa(bin)};
/* 1. teams and games */
const todo=[START],seen=new Set(),games=new Map();
while(todo.length){const team=todo.shift();if(seen.has(team))continue;seen.add(team);
  const doc=new DOMParser().parseFromString(await (await fetch(team+'schedule/')).text(),'text/html');
  for(const tr of doc.querySelectorAll('tr')){const as=[...tr.querySelectorAll('a')],box=as.find(a=>/box score/i.test(a.textContent));
    for(const a of as){const m=(a.getAttribute('href')||'').match(/^(?:https:\/\/www\.maxpreps\.com)?(\/ca\/([^/]+)\/[^/]+\/football\/)$/);if(m&&CITIES.has(m[2])&&!seen.has(m[1])&&!todo.includes(m[1]))todo.push(m[1])}
    if(box){const h=box.getAttribute('href').replace('https://www.maxpreps.com','');const dm=h.match(/\/(\d+)-(\d+)-20\d\d\//);if(dm&&(+dm[1]===11&&+dm[2]>=1&&+dm[2]<=9))games.set(h.split('?c=')[1],h)}}
  await sleep(250)}
console.log('teams',seen.size,'games',games.size);
/* 2. box scores: 23 numbers per player in the app's KEYS order (passYd ... punts) */
const out={};
for(const [c,h] of games){try{const o=stats(await dec(h+'&tab=Stats'));const g={d:(h.match(/\/(\d+-\d+-20\d\d)\//)||[])[1],h,t:[]};
  if(!o)g.nostats=1;else for(const tm of o.teams){const S=o.statsByTeamId[tm.id],P={};
    if(S)for(const grp of S.groups)for(const sg of grp.subgroups){const st=sg.stats;if(!st)continue;const N=st.columns.map(c=>c.name);
      for(const r of st.rows||[]){const nc=r.columns[N.indexOf('Name')];if(!nc||!nc.href)continue;const m=nc.href.match(/athletes\/([^/]+)\/\?careerid=(\w+)/);if(!m)continue;
        const p=P[m[1]+'|'+m[2]]||(P[m[1]+'|'+m[2]]={n:nc.value,a:new Array(23).fill(0)}),a=p.a,v=n=>{const i=N.indexOf(n);const x=i<0?0:parseFloat(r.columns[i].value);return isNaN(x)?0:x};
        switch(sg.name){case 'Passing':a[0]+=v('PassingYards');a[1]+=v('PassingTD');a[2]+=v('PassingInt');break;
          case 'Rushing':a[3]+=v('RushingYards');a[4]+=v('RushingTDNum');break;
          case 'Receiving':a[5]+=v('ReceivingNum');a[6]+=v('ReceivingYards');a[7]+=v('ReceivingTDNum');break;
          case 'Offensive Fumbles and Pancake Blocks':a[8]+=v('OffensiveFumblesLost');break;
          case 'Tackles':a[9]+=v('TotalTackles');break;
          case 'Sacks':a[10]+=v('Sacks');break;
          case 'Defensive Statistics':a[11]+=v('INTs');a[12]+=v('CausedFumbles');a[13]+=v('FumbleRecoveries');break;
          case 'Touchdowns':a[14]+=v('FumbleReturnedTDNum')+v('IntReturnedTDNum');a[15]+=v('PuntReturnedTDNum')+v('KickoffReturnedTDNum');break;
          case 'PATs and Field Goals':{const pm=v('PATKickingMade'),fm=v('FGMade');a[16]+=pm;a[17]+=v('PATKickingAtt')-pm;a[18]+=fm;a[19]+=v('FGAttempted')-fm;break}
          case 'Punts':a[20]+=v('PuntYards');a[21]+=v('PuntInside20');a[22]+=v('PuntNum');break}}}
    g.t.push({l:tm.label,p:Object.entries(P).filter(([k,p])=>p.a.some(x=>x)).map(([k,p])=>{let l=22;while(l>=0&&!p.a[l])l--;return [k,p.n,p.a.slice(0,l+1)]})})}
  out[c]=g}catch(e){console.warn(h,e)}await sleep(250)}
/* 3. rosters: career id -> [name, class, positions, team] */
const ros={};
for(const team of seen){try{const doc=new DOMParser().parseFromString(await (await fetch(team+'roster/')).text(),'text/html');
  for(const r of doc.querySelectorAll('tr')){const a=r.querySelector('a[href*="careerid"]');if(!a)continue;const c=[...r.children].map(x=>x.textContent.trim()),m=a.getAttribute('href').match(/careerid=(\w+)/);if(m)ros[m[1]]=[c[1],c[2],c[3],team]}}catch(e){console.warn(team,e)}await sleep(250)}
window.__Z=await gz(out);window.__ZR=await gz(ros);window.__DONE=1;console.log('done: window.__Z',__Z.length,'window.__ZR',__ZR.length);
})();
