"""Find dead CSS in index.html.
  A) declarations redefined later by the exact same selector (same or unconditional context, same/greater !important)
  B) whole rules whose selector names a class/id that appears nowhere in the app's HTML/JS (or tools that inject markup)
Writes plan to cssplan.json; with --apply writes index.html."""
import re,sys,json,os
ROOT='/home/claude/varsity/';src=open(ROOT+'index.html').read()
# --- scan <style> blocks
blocks=[(m.start(1),m.end(1)) for m in re.finditer(r'<style[^>]*>(.*?)</style>',src,re.S)]
def skip_ws_comments(s,i,end):
    while i<end:
        if s.startswith('/*',i):
            j=s.find('*/',i+2);i=end if j<0 else j+2
        elif s[i].isspace():i+=1
        else:break
    return i
def find_block_end(s,i,end):
    """i at '{'; return index after matching '}' honoring strings/comments/parens"""
    d=0;q=None;par=0
    while i<end:
        c=s[i]
        if q:
            if c=='\\':i+=2;continue
            if c==q:q=None
        elif s.startswith('/*',i):i=s.find('*/',i+2)+2;continue
        elif c in '"\'':q=c
        elif c=='(':par+=1
        elif c==')':par-=1
        elif c=='{' and par==0:d+=1
        elif c=='}' and par==0:
            d-=1
            if d==0:return i+1
        i+=1
    raise Exception('unbalanced')
kfs=[]
rules=[]   # dict(ctx, sel, sel_start, body_start, body_end, decls=[...])
def parse_decls(s,a,b):
    out=[];i=a
    while i<b:
        i=skip_ws_comments(s,i,b)
        if i>=b:break
        st=i;q=None;par=0
        while i<b:
            c=s[i]
            if q:
                if c=='\\':i+=2;continue
                if c==q:q=None
            elif s.startswith('/*',i):i=s.find('*/',i+2)+2;continue
            elif c in '"\'':q=c
            elif c=='(':par+=1
            elif c==')':par-=1
            elif c==';' and par==0:break
            i+=1
        en=i;txt=s[st:en]
        if ':' in txt:
            prop,val=txt.split(':',1);prop=prop.strip().lower()
            imp=bool(re.search(r'!\s*important\s*$',val.strip()))
            out.append(dict(prop=prop,val=val.strip(),imp=imp,start=st,end=min(i+1,b)))
        i+=1
    return out
def walk(s,a,b,ctx):
    i=a
    while i<b:
        i=skip_ws_comments(s,i,b)
        if i>=b:break
        j=s.find('{',i)
        if j<0 or j>=b:break
        head=s[i:j].strip()
        if head.startswith('@') and ';' in head.split('{')[0][:head.find('{') if '{' in head else len(head)] and s.find(';',i)<j:
            i=s.find(';',i)+1;continue   # @import/@charset
        e=find_block_end(s,j,b)
        if head.startswith('@media') or head.startswith('@supports') or head.startswith('@container') or head.startswith('@layer'):
            walk(s,j+1,e-1,ctx+(re.sub(r'\s+',' ',head),))
        elif re.match(r'@(-webkit-)?keyframes\s',head):
            kfs.append((head.split()[1],i,e))
        elif head.startswith('@'):
            pass   # font-face, page: leave alone
        else:
            rules.append(dict(ctx=ctx,sel=re.sub(r'\s+',' ',head),sel_start=i,body_start=j+1,body_end=e-1,end=e,decls=parse_decls(s,j+1,e-1)))
        i=e
for a,b in blocks:walk(src,a,b,())
# --- protected ranges: literal strings make_basketball.py and preview tools look for
prot=[]
for f in ['tools/make_basketball.py','tools/preview/make_previews.py','tools/preview/build_preview.py','tools/preview/make_newuser_preview.py']:
    t=open(ROOT+f).read()
    for m in re.finditer(r"""(?:rep|between|line_replace|replace|count)\(\s*s?\s*,?\s*(['"])((?:\\.|(?!\1).){6,})\1""",t):
        lit=m.group(2)
        try:lit=bytes(lit,'utf-8').decode('unicode_escape').encode('latin-1').decode('utf-8')
        except Exception:pass
        k=0
        while True:
            k=src.find(lit,k)
            if k<0:break
            prot.append((k,k+len(lit)));k+=1
