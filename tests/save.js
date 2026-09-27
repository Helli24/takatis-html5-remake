// boss 1 -> save screen -> slot 2 -> quit -> new game shows slot -> load it
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});const p=await b.newPage({viewport:{width:700,height:520}});
await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});
const errs=[];p.on('pageerror',e=>errs.push('PAGE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('CONS '+m.text())});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(3000);const out=process.argv[3];
await p.evaluate(()=>{for(let i=0;i<6;i++)localStorage.removeItem('takatis.slot'+i);});
const st=()=>p.evaluate(()=>{const {G,P}=__dbg();return {state:G.state,sel:G.sel,level:G.level,lives:G.lives,score:G.score,diff:G.diff,over:G.over,lvl:P&&P.lvl,rockets:P&&P.rockets,weapon:P&&P.weapon};});
const tick=n=>p.evaluate(n=>{__tick(n);},n);
const down=c=>p.evaluate(c=>dispatchEvent(new KeyboardEvent('keydown',{code:c,key:c})),c);
const up=c=>p.evaluate(c=>dispatchEvent(new KeyboardEvent('keyup',{code:c,key:c})),c);
const tap=async(c,hold=2)=>{await down(c);await tick(hold);await up(c);await tick(2);};
const shot=async n=>p.screenshot({path:`${out}/sv_${n}.png`,clip:{x:30,y:20,width:640,height:480}});
await p.evaluate(()=>{__startBoss(1);const {G,P}=__dbg();P.lvl=[2,1,0];P.rockets=3;G.lives=4;G.diff=1;});
for(let f=0;f<3000;f++){const s=await p.evaluate(f=>{const {G,P}=__dbg();P.dead=0;P.energy=3;if(f===1200)dispatchEvent(new KeyboardEvent('keydown',{code:'F4',key:'F4'}));if(f===1202)dispatchEvent(new KeyboardEvent('keyup',{code:'F4',key:'F4'}));__tick(1);return G.state;},f);if(s==='save'){console.log('save at',f);break;}}
await tick(3);await tap('ArrowDown');await shot('save');console.log('save',JSON.stringify(await st()));
await tap('Enter');await tick(3);console.log('after save',JSON.stringify(await st()));
console.log('stored',await p.evaluate(()=>localStorage.getItem('takatis.slot1')));
for(let i=0;i<300&&(await st()).state!=='play';i++)await tick(1);console.log('play',JSON.stringify(await st()));
await tap('Escape');await tap('ArrowRight');await tap('Enter');await tick(3);console.log('quit',JSON.stringify(await st()));
await tap('Space');await tick(3);console.log('menu?',JSON.stringify(await st()));
await tap('ArrowUp');await tap('Enter');await tick(3);console.log('newgame?',JSON.stringify(await st()));
await tap('ArrowDown');await tap('ArrowDown');await tick(2);await shot('newgame_slots');
await tap('Enter');await tick(3);console.log('loaded',JSON.stringify(await st()));await tick(30);await shot('loaded_ready');
console.log(errs.slice(0,8).join('\n')||'no errors');await b.close();})();
