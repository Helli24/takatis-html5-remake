"""Fix effect sprite sheets (16x16 frame grids) and draw the item carried by a container claw."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))

# --- build.py: these sheets are 4x4 grids of 16x16 frames, not single 64x64 images
b = os.path.join(HERE, 'build.py')
s = open(b, encoding='utf-8').read()
for old, new in [
    ("'smoke': ('smoke', 64, 64), 'lasersmoke': ('lasersmoke', 64, 64), 'shieldflare': ('shieldflare', 64, 64),",
     "'smoke': ('smoke', 16, 16), 'lasersmoke': ('lasersmoke', 16, 16), 'shieldflare': ('shieldflare', 16, 16),"),
    ("'debris1': ('debris1', 64, 64), 'debris2': ('debris2', 64, 64), 'debris3': ('Debris3', 64, 64),",
     "'debris1': ('debris1', 16, 16), 'debris2': ('debris2', 16, 16), 'debris3': ('Debris3', 16, 16),"),
    ("'dragontail': ('dragontail', 40, 40), 'drive': ('drive', 64, 64), 'rail': ('rail', 11, 32),",
     "'dragontail': ('dragontail', 40, 40), 'drive': ('drive', 16, 16), 'rail': ('rail', 11, 32),"),
]:
    assert s.count(old) == 1, old[:50]
    s = s.replace(old, new)
open(b, 'w', encoding='utf-8').write(s)

# --- template
p = os.path.join(HERE, 'template.html')
t = open(p, encoding='utf-8').read()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


# item icon frames in powerups.gfx (verified by comparing with the single pu_*.gfx sprites)
rep("const ITEM_SPR={spread:'pu_spread',laser:'pu_laser',bounce:'pu_bounce',rocket:'pu_rocket',line:'pu_line',shield:'pu_shield',oneup:'pu_oneup'};",
    "const ITEM_SPR={spread:'pu_spread',laser:'pu_laser',bounce:'pu_bounce',rocket:'pu_rocket',line:'pu_line',shield:'pu_shield',oneup:'pu_oneup'};\n"
    "const ITEM_FRAME={spread:0,laser:1,bounce:2,rocket:3,line:4,shield:5,oneup:6};   // powerups.gfx")

# smoke of a damaged enemy: one small puff, 1/7 chance per frame (as in the original), spawned in the update, not the draw
rep("    if(!e.spr)continue;if(e.flash&&e.flash%2){ctx.globalAlpha=0.5;}frame(e.spr,e.f,e.x,e.y+(e.off||0),e.dir<0);ctx.globalAlpha=1;\n"
    "    if(e.hp<1e9&&e.hp<ET[e.type][0]/2&&e.t%4===0)G.fx.push({spr:'smoke',x:e.x+e.w/2-32,y:e.y-20,vx:0.5,vy:-1,f:0,rate:8,n:6});}",
    "    if(!e.spr)continue;if(e.flash&&e.flash%2){ctx.globalAlpha=0.5;}frame(e.spr,e.f,e.x,e.y+(e.off||0),e.dir<0);ctx.globalAlpha=1;\n"
    "    if(e.type===9&&e.item)frame('powerups',ITEM_FRAME[e.item],e.x+11,e.y+41);}   // the claw carries its powerup visibly")
rep("    if(e.x<-e.w-700||e.x>W+700||e.y<-300||e.y>780)e.dead=true;",
    "    if(e.hp<1e9&&e.hp<=ET[e.type][0]/2&&(Math.random()*7|0)===3)G.fx.push({spr:'smoke',x:cx-8,y:cy-8,vx:-0.6,vy:-0.7,f:0,rate:2,n:16});\n"
    "    if(e.x<-e.w-700||e.x>W+700||e.y<-300||e.y>780)e.dead=true;")
# player death debris: 16x16 frames now
rep("for(let i=0;i<3;i++)G.fx.push({spr:'debris'+(1+i),x:P.x,y:P.y,vx:(Math.random()-.5)*4,vy:-2-Math.random()*3,f:0,rate:5,n:1,grav:true,life:60});",
    "for(let i=0;i<3;i++)G.fx.push({spr:'debris'+(1+i),x:P.x+16+i*8,y:P.y+8,vx:(Math.random()-.5)*4,vy:-2-Math.random()*3,f:0,rate:6,n:16,grav:true,life:70});")
open(p, 'w', encoding='utf-8').write(t)
print('patched')
