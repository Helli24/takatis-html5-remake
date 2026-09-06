"""One-off patch: 3D end bosses (WebGL) with boss fights at the end of every second stage."""
import os
HERE = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(HERE, 'template.html')
t = open(p, encoding='utf-8').read()


def rep(old, new):
    global t
    assert t.count(old) == 1, old[:70]
    t = t.replace(old, new)


# ---------------------------------------------------------------- build.py: export meshes + skins
b = os.path.join(HERE, 'build.py')
s = open(b, encoding='utf-8').read()
assert "data['paths'] = paths" in s
s = s.replace("data['paths'] = paths", """data['paths'] = paths

# 3D bosses: DirectX .x meshes -> flat arrays, skins are plain (unscrambled) BMPs
from xfile import parse_x, transform, triangulate, vertex_normals
BOSS_PARTS = {1: ['a01', 'b01', 'c01'], 2: ['a02', 'b02'], 3: ['003'], 4: ['004'], 5: ['005'], 6: ['a06', 'b06']}
data['bosses'] = {}
for bid, parts in BOSS_PARTS.items():
    lst = []
    for part in parts:
        x = parse_x(os.path.join(ROOT, 'assets', '3D', 'endboss_' + part + '.x'))
        v = transform(x['verts'], x['matrix'])
        tris = triangulate(x['faces'])
        nrm = vertex_normals(v, tris)
        uv = x['uvs'] or [(0, 0)] * len(v)
        lst.append({'name': part, 'v': [round(c, 3) for pnt in v for c in pnt], 'n': [round(c, 3) for pnt in nrm for c in pnt],
                    'uv': [round(c, 4) for pnt in uv for c in pnt], 'i': [i for tri in tris for i in tri],
                    'tex': (x['texture'] or '').replace('.bmp', ''), 'color': x['color'][:3]})
    data['bosses'][bid] = lst


def bmp_any_png(path):
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    bpp = struct.unpack_from('<H', d, 28)[0]
    h = abs(h)
    rows = []
    if bpp == 8:
        pal = [tuple(d[54 + i * 4:54 + i * 4 + 3][::-1]) for i in range(256)]
        stride = (w + 3) & ~3
        raw = [d[off + y * stride:off + y * stride + w] for y in range(h)][::-1]
        for r in raw:
            rows.append(b''.join(bytes(pal[i]) + b'\\xff' for i in r))
    else:
        stride = (w * 3 + 3) & ~3
        raw = [d[off + y * stride:off + y * stride + w * 3] for y in range(h)][::-1]
        for r in raw:
            rows.append(b''.join(bytes((r[i + 2], r[i + 1], r[i])) + b'\\xff' for i in range(0, w * 3, 3)))
    return 'data:image/png;base64,' + base64.b64encode(png_bytes(w, h, rows)).decode()


data['skins'] = {}
for f in os.listdir(os.path.join(EX, '3D')):
    if f.lower().endswith('.bmp'):
        data['skins'][f.lower()[:-4]] = bmp_any_png(os.path.join(EX, '3D', f))
SPRITES_EXTRA = {'bosshud': ('bosshud', 270, 26), 'bossenergy': ('bossenergy', 200, 24)}
for k, (f, fw, fh) in SPRITES_EXTRA.items():
    data['sprites'][k] = gfx(f, fw, fh)""")
open(b, 'w', encoding='utf-8').write(s)

