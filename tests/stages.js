const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2000);
for(let lv=0;lv<12;lv++){
 const r=await p.evaluate(lv=>{window.__wall={};__startBoss(1);const {G}=__dbg();__lv(lv);G.state="play";G.gamma=100;G.speed=1;
   const seen={},shotsBy={};let n=0,maxE=0;
   while(G.scroll<G.maxScroll-2&&n<40000){const P=__dbg().P;P.dead=0;P.energy=3;P.y=184;P.x=200;__tick(1);n++;if(G.state!=='play')G.state='play';
     for(const e of G.enemies)seen[e.type]=(seen[e.type]||0)+0;maxE=Math.max(maxE,G.enemies.length);}
   const spawned={};for(const o of __dbg().G?[]:[]){}
   return {lv,frames:n,maxE,wall:window.__wall,eshots:G.shots.length};},lv);
 console.log(JSON.stringify(r));}
console.log(errs.join('\n')||'no errors');await b.close();})();
