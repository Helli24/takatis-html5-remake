"""Spinner cooldown fix, bigger death explosion, HUD digit tuning, and the original menu system."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, 'template.html')
t = open(p, encoding='utf-8').read()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


# --- 1) spinner: cooldown must tick every frame, the frame-1 gate only decides when it may fire
rep("      case 2:e.f=animFrame(e);if(e.f===1&&--e.shoot<=0&&e.x<W&&(Math.random()*11|0)===1){eshot(e.x,e.y+3,-5,0,'blob');eshot(e.x,e.y+33,-5,0,'blob');sfx('laser',0.3);e.shoot=10;}break;",
    "      case 2:e.f=animFrame(e);if(e.shoot>0)e.shoot--;\n        if(e.f===1&&e.shoot<=0&&e.x<W&&(Math.random()*11|0)===1){eshot(e.x,e.y+3,-5,0,'blob');eshot(e.x,e.y+33,-5,0,'blob');sfx('laser',0.3);e.shoot=10;}break;")

# --- 2) death explosion: fireball + debris + smoke instead of a single sprite
rep("function explode(x,y,big,player){G.fx.push({spr:big?'explosion':'explosion2',x:x-(big?30:24),y:y-(big?25:24),f:0,rate:big?4:5,n:big?8:6});sfx(player?'bigexplosion':'explosion',player?0.8:0.45,big?1:1.3);}",
    """function explode(x,y,big,player){
  G.fx.push({spr:'explosion',x:x-30,y:y-25,f:0,rate:4,n:8});
  if(big){G.fx.push({spr:'explosion2',x:x-24-14,y:y-24+6,f:-2,rate:5,n:6});
          G.fx.push({spr:'explosion2',x:x-24+16,y:y-24-10,f:-4,rate:5,n:6});}
  const n=big?7:4;
  for(let i=0;i<n;i++){const a=Math.random()*Math.PI*2,s=1+Math.random()*(big?3.5:2.2);
    G.fx.push({spr:'debris'+(1+(i%3)),x:x-8,y:y-8,vx:Math.cos(a)*s,vy:Math.sin(a)*s,f:0,rate:3,n:16,grav:true,life:big?55:35});}
  for(let i=0;i<(big?4:2);i++)G.fx.push({spr:'smoke',x:x-8+(Math.random()-.5)*22,y:y-8+(Math.random()-.5)*22,vx:-0.4,vy:-0.5,f:0,rate:3,n:16});
  sfx(player?'bigexplosion':'explosion',player?0.8:0.5,big?0.9:1.25);}""")

# --- 3) HUD digits: narrower dash, and optically centred in the box (the original sits 2 px higher)
rep("else if(ch==='-'){ctx.fillStyle='#b9b9b9';ctx.fillRect(x+1,y+4,6,2);}",
    "else if(ch==='-'){ctx.fillStyle='#b9b9b9';ctx.fillRect(x+2,y+4,5,2);}")
rep("num(G.lives,98,455);num(level().stage,161,455);num(G.score,514,455);",
    "num(G.lives,98,457);num(level().stage,160,457);num(G.score,514,457);")

# --- 4) menu system (main menu from menu.gfx, start submenu with difficulty and 6 save slots)
rep("const ITEM_FRAME=", """const MENU_ITEMS=['start','options','help','highscore','credits','quit'];
const SLOTS=6;
function slotKey(i){return 'takatis.slot'+i;}
function readSlot(i){try{return JSON.parse(localStorage.getItem(slotKey(i)));}catch(e){return null;}}
function writeSlot(i,v){try{localStorage.setItem(slotKey(i),JSON.stringify(v));}catch(e){}}
function panel(x,y,w,h){ctx.fillStyle='rgba(46,32,18,.95)';ctx.fillRect(x,y,w,h);
  ctx.strokeStyle='#7d6134';ctx.lineWidth=3;ctx.strokeRect(x+1.5,y+1.5,w-3,h-3);
  ctx.strokeStyle='#3a2a14';ctx.lineWidth=1;ctx.strokeRect(x+5.5,y+5.5,w-11,h-11);}