# ---------------------------------------------------------------- template: WebGL renderer + boss logic
rep("// ---------- input", r"""// ---------- 3D bosses (WebGL, drawn into the 2D playfield)
const GL={cv:null,gl:null,prog:null,meshes:{},tex:{},ready:false};
function glInit(){if(GL.ready)return true;try{const c=document.createElement('canvas');c.width=W;c.height=PH;const gl=c.getContext('webgl',{alpha:true,premultipliedAlpha:false,antialias:true});if(!gl)return false;
  const vs=`attribute vec3 p;attribute vec3 n;attribute vec2 t;uniform mat4 mvp;uniform mat4 m;varying vec3 vn;varying vec2 vt;void main(){gl_Position=mvp*vec4(p,1.0);vn=mat3(m)*n;vt=t;}`;
  const fs=`precision mediump float;varying vec3 vn;varying vec2 vt;uniform sampler2D s;uniform float useTex;uniform vec3 col;uniform float flash;void main(){vec3 N=normalize(vn);float d=max(dot(N,normalize(vec3(-0.4,0.6,0.7))),0.0);float li=0.35+0.75*d;vec3 c=useTex>0.5?texture2D(s,vt).rgb:col;c=c*li+flash*vec3(0.6,0.2,0.1);gl_FragColor=vec4(c,1.0);}`;
  const sh=(ty,src)=>{const h=gl.createShader(ty);gl.shaderSource(h,src);gl.compileShader(h);if(!gl.getShaderParameter(h,gl.COMPILE_STATUS))throw gl.getShaderInfoLog(h);return h;};
  const pr=gl.createProgram();gl.attachShader(pr,sh(gl.VERTEX_SHADER,vs));gl.attachShader(pr,sh(gl.FRAGMENT_SHADER,fs));gl.linkProgram(pr);
  GL.cv=c;GL.gl=gl;GL.prog=pr;GL.loc={p:gl.getAttribLocation(pr,'p'),n:gl.getAttribLocation(pr,'n'),t:gl.getAttribLocation(pr,'t'),mvp:gl.getUniformLocation(pr,'mvp'),m:gl.getUniformLocation(pr,'m'),s:gl.getUniformLocation(pr,'s'),useTex:gl.getUniformLocation(pr,'useTex'),col:gl.getUniformLocation(pr,'col'),flash:gl.getUniformLocation(pr,'flash')};
  gl.enable(gl.DEPTH_TEST);gl.enable(gl.CULL_FACE);gl.cullFace(gl.BACK);
  for(const k in DATA.skins){const tx=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tx);const im=new Image();im.onload=()=>{gl.bindTexture(gl.TEXTURE_2D,tx);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,im);gl.generateMipmap(gl.TEXTURE_2D);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);};im.src=DATA.skins[k];
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([128,128,128,255]));GL.tex[k]=tx;}
  for(const bid in DATA.bosses){GL.meshes[bid]=DATA.bosses[bid].map(pt=>{const buf=(arr,ty)=>{const bb=gl.createBuffer();gl.bindBuffer(ty,bb);gl.bufferData(ty,arr,gl.STATIC_DRAW);return bb;};
    const vs=new Float32Array(pt.v);let minx=1e9,maxx=-1e9,miny=1e9,maxy=-1e9,minz=1e9,maxz=-1e9;for(let i=0;i<vs.length;i+=3){minx=Math.min(minx,vs[i]);maxx=Math.max(maxx,vs[i]);miny=Math.min(miny,vs[i+1]);maxy=Math.max(maxy,vs[i+1]);minz=Math.min(minz,vs[i+2]);maxz=Math.max(maxz,vs[i+2]);}
    return {name:pt.name,vb:buf(vs,gl.ARRAY_BUFFER),nb:buf(new Float32Array(pt.n),gl.ARRAY_BUFFER),tb:buf(new Float32Array(pt.uv),gl.ARRAY_BUFFER),ib:buf(new Uint16Array(pt.i),gl.ELEMENT_ARRAY_BUFFER),cnt:pt.i.length,tex:pt.tex,color:pt.color,bb:[minx,maxx,miny,maxy,minz,maxz]};});}
  GL.ready=true;return true;}catch(e){console.error('webgl',e);return false;}}
function mat4mul(a,b){const o=new Float32Array(16);for(let i=0;i<4;i++)for(let j=0;j<4;j++){let s=0;for(let k=0;k<4;k++)s+=a[k*4+j]*b[i*4+k];o[i*4+j]=s;}return o;}
function mat4rot(ax,ay,az){const cx=Math.cos(ax),sx=Math.sin(ax),cy=Math.cos(ay),sy=Math.sin(ay),cz=Math.cos(az),sz=Math.sin(az);
  const X=new Float32Array([1,0,0,0,0,cx,sx,0,0,-sx,cx,0,0,0,0,1]),Y=new Float32Array([cy,0,-sy,0,0,1,0,0,sy,0,cy,0,0,0,0,1]),Z=new Float32Array([cz,sz,0,0,-sz,cz,0,0,0,0,1,0,0,0,0,1]);return mat4mul(Z,mat4mul(Y,X));}
const CAM_D=900,FOV=0.55;
function pxPerUnit(){return PH/(2*CAM_D*Math.tan(FOV/2));}
function bossDraw(B){if(!glInit())return;const gl=GL.gl;gl.viewport(0,0,W,PH);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.useProgram(GL.prog);
  const f=1/Math.tan(FOV/2),asp=W/PH,near=100,far=3000;const P=new Float32Array([f/asp,0,0,0,0,f,0,0,0,0,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);
  const ppu=pxPerUnit();const parts=GL.meshes[B.id];
  for(let k=0;k<parts.length;k++){const pt=parts[k],pp=B.parts[k];
    const sc=B.scale;const R=mat4rot(pp.rx,pp.ry,pp.rz);
    // model: scale, rotate, translate into camera space (x right, y up, z towards viewer)
    const wx=(B.x-W/2+pp.ox)/ppu,wy=-(B.y-PH/2+pp.oy)/ppu,wz=pp.oz/ppu;
    const S=new Float32Array([sc,0,0,0,0,sc,0,0,0,0,sc,0,0,0,0,1]);const M=mat4mul(R,S);M[12]=wx;M[13]=wy;M[14]=wz-CAM_D;
    const MVP=mat4mul(P,M);
    gl.uniformMatrix4fv(GL.loc.mvp,false,MVP);gl.uniformMatrix4fv(GL.loc.m,false,R);gl.uniform1f(GL.loc.flash,B.flash>0?0.8:0);
    if(pt.tex&&GL.tex[pt.tex]){gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,GL.tex[pt.tex]);gl.uniform1i(GL.loc.s,0);gl.uniform1f(GL.loc.useTex,1);}else{gl.uniform1f(GL.loc.useTex,0);gl.uniform3fv(GL.loc.col,pt.color);}
    gl.bindBuffer(gl.ARRAY_BUFFER,pt.vb);gl.enableVertexAttribArray(GL.loc.p);gl.vertexAttribPointer(GL.loc.p,3,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,pt.nb);gl.enableVertexAttribArray(GL.loc.n);gl.vertexAttribPointer(GL.loc.n,3,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ARRAY_BUFFER,pt.tb);gl.enableVertexAttribArray(GL.loc.t);gl.vertexAttribPointer(GL.loc.t,2,gl.FLOAT,false,0,0);
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,pt.ib);gl.drawElements(gl.TRIANGLES,pt.cnt,gl.UNSIGNED_SHORT,0);}
  ctx.drawImage(GL.cv,0,0);}
// boss definitions: target pixel height, hp, part animation
const BOSS_DEF={1:{h:230,hp:400,name:'GUARDIAN'},2:{h:260,hp:500,name:'ROTOR'},3:{h:150,hp:550,name:'FIGHTER'},4:{h:190,hp:650,name:'VIRUS'},5:{h:250,hp:750,name:'CRUSHER'},6:{h:210,hp:900,name:'THE BRAIN'}};
function bossStart(){if(!glInit()){G.stageClear=true;return;}const id=level().theme;const def=BOSS_DEF[id];const parts=GL.meshes[id];
  let miny=1e9,maxy=-1e9,minx=1e9,maxx=-1e9;for(const pt of parts){minx=Math.min(minx,pt.bb[0]);maxx=Math.max(maxx,pt.bb[1]);miny=Math.min(miny,pt.bb[2]);maxy=Math.max(maxy,pt.bb[3]);}
  const ppu=pxPerUnit();const scale=def.h/((maxy-miny)*ppu);const wpx=(maxx-minx)*ppu*scale;
  G.boss={id,def,x:W+wpx,y:PH/2,w:wpx,h:def.h,hp:def.hp,maxhp:def.hp,t:0,flash:0,scale,shoot:120,phase:0,dying:0,cx:(minx+maxx)/2*scale*ppu,cy:(miny+maxy)/2*scale*ppu,
    parts:parts.map(()=>({rx:0,ry:0,rz:0,ox:0,oy:0,oz:0}))};
  G.speed=0;musicPlay('boss');sfx('v_bigone',0.9);}
function bossUpdate(){const B=G.boss;B.t++;if(B.flash>0)B.flash--;const d=G.diff;
  if(B.dying){B.dying--;if(B.dying%6===0){explode(B.x-B.w/2+Math.random()*B.w,B.y-B.h/2+Math.random()*B.h,Math.random()<0.5);sfx('explosion',0.5,0.8+Math.random()*.4);}
    B.parts.forEach((pp,i)=>{pp.rz+=0.02*(i+1);pp.oy+=0.5;});if(B.dying===0){G.score+=5000;G.boss=null;G.stageClear=true;}return;}
  // entrance, then hovering pattern
  const tx=W-B.w/2-30;if(B.x>tx)B.x-=2;else B.x=tx+Math.sin(B.t*0.012)*25;
  B.y=PH/2+Math.sin(B.t*0.02)*(PH/2-B.h/2-20);
  // part animation per boss
  const pp=B.parts;switch(B.id){
    case 1:pp[0].ry=Math.sin(B.t*0.03)*0.4;pp[1].rz=Math.sin(B.t*0.02)*0.15;pp[2].ry=B.t*0.05;break;
    case 2:pp[0].ry=Math.sin(B.t*0.02)*0.5;pp[1].ry=B.t*0.25;break;
    case 3:pp[0].ry=Math.PI/2+Math.sin(B.t*0.03)*0.3;pp[0].rz=Math.sin(B.t*0.05)*0.2;break;
    case 4:pp[0].ry=B.t*0.03;pp[0].rx=Math.sin(B.t*0.02)*0.4;break;
    case 5:pp[0].ry=Math.PI+Math.sin(B.t*0.015)*0.3;pp[0].rx=Math.sin(B.t*0.03)*0.15;break;
    case 6:pp[0].ry=B.t*0.02;pp[0].rx=Math.sin(B.t*0.03)*0.3;pp[1].ry=-B.t*0.06;pp[1].oy=Math.sin(B.t*0.05)*30;break;}
  // attacks: aimed bursts, faster when damaged
  const rate=[110,85,60][d]*(B.hp<B.maxhp/2?0.7:1);
  if(--B.shoot<=0&&B.x<W){const cx=B.x-B.w/4,cy=B.y;const ang=Math.atan2(P.y+17-cy,P.x+24-cx);
    if(B.phase%3===2){for(let k=0;k<8;k++){const a=k*Math.PI/4+B.t*0.01;eshot(cx,cy,Math.cos(a)*3,Math.sin(a)*3,'blob');}}
    else{for(const da of [-0.25,0,0.25])eshot(cx,cy,Math.cos(ang+da)*4.5,Math.sin(ang+da)*4.5,B.id>=4?'chaseshot':'bullet');}
    sfx('laser2',0.4);B.shoot=rate;B.phase++;}
  // player collision
  if(!P.dead&&hit({x:B.x-B.w/2+10,y:B.y-B.h/2+10,w:B.w-20,h:B.h-20},{x:P.x+10,y:P.y+8,w:P.w-20,h:P.h-16}))hurtPlayer(2);
  // player shots
  for(const s of G.shots){if(s.dead||s.homing)continue;if(hit(s,{x:B.x-B.w/2+8,y:B.y-B.h/2+8,w:B.w-16,h:B.h-16})){B.hp-=s.dmg;B.flash=4;puff(s.x+s.w,s.y+s.h/2);s.dead=true;
      if(B.hp<=0){B.hp=0;B.dying=150;sfx('bigexplosion',0.9);musicPlay('clear');}}}
  for(const L of G.lines)for(const sg of L.segs)if(sg.alive&&hit({x:L.x,y:sg.y,w:16,h:32},{x:B.x-B.w/2,y:B.y-B.h/2,w:B.w,h:B.h})){B.hp-=3;B.flash=4;sg.alive=false;}
}
function bossHUD(){const B=G.boss;frame('bosshud',0,185,PY+2);const s=S.bossenergy;const wdt=Math.round(200*B.hp/B.maxhp);if(wdt>0)ctx.drawImage(s.img,0,0,wdt,24,220,PY+3,wdt,24);}
// ---------- input""")

