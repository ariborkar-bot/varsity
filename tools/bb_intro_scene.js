  /* 3. BASKETBALL: a hoop fades in on the right, the dunker sprints in, takes off over the defender and posterizes him.
        Every phase is a Web Animations track pinned to one shared clock (startTime), so timers never make it stutter. */
  const T_RUN=2950,B0=document.timeline.currentTime;
  run.style.width=drun.style.width='clamp(112px,29vw,178px)';
  const wr=word.getBoundingClientRect(),pw=run.clientWidth,elTop=run.offsetTop;
  const leftEdge=-sr.left-pw-20,rightEdge=vw-sr.left+20;
  const cbz=(x1,y1,x2,y2)=>t=>{if(t<=0)return 0;if(t>=1)return 1;let u=t;
    for(let i=0;i<9;i++){const m=1-u,x=3*m*m*u*x1+3*m*u*u*x2+u*u*u,d=3*m*m*x1+6*m*u*(x2-x1)+3*u*u*(1-x2);if(Math.abs(d)<1e-6)break;u=clamp(u-(x-t)/d,0,1)}
    const m=1-u;return 3*m*m*u*y1+3*m*u*u*y2+u*u*u};
  /* one animation track: pts = [[ms, value], ...]; eas = easing of each segment; st = start on the shared clock (ms before speed-up) */
  const trk=(n,prop,pts,eas,st,fill)=>{const T=pts[pts.length-1][0];
    const kf=pts.map((p,i)=>{const k={offset:p[0]/T,[prop]:p[1]};if(i<pts.length-1)k.easing=(eas&&(eas[i]||eas[eas.length-1]))||'linear';return k});
    const a=n.animate(kf,{duration:T,fill:fill||'forwards',easing:'linear'});a.playbackRate=RATE;a.startTime=B0+st/RATE;anims.push(a);return a};
  const rot0=n=>{const m=getComputedStyle(n).transform;if(!m||m==='none')return 0;const v=m.slice(m.indexOf('(')+1,-1).split(',').map(Number);return Math.atan2(v[1],v[0])*57.2958};
  const limb=(root,sel,pts,eas,st)=>{const n=root.querySelector(sel);if(!n)return;const c=rot0(n);return trk(n,'transform',pts.map(([t,a],i)=>[t,'rotate('+(i?a:c)+'deg)']),eas,st)};

  /* basketball look: bare heads, tank tops, shorts, sneakers, a real basketball in the hand */
  const bbLook=(root,hair,shoe,band)=>{const sv=root.querySelector('svg'),pl=sv.querySelector('.pl');
    pl.querySelectorAll(':scope > path').forEach(p=>p.remove());
    const hd=pl.querySelector(':scope > circle');hd.setAttribute('r','10.6');hd.setAttribute('cy','27');hd.setAttribute('fill','#D9A47A');
    hd.insertAdjacentHTML('afterend',`<path d="M54.2 26Q53.6 14.6 65 15Q76.6 15.4 76 26Q72.4 20.6 65 21.4Q58 22 54.2 26Z" fill="${hair}"/><circle cx="71.4" cy="27" r="1.25" fill="#2a1a10"/>${band?`<path d="M54.6 23.6Q65 19.8 75.8 23.6" stroke="${band}" stroke-width="2.4" fill="none" stroke-linecap="round"/>`:''}`);
    sv.querySelectorAll('.aB>path,.aN>path').forEach(p=>{p.setAttribute('stroke','#D9A47A');p.setAttribute('stroke-width','6.4')});
    sv.querySelectorAll('.sB>path,.sN>path').forEach(p=>{p.setAttribute('stroke','#D9A47A');p.setAttribute('stroke-width','6.8')});
    sv.querySelectorAll('.sB>ellipse,.sN>ellipse').forEach(e=>e.setAttribute('fill',shoe));
    const bl=sv.querySelector('.bl');if(bl)bl.innerHTML='<circle cx="61" cy="76" r="8.2" fill="#E8741C" stroke="#7a3406" stroke-width=".9"/><path d="M52.8 76H69.2M61 67.8V84.2M55.2 69.6Q58.8 76 55.2 82.4M66.8 69.6Q63.2 76 66.8 82.4" stroke="#4a1f05" stroke-width=".8" fill="none"/>'};
  bbLook(run,'#1c1c24','#fff','#fff');bbLook(drun,'#2a1c14','#FFC23D',null);
  const BALLSVG='<svg viewBox="0 0 24 24" style="width:100%;height:100%;display:block"><defs><radialGradient id="inbg" cx="36%" cy="30%" r="75%"><stop offset="0" stop-color="#FFB45E"/><stop offset=".55" stop-color="#E8741C"/><stop offset="1" stop-color="#9A4308"/></radialGradient></defs><circle cx="12" cy="12" r="11.2" fill="url(#inbg)" stroke="#6b2d06" stroke-width=".7"/><g fill="none" stroke="#4a1f05" stroke-width="1" stroke-linecap="round"><path d="M1 12H23M12 1V23"/><path d="M4 4Q9 12 4 20M20 4Q15 12 20 20"/></g></svg>';
  const BW=pw*.165;ball.innerHTML=BALLSVG;ball.style.width=ball.style.height=BW+'px';
  run.style.transform=drun.style.transform='none';run.style.zIndex=3;drun.style.zIndex=2;
  drun.querySelector('.in-fl').style.transformOrigin='50% 60%';

  /* ----- the numbers ----- */
  const FEET=elTop+pw*.87,LIFT=pw*1.42,F=780,HANG=380,DROP=430,SETTLE=640,TOTAL=F+HANG+DROP+SETTLE;
  const rimR=pw*.25,rimX=Math.min(W-Math.max(pw*.62,52),wr.right-sr.left+pw*.5);
  const rimY=elTop+pw*.1-LIFT,bw=Math.max(6,pw*.07),bh=pw*.74,bx=rimX+rimR+pw*.07,by=rimY-bh*.58;
  const ex=cbz(.3,.4,.6,1),EX='cubic-bezier(.3,.4,.6,1)',EY='cubic-bezier(.14,.62,.3,1)',GRAV='cubic-bezier(.55,0,.9,.65)';
  const dunkLeft=rimX-pw*.52,VR=pw*.0058,Df=Math.min(.75*VR*F,pw*1.75),takeLeft=dunkLeft-Df;   /* take off on screen, so the run-up is seen */
  const RUN_IN=clamp((takeLeft-leftEdge)/(1.33*Df/F),700,1400),T_TO=T_RUN+RUN_IN;
  const tX=.5*F,fc=ex(tX/F),defLeft=takeLeft+fc*Df;          /* the defender stands where the dunker is passing at tX */
  const Jh=pw*.46,T_DA=T_TO-220,CT=220+tX;                    /* defender timeline starts 220 ms before take-off; CT = contact */

  /* the hoop: back half (board, bracket, back of the rim) sits behind the players, front of the rim and the net in front of the ball */
  const hb=document.createElement('div'),hf=document.createElement('div');
  const hs='position:absolute;left:0;top:0;width:'+W+'px;height:'+H+'px;pointer-events:none;opacity:0';
  hb.style.cssText=hf.style.cssText=hs;
  const arc=(sw)=>`M${rimX-rimR} ${rimY}A${rimR} ${rimR*.22} 0 0 ${sw} ${rimX+rimR} ${rimY}`;
  let nd='';const bw2=rimR*.5,NH=pw*.4,tp=i=>rimX-rimR+i*rimR/2,bt=i=>rimX-bw2+i*bw2/2;
  for(let i=0;i<4;i++)nd+=`M${tp(i)} ${rimY}L${bt(i+1)} ${rimY+NH}M${tp(i+1)} ${rimY}L${bt(i)} ${rimY+NH}`;
  nd+=`M${rimX-rimR*.78} ${rimY+NH*.4}Q${rimX} ${rimY+NH*.4+rimR*.16} ${rimX+rimR*.78} ${rimY+NH*.4}M${rimX-rimR*.62} ${rimY+NH*.72}Q${rimX} ${rimY+NH*.72+rimR*.14} ${rimX+rimR*.62} ${rimY+NH*.72}`;
  const svgO=`<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" style="position:absolute;left:0;top:0;overflow:visible">`;
  hb.innerHTML=svgO+`<defs><linearGradient id="inGl" x1="0" x2="1"><stop offset="0" stop-color="#eaf3ff" stop-opacity=".8"/><stop offset="1" stop-color="#7fa8ff" stop-opacity=".38"/></linearGradient><linearGradient id="inPole" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#9db6e6"/><stop offset="1" stop-color="#9db6e6" stop-opacity="0"/></linearGradient></defs>
    <rect x="${bx+bw+1}" y="${by+bh*.7}" width="4" height="${FEET-(by+bh*.7)}" fill="url(#inPole)"/>
    <rect x="${rimX+rimR-1}" y="${rimY-1.8}" width="${bx-(rimX+rimR)+2}" height="3.6" rx="1.2" fill="#c9d6f2"/>
    <rect x="${bx}" y="${by}" width="${bw}" height="${bh}" rx="2.5" fill="url(#inGl)" stroke="#e2eeff" stroke-width="1.4"/>
    <rect id="inGlow" x="${bx-3}" y="${by-3}" width="${bw+6}" height="${bh+6}" rx="5" fill="#fff" opacity="0"/>
    <g class="rimB" style="transform-origin:${bx}px ${rimY}px"><path d="${arc(1)}" stroke="#ff7a1a" stroke-opacity=".35" stroke-width="7" fill="none"/><path d="${arc(1)}" stroke="#ff8a2e" stroke-width="3.2" stroke-linecap="round" fill="none"/></g></svg>`;
  hf.innerHTML=svgO+`<g class="rimF" style="transform-origin:${bx}px ${rimY}px"><g class="net" style="transform-origin:${rimX}px ${rimY}px"><path d="${nd}" stroke="#fff" stroke-opacity=".82" stroke-width="1.15" fill="none" stroke-linecap="round"/></g>
    <path d="${arc(0)}" stroke="#ff7a1a" stroke-opacity=".35" stroke-width="7" fill="none"/><path d="${arc(0)}" stroke="#ff9a3e" stroke-width="3.4" stroke-linecap="round" fill="none"/></g></svg>`;
  stage.insertBefore(hb,run);ball.after(hf);
  [hb,hf].forEach(n=>trk(n,'opacity',[[0,0],[500,1]],['ease-out'],T_RUN-350,'both'));
  trk(tag,'opacity',[[0,1],[260,0]],null,T_RUN+RUN_IN-420,'both');

  /* ----- run-in: the dunker dribbles in from the left, the defender slides in from the right and sets up under the hoop ----- */
  const cycRun=cycle(run,1),cycDef=cycle(drun,0);
  trk(run,'translate',[[0,leftEdge+'px 0px'],[RUN_IN,takeLeft+'px 0px']],null,T_RUN,'both');
  trk(drun,'translate',[[0,rightEdge+'px 0px'],[RUN_IN-220,defLeft+'px 0px']],['cubic-bezier(.2,.5,.5,1)'],T_RUN,'both');
  speedOn=true;
  at(T_RUN+RUN_IN-120,()=>{speedOn=false});

  /* ----- defender: sets his feet, jumps late, gets jumped over and falls on his back ----- */
  at(T_DA,()=>{
    cycDef.forEach(a=>a.cancel());
    const d=drun,sh=d.querySelector('.in-sh'),fl=d.querySelector('.in-fl'),s=T_DA;
    /* feet: stance, jump, tuck, then kicked up as he goes over */
    limb(d,'.tN',[[0],[200,-30],[CT-110,-48],[CT,-40],[CT+210,-78],[CT+520,-22],[CT+760,-34]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.sN',[[0],[200,50],[CT-110,38],[CT,44],[CT+210,24],[CT+520,10],[CT+760,22]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.tB',[[0],[200,12],[CT-110,-18],[CT,-14],[CT+210,-50],[CT+520,-6],[CT+760,-16]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.sB',[[0],[200,44],[CT-110,56],[CT,56],[CT+210,30],[CT+520,18],[CT+760,28]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    /* arms: out wide, straight up to contest, flung back */
    limb(d,'.aN',[[0],[200,-96],[CT-110,-168],[CT,-170],[CT+200,-118],[CT+520,-52],[CT+760,-74]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.fN',[[0],[200,-26],[CT-110,-4],[CT,-4],[CT+200,-36],[CT+520,-20],[CT+760,-30]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.aB',[[0],[200,-108],[CT-110,-160],[CT,-164],[CT+200,-100],[CT+520,-30],[CT+760,-48]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.fB',[[0],[200,-24],[CT-110,-6],[CT,-6],[CT+200,-40],[CT+520,-18],[CT+760,-26]],['ease-out','ease-out','linear','ease-out','ease-in-out','ease-out'],s);
    limb(d,'.pl',[[0],[200,2],[CT,-4],[CT+300,6]],['ease-out','ease-out','ease-out'],s);
    /* body: slides back a little on impact; up for the jump, down onto the floor */
    trk(d,'translate',[[0,defLeft+'px 0px'],[CT,defLeft+'px 0px'],[CT+620,(defLeft+pw*.5)+'px 0px']],['linear','cubic-bezier(.2,.7,.4,1)'],s);
    const L0=CT-30,gnd=pw*.2;
    const dy=trk(d,'transform',[[0,'translateY(0px)'],[270,'translateY(0px)'],[L0,`translateY(${-Jh}px)`],[CT+110,`translateY(${-Jh*.5}px)`],[CT+500,`translateY(${gnd}px)`],[CT+620,`translateY(${gnd-pw*.05}px)`],[CT+760,`translateY(${gnd}px)`]],
      ['linear','cubic-bezier(.1,.7,.3,1)','cubic-bezier(.4,0,.8,.6)','cubic-bezier(.45,0,.9,.6)','ease-out','ease-in'],s);
    trk(fl,'rotate',[[0,'0deg'],[CT,'0deg'],[CT+170,'34deg'],[CT+500,'101deg'],[CT+620,'93deg'],[CT+760,'101deg']],['linear','cubic-bezier(.1,.7,.3,1)','cubic-bezier(.45,0,.8,.7)','ease-out','ease-in'],s);
    /* shadow stays on the floor, then goes away once he is lying down */
    trk(sh,'translate',[[0,'0px 0px'],[270,'0px 0px'],[L0,`0px ${Jh}px`],[CT+110,`0px ${Jh*.5}px`],[CT+500,'0px 0px']],['linear','cubic-bezier(.1,.7,.3,1)','cubic-bezier(.4,0,.8,.6)','cubic-bezier(.45,0,.9,.6)'],s);
    trk(sh,'opacity',[[0,1],[CT,1],[CT+160,0]],null,s);
    /* he hits the floor: dust */
    at(CT+500-0,()=>{const x=sr.left+defLeft+pw*.5+pw*.5,y=sr.top+FEET;
      for(let j=0;j<5;j++)emit({k:'puff',add:0,x:x+R(-pw*.5,pw*.4),y:y-2,vx:R(-140,140),vy:R(-70,-10),drag:.94,life:R(500,800),sz:R(9,16),col:'150,185,245',a:.8});
      rings.push({x,y,t0:now,dur:520,r:pw*1.1,col:'170,205,255',a:.7,w:2.4,sq:.2})});
  });

  /* ----- take-off: leap, rise over the defender, jam it ----- */
  at(T_TO,()=>{
    cycRun.forEach(a=>a.cancel());
    const d=run,sh=d.querySelector('.in-sh'),s=T_TO,Y=pw;
    const landT=F+HANG+DROP;
    trk(d,'translate',[[0,takeLeft+'px 0px'],[F,dunkLeft+'px 0px'],[TOTAL,dunkLeft+'px 0px']],[EX,'linear'],s);
    const lift=[[0,0],[F,-LIFT],[F+HANG*.4,-(LIFT-pw*.07)],[F+HANG,-(LIFT-pw*.04)],[landT,0],[TOTAL,0]];
    const le=[EY,'ease-out','ease-in-out',GRAV,'linear'];
    trk(d,'transform',lift.map(([t,y])=>[t,`translateY(${y}px)`]),le,s);
    trk(sh,'translate',lift.map(([t,y])=>[t,`0px ${-y}px`]),le,s);
    trk(sh,'opacity',[[0,1],[F,.3],[F+HANG,.35],[landT,1]],[EY,'linear','ease-in'],s);
    /* legs: push off, drive the lead knee, tuck, then reach for the floor and absorb the landing */
    const lg=(sel,a)=>limb(d,sel,[[0],[130,a[0]],[F*.45,a[1]],[F,a[2]],[F+HANG,a[3]],[landT-90,a[4]],[landT+110,a[5]],[TOTAL,a[6]]],['ease-out','ease-out','ease-in-out','ease-in-out','ease-in','ease-out','ease-out'],s);
    lg('.tN',[-40,-104,-84,-64,-14,-58,-4]);lg('.sN',[58,92,66,44,6,82,6]);
    lg('.tB',[22,-6,10,4,8,-40,6]);lg('.sB',[24,100,104,76,6,86,8]);
    /* arms: ball swings back and up, locks overhead, hangs on the rim, then comes down */
    const am=(sel,a)=>limb(d,sel,[[0],[130,a[0]],[F*.55,a[1]],[F,a[2]],[F+HANG,a[3]],[landT-60,a[4]],[landT+120,a[5]],[TOTAL,a[6]]],['ease-out','ease-in-out','ease-out','linear','ease-in-out','ease-out','ease-out'],s);
    am('.aN',[26,-118,-150,-152,-96,-56,-24]);am('.fN',[-46,-34,-8,-8,-30,-60,-100]);
    am('.aB',[34,-132,-96,-80,-52,-70,-30]);am('.fB',[-60,-30,-18,-20,-40,-30,-80]);
    /* body: leans back as he rises, sinks into the landing */
    trk(d.querySelector('.pl'),'transform',[[0,`rotate(${rot0(d.querySelector('.pl'))}deg)`],[F*.4,'rotate(-2deg)'],[F,'rotate(-15deg)'],[F+HANG*.5,'rotate(-7deg)'],[F+HANG,'rotate(3deg)'],[landT,'rotate(5deg)'],[landT+110,'translateY(8px) rotate(11deg)'],[TOTAL,'translateY(0px) rotate(0deg)']],
      ['ease-out','ease-out','ease-in-out','ease-in-out','ease-in','ease-out','ease-out'],s);
    /* the ball leaves his hand at the slam and drops through the net, then bounces away */
    const bl=d.querySelector('.bl');if(bl)trk(bl,'opacity',[[0,1],[F-1,1],[F,0]],null,s);
    const bp=(x,y,r)=>`translate(${x-BW/2}px,${y-BW/2}px) rotate(${r}deg)`,fy=FEET-BW/2;
    trk(ball,'transform',[[F,bp(rimX,rimY,0)],[F+330,bp(rimX-pw*.1,fy,160)],[F+560,bp(rimX-pw*.34,fy-pw*.5,260)],[F+790,bp(rimX-pw*.56,fy,380)],[F+940,bp(rimX-pw*.7,fy-pw*.2,440)],[F+1090,bp(rimX-pw*.82,fy,500)],[F+1190,bp(rimX-pw*.9,fy-pw*.07,530)],[F+1290,bp(rimX-pw*.96,fy,550)]],
      ['cubic-bezier(.5,0,.9,.6)','ease-out','ease-in','ease-out','ease-in','ease-out','ease-in'],s);
    trk(ball,'opacity',[[0,0],[F-1,0],[F,1],[F+1300,1],[F+1550,0]],null,s,'both');
    /* rim, net and board react */
    const rimK=[[F,'rotate(0deg)'],[F+80,'rotate(7deg)'],[F+220,'rotate(-3.5deg)'],[F+360,'rotate(2deg)'],[F+520,'rotate(-.8deg)'],[F+700,'rotate(0deg)']];
    trk(hb.querySelector('.rimB'),'transform',rimK,['ease-out','ease-in-out'],s);trk(hf.querySelector('.rimF'),'transform',rimK,['ease-out','ease-in-out'],s);
    trk(hf.querySelector('.net'),'transform',[[F,'scale(1,1) skewX(0deg)'],[F+130,'scale(1.08,1.4) skewX(-6deg)'],[F+310,'scale(.96,.9) skewX(5deg)'],[F+500,'scale(1,1.06) skewX(-2deg)'],[F+700,'scale(1,1) skewX(0deg)']],['ease-out','ease-in-out'],s);
    trk(hb.querySelector('#inGlow'),'opacity',[[F-1,0],[F,.85],[F+420,0]],['ease-out'],s);
  });

  /* ----- the slam: flash, shake, sparks, V gems, letters ripple ----- */
  at(T_TO+F,()=>{
    const ix=sr.left+rimX,iy=sr.top+rimY;
    A(white,[{opacity:.5},{opacity:0}],{duration:380,easing:'ease-out',fill:'forwards'});
    rings.push({x:ix,y:iy,t0:now,dur:720,r:Math.max(CW,CH)*.55,col:'255,200,120',a:1,w:6});
    rings.push({x:ix,y:iy,t0:now+70,dur:950,r:Math.max(CW,CH)*.75,col:'255,255,255',a:.55,w:3});
    flares.push({x:ix,y:iy,t0:now,dur:760,len:Math.min(CW*.8,620)});boost=1.5;
    flash.style.left=rimX+'px';flash.style.top=rimY+'px';
    A(flash,[{opacity:1,transform:'translate(-50%,-50%) scale(.3)'},{opacity:0,transform:'translate(-50%,-50%) scale(3.2)'}],{duration:500,easing:'ease-out'});
    boom.textContent='POSTERIZED!';boom.style.left=clamp(rimX-pw*.2,pw*1.1,W-pw*1.1)+'px';boom.style.top=(rimY-pw*.62)+'px';
    A(boom,[{opacity:0,transform:'translate(-50%,-50%) scale(.3) rotate(8deg)'},{opacity:1,transform:'translate(-50%,-50%) scale(1.25) rotate(5deg)',offset:.22},{opacity:1,transform:'translate(-50%,-54%) scale(1.1) rotate(5deg)',offset:.7},{opacity:0,transform:'translate(-50%,-70%) scale(1) rotate(5deg)'}],{duration:1500,easing:'ease-out'});
    shakeEls.forEach(n=>A(n,[{translate:'0 0'},{translate:'6px 4px'},{translate:'-5px -3px'},{translate:'3px 2px'},{translate:'-1px -1px'},{translate:'0 0'}],{duration:380,fill:'none'}));
    if(navigator.vibrate)try{navigator.vibrate([30,20,50])}catch(_){}
    for(let i=0;i<38;i++){const a=R(-3.14,0.1),s=R(180,820);emit({k:'spark',x:ix,y:iy,vx:Math.cos(a)*s,vy:Math.sin(a)*s,grav:1100,drag:.965,life:R(500,1200),sz:R(1.2,3),col:i%3?'255,190,90':'255,255,255'})}
    /* V gems */
    const n=small?9:13;
    for(let i=0;i<n;i++){
      const g=document.createElement('img');g.src='logo.png';g.alt='';g.className='in-jewel';
      const sz=(small?24:32)+Math.random()*(small?30:48);g.style.width=g.style.height=sz+'px';stage.appendChild(g);
      const ang=-Math.PI*(0.05+Math.random()*.9),sp=130+Math.random()*(small?170:290);
      const mx=Math.cos(ang)*sp*.6,my=Math.sin(ang)*sp*.6,ex2=Math.cos(ang)*sp,ey2=Math.sin(ang)*sp+H*.5,rt=(Math.random()*2-1)*540,gx=rimX-sz/2,gy=rimY-sz/2;
      A(g,[{opacity:1,transform:`translate(${gx}px,${gy}px) scale(.2) rotate(0)`},{opacity:1,transform:`translate(${gx+mx}px,${gy+my}px) scale(1) rotate(${rt*.5}deg)`,offset:.35},{opacity:0,transform:`translate(${gx+ex2}px,${gy+ey2}px) scale(.8) rotate(${rt}deg)`}],
        {duration:950+Math.random()*500,delay:Math.random()*90,easing:'cubic-bezier(.2,.6,.5,1)'});
    }
    /* the shock runs through VARSITY and the logo */
    letters.forEach(l=>{const r=l.getBoundingClientRect(),dist=Math.abs(r.left-sr.left+r.width/2-rimX),dl=Math.min(dist*1.1,380),amp=clamp(26-dist*.045,8,24);
      A(l,[{transform:'translateY(0) scale(1)'},{transform:`translateY(${-amp}px) scale(1.07)`,offset:.35},{transform:'translateY(2px) scale(.99)',offset:.7},{transform:'translateY(0) scale(1)'}],{duration:520,delay:dl,fill:'none',easing:'ease-out'})});
    A(gem,[{transform:'translate(-50%,-50%) scale(1)'},{transform:'translate(-50%,-50%) scale(1.13)',offset:.3},{transform:'translate(-50%,-50%) scale(1)'}],{duration:700,fill:'none',easing:'ease-out'});
    A(halo,[{opacity:1,transform:'translate(-50%,-50%) scale(1)'},{opacity:1,transform:'translate(-50%,-50%) scale(1.4)',offset:.3},{opacity:1,transform:'translate(-50%,-50%) scale(1)'}],{duration:800,fill:'none',easing:'ease-out'});
  });

  /* ----- he lets go and lands: dust and a small thud ----- */
  at(T_TO+F+HANG+DROP,()=>{const x=sr.left+dunkLeft+pw*.5,y=sr.top+FEET;
    for(let j=0;j<6;j++)emit({k:'puff',add:0,x:x+R(-pw*.4,pw*.4),y:y-2,vx:R(-170,170),vy:R(-80,-10),drag:.94,life:R(500,850),sz:R(9,17),col:'150,185,245',a:.85});
    for(let j=0;j<10;j++)emit({k:'spark',x,y:y-4,vx:R(-280,280),vy:R(-300,-60),grav:1000,drag:.97,life:R(300,600),sz:R(1,2),col:'200,225,255'});
    rings.push({x,y,t0:now,dur:560,r:pw*1.3,col:'170,205,255',a:.7,w:2.4,sq:.2});
    shakeEls.forEach(n=>A(n,[{translate:'0 0'},{translate:'0 3px'},{translate:'0 -1px'},{translate:'0 0'}],{duration:240,fill:'none'}))});

  /* 4. into the app */
  const T_HIT=T_TO+F;
  at(T_TO+TOTAL,finish);
