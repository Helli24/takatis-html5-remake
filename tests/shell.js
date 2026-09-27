// walks through the shell screens and takes screenshots
const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch({args:['--use-gl=swiftshader','--enable-webgl','--ignore-gpu-blocklist']});const p=await b.newPage({viewport:{width:700,height:520}});
await p.addInitScript(()=>{window.requestAnimationFrame=()=>0;});
const errs=[];p.on('pageerror',e=>errs.push('PAGE '+e.message));p.on('console',m=>{if(m.type()==='error')errs.push('CONS '+m.text())});
await p.goto('file://'+process.argv[2]);await p.waitForTimeout(3000);
const out=process.argv[3];let shotN=0;
const tick=n=>p.evaluate(n=>{__tick(n);const {G}=__dbg();return {state:G.state,sub:G.sub,sel:G.sel,blk:!!G.blk,wait:!!G.wait,go:G.go,over:G.over,gamma:G.gamma,err:window.__lastErr||null};},n);
const down=c=>p.evaluate(c=>dispatchEvent(new KeyboardEvent('keydown',{code:c,key:c})),c);
const up=c=>p.evaluate(c=>dispatchEvent(new KeyboardEvent('keyup',{code:c,key:c})),c);
const tap=async(c,hold=2)=>{await down(c);await tick(hold);await up(c);return tick(2);};
const shot=async name=>{await p.screenshot({path:`${out}/sh_${String(++shotN).padStart(2,'0')}_${name}.png`,clip:{x:30,y:20,width:640,height:480}});};
const log=(n,r)=>console.log(n,JSON.stringify(r));
log('boot',await tick(2));await shot('boot');
await p.evaluate(()=>{__dbg().G.clicked=true;});log('click',await tick(3));
log('intro0',await tick(300));await shot('pl');            // Poke53280 fade in
log('intro',await tick(700));await shot('loading');
log('intro',await tick(650));await shot('intro1');
const want=async(st,msg)=>{let r;for(let i=0;i<20;i++){r=await tick(1);if(r.state===st)return r;}console.log('!! expected',st,'got',r.state,msg||'');return r;};
await down('Escape');log('esc',await tick(5));await up('Escape');log('after esc (menu)',await tick(3));
const cur=async()=>(await tick(1)).state;
const toMenu=async()=>{for(let k=0;k<5;k++){const s=await cur();if(s==='menu')return;if(s==='title')await tap('Space');else await tap('Escape');}};
const item=async(i,st)=>{await toMenu();for(let k=0;k<6;k++)await tap('ArrowUp');for(let k=0;k<i;k++)await tap('ArrowDown');await tap('Enter');return want(st);};
await tap('Escape');await want('title');log('title',await tick(60));await shot('title');
await toMenu();await shot('menu');await tap('ArrowDown');await shot('menu_sel1');
await item(1,'options');await shot('options');
await down('ArrowRight');await tick(10);await up('ArrowRight');
await tap('ArrowDown');await tap('ArrowDown');await tick(2);await shot('options_jukebox');
await item(2,'help');await shot('help1');
for(let i=2;i<=5;i++){await tap('ArrowDown');await tick(2);await shot('help'+i);}
await item(3,'hiscore');await tick(60);await shot('highscore');
await down('F8');await tick(2);await up('F8');await tick(2);await shot('highscore_nofx');
await down('F7');await tick(2);await up('F7');await tick(150);await shot('highscore_fx');
await item(4,'credits');await tick(200);await shot('credits');await tick(600);await shot('credits2');
await item(0,'newgame');await shot('newgame');
await tap('ArrowRight');await tick(2);await shot('newgame_normal');
await tap('Enter');log('start',await tick(1));await tick(20);await shot('ready');log('ready',await tick(200));await shot('play');
await tap('F1');log('help ingame',await tick(3));await shot('ingame_help');await tap('Escape');log('back',await tick(3));
await tap('F2');log('opts ingame',await tick(3));await shot('ingame_options');await tap('Escape');log('back',await tick(3));
await tap('Escape');log('quit dlg',await tick(3));await shot('ingame_quit');await tap('ArrowRight');await tick(2);await shot('ingame_quit_ja');
await tap('ArrowLeft');await tap('Enter');log('back to game',await tick(3));
await p.evaluate(()=>{const {G,P}=__dbg();G.lives=1;G.score=65000;P.dead=2;});log('dying',await tick(3));log('fade',await tick(60));
log('go',await tick(40));await shot('gameover_rise');log('go3',await tick(150));await shot('gameover_entry');
for(const c of ['KeyT','KeyE','KeyS','KeyT']){await tap(c,1);await tick(12);}
await down('ShiftLeft');await tap('KeyX',1);await up('ShiftLeft');await tick(12);await shot('gameover_name');
log('enter name',await tap('Enter'));await tick(10);await shot('highscore_new');
console.log(errs.slice(0,8).join('\n')||'no errors');await b.close();})();