# level end: boss on every second stage
rep("if(G.scroll>=G.maxScroll){G.scroll=G.maxScroll;G.stageClear=true;}",
    "if(G.scroll>=G.maxScroll){G.scroll=G.maxScroll;if(G.level%2===1&&!G.boss&&!G.bossDone){bossStart();}else if(!G.boss)G.stageClear=true;}\n  if(G.boss)bossUpdate();")
rep("if(e.end){G.stageClear=true;}", "if(e.end){if(G.level%2===1&&!G.boss&&!G.bossDone)bossStart();else G.stageClear=true;}")
rep("G.enemies=[];G.shots=[];G.eshots=[];G.fx=[];G.items=[];G.lines=[];G.next=0;",
    "G.enemies=[];G.shots=[];G.eshots=[];G.fx=[];G.items=[];G.lines=[];G.next=0;G.boss=null;G.bossDone=false;")
rep("if(B.dying===0){G.score+=5000;G.boss=null;G.stageClear=true;}return;}",
    "if(B.dying===0){G.score+=5000;G.boss=null;G.bossDone=true;G.stageClear=true;}return;}")
# rockets ignore bosses (manual) - already skipped via s.homing; beam does not pierce bosses - handled (shot dies)
# draw boss between shots and player, HUD bar
rep("  for(const s of G.eshots)frame(s.spr,", "  if(G.boss)bossDraw(G.boss);\n  for(const s of G.eshots)frame(s.spr,")
rep("if(G.info){ctx.fillStyle='rgba(0,0,0,.5)';ctx.fillRect(0,PY,250,110);", "if(G.boss)bossHUD();\n  if(G.info){ctx.fillStyle='rgba(0,0,0,.5)';ctx.fillRect(0,PY,250,110);")
rep("else if(G.state==='clear'){drawCenter('STAGE CLEAR',200,0);drawCenter('BONUS 1000  +1 LIFE',235,2);if(G.level%2===1)drawCenter('(ENDGEGNER FOLGT IN STUFE 4)',270,3);}",
    "else if(G.state==='clear'){drawCenter('STAGE CLEAR',200,0);drawCenter('BONUS 1000  +1 LIFE',235,2);if(G.bossDone)drawCenter('BOSS DESTROYED  +5000',270,3);}")
# F2 during a boss fight kills the boss
rep("if(pressed.F2){G.stageClear=true;}", "if(pressed.F2){if(G.boss){G.boss.hp=0;G.boss.dying=150;}else G.stageClear=true;}")
open(p, 'w', encoding='utf-8').write(t)
print('boss patched')
