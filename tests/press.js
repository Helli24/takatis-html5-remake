// shoot at the first press of 1-1 and record hp, draws and screenshots
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:700,height:520}});await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});
const errs=[];p.on('pageerror',e=>errs.push(e.message));
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(2000);
await p.evaluate(()=>{__lv(0);const {G}=__dbg();G.state='play';G.gamma=100;G.scroll=9778-640+100;G.next=0;
  const l=__dbg().G;});
const out=[];
for(let f=0;f<120;f++){
  const r=await p.evaluate((f)=>{const {G,P}=__dbg();P.dead=0;P.energy=3;P.x=300;P.y=80;
    const key=(t,c,k)=>dispatchEvent(new KeyboardEvent(t,{code:c,key:k}));
    if(f%4===0)key('keydown','Space',' ');if(f%4===2)key('keyup','Space',' ');
    __tick(1);const e=G.enemies.find(e=>e.type===26||e.type===27);
    return e?{f,x:e.x,y:e.y,hp:e.hp,dead:e.dead,fr:e.f,n:G.enemies.length,st:G.state}:{f,none:true,n:G.enemies.length,st:G.state,sc:G.scroll};},f);
  out.push(r);if(f>=40&&f<=46)await p.screenshot({path:`${process.argv[3]}/press_${f}.png`,clip:{x:30,y:20,width:640,height:480}});}
console.log(out.filter((r,i)=>i%6===0).map(r=>JSON.stringify(r)).join('\n'));console.log(errs.join('\n')||'no errors');await b.close();})();