def protected(a,b):return any(a<pe and b>ps for ps,pe in prot)
RISKY=re.compile(r'dvh|svh|lvh|env\(|clamp\(|\bmin\(|\bmax\(|color-mix|-webkit-|-moz-|oklch|lch\(|@supports|fit-content|dynamic',re.I)
# A) overridden declarations
dead=set()
for ri,r in enumerate(rules):
    for d in r['decls']:
        for r2 in rules[ri+1:]:
            if r2['sel']!=r['sel']:continue
            if not(r2['ctx']==() or r2['ctx']==r['ctx']):continue
            hit=[d2 for d2 in r2['decls'] if d2['prop']==d['prop'] and (d2['imp'] or not d['imp']) and not RISKY.search(d2['val'])]
            if hit:dead.add((ri,d['start']));break
# within one rule: duplicate property later in the same rule
for ri,r in enumerate(rules):
    ds=r['decls']
    for k,d in enumerate(ds):
        if any(d2['prop']==d['prop'] and (d2['imp'] or not d['imp']) and not RISKY.search(d2['val']) and not RISKY.search(d['val']) for d2 in ds[k+1:]):
            dead.add((ri,d['start']))
# B) unused selectors
others=src
for f in ['tools/make_basketball.py','tools/preview/make_newuser_preview.py','tools/preview/make_previews.py','games.js','sw.js']:
    others+=open(ROOT+f).read()
# text outside style blocks only
nost=re.sub(r'<style[^>]*>.*?</style>','',others,flags=re.S)
def token_used(t):
    if re.search(r'(?<![\w-])'+re.escape(t)+r'(?![\w-])',nost):return True
    # dynamic class built from a prefix: rar-${r}, 'pos '+x, "x-"+y
    for k in range(1,len(t)):
        p=t[:k]
        if re.search(r'(?<![\w-])'+re.escape(p)+r"""(\$\{|'\s*\+|"\s*\+|`\s*\+)""",nost):return True
    return False
deadrules=set()
for ri,r in enumerate(rules):
    parts=[x.strip() for x in re.split(r',(?![^(]*\))',r['sel'])]
    def part_dead(p):
        toks=re.findall(r'[.#]([A-Za-z_][\w-]*)',re.sub(r':not\([^)]*\)|:is\([^)]*\)|:where\([^)]*\)|\[[^\]]*\]','',p))
        return any(not token_used(t) for t in toks)
    if parts and all(part_dead(p) for p in parts):deadrules.add(ri)
# --- plan edits
edits=[]
for ri,r in enumerate(rules):
    if protected(r['sel_start'],r['end']):
        continue
    if ri in deadrules:edits.append((r['sel_start'],r['end'],'rule',r['sel'][:60]));continue
    keep=[d for d in r['decls'] if (ri,d['start']) not in dead]
    if len(keep)<len(r['decls']):
        if not keep:edits.append((r['sel_start'],r['end'],'empty',r['sel'][:60]))
        else:
            for d in r['decls']:
                if (ri,d['start']) in dead:edits.append((d['start'],d['end'],'decl',r['sel'][:40]+' '+d['prop']))
for name,a,b in kfs:
    if protected(a,b):continue
    rest=src[:a]+src[b:]
    if not re.search(r'(?<![\w-])'+re.escape(name)+r'(?![\w-])',rest+open(ROOT+'tools/make_basketball.py').read()):edits.append((a,b,'keyframes',name))
edits.sort()
saved=sum(b-a for a,b,_,_ in edits)
from collections import Counter
print('rules',len(rules),'dead decls',len(dead),'dead rules',len(deadrules),'edits',len(edits),'saves %d KB'%(saved//1024),Counter(e[2] for e in edits))
json.dump(edits,open('/home/claude/cmp/cssplan.json','w'))
if '--apply' in sys.argv:
    out=src
    for a,b,_,_ in sorted(edits,reverse=True):out=out[:a]+out[b:]
    open(ROOT+'index.html','w').write(out);print('applied',len(src)//1024,'->',len(out)//1024,'KB')
