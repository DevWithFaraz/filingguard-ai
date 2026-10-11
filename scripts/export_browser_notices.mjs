import fs from 'node:fs';
import path from 'node:path';
const root=process.cwd();
fs.mkdirSync('.runtime/t059',{recursive:true});
const seen=new Map();
function resolvePackage(name, from) {
  let dir=from;
  while (true) {
    const candidate=path.join(dir,'node_modules',name,'package.json');
    if (fs.existsSync(candidate)) return candidate;
    const parent=path.dirname(dir); if (parent===dir) throw Error('Missing package '+name);
    dir=parent;
  }
}
function visit(file) {
  const p=JSON.parse(fs.readFileSync(file,'utf8'));
  const key=p.name+'@'+p.version;
  if(seen.has(key))return;
  const dir=path.dirname(file);
  const files=fs.readdirSync(dir).filter(f=>/^(license|licence|copying|notice)(\.|$)/i.test(f)&&fs.statSync(path.join(dir,f)).isFile());
  seen.set(key,{p,dir,files});
  for(const name of Object.keys(p.dependencies||{}))visit(resolvePackage(name,dir));
}
const web=JSON.parse(fs.readFileSync('apps/web/package.json','utf8'));
for(const name of Object.keys(web.dependencies))visit(resolvePackage(name,path.join(root,'apps/web')));
const out=['FilingGuard browser dependency notices','Generated from installed locked browser dependency closure; includes package dependencies, not only tree-shaken modules.','GSAP and @gsap/react: https://gsap.com/standard-license',''];
const inventory=[];
for(const [key,{p,dir,files}] of [...seen].sort((a,b)=>a[0].localeCompare(b[0]))) {
  inventory.push({package:key,license:p.license||'UNDECLARED',files,source:p.homepage||p.repository?.url||p.repository||null});
  out.push('='.repeat(72),key,'Declared license: '+(p.license||'UNDECLARED'),'Source: '+(p.homepage||p.repository?.url||p.repository||'See package metadata'));
  if(!files.length)out.push('Package supplies no separate root license file; consult declared license/source above.');
  for(const f of files)out.push('\n'+f+'\n',fs.readFileSync(path.join(dir,f),'utf8'));
}
fs.mkdirSync('apps/web/public',{recursive:true});
fs.writeFileSync('apps/web/public/third-party-notices.txt',out.join('\n'));
fs.writeFileSync('.runtime/t059/browser-license-inventory.json',JSON.stringify(inventory,null,2));
