const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2000);
const out=await p.evaluate(()=>{__startBoss(1);const {G,P}=__dbg();G.scroll=0;G.enemies=[];G.next=1e9;P.lvl=[1,1,1];P.weapon=1;P.x=10;P.y=184;
  // monkeypatch solidAt-free check: record the first pair
  dispatchEvent(new KeyboardEvent('keydown',{code:'Space'}));__tick(1);dispatchEvent(new KeyboardEvent('keyup',{code:'Space'}));
  const a=G.shots.find(s=>s.type===7&&!s.b22),c=G.shots.find(s=>s.type===7&&s.b22);const res=[];for(let i=0;i<34;i++){res.push([a.off,c.off,a.act?'':'x']);__tick(1);}
  return {res,cool:P.cool};});
console.log(JSON.stringify(out.res.map(r=>r[0]+'/'+r[1]+r[2])));console.log(errs.join('\n')||'no errors');await b.close();})();
