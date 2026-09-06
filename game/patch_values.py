"""HUD digits (font2), original animation speeds, original spinner fire rule, original weapon damage."""
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')
t = open(p, encoding='utf-8').read()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


# --- 1) HUD numbers use font2.gfx (8x10 silver digits), measured from the original video: ink rows 455..463
rep("function small(str,x,y){str=String(str);const s=S.font2;for(let i=0;i<str.length;i++){const c=str.charCodeAt(i)-48;if(c<0||c>9)continue;ctx.drawImage(s.img,c*8,0,8,10,x+i*8,y,8,10);}}",
    """function num(str,cx,y){str=String(str);const s=S.font2;let x=Math.round(cx-str.length*4);
  for(const ch of str){const c=ch.charCodeAt(0)-48;
    if(c>=0&&c<=9)ctx.drawImage(s.img,c*8,0,8,10,x,y,8,10);
    else if(ch==='-'){ctx.fillStyle='#b9b9b9';ctx.fillRect(x+1,y+4,6,2);}
    x+=8;}}""")
rep("text(G.lives,96,453,0,1);text(level().stage,159,453,0,1);text(G.score,512,453,0,1);",
    "num(G.lives,96,455);num(level().stage,159,455);num(G.score,512,455);")

# --- 2) animation frames/delay per enemy type, straight from the enemy init function (fields +0x3c, +0x44)
rep("const WALL_DIE=new Set([0,1,2,9,15,24,33]);",
    """const WALL_DIE=new Set([0,1,2,9,15,24,33]);
// [frame count, frame delay] per enemy type - from Takatis.exe enemy init (+0x3c, +0x44)
const ANIM={0:[32,5],1:[5,9],2:[16,7],9:[1,1],10:[3,10],11:[3,10],12:[8,10],13:[4,6],14:[4,10],15:[5,12],16:[8,7],17:[1,1],
  18:[1,1],19:[1,1],20:[1,1],21:[1,1],22:[9,10],23:[4,10],24:[4,16],25:[18,8],26:[1,1],27:[1,1],28:[6,7],29:[3,10],30:[5,15],31:[10,60],32:[5,8],33:[1,1]};
function animFrame(e){const a=ANIM[e.type];if(!a)return Math.floor(e.t/6);return Math.floor(e.t/a[1])%a[0];}""")
for old, new in [
    ("case 0:e.f+=e.rot;break;", "case 0:e.f+=e.rot;break;"),
    ("      case 1:e.f=Math.floor(e.t/5);break;", "      case 1:e.f=animFrame(e);break;"),
    ("      case 15:e.f=Math.floor(e.t/5);if(--e.shoot<=0&&e.x<W){eshot(e.x-15,e.y+7,-4,0,'chaseshot');sfx('laser',0.3);e.shoot=150;}break;",
     "      case 15:e.f=animFrame(e);if(--e.shoot<=0&&e.x<W){eshot(e.x-15,e.y+7,-4,0,'chaseshot');sfx('laser',0.3);e.shoot=150;}break;"),
    ("      case 24:e.f=Math.floor(e.t/5);", "      case 24:e.f=animFrame(e);"),
    ("      case 12:e.f=Math.floor(e.t/8)%4;", "      case 12:e.f=animFrame(e);"),
    ("      case 14:e.f=Math.floor(e.t/6);", "      case 14:e.f=animFrame(e);"),
    ("      case 13:e.f=Math.floor(e.t/6);break;", "      case 13:e.f=animFrame(e);break;"),
    ("      case 16:e.f=Math.floor(e.t/6);if(dist<260", "      case 16:e.f=animFrame(e);if(dist<260"),
    ("e.f=Math.floor(e.t/6)%9+(e.vy>0?0:9);", "e.f=Math.floor(e.t/8)%9+(e.vy>0?0:9);"),
    ("      case 28:if(!e.staticPath){e.f=Math.floor(e.t/4);break;}", "      case 28:if(!e.staticPath){e.f=animFrame(e);break;}"),
    ("      case 29:e.f=Math.floor(e.t/10)%3;", "      case 29:e.f=animFrame(e);"),
    ("      case 30:e.y+=e.vy;if(solidAt(cx,e.y-1)||solidAt(cx,e.y+e.h+1)||e.y<0||e.y+e.h>PH)e.vy=-e.vy;e.f=Math.floor(e.t/5);",
     "      case 30:e.y+=e.vy;if(solidAt(cx,e.y-1)||solidAt(cx,e.y+e.h+1)||e.y<0||e.y+e.h>PH)e.vy=-e.vy;e.f=animFrame(e);"),
    ("      case 32:e.f=Math.floor(e.t/6);", "      case 32:e.f=animFrame(e);"),
    ("      case 22:e.f=Math.floor(e.t/3);break;case 23:e.f=Math.floor(e.t/5);break;", "      case 22:e.f=animFrame(e);break;case 23:e.f=animFrame(e);break;"),
    ("      default:e.f=Math.floor(e.t/6);", "      default:e.f=animFrame(e);"),
]:
    rep(old, new)

# --- 3) spinner: the original only fires on animation frame 1, with a 1/11 chance and a 10 frame cooldown
rep("      case 2:e.f=Math.floor(e.t/3);if(--e.shoot<=0&&e.x<W&&Math.floor(Math.random()*11)===1){eshot(e.x,e.y+3,-5,0,'blob');eshot(e.x,e.y+33,-5,0,'blob');sfx('laser',0.3);e.shoot=10;}break;",
    "      case 2:e.f=animFrame(e);if(e.f===1&&--e.shoot<=0&&e.x<W&&(Math.random()*11|0)===1){eshot(e.x,e.y+3,-5,0,'blob');eshot(e.x,e.y+33,-5,0,'blob');sfx('laser',0.3);e.shoot=10;}break;")

