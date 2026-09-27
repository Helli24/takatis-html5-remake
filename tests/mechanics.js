const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});
const p=await b.newPage({viewport:{width:900,height:700}});await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});const errs=[];
p.on('pageerror',e=>errs.push('PAGEERR '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('CONSOLE '+m.text())});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2500);
const R={};
// start stage 1 via the debug hook and clear enemies
await p.evaluate(()=>{__startBoss(1);const {G}=__dbg();G.scroll=0;G.enemies=[];G.next=1e9;G.lives=5;});
const key=async(code,down)=>p.evaluate(([c,d])=>dispatchEvent(new KeyboardEvent(d?'keydown':'keyup',{code:c,key:c})),[code,down]);
const st=()=>p.evaluate(()=>{const {G,P}=__dbg();return {x:P.x,y:P.y,bank:P.bank,beam:P.beam,shots:G.shots.filter(s=>!s.own).map(s=>[s.type,s.x,s.y,s.vx,s.vy,s.dmg]),lines:G.shots.filter(s=>s.type===5).length,energy:P.energy,dead:P.dead,lives:G.lives,rockets:P.rockets,linesN:P.lines,state:G.state}});
const tick=n=>p.evaluate(n=>__tick(n),n);
let a=await st();await key('ArrowRight',1);await tick(10);let c=await st();await key('ArrowRight',0);R.speedX=(c.x-a.x)/10;
a=await st();await key('ArrowDown',1);await tick(12);c=await st();await key('ArrowDown',0);R.speedY=(c.y-a.y)/12;R.bankDown=c.bank;
await key('ArrowUp',1);await key('ArrowDown',1);a=await st();await tick(5);c=await st();await key('ArrowUp',0);await key('ArrowDown',0);R.cancelMove=c.y-a.y;
// beam: 124 frames to full
await key('ControlLeft',1);await tick(124);R.beamFull=(await st()).beam;await key('ControlLeft',0);await tick(1);R.beamShot=(await st()).shots.map(s=>s[0]+'/'+s[5]);
await p.evaluate(()=>{__dbg().G.shots=[]});
// spread lvl4 one press
await p.evaluate(()=>{__dbg().P.lvl=[4,4,4];});
await key('Space',1);await tick(1);R.spread4=(await st()).shots.length;await tick(10);R.spreadHeld=(await st()).shots.length;await key('Space',0);
await p.evaluate(()=>{__dbg().G.shots=[]});
// laser: weapon 3
await key('Digit3',1);await tick(1);await key('Digit3',0);
await key('Space',1);await tick(30);const ls=(await st()).shots;await key('Space',0);R.laserShots=ls.length;R.laserY=ls.slice(0,2).map(s=>Math.round(s[2]));
await p.evaluate(()=>{__dbg().G.shots=[]});
// powerline
await key('Enter',1);await tick(1);await key('Enter',0);c=await st();R.powerline=[c.lines, c.linesN];
// death: 4 enemy-shot hits
await p.evaluate(()=>{const {G,P}=__dbg();G.shots=[];for(let i=0;i<4;i++)__eshot(P.x+10,P.y+10,'bullet');});
await tick(1);c=await st();R.afterHits=[c.energy,c.dead];
await tick(399);c=await st();R.afterDeath=[c.lives,c.dead,c.rockets,c.linesN,c.state,c.energy];
await p.screenshot({path:process.argv[3]+'/mech.png'});
console.log(JSON.stringify(R));console.log(errs.join('\n')||'no errors');await b.close();})();
