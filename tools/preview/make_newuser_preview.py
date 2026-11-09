"""Build "new user" previews: the app as a brand-new person sees it, from the sign-in screen on.

    python3 tools/preview/make_newuser_preview.py [out_dir]    (default /tmp/varsity-previews)

Writes out_dir/varsity-football-newuser.html and out_dir/varsity-basketball-newuser.html. Unlike the normal previews (demo mode,
already signed in), these run the LIVE code path with a fake Supabase that only exists inside the file: Create account / Sign in
always work (nothing is sent anywhere), then you get the real "make your profile" screen, the welcome pack and everything after.
Data lives in memory: reloading after you made a profile starts that part again. Closing the tab (or Sign out) starts over.
The real Supabase library tags are removed, so the file can never reach the real database."""
import os, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/varsity-previews'
os.makedirs(OUT, exist_ok=True)
subprocess.check_call([sys.executable, os.path.join(ROOT, 'tools', 'make_basketball.py')], stdout=subprocess.DEVNULL)

FAKE = r"""<script>/* new-user preview: fake Supabase, nothing leaves this file */
window.__NU=1;(function(){
  /* the claude.ai file viewer runs files in a sandbox where storage can throw: fall back to memory */
  const ss=(()=>{try{const s=window.sessionStorage;s.setItem('nu-t','1');s.removeItem('nu-t');return s}catch(_){const m={};return {getItem:k=>k in m?m[k]:null,setItem:(k,v)=>{m[k]=String(v)},removeItem:k=>{delete m[k]}}}})(),IN=ss.getItem('nu-in');
  if(!IN){try{Object.keys(localStorage).forEach(k=>{if(/^(vs-|gf-|varsity|gsd-|fg|nt-|in-|intro)/i.test(k))localStorage.removeItem(k)})}catch(_){}}
  const em=()=>ss.getItem('nu-email')||'you@example.com',user=()=>({id:'nu-me',email:em()}),ok=x=>Promise.resolve({data:x,error:null});
  const any=()=>new Proxy(function(){},{get:(t,k)=>k==='then'?(r=>r({data:null,error:null})):any(),apply:()=>any()});
  const signIn=({email})=>{ss.setItem('nu-in','1');if(email)ss.setItem('nu-email',email);return ok({session:{user:{id:'nu-me',email}},user:{id:'nu-me',email}})};
  const auth={getSession:()=>ok({session:IN?{user:user(),access_token:'preview'}:null}),onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),
    signUp:signIn,signInWithPassword:signIn,signOut:()=>{ss.removeItem('nu-in');return ok(null)},resetPasswordForEmail:()=>ok(null),updateUser:()=>ok(null)};
  const client=new Proxy({auth,rpc:()=>ok(false)},{get:(t,k)=>k in t?t[k]:any()});
  /* sign in without reloading the page (a reload in the viewer's sandbox would forget you) */
  window.nuIn=email=>{ME.uid='nu-me';ME.email=email||em();ME.mode='live';S.seen=null;S.loaded.seen=true;AUTH.busy=false;touch();if(!myProfile())openName()};
  /* the viewer's sandbox blocks real form submits: send the submit event ourselves (after the usual checks) */
  const sub=f=>{if(f.reportValidity&&!f.reportValidity())return;f.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))};
  document.addEventListener('click',e=>{const b=e.target.closest&&e.target.closest('button[type=submit]'),f=b&&b.form;if(f&&/^(au|nm)-form$/.test(f.id)){e.preventDefault();sub(f)}},true);
  document.addEventListener('keydown',e=>{const f=e.key==='Enter'&&e.target.form;if(f&&/^(au|nm)-form$/.test(f.id)&&e.target.tagName==='INPUT'&&e.target.type!=='checkbox'){e.preventDefault();sub(f)}},true);
  Object.defineProperty(window,'supabase',{value:Object.freeze({createClient:()=>client}),writable:false,configurable:false});
})();</script>
<div style="position:fixed;left:8px;bottom:8px;z-index:2147483647;display:flex;gap:6px;align-items:center;font:800 11px/1 system-ui"><span style="background:#FFC23D;color:#1b1200;padding:5px 8px;border-radius:99px;opacity:.85;pointer-events:none">NEW-USER PREVIEW · nothing is saved</span><button type="button" onclick="nuFill()" style="font:inherit;background:#fff;color:#1b1200;border:0;padding:5px 9px;border-radius:99px;cursor:pointer">Fill demo answers</button></div>
<script>/* owner: fill whatever sign-up / profile form is showing with demo answers (you still tap the button yourself) */
function nuFill(){const set=(id,v)=>{const e=document.getElementById(id);if(!e)return 0;if(e.type==='checkbox'){if(!e.checked)e.click()}else{e.value=v;e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}))}return 1};
  const n=set('au-email','demo'+Math.floor(Math.random()*900+100)+'@varsity.test')+set('au-pass','demo1234')+set('au-age',1)+set('nm-name','Demo Player');
  if(!n)alert('No sign-up or profile form is showing right now.')}</script>"""

LIB = ['<script src="vendor/supabase.min.js"></script>',
       """<script>/* v314: the login library is hosted with the app (vendor/). The two CDNs are only backups, for the rare case the local copy cannot load */window.supabase||document.write('<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"><\\/script>')</script>""",
       """<script>window.supabase||document.write('<script src="https://unpkg.com/@supabase/supabase-js@2.45.4/dist/umd/supabase.min.js"><\\/script>')</script>"""]


def build(src, dest, other):
    tmp = os.path.join(OUT, '_nu.html')
    subprocess.check_call([sys.executable, '-I', os.path.join(HERE, 'build_preview.py'), ROOT, tmp, src], stdout=subprocess.DEVNULL)
    h = open(tmp, encoding='utf-8').read()
    for i, x in enumerate(LIB):
        assert h.count(x) == 1, ('lib tag', i)
        h = h.replace(x, FAKE if i == 0 else '', 1)
    assert 'document.write(\'<script src="https://cdn.jsdelivr.net' not in h and '<script src="vendor/supabase.min.js">' not in h
    a = 'DB=supaDb(SB);'
    assert h.count(a) == 1, a
    h = h.replace(a, 'DB=window.__NU?memDb():supaDb(SB);', 1)
    for a in ['if(data.session){location.reload();return}', 'if(!r.error){location.reload();return}', "else{const {error}=await SB.auth.signInWithPassword({email,password:pw});if(error)throw error;location.reload();return}"]:
        assert h.count(a) == 1, a
        h = h.replace(a, a.replace('location.reload()', 'nuIn(email)'), 1)
    h = h.replace('</head>', '<style>#tab-admin{display:none!important}</style></head>', 1)
    me, oth = ('index.html', 'basketball.html') if src == 'index.html' else ('basketball.html', 'index.html')
    h = h.replace('href="%s"' % oth, 'href="%s"' % other).replace('href="%s"' % me, 'href="%s"' % dest)
    open(os.path.join(OUT, dest), 'w', encoding='utf-8').write(h)
    os.remove(tmp)


build('index.html', 'varsity-football-newuser.html', 'varsity-basketball-newuser.html')
build('basketball.html', 'varsity-basketball-newuser.html', 'varsity-football-newuser.html')
print('wrote', os.path.join(OUT, 'varsity-football-newuser.html'), 'and', os.path.join(OUT, 'varsity-basketball-newuser.html'))
