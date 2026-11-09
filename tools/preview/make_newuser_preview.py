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
  const ss=sessionStorage,IN=ss.getItem('nu-in');
  if(!IN){try{Object.keys(localStorage).forEach(k=>{if(/^(vs-|gf-|varsity|gsd-|fg|nt-|in-|intro)/i.test(k))localStorage.removeItem(k)})}catch(_){}}
  const em=()=>ss.getItem('nu-email')||'you@example.com',user=()=>({id:'nu-me',email:em()}),ok=x=>Promise.resolve({data:x,error:null});
  const any=()=>new Proxy(function(){},{get:(t,k)=>k==='then'?(r=>r({data:null,error:null})):any(),apply:()=>any()});
  const signIn=({email})=>{ss.setItem('nu-in','1');if(email)ss.setItem('nu-email',email);return ok({session:{user:{id:'nu-me',email}},user:{id:'nu-me',email}})};
  const auth={getSession:()=>ok({session:IN?{user:user(),access_token:'preview'}:null}),onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),
    signUp:signIn,signInWithPassword:signIn,signOut:()=>{ss.removeItem('nu-in');return ok(null)},resetPasswordForEmail:()=>ok(null),updateUser:()=>ok(null)};
  const client=new Proxy({auth,rpc:()=>ok(false)},{get:(t,k)=>k in t?t[k]:any()});
  Object.defineProperty(window,'supabase',{value:Object.freeze({createClient:()=>client}),writable:false,configurable:false});
})();</script>
<div style="position:fixed;left:8px;bottom:8px;z-index:2147483647;background:#FFC23D;color:#1b1200;font:800 11px/1 system-ui;padding:5px 8px;border-radius:99px;opacity:.85;pointer-events:none">NEW-USER PREVIEW · nothing is saved</div>"""

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
    h = h.replace('</head>', '<style>#tab-admin{display:none!important}</style></head>', 1)
    me, oth = ('index.html', 'basketball.html') if src == 'index.html' else ('basketball.html', 'index.html')
    h = h.replace('href="%s"' % oth, 'href="%s"' % other).replace('href="%s"' % me, 'href="%s"' % dest)
    open(os.path.join(OUT, dest), 'w', encoding='utf-8').write(h)
    os.remove(tmp)


build('index.html', 'varsity-football-newuser.html', 'varsity-basketball-newuser.html')
build('basketball.html', 'varsity-basketball-newuser.html', 'varsity-football-newuser.html')
print('wrote', os.path.join(OUT, 'varsity-football-newuser.html'), 'and', os.path.join(OUT, 'varsity-basketball-newuser.html'))
