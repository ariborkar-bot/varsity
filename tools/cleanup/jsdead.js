// Find top-level declarations in index.html's inline scripts that nothing references.
const fs=require('fs'),acorn=require('acorn'),walk=require('acorn-walk');
const ROOT='/home/claude/varsity/';const src=fs.readFileSync(ROOT+'index.html','utf8');
const re=/<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)<\/script>/g;let m;const scripts=[];
while((m=re.exec(src))){scripts.push({start:m.index+m[0].indexOf('>')+1,code:m[1]})}
// reference corpus outside index scripts: tools that inject code + other files
let extra='';for(const f of ['tools/make_basketball.py','tools/preview/make_previews.py','tools/preview/build_preview.py','tools/preview/make_newuser_preview.py','games.js','stats.js','sw.js','tools/add_scores.py'])try{extra+=fs.readFileSync(ROOT+f,'utf8')}catch(e){}
// html outside scripts (onclick=...)
const html=src.replace(re,'');
const decls=[];const refs=new Map();
scripts.forEach((s,si)=>{
  let ast;try{ast=acorn.parse(s.code,{ecmaVersion:'latest',sourceType:'script',allowHashBang:true})}catch(e){console.error('parse fail script',si,e.message);return}
  for(const n of ast.body){
    if(n.type==='FunctionDeclaration')decls.push({name:n.id.name,si,start:n.start,end:n.end,kind:'fn'});
    else if(n.type==='VariableDeclaration'&&n.declarations.length===1&&n.declarations[0].id.type==='Identifier'){
      const init=n.declarations[0].init;
      // only pure-ish initializers (functions, literals, objects/arrays) so removal can't drop side effects
      const pure=!init||['ArrowFunctionExpression','FunctionExpression','Literal','ObjectExpression','ArrayExpression','TemplateLiteral'].includes(init.type);
      if(pure)decls.push({name:n.declarations[0].id.name,si,start:n.start,end:n.end,kind:n.kind});
    }
  }
  walk.full(ast,node=>{if(node.type==='Identifier'){const a=refs.get(node.name)||[];a.push([si,node.start]);refs.set(node.name,a)}});
});
let dead=new Set();
for(let iter=0;iter<10;iter++){
  let added=0;
  for(const d of decls){
    if(dead.has(d))continue;
    const r=(refs.get(d.name)||[]).filter(([si,p])=>{
      if(si===d.si&&p>=d.start&&p<d.end)return false;           // inside itself
      for(const x of dead)if(si===x.si&&p>=x.start&&p<x.end)return false; // inside dead code
      return true});
    const word=new RegExp('(^|[^\\w$.])'+d.name.replace(/\$/g,'\\$')+'(?![\\w$])');
    if(r.length===0&&!word.test(extra)&&!word.test(html)){dead.add(d);added++}
  }
  if(!added)break;
}
const out=[...dead].map(d=>({name:d.name,kind:d.kind,a:scripts[d.si].start+d.start,b:scripts[d.si].start+d.end}));
out.sort((x,y)=>x.a-y.a);
fs.writeFileSync('/home/claude/cmp/jsplan.json',JSON.stringify(out));
console.log('decls',decls.length,'dead',out.length,'bytes',out.reduce((t,d)=>t+d.b-d.a,0));
console.log(out.map(d=>d.name+'('+(d.b-d.a)+')').join(' '));