# --- 4) weapon damage and shot counts exactly as in the original (7th argument of the shot spawn call)
rep("""function fireSpread(){const lv=P.lvl[0];const angs=[[0],[-10,10],[0,-20,20],[0,-10,10,-35,35]][lv-1];const FR={0:0,'-10':1,10:2,'-20':3,20:4,'-35':5,35:6};
  for(const a of angs){const r=a*Math.PI/180;G.shots.push({kind:'spread',x:P.x+42,y:P.y+9,w:18,h:17,vx:Math.cos(r)*8,vy:Math.sin(r)*8,dmg:1,f:0,fixed:FR[a]});}""",
    """function fireSpread(){const lv=P.lvl[0];   // 1/3/5/7 shots, integer velocities, 3 damage each
  const V=[[[8,0]],[[8,0],[7,-1],[7,1]],[[8,0],[7,-1],[7,1],[6,-2],[6,2]],[[8,0],[7,-1],[7,1],[6,-2],[6,2],[5,-3],[5,3]]][lv-1];
  const FR={0:0,'-1':1,1:2,'-2':3,2:4,'-3':5,3:6};
  for(const v of V)G.shots.push({kind:'spread',x:P.x+42,y:P.y+9,w:18,h:17,vx:v[0],vy:v[1],dmg:3,f:0,fixed:FR[v[1]]});""")
rep("""  G.shots.push({kind:'laser',x:P.x+40,y:P.y+8+off,w:24,h:12,vx:10,vy:0,dmg:2,f:0,sine:1,ph:P.laserPhase});
  G.shots.push({kind:'laser',x:P.x+40,y:P.y+8-off,w:24,h:12,vx:10,vy:0,dmg:2,f:0,sine:1,ph:P.laserPhase+Math.PI});""",
    """  const dm=[5,4,3,3][lv-1];   // damage per stage from the original
  G.shots.push({kind:'laser',x:P.x+40,y:P.y+8+off,w:24,h:12,vx:5,vy:0,dmg:dm,f:0,sine:1,ph:P.laserPhase});
  G.shots.push({kind:'laser',x:P.x+40,y:P.y+8-off,w:24,h:12,vx:5,vy:0,dmg:dm,f:0,sine:1,ph:P.laserPhase+Math.PI});""")
rep("function fireBounce(){const lv=P.lvl[2];G.shots.push({kind:'bounce1',x:P.x+40,y:P.y+5,w:24,h:24,vx:6,vy:0,dmg:3,f:0,bounce:true,size:1});\n  if(lv>=4){G.shots.push({kind:'bounce3',x:P.x+40,y:P.y+5,w:12,h:12,vx:5,vy:-3,dmg:1,bounce:true,size:3});G.shots.push({kind:'bounce3',x:P.x+40,y:P.y+15,w:12,h:12,vx:5,vy:3,dmg:1,bounce:true,size:3});}",
    "function fireBounce(){const lv=P.lvl[2];G.shots.push({kind:'bounce1',x:P.x+40,y:P.y+5,w:24,h:24,vx:9,vy:0,dmg:4,f:0,bounce:true,size:1,bounces:0});\n  if(lv>=4){G.shots.push({kind:'bounce3',x:P.x+40,y:P.y+5,w:12,h:12,vx:8,vy:-3,dmg:3,f:0,bounce:true,size:3,bounces:0});G.shots.push({kind:'bounce3',x:P.x+40,y:P.y+15,w:12,h:12,vx:8,vy:3,dmg:3,f:0,bounce:true,size:3,bounces:0});}")
rep("dmg:2,f:0,bounce:true,size:2,bounces:0});}", "dmg:4,f:0,bounce:true,size:2,bounces:0});}")
rep("dmg:1,f:0,bounce:true,size:3,bounces:0});}}", "dmg:3,f:0,bounce:true,size:3,bounces:0});}}")
rep("G.shots.push({kind:'rocket',x:P.x+20,y:P.y+20,w:16,h:16,vx:5,vy:0,dmg:12,f:0,homing:true,target:null});",
    "G.shots.push({kind:'rocket',x:P.x+20,y:P.y+20,w:16,h:16,vx:5,vy:0,dmg:100,f:0,homing:true,target:null});")
rep("const segs=[];for(let i=-7;i<=7;i++)segs.push({y:cy-16+i*32,alive:true});G.lines.push({x:P.x+30,segs,t:0});",
    "const segs=[];for(let i=-7;i<=7;i++)segs.push({y:cy-16+i*32,alive:true});G.lines.push({x:P.x+30,segs,t:0});")
rep("for(const L of G.lines){L.x+=6;", "for(const L of G.lines){L.x+=15;")
rep("damageEnemy(e,6,L.x+8,sg.y+16);sg.alive=false;break;", "damageEnemy(e,8,L.x+8,sg.y+16);sg.alive=false;break;")
rep("vx:7,vy:0,dmg:[3,8,16,40][lv-1],f:0,pierce:lv===4,beam:true,anim:true});",
    "vx:8,vy:0,dmg:[10,15,20,25][lv-1],f:0,pierce:lv===4,beam:true,anim:true});")
# boss hit points scaled to the real weapon damage (a rocket does 100)
import re as _re
def _bosshp(m):
    old=int(m.group(1)); mapping={400:700,500:900,550:1000,650:1200,750:1400,900:1800}
    return 'hp:%d' % mapping.get(old, old)
_start=t.index('const BOSS_DEF=')
_end=t.index(';', _start)
t = t[:_start] + _re.sub(r'hp:(\d+)', _bosshp, t[_start:_end]) + t[_end:]
open(p, 'w', encoding='utf-8').write(t)
print('patched')
