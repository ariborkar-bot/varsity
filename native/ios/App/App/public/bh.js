/* ---------- Bobblehead engine (bh.js, v400, owner Nov 10): the cartoon bobblehead in Locker → Avatar (owner, Nov 9): one high-quality starter bobblehead.
   The figure is SCULPTED: every part is a smooth distance field (rounded shapes blended together) turned into a mesh by marching cubes,
   with soft contact shading baked into the vertex colours. three.js (vendor/three-bh.min.js) is loaded only when needed.
   BH.load(url) → BH.view(canvas).set(cfg) ; cfg = {name,num,skin, sleeve:{c,c2,d,arm}, plate:{c,c2,d,txt}} (sleeve/plate = an item's bh spec; patterns are drawn by window.bhPat in index.html) ---------- */
const BH=(function(){
  let T=null,loading=null;
  const load=url=>{if(T)return Promise.resolve(T);if(loading)return loading;
    loading=new Promise((ok,no)=>{if(window.THREE&&window.THREE.WebGLRenderer){T=window.THREE;ok(T);return}
      const s=document.createElement('script');s.src=url;s.async=true;s.onload=()=>{T=window.THREE;T&&T.WebGLRenderer?ok(T):(loading=null,no(new Error('three')))};s.onerror=()=>{loading=null;s.remove();no(new Error('load'))};document.head.appendChild(s)});
    return loading};
  const glOK=()=>{try{const c=document.createElement('canvas');return !!(c.getContext('webgl2')||c.getContext('webgl'))}catch(_){return false}};
  const PI=Math.PI,TAU=PI*2,rng=seed=>{let s=seed>>>0||1;return()=>(s=(Math.imul(s,1664525)+1013904223)>>>0)/4294967296};
  const hx=h=>{h=String(h||'#888').replace('#','');if(h.length===3)h=h.split('').map(x=>x+x).join('');const n=parseInt(h,16)||0;return[n>>16&255,n>>8&255,n&255]};
  const shade=(h,k)=>{const c=hx(h);return'#'+c.map(v=>Math.max(0,Math.min(255,Math.round(k>=0?v+(255-v)*k:v*(1+k)))).toString(16).padStart(2,'0')).join('')};
  const V3=(x,y,z)=>new T.Vector3(x,y,z);
  const FONT='"Barlow Condensed","Arial Narrow",Arial,sans-serif';
  const TEX=new Map();
  function tex(key,w,h,draw,o){o=o||{};if(TEX.has(key))return TEX.get(key);const c=document.createElement('canvas');c.width=w;c.height=h;draw(c.getContext('2d'),w,h);
    const t=new T.CanvasTexture(c);t.colorSpace=o.data?T.NoColorSpace:T.SRGBColorSpace;t.anisotropy=8;if(o.rep){t.wrapS=t.wrapT=T.RepeatWrapping;t.repeat.set(o.rep[0],o.rep[1])}else if(o.wrapS)t.wrapS=T.RepeatWrapping;TEX.set(key,t);return t}
  /* ---------- distance-field building blocks ---------- */
  const L3=(x,y,z)=>Math.sqrt(x*x+y*y+z*z),L2=(x,y)=>Math.sqrt(x*x+y*y);
  const smin=(a,b,k)=>{const h=Math.max(k-Math.abs(a-b),0)/k;return Math.min(a,b)-h*h*k*.25};
  const smax=(a,b,k)=>-smin(-a,-b,k);
  const sph=(x,y,z,cx,cy,cz,r)=>L3(x-cx,y-cy,z-cz)-r;
  const ell=(x,y,z,cx,cy,cz,rx,ry,rz)=>{const px=x-cx,py=y-cy,pz=z-cz,k0=L3(px/rx,py/ry,pz/rz),k1=L3(px/(rx*rx),py/(ry*ry),pz/(rz*rz));return k1<1e-9?-Math.min(rx,ry,rz):k0*(k0-1)/k1};
  const cone=(x,y,z,ax,ay,az,bx,by,bz,r1,r2)=>{const pax=x-ax,pay=y-ay,paz=z-az,bax=bx-ax,bay=by-ay,baz=bz-az;let h=(pax*bax+pay*bay+paz*baz)/(bax*bax+bay*bay+baz*baz);h=h<0?0:h>1?1:h;return L3(pax-bax*h,pay-bay*h,paz-baz*h)-(r1+(r2-r1)*h)};
  const box2=(a,b,ca,cb,ha,hb,r)=>{const qa=Math.abs(a-ca)-ha+r,qb=Math.abs(b-cb)-hb+r;return L2(Math.max(qa,0),Math.max(qb,0))+Math.min(Math.max(qa,qb),0)-r};
  const bead=(a,b,r)=>Math.sqrt(a*a+b*b)-r;                         /* a tube along the line where two surfaces cross */
  const tor=(x,y,z,cx,cy,cz,ax,ay,az,R,r)=>{const qx=x-cx,qy=y-cy,qz=z-cz,h=qx*ax+qy*ay+qz*az;return L2(L3(qx-ax*h,qy-ay*h,qz-az*h)-R,h)-r};
  /* ---------- marching cubes: distance field → smooth mesh, with baked soft shading ---------- */
  function mc(f,b0,b1,h,o){o=o||{};const ET=T.edgeTable,TT=T.triTable,B=4;
    const nx=Math.ceil((b1[0]-b0[0])/h/B)*B,ny=Math.ceil((b1[1]-b0[1])/h/B)*B,nz=Math.ceil((b1[2]-b0[2])/h/B)*B,sx=nx+1,sy=ny+1,sxy=sx*sy;
    const F=new Float32Array(sx*sy*(nz+1));F.fill(NaN);
    const X=i=>b0[0]+i*h,Y=j=>b0[1]+j*h,Z=k=>b0[2]+k*h;
    const val=(i,j,k)=>{const q=i+sx*j+sxy*k;let v=F[q];if(v!==v)v=F[q]=f(X(i),Y(j),Z(k));return v};
    const pos=[],idx=[],em=new Map(),R=B*h*.87*1.7,E=new Int32Array(12);
    const ev=(i,j,k,ax)=>{const key=(i+sx*j+sxy*k)*3+ax;let id=em.get(key);if(id!==undefined)return id;const a=val(i,j,k),b=val(i+(ax===0?1:0),j+(ax===1?1:0),k+(ax===2?1:0)),t=a/(a-b);
      id=pos.length/3;pos.push(X(i)+(ax===0?t*h:0),Y(j)+(ax===1?t*h:0),Z(k)+(ax===2?t*h:0));em.set(key,id);return id};
    for(let bk=0;bk<nz;bk+=B)for(let bj=0;bj<ny;bj+=B)for(let bi=0;bi<nx;bi+=B){
      if(Math.abs(f(X(bi+B/2),Y(bj+B/2),Z(bk+B/2)))>R)continue;
      for(let k=bk;k<bk+B;k++)for(let j=bj;j<bj+B;j++)for(let i=bi;i<bi+B;i++){
        const f0=val(i,j,k),f1=val(i+1,j,k),f2=val(i,j+1,k),f3=val(i+1,j+1,k),f4=val(i,j,k+1),f5=val(i+1,j,k+1),f6=val(i,j+1,k+1),f7=val(i+1,j+1,k+1);
        let c=0;if(f0<0)c|=1;if(f1<0)c|=2;if(f2<0)c|=8;if(f3<0)c|=4;if(f4<0)c|=16;if(f5<0)c|=32;if(f6<0)c|=128;if(f7<0)c|=64;
        const bits=ET[c];if(!bits)continue;
        if(bits&1)E[0]=ev(i,j,k,0);if(bits&2)E[1]=ev(i+1,j,k,1);if(bits&4)E[2]=ev(i,j+1,k,0);if(bits&8)E[3]=ev(i,j,k,1);
        if(bits&16)E[4]=ev(i,j,k+1,0);if(bits&32)E[5]=ev(i+1,j,k+1,1);if(bits&64)E[6]=ev(i,j+1,k+1,0);if(bits&128)E[7]=ev(i,j,k+1,1);
        if(bits&256)E[8]=ev(i,j,k,2);if(bits&512)E[9]=ev(i+1,j,k,2);if(bits&1024)E[10]=ev(i+1,j+1,k,2);if(bits&2048)E[11]=ev(i,j+1,k,2);
        for(let t=c<<4;TT[t]!==-1;t+=3){const a=E[TT[t]],b=E[TT[t+1]],d=E[TT[t+2]];if(a!==b&&b!==d&&a!==d)idx.push(a,b,d)}}}
    let n=pos.length/3;const nor=new Float32Array(n*3),e=h*.6;
    for(let v=0;v<n;v++){const x=pos[v*3],y=pos[v*3+1],z=pos[v*3+2];let gx=f(x+e,y,z)-f(x-e,y,z),gy=f(x,y+e,z)-f(x,y-e,z),gz=f(x,y,z+e)-f(x,y,z-e);const l=L3(gx,gy,gz)||1;nor[v*3]=gx/l;nor[v*3+1]=gy/l;nor[v*3+2]=gz/l}
    for(let t=0;t<idx.length;t+=3){const a=idx[t]*3,b=idx[t+1]*3,c=idx[t+2]*3,ux=pos[b]-pos[a],uy=pos[b+1]-pos[a+1],uz=pos[b+2]-pos[a+2],vx=pos[c]-pos[a],vy=pos[c+1]-pos[a+1],vz=pos[c+2]-pos[a+2];
      if((uy*vz-uz*vy)*nor[a]+(uz*vx-ux*vz)*nor[a+1]+(ux*vy-uy*vx)*nor[a+2]<0){const s=idx[t+1];idx[t+1]=idx[t+2];idx[t+2]=s}}
    const col=new Float32Array(n*3),tint=o.tint||[.34,.36,.44],occ=o.occ||f;
    for(let v=0;v<n;v++){const x=pos[v*3],y=pos[v*3+1],z=pos[v*3+2],a=nor[v*3],b=nor[v*3+1],c=nor[v*3+2];let s=0;
      for(let i=1;i<=4;i++){const d=i*.035;s+=Math.max(0,d-occ(x+a*d,y+b*d,z+c*d))/i}
      const ao=Math.max(0,Math.min(1,1-s*(o.aoK||5.5)));for(let q=0;q<3;q++)col[v*3+q]=tint[q]+(1-tint[q])*ao}
    const g=new T.BufferGeometry();let P=pos,N=Array.from(nor),C=Array.from(col);
    if(o.uv){const U=[];for(let v=0;v<n;v++){const q=o.uv(pos[v*3],pos[v*3+1],pos[v*3+2]);U.push(q[0],q[1])}
      for(let t=0;t<idx.length;t+=3){const us=[U[idx[t]*2],U[idx[t+1]*2],U[idx[t+2]*2]];if(Math.max(...us)-Math.min(...us)>.5)for(let q=0;q<3;q++)if(us[q]<.5){const v=idx[t+q];
          P.push(P[v*3],P[v*3+1],P[v*3+2]);N.push(N[v*3],N[v*3+1],N[v*3+2]);C.push(C[v*3],C[v*3+1],C[v*3+2]);U.push(U[v*2]+1,U[v*2+1]);idx[t+q]=P.length/3-1}}
      g.setAttribute('uv',new T.Float32BufferAttribute(U,2))}
    g.setAttribute('position',new T.Float32BufferAttribute(P,3));g.setAttribute('normal',new T.Float32BufferAttribute(N,3));g.setAttribute('color',new T.Float32BufferAttribute(C,3));g.setIndex(idx);g.userData.keep=1;return g}
  const QH=(navigator.hardwareConcurrency||8)<=4||/Android|iPhone|iPad/i.test(navigator.userAgent)?1.12:1;
  const GEO=new Map(),geo=(k,mk)=>{if(!GEO.has(k))GEO.set(k,mk());return GEO.get(k)};
  const nrm=v=>{const l=L3(v[0],v[1],v[2]);return[v[0]/l,v[1]/l,v[2]/l]};
  /* ================= BODY (y=0 = top of the base, faces +z). A tiny chunky body under a huge head. ================= */
  const HY=1.3,BSX=1.07,BSY=1.2,HS=.86,GAP=.2;                                                   /* height of the head's centre */
  const torso=(x,y,z)=>smin(ell(x,y,z,0,.47,0,.27,.2,.215),ell(x,y,z,0,.36,0,.255,.13,.2),.1);
  /* shoulder pads, built like real ones: a chest/back plate laced down the middle, an epaulet from the neck out over each shoulder, and a cap hanging over the arm */
  const padL=(x,y,cx,cy,t)=>{const dx=Math.abs(x)-cx,dy=y-cy,c=Math.cos(t),sn=Math.sin(t);return[dx*c-dy*sn,dx*sn+dy*c]};
  const plateEdge=x=>.5+.95*x*x,epO=(l,z)=>ell(l[0],l[1],z,0,0,0,.205,.058,.205),capO=(l,z)=>ell(l[0],l[1],z,0,0,0,.155,.105,.2);
  const EP=[.245,.66,.26],CP=[.425,.585,.78];
  const bpS=(x,y,z)=>smin(ell(x,y,z,0,.47,0,.27,.2,.215),ell(x,y,z,0,.36,0,.255,.13,.2),.1)-.03;
  const bpR=(x,y)=>box2(x,y,0,.38,.14,.09,.045);
  
  const footL=(x,z,s)=>{const a=s*.3,c=Math.cos(a),sn=Math.sin(a),dx=x-s*.155,dz=z-.02;return[dx*c-dz*sn,dx*sn+dz*c]};
  const shoeUp=(lx,y,lz)=>smin(ell(lx,y,lz,0,.075,-.02,.108,.088,.11),ell(lx,y,lz,0,.062,.1,.108,.072,.125),.07);
  const D={
    jersey:(x,y,z)=>smax(torso(x,y,z),.3-y,.02),
    pants:(x,y,z)=>{const s=x<0?-1:1;let d=ell(x,y,z,0,.28,0,.25,.13,.195);d=smin(d,cone(x,y,z,s*.14,.26,0,s*.152,.13,.01,.122,.112),.05);return smax(d,.118-y,.015)},
    shoe:(x,y,z)=>{const s=x<0?-1:1,l=footL(x,z,s);return smax(shoeUp(l[0],y,l[1]),.032-y,.012)},
    white:(x,y,z)=>{const s=x<0?-1:1,l=footL(x,z,s);return Math.min(smax(shoeUp(l[0],.05,l[1])-.018,Math.abs(y-.019)-.019,.014),tor(x,y,z,0,.66,0,0,1,0,.105,.032))},
    pads:(x,y,z)=>{const t=torso(x,y,z)-.034;let d=Math.abs(t)-.021;d=smax(d,plateEdge(x)-y,.014);d=smax(d,Math.abs(x)-.3,.02);d=smax(d,.14-L2(x,z),.02);d=smax(d,.011-Math.abs(x)-(z<0?1:0),.008);
      const e=padL(x,y,EP[0],EP[1],EP[2]),c=padL(x,y,CP[0],CP[1],CP[2]);return Math.min(d,smax(epO(e,z),-.022-e[1],.012),smax(capO(c,z),-.04-c[1],.012))},
    trim:(x,y,z)=>{const t=torso(x,y,z)-.034,e=padL(x,y,EP[0],EP[1],EP[2]),c=padL(x,y,CP[0],CP[1],CP[2]);
      return Math.min(Math.max(bead(t,plateEdge(x)-y,.022),Math.abs(x)-.3),bead(epO(e,z),e[1]+.022,.016),bead(capO(c,z),c[1]+.04,.019))}};
  D.plate=(x,y,z)=>z>0?1:smax(Math.abs(bpS(x,y,z))-.02,bpR(x,y),.012);
  D.strap=(x,y,z)=>z>0?1:smax(Math.abs(bpS(x,y,z)+.012)-.01,Math.max(Math.abs(Math.abs(x)-.075)-.022,Math.abs(y-.5)-.06),.006);
  D.plateTrim=(x,y,z)=>z>0?1:bead(bpS(x,y,z),bpR(x,y),.02);
  const bodyOcc=(x,y,z)=>Math.min(y+.002,D.plate(x,y,z),D.jersey(x,y,z),D.pants(x,y,z),D.shoe(x,y,z),D.white(x,y,z),D.pads(x,y,z),D.trim(x,y,z),sph(x,y,z,0,HY,0,.63));
  const bodyGeo=(k,o)=>geo('b:'+k,()=>mc(D[k],[-.6,-.02,-.36],[.6,.82,.4],.0105*QH,Object.assign({occ:bodyOcc,aoK:4.5},o||{})));
  /* one arm, in its own frame (shoulder at 0,0,0, hanging down); the other side is its mirror */
  const A={sleeve:(x,y,z)=>cone(x,y,z,0,0,0,.045,-.115,0,.108,.102),
    skin:(x,y,z)=>cone(x,y,z,.045,-.115,0,.092,-.285,0,.08,.07),
    hand:(x,y,z)=>{const lx=(x-.105)*.958+(y+.345)*.287,ly=-(x-.105)*.287+(y+.345)*.958,lz=z-.005;let d=ell(lx,ly,lz,0,.01,0,.07,.075,.082);for(let i=0;i<4;i++){const zz=-.054+i*.036;d=smin(d,cone(lx,ly,lz,-.03,-.052,zz,.035,-.052,zz,.024,.024),.012)}return smin(d,cone(lx,ly,lz,-.05,.02,.06,-.02,-.03,.09,.027,.024),.015)},
    cover:(x,y,z)=>cone(x,y,z,.05,-.13,0,.088,-.258,0,.088,.082),
    band:(x,y,z)=>{const a=nrm([.28,-.96,0]);return tor(x,y,z,.085,-.252,0,a[0],a[1],a[2],.074,.023)}};
  const armOcc=(x,y,z)=>Math.min(A.sleeve(x,y,z),A.skin(x,y,z),A.band(x,y,z),A.hand(x,y,z));
  const armGeo=(k,o)=>geo('a:'+k,()=>mc(A[k],[-.16,-.48,-.16],[.26,.14,.16],.0095*QH,Object.assign({occ:armOcc,aoK:4},o||{})));
  const coverUV=(x,y,z)=>{const dx=.29,dy=-.957,qx=x-.045,qy=y+.115,t=qx*dx+qy*dy,rx=qx-dx*t,ry=qy-dy*t,rp=rx*-dy+ry*dx;return[((Math.atan2(z,rp)/TAU+.5)%1+1)%1,Math.max(0,Math.min(1,(t-.01)/.15))]};
  const patTex=(bh,kind,w,h)=>tex('pat|'+kind+'|'+JSON.stringify(bh),w,h,(g,W,H)=>{if(window.bhPat)window.bhPat(g,W,H,bh,kind);else{g.fillStyle=bh.c||'#888';g.fillRect(0,0,W,H)}},{wrapS:1});
  /* ================= HEAD (origin = centre of the head) ================= */
  const headF=(x,y,z)=>smin(smin(ell(x,y,z,0,.02,0,.49,.45,.46),ell(x,y,z,0,-.2,.07,.37,.27,.37),.16),ell(x,y,z,0,-.02,.465,.045,.05,.05),.05);
  const HO=(x,y,z)=>ell(x,y,z,0,.03,-.02,.625,.6,.65);
  const HC=(x,y,z)=>smin(Math.max(box2(x,y,0,-.015,.44,.285,.2),.1-z),y+.47,.05);
  const H={head:headF,
    shell:(x,y,z)=>{const o=HO(x,y,z);return smax(Math.max(o,-(o+.05)),-HC(x,y,z),.04)},
    rim:(x,y,z)=>bead(HO(x,y,z)+.025,HC(x,y,z),.037),
    liner:(x,y,z)=>{const o=HO(x,y,z);return smax(Math.max(o+.045,-(headF(x,y,z)-.004)),-(HC(x,y,z)+.035),.03)},
    stripe:(x,y,z)=>smax(smax(Math.abs(HO(x,y,z)-.001)-.011,Math.abs(x)-.078,.012),-(HC(x,y,z)+.05),.02)+(z>0&&y<.1?1:0)};
  const headOcc=(x,y,z)=>Math.min(headF(x,y,z),H.shell(x,y,z),H.liner(x,y,z),H.rim(x,y,z));
  const headGeo=(k,o)=>geo('h:'+k,()=>mc(H[k],[-.72,-.66,-.74],[.72,.7,.72],.0115*QH,Object.assign({occ:headOcc,aoK:4},o||{})));
  function hit(f,o,d,t0,t1){let a=t0,b=t1;for(let i=0;i<40;i++){const m=(a+b)/2;f(o[0]+d[0]*m,o[1]+d[1]*m,o[2]+d[2]*m)<0?a=m:b=m}return V3(o[0]+d[0]*a,o[1]+d[1]*a,o[2]+d[2]*a)}
  const gradN=(f,p)=>{const e=.004;return V3(f(p.x+e,p.y,p.z)-f(p.x-e,p.y,p.z),f(p.x,p.y+e,p.z)-f(p.x,p.y-e,p.z),f(p.x,p.y,p.z+e)-f(p.x,p.y,p.z-e)).normalize()};
  const onHead=(x,y,out)=>{const p=hit(headF,[x,y,0],[0,0,1],0,.8),n=gradN(headF,p);return{p:p.clone().addScaledVector(n,out||0),n}};
  const onShell=(dx,dy,dz,out)=>{const d=nrm([dx,dy,dz]),p=hit(HO,[0,.03,-.02],d,0,1.3),n=gradN(HO,p);return{p:p.clone().addScaledVector(n,out||0),n}};
  /* ---------- cartoon look: banded shading + ink outlines ---------- */
  /* v401 look: a glossy collectible figure (reflections, soft shadows, rim light). toonV = sculpted meshes with baked shading, toonP = plain meshes. */
  const FIN={gloss:{roughness:.2,clearcoat:1,clearcoatRoughness:.05},plastic:{roughness:.32,clearcoat:.8,clearcoatRoughness:.12},satin:{roughness:.5,sheen:.6,sheenRoughness:.4,clearcoat:.15,clearcoatRoughness:.4},cloth:{roughness:.78,sheen:.5,sheenRoughness:.5},skin:{roughness:.5,sheen:.25,sheenRoughness:.5,clearcoat:.1,clearcoatRoughness:.5},rubber:{roughness:.7},metal:{metalness:1,roughness:.16},steel:{metalness:.55,roughness:.28,clearcoat:.6,clearcoatRoughness:.15}};
  const pm=(c,o,v)=>{o=Object.assign({},o||{});const f=FIN[o.fin||'plastic'];delete o.fin;return new T.MeshPhysicalMaterial(Object.assign({color:c,vertexColors:!!v},f,o))};
  const toonV=(c,o)=>pm(c,o,true),toonP=(c,o)=>pm(c,o,false);
  function ink(m){return m}
  function mesh(g,m,w){const o=new T.Mesh(g,m);o.castShadow=true;o.receiveShadow=true;if(w)ink(o,w);return o}
  function tube(pts,r,mat,w,n,closed){const c=new T.CatmullRomCurve3(pts,!!closed,'centripetal',.5),m=mesh(new T.TubeGeometry(c,n||60,r,14,!!closed),mat,w);
    if(!closed)for(const p of [pts[0],pts[pts.length-1]]){const s=mesh(new T.SphereGeometry(r,14,10),mat,w);s.position.copy(p);m.add(s)}return m}
  const SKIN=['#FFE0C7','#FBCFA6','#F0BC8C','#DDA06C','#BD7F50','#93603A','#70452A','#4E301D'];
  const W_=.011;
  /* ---------- face: simple and expressive ---------- */
  function face(G,cfg){const skin=SKIN[cfg.skin==null?2:cfg.skin|0]||SKIN[2];
    G.add(mesh(headGeo('head',{tint:[.72,.44,.38]}),toonV(skin,{fin:'skin'})));
    const dark=new T.MeshBasicMaterial({color:'#1c1310'}),white=new T.MeshBasicMaterial({color:'#f3f1ec'}),irisM=new T.MeshBasicMaterial({color:cfg.eyes||'#3a2415'}),eyes=[],happy=[];
    /* focused eyes: flat-topped, a heavy lid line that drops toward the nose */
    for(const s of [-1,1]){const {p,n}=onHead(s*.165,.075,.004),e=new T.Group();e.position.copy(p);e.lookAt(p.clone().add(n));e.rotateY(-s*.1);G.add(e);
      const rimE=new T.Mesh(new T.SphereGeometry(1,32,24),dark);rimE.scale.set(.074,.045,.02);rimE.position.y=-.006;e.add(rimE);
      const wh=new T.Mesh(new T.SphereGeometry(1,32,24),white);wh.scale.set(.066,.037,.026);wh.position.y=-.006;e.add(wh);
      const ir=new T.Mesh(new T.SphereGeometry(1,24,16),irisM);ir.scale.set(.034,.036,.012);ir.position.set(-s*.01,-.004,.02);e.add(ir);
      const pu=new T.Mesh(new T.SphereGeometry(1,20,14),dark);pu.scale.set(.019,.021,.008);pu.position.set(-s*.01,-.004,.029);e.add(pu);
      const h1=new T.Mesh(new T.SphereGeometry(1,12,8),white);h1.scale.set(.008,.009,.005);h1.position.set(-s*.01+.012,.008,.035);e.add(h1);
      const lid=[];for(let i=0;i<=4;i++){const t=i/4-.5;lid.push(V3(t*.17,.026+s*t*.05,.022))}e.add(tube(lid,.0135,dark,0,10));eyes.push(e);
      const eb=[];for(let i=0;i<=6;i++){const t=i/6-.5;eb.push(onHead(s*.18+t*.15,-.012-.01*(1-4*t*t),-.007).p)}G.add(tube(eb,.021,dark,0,16))}
    /* a small closed smirk */
    const M=(x,y)=>onHead(x,y,.006).p;G.add(tube([M(-.075,-.182),M(-.03,-.19),M(.03,-.188),M(.075,-.172),M(.1,-.15)],.0095,dark,0,30));
    return{eyes,happy}}
  /* ---------- helmet: a round bucket with one bold stripe and a chunky two-bar mask ---------- */
  function helmet(G,cfg){const hc=cfg.helm||'#f7f8fa',sc=cfg.stripe||'#353d50',mk=cfg.mask||'#8d95a3';
    G.add(mesh(headGeo('shell'),toonV(hc,{fin:'gloss'}),W_));G.add(mesh(headGeo('rim'),toonV('#1e2230',{fin:'rubber'}),0));G.add(mesh(headGeo('liner'),toonV('#262b3a',{fin:'rubber'})));G.add(mesh(headGeo('stripe'),toonV(sc,{fin:'gloss'}),0));
    const bar=toonP(mk,{fin:'steel'}),R=.034,B=(t,y)=>V3(.665*Math.sin(t),y,.0+.705*Math.cos(t));
    for(const y of [-.085,-.275]){const p=[];for(let i=0;i<=14;i++)p.push(B(-1.22+2.44*i/14,y));G.add(tube(p,R,bar,W_*.8,70))}
    for(const t of [-.62,.62])G.add(tube([B(t,-.085),B(t,-.18),B(t,-.275)],R*.9,bar,W_*.8,12));
    const dk=toonP('#2b3145');for(const s of [-1,1]){for(const y of [-.085,-.275]){const c=mesh(new T.SphereGeometry(.052,20,14),dk,0);c.position.copy(B(s*1.22,y));c.scale.set(.6,1,1);G.add(c)}
      const e=onShell(s*1,-.12,-.02,.002),d=mesh(new T.CircleGeometry(.075,32),new T.MeshBasicMaterial({color:'#2b3145'}),0);d.castShadow=false;d.position.copy(e.p);d.lookAt(e.p.clone().add(e.n));G.add(d);
      const d2=new T.Mesh(new T.RingGeometry(.075,.092,32),new T.MeshBasicMaterial({color:'#c9d0db'}));d2.position.copy(e.p);d2.lookAt(e.p.clone().add(e.n));G.add(d2)}
    /* painted shine */
    {const N=16,Mv=10,P=[],U=[],I=[];for(let j=0;j<=Mv;j++)for(let i=0;i<=N;i++){const th=-.95+.6*i/N,el=.55+.42*j/Mv,q=onShell(Math.sin(th)*Math.cos(el),Math.sin(el),Math.cos(th)*Math.cos(el),.004).p;P.push(q.x,q.y,q.z);U.push(i/N,j/Mv)}
      for(let j=0;j<Mv;j++)for(let i=0;i<N;i++){const a=j*(N+1)+i,b=a+N+1;I.push(a,a+1,b,a+1,b+1,b)}const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(P,3));g.setAttribute('uv',new T.Float32BufferAttribute(U,2));g.setIndex(I);
      G.add(new T.Mesh(g,new T.MeshBasicMaterial({map:tex('shine',128,128,(c,w,h)=>{c.clearRect(0,0,w,h);c.fillStyle='rgba(255,255,255,.95)';c.beginPath();c.roundRect(14,14,70,100,34);c.fill();c.beginPath();c.roundRect(96,40,20,48,10);c.fill()}),transparent:true,depthWrite:false,opacity:cfg.helm?.55:.0})))}}
  /* ---------- body ---------- */
  function jerseyTex(j,num){return tex('jy3|'+JSON.stringify(j)+'|'+num,1024,512,(g,w,h)=>{g.fillStyle=j.c;g.fillRect(0,0,w,h);const n=String(num==null?'':num);if(!n)return;g.textAlign='center';g.textBaseline='middle';g.lineJoin='round';
      for(const u of [.25]){g.save();g.translate(u*w,(1-(.4-.28)/.4)*h);g.scale(.5,1);const s=300;g.font=`900 ${s}px ${FONT}`;g.lineWidth=34;g.strokeStyle=j.t;g.strokeText(n,0,0);g.fillStyle=j.n;g.fillText(n,0,0);g.restore()}},{wrapS:1})}
  function body(G,cfg){const j=Object.assign({c:'#353d50',n:'#ffffff',t:'#12151d',pt:'#eef0f4'},cfg.jersey||{}),skin=SKIN[cfg.skin==null?2:cfg.skin|0]||SKIN[2],pc=cfg.pads||'#9aa2af';
    G.add(mesh(bodyGeo('jersey',{uv:(x,y,z)=>[((Math.atan2(x,z)/TAU+.25)%1+1)%1,(y-.28)/.4]}),toonV('#ffffff',{map:jerseyTex(j,cfg.num),fin:'cloth',sheenColor:new T.Color('#8fa0c4')}),W_));
    G.add(mesh(bodyGeo('pants'),toonV(j.pt,{fin:'satin',sheenColor:new T.Color('#ffffff')}),W_));G.add(mesh(bodyGeo('shoe'),toonV('#15171d',{fin:'gloss'}),W_));G.add(mesh(bodyGeo('white'),toonV('#f4f5f7',{fin:'satin'}),W_*.7));
    G.add(mesh(bodyGeo('pads'),toonV(pc),W_));G.add(mesh(bodyGeo('trim'),toonV(shade(pc,-.45)),0));for(const sd of [-1,1])for(const a of [-.8,0,.8]){const q=hit(D.pads,[sd*.42,.57,Math.sin(a)*.1],nrm([sd*.8,.3,Math.sin(a)*.75]),0,.5),rv=new T.Mesh(new T.SphereGeometry(.016,12,8),toonP('#ffffff'));rv.position.copy(q);G.add(rv)}
    {const pl=cfg.plate,pm=pl?toonV('#ffffff',{map:patTex(pl,'plate',256,170)}):toonV(pc);G.add(mesh(bodyGeo('plate',{uv:(x,y,z)=>[(-x+.14)/.28,(y-.29)/.18]}),pm,W_));G.add(mesh(bodyGeo('strap'),toonV('#3a4158'),0));G.add(mesh(bodyGeo('plateTrim'),toonV(pl?shade(pl.c2||pl.c||'#888',-.55):shade(pc,-.45)),0))}
    const sl=cfg.sleeve,arms=[];for(const s of [1,-1]){const a=new T.Group();a.position.set(s*.335,.5,0);const in_=new T.Group();in_.scale.x=s;a.add(in_);
      in_.add(mesh(armGeo('sleeve'),toonV(j.c,{fin:'cloth',sheenColor:new T.Color('#8fa0c4')}),W_));in_.add(mesh(armGeo('skin',{tint:[.8,.5,.42]}),toonV(skin,{fin:'skin'}),W_));in_.add(mesh(armGeo('hand'),toonV(cfg.glove||'#3a4254',{fin:'rubber'}),W_));in_.add(mesh(armGeo('band'),toonV('#ffffff'),0));if(sl&&(sl.arm!=='L'||s===1))in_.add(mesh(armGeo('cover',{uv:coverUV}),toonV('#ffffff',{map:patTex(sl,'sleeve',256,256)}),W_*.6));G.add(a);arms.push(a)}
    /* football */
    const ball=new T.Group(),pr=[];for(let i=0;i<=32;i++){const t=i/32*2-1;pr.push(new T.Vector2(.092*Math.pow(Math.max(0,1-t*t),.6)+.0005,t*.15))}
    ball.add(mesh(new T.LatheGeometry(pr,40),toonP('#ffffff',{map:tex('ball3',256,256,(g,w,h)=>{g.fillStyle='#a8551f';g.fillRect(0,0,w,h);g.fillStyle='#ffffff';g.fillRect(0,h*.16,w,h*.06);g.fillRect(0,h*.78,w,h*.06);g.fillRect(w*.24,h*.36,w*.02,h*.28);for(let i=0;i<5;i++)g.fillRect(w*.215,h*(.39+i*.05),w*.07,h*.02)})}),W_));G.add(ball);
    /* the spring */
    const sg=new T.Group();sg.position.y=.64;const pts=[];for(let i=0;i<=90;i++){const t=i/90;pts.push(V3(Math.cos(t*TAU*3.2)*.085,t*.23,Math.sin(t*TAU*3.2)*.085))}sg.add(mesh(new T.TubeGeometry(new T.CatmullRomCurve3(pts),160,.024,10),toonP('#eef2f6',{fin:'metal'}),W_*.7));G.add(sg);
    return{arms,ball,spring:sg}}
  function base(G,cfg){const pr=[[0,-.24],[.66,-.24],[.7,-.225],[.715,-.19],[.715,-.06],[.7,-.025],[.66,0],[0,0]].map(([x,y])=>new T.Vector2(x,y));
    const b=mesh(new T.LatheGeometry(pr,96),toonP(cfg.base||'#141a2e',{fin:'gloss'}),W_);b.receiveShadow=true;G.add(b);
    const top=new T.Mesh(new T.CircleGeometry(.655,64),toonP('#1b2340',{fin:'gloss'}));top.rotation.x=-PI/2;top.position.y=.002;top.receiveShadow=true;G.add(top);
    for(const y of [-.035,-.215]){const r=new T.Mesh(new T.TorusGeometry(.716,.014,10,96),toonP('#f2c04a',{fin:'metal',roughness:.22}));r.rotation.x=PI/2;r.position.y=y;G.add(r)}
    const nm=(cfg.name||'VARSITY').toUpperCase(),pt=tex('pl3|'+nm,1024,180,(g,w,h)=>{g.fillStyle='#FFC93A';g.beginPath();g.roundRect(0,0,w,h,50);g.fill();g.fillStyle='#1b2238';g.textAlign='center';g.textBaseline='middle';let s=128;g.font=`900 ${s}px ${FONT}`;while(g.measureText(nm).width>w*.84&&s>40){s-=4;g.font=`900 ${s}px ${FONT}`}g.fillText(nm,w/2,h*.55)});
    const pl=new T.Mesh(new T.CylinderGeometry(.722,.722,.11,48,1,true,-.42,.84),new T.MeshBasicMaterial({map:pt,transparent:true}));pl.position.y=-.125;G.add(pl)}
  function figure(cfg){const root=new T.Group(),hop=new T.Group(),bodyG=new T.Group(),pivot=new T.Group(),headG=new T.Group();root.add(hop);base(root,cfg);hop.add(bodyG);const B=body(bodyG,cfg);
    pivot.position.set(0,.66*BSY,0);hop.add(pivot);headG.scale.setScalar(HS);headG.position.set(0,GAP+.47*HS,0);pivot.add(headG);bodyG.scale.set(BSX,BSY,BSX);const F=face(headG,cfg);helmet(headG,Object.assign({helm:'#ffffff'},cfg));return Object.assign({root,hop,body:bodyG,pivot,head:headG},B,F)}
  function disposeTree(o){o.traverse(x=>{if(x.geometry&&!x.geometry.userData.keep)x.geometry.dispose()})}
  function setupScene(r){const scene=new T.Scene(),pg=new T.PMREMGenerator(r);scene.environment=pg.fromScene(new T.RoomEnvironment(),.03).texture;scene.environmentIntensity=.7;pg.dispose();
    const key=new T.DirectionalLight('#fff1e0',2.6);key.position.set(-2.4,4.6,3.8);key.castShadow=true;key.shadow.mapSize.set(1024,1024);const sc=key.shadow.camera;sc.left=-1.4;sc.right=1.4;sc.top=2.7;sc.bottom=-.6;sc.near=.5;sc.far=14;key.shadow.radius=6;key.shadow.bias=-.0004;key.shadow.normalBias=.02;scene.add(key);
    const r1=new T.DirectionalLight('#4f9dff',2.8);r1.position.set(3.6,2.6,-3);scene.add(r1);const r2=new T.DirectionalLight('#ffb066',1.7);r2.position.set(-3.6,2.2,-3.2);scene.add(r2);scene.add(new T.HemisphereLight('#dfe8ff','#2a2233',.45));
    const sh=new T.Mesh(new T.PlaneGeometry(3.6,3.6),new T.MeshBasicMaterial({map:tex('floor',256,256,(g,w,h)=>{const q=g.createRadialGradient(128,128,20,128,128,128);q.addColorStop(0,'rgba(0,0,0,.6)');q.addColorStop(.5,'rgba(0,0,0,.25)');q.addColorStop(1,'rgba(0,0,0,0)');g.fillStyle=q;g.fillRect(0,0,w,h)}),transparent:true,depthWrite:false}));sh.rotation.x=-PI/2;sh.position.y=-.241;scene.add(sh);
    const gl=new T.Mesh(new T.PlaneGeometry(6,6),new T.MeshBasicMaterial({map:tex('glow',256,256,(g,w,h)=>{const q=g.createRadialGradient(128,128,0,128,128,128);q.addColorStop(0,'rgba(110,160,255,.5)');q.addColorStop(.45,'rgba(60,100,230,.16)');q.addColorStop(1,'rgba(40,60,160,0)');g.fillStyle=q;g.fillRect(0,0,w,h)}),transparent:true,depthWrite:false,blending:T.AdditiveBlending}));gl.position.set(0,1.05,-1.6);scene.add(gl);return{scene}}
  function mkRenderer(canvas,w,h,pr){const r=new T.WebGLRenderer({canvas,antialias:true,alpha:true,powerPreference:'high-performance'});r.setPixelRatio(pr);r.setSize(w,h,false);r.toneMapping=T.ACESFilmicToneMapping;r.toneMappingExposure=1.05;r.shadowMap.enabled=true;r.shadowMap.type=T.PCFShadowMap;r.setClearColor(0,0);return r}
  /* the viewer. Always alive: bounces to a beat, head wobbles on its spring, blinks, and every few seconds tosses the ball, hops or waves. Drag to spin, tap for a boing. */
  function view(canvas,o){o=o||{};const W=()=>Math.max(50,canvas.clientWidth||300),H=()=>Math.max(50,canvas.clientHeight||300);
    const r=mkRenderer(canvas,W(),H(),o.pr||Math.min(2,window.devicePixelRatio||1)),{scene}=setupScene(r),cam=new T.PerspectiveCamera(26,W()/H(),.1,50);
    let manual=false,fig=null,key='',yaw=-.35,yawV=0,drag=null,last=performance.now(),tm=0,raf=0,idle=0,alive=true,sz='',blink=2,bt=-1,shot=o.shot||null,em=null,et=0,nextE=3,happyT=0,ei=0;
    const bob={x:0,z:0,vx:0,vz:0,y:0,vy:0,t:0,vt:0};const tmpV=()=>new T.Vector3();
    const frame=()=>{const w=W(),h=H(),s=w+'x'+h+(shot||'');if(s!==sz){sz=s;r.setSize(w,h,false);cam.aspect=w/h;if(shot==='face'){cam.fov=22;cam.position.set(.5,1.42,4.2);cam.lookAt(0,1.2,0)}else{cam.fov=h/w>1.3?31:26;cam.position.set(0,1.25,6.6);cam.lookAt(0,.84,0)}cam.updateProjectionMatrix()}};
    function set(cfg){const k=JSON.stringify(cfg);if(k===key)return;key=k;const old=fig;fig=figure(cfg);scene.add(fig.root);if(old){scene.remove(old.root);disposeTree(old.root);kick(.8)}}
    function kick(s,dir){const a=dir==null?Math.random()*TAU:dir;bob.vx+=Math.cos(a)*s*4.5;bob.vz+=Math.sin(a)*s*4.5;bob.vy+=s*1.4;bob.vt+=(Math.random()-.5)*s*3}
    function emote(n){em=n;et=0;if(n==='wave')happyT=1.6}
    const ease=t=>t*t*(3-2*t),cl=(t)=>Math.max(0,Math.min(1,t));
    function adv(dt){tm+=dt;frame();if(!fig){r.render(scene,cam);return}
      if(!drag){idle+=dt;yaw+=yawV*dt;yawV*=Math.pow(.15,dt);if(idle>2.5){const tg=-.35+Math.sin(tm*.3)*.45;yaw+=(tg-yaw)*Math.min(1,dt*.6)}}
      if(!manual){nextE-=dt;if(nextE<=0&&!em){nextE=4+Math.random()*2.5;emote(['toss','nod'][ei++%2])}}
      /* groove: the body squashes to a beat and the head lags behind on the spring */
      const beat=Math.sin(tm*2.1)*.35,sq=.006*Math.sin(tm*2.1);let hopY=0,sqE=0,aR=-1.05,aRz=.1,aL=.12+.05*Math.sin(tm*2.6),aLz=.0,ballFree=null;
      if(em){et+=dt;
        if(em==='hop'){const T0=.16,T1=.5,T2=.2;if(et<T0)sqE=-.14*Math.sin(et/T0*PI/2);else if(et<T0+T1){const q=(et-T0)/T1;hopY=.34*4*q*(1-q);sqE=.1*(1-q);if(q<.1)bob.vy+=-9*dt}else if(et<T0+T1+T2){const q=(et-T0-T1)/T2;sqE=-.16*Math.sin(q*PI);if(q<.15){bob.vy+=14*dt;bob.vx+=10*dt}}else em=null;aL=-.5*cl(et/.3)*(em?1:0);aLz=.9*Math.sin(cl(et/(T0+T1))*PI)}
        else if(em==='toss'){const U=.22,F=.95;if(et<U){aR=-1.05-1.0*ease(et/U)}else if(et<U+F){const q=(et-U)/F;aR=-2.05+1.0*ease(cl(q*2.2))-.0;ballFree=q;if(q>.75)aR=-1.05-.25*Math.sin((q-.75)/.25*PI)}else{em=null}}
        else if(em==='nod'){if(et<.05||et>.42&&et<.47)bob.vx+=38*dt;if(et>1)em=null}
        else if(em==='wave'){const D_=1.5;if(et<D_){const q=et/D_,up=ease(cl(q*5))*ease(cl((1-q)*5));aLz=2.5*up;aL=0;fig.arms[0].userData.w=.35*Math.sin(et*16)*up}else{em=null;fig.arms[0].userData.w=0}}}
      happyT=Math.max(0,happyT-dt);
      const k=58,c=1.7;bob.vx+=(-k*bob.x-c*bob.vx+beat*1.6)*dt;bob.vz+=(-k*bob.z-c*bob.vz+Math.cos(tm*2.6)*1.5)*dt;bob.x+=bob.vx*dt;bob.z+=bob.vz*dt;bob.vt+=(-50*bob.t-2.2*bob.vt)*dt;bob.t+=bob.vt*dt;
      const lim=.42;bob.x=Math.max(-lim,Math.min(lim,bob.x));bob.z=Math.max(-lim,Math.min(lim,bob.z));bob.vy+=(-170*bob.y-6*bob.vy)*dt;bob.y+=bob.vy*dt;
      blink-=dt;if(blink<=0){blink=2+Math.random()*2.4;bt=0}let ey=1;if(bt>=0){bt+=dt;const q=bt/.16;ey=1-.92*Math.sin(Math.min(1,q)*PI);if(q>=1)bt=-1}
      const sy=1+sq+sqE,sx=1-(sq+sqE)*.6;fig.root.rotation.y=yaw;fig.hop.position.y=hopY;fig.body.scale.set(sx*BSX,sy*BSY,sx*BSX);
      const py=.66*BSY*sy+Math.max(-.05,Math.min(.1,bob.y*.14));fig.pivot.position.y=py;fig.pivot.rotation.set(bob.x,bob.t+.14*Math.sin(tm*.7),bob.z);
      fig.spring.scale.y=Math.max(.2,(py+GAP+.03-.64*BSY*sy)/(.23*BSY*sy));fig.spring.rotation.set(bob.x*.5,0,bob.z*.5);
      const hp=false;for(const e of fig.eyes){e.visible=!hp;e.scale.y=ey}for(const h of fig.happy)h.visible=hp;
      fig.arms[1].rotation.set(aR,0,-aRz);fig.arms[0].rotation.set(aL,0,aLz+(fig.arms[0].userData.w||0));
      /* the ball rides in the right hand, or flies */
      fig.body.updateMatrixWorld(true);const hand=fig.arms[1].localToWorld(V3(-.115,-.37,.12));fig.hop.worldToLocal(hand);
      if(ballFree!=null&&ballFree<.92){const q=ballFree/.92;fig.ball.position.set(hand.x*(1-.0),.0,hand.z);fig.ball.position.y=.78+ .0+ (1.05)*4*q*(1-q)*.62+ (hand.y-.78)*(q>.85?(q-.85)/.15:0)+(q<.1?(hand.y-.78)*(1-q/.1):0);fig.ball.position.x=-.36;fig.ball.position.z=.36;fig.ball.rotation.set(q*TAU*2+.5,0,.4)}
      else{fig.ball.position.copy(hand);fig.ball.rotation.set(.5,0,.4)}
      r.render(scene,cam)}
    function tick(now){raf=0;if(!alive||manual)return;if(!canvas.isConnected||document.hidden)return;const dt=Math.min(.05,(now-last)/1000);last=now;adv(dt);raf=requestAnimationFrame(tick)}
    const start=()=>{if(!raf&&alive&&!manual){last=performance.now();raf=requestAnimationFrame(tick)}};
    canvas.style.touchAction='pan-y';
    canvas.addEventListener('pointerdown',e=>{drag={t:performance.now(),moved:0,lx:e.clientX,lt:performance.now()};idle=0;try{canvas.setPointerCapture(e.pointerId)}catch(_){}});
    canvas.addEventListener('pointermove',e=>{if(!drag)return;const dx=e.clientX-drag.lx,now=performance.now();drag.moved+=Math.abs(dx);yaw+=dx*.012;yawV=dx*.012/Math.max(.008,(now-drag.lt)/1000);drag.lx=e.clientX;drag.lt=now;bob.vz+=-dx*.03;bob.vt+=dx*.02});
    canvas.addEventListener('pointerup',()=>{if(!drag)return;const d=drag;drag=null;idle=0;if(d.moved<6&&performance.now()-d.t<400)kick(1.2)});canvas.addEventListener('pointercancel',()=>{drag=null});
    document.addEventListener('visibilitychange',()=>{if(!document.hidden)start()});
    return{set,start,kick,emote,canvas,turn:y=>{yaw=y;yawV=0;idle=-1e9},film:(dt,y)=>{manual=true;if(y!=null){yaw=y;idle=-1e9}adv(dt)},dispose:()=>{alive=false;if(raf)cancelAnimationFrame(raf);r.dispose()}}}
  return{load,glOK,view,SKIN,ready:()=>!!T}})();
