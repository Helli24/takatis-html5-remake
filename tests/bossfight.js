// usage: node bossfight.js html outdir id frameList [fire=1] [killAt=-1]
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});const p=await b.newPage({viewport:{width:700,height:520}});await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});
const errs=[];p.on('pageerror',e=>errs.push('PAGE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('CONS '+m.text())});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2500);
const id=+process.argv[4];const shots=(process.argv[5]||'200,500,900').split(',').map(Number);const fire=+(process.argv[6]||1),killAt=+(process.argv[7]||-1);
await p.evaluate(id=>{__startBoss(id);},id);
let t=0;
for(const target of shots){
  const r=await p.evaluate(([t0,n,fire,killAt])=>{const {G}=__dbg();let err=null;const key=(type,code,k)=>dispatchEvent(new KeyboardEvent(type,{code,key:k}));
    for(let i=0;i<n;i++){const P=__dbg().P,f=t0+i;P.dead=0;P.energy=3;
      if(G.bossActive){const by=__boss().by,bh=270;P.y=Math.max(0,Math.min(380,(by-16)+100));
        if(fire&&f%8===0)key('keydown','Space',' ');if(fire&&f%8===4)key('keyup','Space',' ');}
      if(f===killAt){key('keydown','F4','F4');}if(f===killAt+2)key('keyup','F4','F4');
      try{__tick(1);}catch(e){err=String(e.stack||e);break;}if(G.state==='dead')G.state='play';}
    const B=G.boss;return {err,state:G.state,phase:B&&B.phase,boss:__boss(),fx:__fx(),endPhase:G.endPhase,endT:G.endT,px:__dbg().P.x,score:G.score,level:G.level};},[t,target-t,fire,killAt]);
  t=target;console.log(target,JSON.stringify(r));
  await p.screenshot({path:`${process.argv[3]}/fight${id}_${target}.png`,clip:{x:30,y:20,width:640,height:480}});
  if(r.err)break;}
console.log(errs.slice(0,5).join('\n')||'no errors');await b.close();})();