const ITEM_FRAME=""")

rep("case 'title':if(pressed.KeyC){", """case 'menu':{
      if(pressed.ArrowUp)G.menuSel=(G.menuSel+MENU_ITEMS.length-1)%MENU_ITEMS.length;
      if(pressed.ArrowDown)G.menuSel=(G.menuSel+1)%MENU_ITEMS.length;
      if(pressed.Escape)G.state='title';
      if(pressed.Enter||pressed.Space){const it=MENU_ITEMS[G.menuSel];
        if(it==='start'){G.state='start';G.startRow=0;G.slotSel=0;}
        else if(it==='options'){G.state='options';G.optSel=0;}
        else if(it==='help'){G.state='help';G.page=0;}
        else if(it==='highscore')G.state='hiscore';
        else if(it==='credits'){G.state='credits';G.creditY=PH;}
        else if(it==='quit')G.state='title';}
      break;}
    case 'start':{
      if(pressed.ArrowUp)G.startRow=Math.max(0,G.startRow-1);
      if(pressed.ArrowDown)G.startRow=Math.min(SLOTS,G.startRow+1);
      if(G.startRow===0){if(pressed.ArrowLeft)G.diff=Math.max(0,G.diff-1);if(pressed.ArrowRight)G.diff=Math.min(2,G.diff+1);}
      if(pressed.Escape)G.state='menu';
      if(pressed.Enter||pressed.Space){
        if(G.startRow===0){G.lives=5;G.score=0;P=null;G.slot=null;startLevel(0);}
        else{const sv=readSlot(G.startRow-1);
          if(sv){G.diff=sv.diff;G.lives=sv.lives;G.score=sv.score;G.slot=G.startRow-1;P=newPlayer();P.lvl=sv.lvl.slice();P.weapon=sv.weapon;P.rockets=sv.rockets;P.lines=sv.lines;startLevel(sv.level);}
          else{G.lives=5;G.score=0;P=null;G.slot=G.startRow-1;startLevel(0);}}}
      break;}
    case 'options':{
      if(pressed.ArrowUp)G.optSel=(G.optSel+2)%3;if(pressed.ArrowDown)G.optSel=(G.optSel+1)%3;
      if(pressed.ArrowLeft||pressed.ArrowRight){const d=pressed.ArrowRight?1:-1;
        if(G.optSel===0)MUSIC.vol=Math.max(0,Math.min(1,MUSIC.vol+d*0.1));
        else if(G.optSel===1)G.sfxVol=Math.max(0,Math.min(1,(G.sfxVol===undefined?1:G.sfxVol)+d*0.1));
        else G.diff=Math.max(0,Math.min(2,G.diff+d));}
      if(pressed.Escape||pressed.Enter)G.state='menu';
      break;}
    case 'help':{
      if(pressed.ArrowDown||pressed.ArrowRight)G.page=Math.min(HELP.length-1,G.page+1);
      if(pressed.ArrowUp||pressed.ArrowLeft)G.page=Math.max(0,G.page-1);
      if(pressed.Escape||pressed.Enter)G.state='menu';
      break;}
    case 'hiscore':{if(pressed.Escape||pressed.Enter||pressed.Space)G.state='menu';break;}
    case 'credits':{G.creditY-=0.6;if(pressed.Escape||pressed.Enter||G.creditY<-CREDITS.length*18-40)G.state='menu';break;}
    case 'title':if(pressed.Escape){G.state='menu';G.menuSel=0;break;}
      if(pressed.KeyC){""")

# title screen keeps working (Enter still starts directly)
rep("drawCenter('HIGHSCORE '+G.hiscore,360,3);let sv=null;try{sv=JSON.parse(localStorage.getItem('takatis.save'));}catch(e){}if(sv)drawCenter('C - CONTINUE SAVED GAME (STAGE '+LEVELS[sv.level].stage+')',390,3);return;}",
    "drawCenter('HIGHSCORE '+G.hiscore,360,3);return;}")

# menu rendering
rep("  drawPlayfield();drawHUD();", """  if(G.state==='menu'||G.state==='start'||G.state==='options'||G.state==='help'||G.state==='hiscore'||G.state==='credits'){
    ctx.drawImage(S.title.img,0,0);drawMenus();return;}
  drawPlayfield();drawHUD();""")
rep("function drawCenter(str,y,row=0){text(str,W/2,y,row,1);}", """function drawCenter(str,y,row=0){text(str,W/2,y,row,1);}
const HELP=[['STEUERUNG','CURSOR / NUMPAD  BEWEGEN','SPACE  PRIMAERWAFFE','STRG  BEAM AUFLADEN','SHIFT  RAKETE','RETURN  POWERLINE','1 2 3  WAFFE WAEHLEN','P  PAUSE   ESC  MENUE'],
 ['PRIMAERWAFFEN','SPREAD SHOT  4 STUFEN','  BREITER STREUWINKEL','LASER  4 STUFEN','  DAUERFEUER, SCHNELL','BOUNCE  4 STUFEN','  TEILT SICH AN WAENDEN'],
 ['SEKUNDAERWAFFEN','BEAM  4 LADESTUFEN','RAKETE  ZIELSUCHEND','POWERLINE  KRAFTFELD','SCHILD  KURZ UNVERWUNDBAR','ONE UP  EXTRALEBEN'],
 ['CONTAINER','TRAEGER TRAGEN EXTRAS','ABSCHIESSEN GIBT MEHR','ALS DAS EINSAMMELN','','SPEED TRIGGER AENDERN','DIE SCROLLGESCHWINDIGKEIT'],
 ['DIE STORY','DU SITZT AM STEUERKNUEPPEL','EINES RAUMGLEITERS UND','FLIEGST DURCH EINE WELT','VOLLER FINSTERER GESTALTEN','','LETS BLAST THESE ALIENS']];
const CREDITS=['TAKATIS','A TRIBUTE TO MANFRED TRENZ','','PROGRAMMIERUNG','HEIKO KALISTA','','GRAFIK MUSIK LEVELDESIGN','JOERG M WINTERSTEIN','','3D MODELLE','MICHAEL MATZKA','','VOICES','ALEXANDRA HERTSTEIN','SEB KUGLER','','(C) 2002 POKE53280','','BROWSER REMAKE','AUS DEN ORIGINALDATEN'];
function drawMenus(){
  if(G.state==='menu'){const bw=224,bh=64;panel(W/2-bw/2-16,28,bw+32,bh*MENU_ITEMS.length+24);
    for(let i=0;i<MENU_ITEMS.length;i++)ctx.drawImage(S.menu.img,(i===G.menuSel?0:224),i*64,224,64,W/2-bw/2,40+i*64,224,64);
    return;}
  if(G.state==='start'){panel(60,60,520,340);
    drawCenter('START GAME',78,0);
    drawCenter('START A NEW GAME',110,1);
    const dn=['EASY','NORMAL','HARD'];
    for(let i=0;i<3;i++)text(dn[i],150+i*130,134,G.diff===i?2:3,1);
    if(G.startRow===0){text('>',96,134,2,1);text('<',520,134,2,1);}
    drawCenter('CONTINUE A SAVED GAME',166,1);
    text('SLOT  STAGE LIVES  WEAPONS   SKILL  SCORE',300,190,3,1);
    for(let i=0;i<SLOTS;i++){const sv=readSlot(i);const y=212+i*28;const sel=G.startRow===i+1;
      if(sel){ctx.fillStyle='rgba(160,120,40,.25)';ctx.fillRect(70,y-3,500,24);}
      text(String(i+1),90,y,sel?2:3,1);
      if(!sv)text('-- EMPTY SLOT --',300,y,sel?2:3,1);
      else{text(LEVELS[sv.level].stage,160,y,sel?2:3,1);text(String(sv.lives),225,y,sel?2:3,1);
        for(let w=0;w<3;w++)text(String(sv.lvl[w]),275+w*26,y,sel?2:3,1);
        text(dn[sv.diff],420,y,sel?2:3,1);text(String(sv.score),520,y,sel?2:3,1);}}
    return;}
  if(G.state==='options'){panel(120,120,400,220);drawCenter('OPTIONS',140,0);
    const rows=[['MUSIK',Math.round(MUSIC.vol*10)],['SOUND',Math.round((G.sfxVol===undefined?1:G.sfxVol)*10)],['SKILL',['EASY','NORMAL','HARD'][G.diff]]];
    rows.forEach((r,i)=>{const y=190+i*40;text(r[0],200,y,G.optSel===i?2:3,1);text(String(r[1]),380,y,G.optSel===i?2:3,1);});
    drawCenter('ESC  ZURUECK',310,3);return;}
  if(G.state==='help'){panel(60,60,520,340);const pg=HELP[G.page];
    drawCenter(pg[0],86,0);
    for(let i=1;i<pg.length;i++)text(pg[i],90,124+(i-1)*28,i===1?2:3);
    drawCenter('SEITE '+(G.page+1)+'/'+HELP.length+'   CURSOR BLAETTERN   ESC',368,3);return;}
  if(G.state==='hiscore'){panel(140,100,360,260);drawCenter('HIGHSCORE',124,0);
    drawCenter(String(G.hiscore),180,2);drawCenter('LETZTES SPIEL',230,3);drawCenter(String(G.score),260,3);
    drawCenter('ESC  ZURUECK',330,3);return;}
  if(G.state==='credits'){ctx.fillStyle='rgba(0,0,0,.6)';ctx.fillRect(0,0,W,H);
    CREDITS.forEach((l,i)=>{const y=G.creditY+i*20;if(y>-20&&y<H)text(l,W/2,y,l===l.toUpperCase()&&i<2?0:3,1);});return;}}""")
# a saved game now goes into the chosen slot
rep("if(G.level%2===1){try{localStorage.setItem('takatis.save',JSON.stringify({level:G.level+1,score:G.score,lives:G.lives,lvl:P.lvl,weapon:P.weapon,rockets:P.rockets,lines:P.lines,diff:G.diff}));}catch(e){}}",
    "if(G.level%2===1&&G.slot!==null&&G.slot!==undefined)writeSlot(G.slot,{level:G.level+1,score:G.score,lives:G.lives,lvl:P.lvl,weapon:P.weapon,rockets:P.rockets,lines:P.lines,diff:G.diff});")
rep("enemies:[],shots:[],eshots:[],fx:[],items:[],lines:[],timer:0,music:null,stageClear:false,hiscore:0};",
    "enemies:[],shots:[],eshots:[],fx:[],items:[],lines:[],timer:0,music:null,stageClear:false,hiscore:0,menuSel:0,startRow:0,slotSel:0,optSel:0,page:0,creditY:0,slot:null,sfxVol:1};")
# sound volume option
rep("function sfx(name,vol=0.6,rate=1){if(!AC||muted||!buffers[name])return;",
    "function sfx(name,vol=0.6,rate=1){if(!AC||muted||!buffers[name])return;vol*=(G.sfxVol===undefined?1:G.sfxVol);if(vol<=0)return;")
# quitting a game returns to the menu, not the title
rep("G.hiscore=Math.max(G.hiscore,G.score);try{localStorage.setItem('takatis.hiscore',G.hiscore);}catch(e){}G.state='title';musicPlay('title');}else G.state='play';}",
    "G.hiscore=Math.max(G.hiscore,G.score);try{localStorage.setItem('takatis.hiscore',G.hiscore);}catch(e){}G.state='menu';G.menuSel=0;musicPlay('title');}else G.state='play';}")
open(p, 'w', encoding='utf-8').write(t)
print('patched')
