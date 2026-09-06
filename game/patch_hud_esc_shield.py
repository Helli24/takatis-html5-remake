"""HUD placement (measured from hud-unten.gfx), Escape quit dialog, shield kills colliding enemies."""
import os
p = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'template.html')
t = open(p, encoding='utf-8').read()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


# --- 1) HUD: value boxes at x 74..118 / 137..181 / 459..566, interior center y=28 (sprite) -> screen 453;
#            energy slots at x 198/294/390, interior rows 7..15 -> screen 439
rep("text(G.lives,97,447,0,1);text(level().stage,158,447,0,1);text(G.score,515,447,0,1);",
    "text(G.lives,96,453,0,1);text(level().stage,159,453,0,1);text(G.score,512,453,0,1);")
rep("for(let i=0;i<3;i++){if(i<P.energy)frame('energy',0,195+i*96.5,437);}",
    "for(let i=0;i<3;i++){if(i<P.energy)frame('energy',0,195+i*96,439);}")

# --- 2) shield: colliding destructible enemies are destroyed (bosses and indestructibles are not)
rep("      if(P.shield>0){/* shield: no damage either way */}\n      else hurtPlayer(2);",
    "      if(P.shield>0){if(e.hp<1e9){G.score+=e.score;explode(cx,cy,e.w>=48);e.dead=true;}}   // shield rams normal enemies to pieces\n      else hurtPlayer(2);")

# --- 3) Escape: quit dialog like the original ("Spiel beenden ?" with Ja/Nein)
rep("case 'play':if(pressed.KeyP){G.state='pause';break;}",
    "case 'play':if(pressed.Escape){G.state='quit';G.quitSel=0;break;}\n    if(pressed.KeyP){G.state='pause';break;}")
rep("case 'pause':if(pressed.KeyP||pressed.Escape)G.state='play';break;",
    """case 'pause':if(pressed.KeyP||pressed.Escape)G.state='play';break;
    case 'quit':
      if(pressed.ArrowLeft||pressed.ArrowRight||pressed.ArrowUp||pressed.ArrowDown)G.quitSel=G.quitSel?0:1;
      if(pressed.Escape)G.state='play';
      if(pressed.Enter||pressed.Space){if(G.quitSel){G.hiscore=Math.max(G.hiscore,G.score);try{localStorage.setItem('takatis.hiscore',G.hiscore);}catch(e){}G.state='title';musicPlay('title');}else G.state='play';}
      break;""")
rep("else if(G.state==='pause'){ctx.fillStyle='rgba(0,0,0,.5)';ctx.fillRect(0,PY,W,PH);drawCenter('PAUSE',220,0);}",
    """else if(G.state==='pause'){ctx.fillStyle='rgba(0,0,0,.5)';ctx.fillRect(0,PY,W,PH);drawCenter('PAUSE',220,0);}
  else if(G.state==='quit'){const bx=150,by=190,bw=340,bh=110;
    ctx.fillStyle='rgba(20,10,6,.92)';ctx.fillRect(bx,by,bw,bh);ctx.strokeStyle='#8a6a3a';ctx.lineWidth=2;ctx.strokeRect(bx+.5,by+.5,bw-1,bh-1);
    drawCenter('SPIEL BEENDEN ?',by+22,0);
    text('JA',bx+95,by+68,G.quitSel?1:0,1);text('NEIN',bx+245,by+68,G.quitSel?0:2,1);}""")
open(p, 'w', encoding='utf-8').write(t)
print('patched')
