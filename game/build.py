"""Build game/takatis.html from game/template.html + original game data."""
import os, sys, json, base64, struct, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from takatis import Level, level_screens, level_speed, layer_a_width, load_bmp8, wav_bytes

EX = os.path.join(ROOT, 'extracted')
if not os.path.isfile(os.path.join(EX, 'Takatis.exe')):   # first build: unpack the original installer
    from prepare import prepare
    print('unpacking the installer:', prepare(), 'entries')


def png_bytes(w, h, rows):
    raw = b''.join(b'\0' + r for r in rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def q565(c):
    """A colour as the game shows it: it runs in 640x480 with 16 bits (0x485648), GDI truncates the bitmap colours to
    RGB565 when they are copied into the surfaces; the remake expands them again by repeating the top bits."""
    r, g, b = c[0] >> 3, c[1] >> 2, c[2] >> 3
    return (r << 3 | r >> 2, g << 2 | g >> 4, b << 3 | b >> 2)


# the colour key of all keyed surfaces (0x412770) is the green mask of the pixel format, so every colour that
# truncates to pure green is transparent, e.g. (0,253,0) in Lasersmoke and (0,254,0) in 03.tsb
KEY565 = q565((0, 255, 0))


def img_b64(path, key=True):
    w, h, pal, px = load_bmp8(path)
    pal = [q565(c) for c in pal]
    keyidx = {i for i, c in enumerate(pal) if c == KEY565} if key else set()
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            i = px[y * w + x]
            r, g, b = pal[i]
            row += bytes((r, g, b, 0 if i in keyidx else 255))
        rows.append(bytes(row))
    return w, h, 'data:image/png;base64,' + base64.b64encode(png_bytes(w, h, rows)).decode()


gfxdir = {f.lower(): f for f in os.listdir(os.path.join(EX, 'GFX'))}


def gfx(name, fw=None, fh=None, key=True):
    f = gfxdir[name.lower() + '.gfx']
    w, h, src = img_b64(os.path.join(EX, 'GFX', f), key)
    fw = fw or w
    fh = fh or h
    return {'src': src, 'w': w, 'h': h, 'fw': fw, 'fh': fh, 'cols': w // fw, 'frames': (w // fw) * (h // fh)}


# name: (file, frame w, frame h)
SPRITES = {
    'player': ('player', 49, 34), 'player2': ('player2', 49, 34), 'console': ('console', 640, 240),
    'spread': ('spreadshot', 18, 17), 'laser': ('laser', 24, 12),
    'bounce1': ('bounce1', 24, 24), 'bounce2': ('bounce2', 18, 18), 'bounce3': ('bounce3', 12, 12),
    'rocket': ('rocket', 16, 16), 'powerline': ('powerline', 16, 32),
    'beammini': ('beammini', 16, 8), 'beamsmall': ('beamsmall', 32, 16), 'beammed': ('beammed', 48, 24), 'beambig': ('beambig', 64, 32),
    'beamload': ('beam-load', 248, 24), 'beamexplode': ('beamexplode', 50, 50),
    'explosion': ('explosion', 60, 50), 'explosion2': ('explosion2', 48, 48), 'smallexpl': ('small_explosion', 16, 16),
    'smoke': ('smoke', 16, 16), 'lasersmoke': ('lasersmoke', 16, 16), 'shieldflare': ('shieldflare', 16, 16),
    'debris1': ('debris1', 16, 16), 'debris2': ('debris2', 16, 16), 'debris3': ('Debris3', 16, 16),
    'debris4': ('Debris4', 16, 16), 'debris5': ('debris5', 16, 16),
    'bullet': ('turret-bullet', 8, 8), 'walkershot': ('walkershot', 24, 24), 'bullspread': ('bullspread', 18, 13), 'chaseshot': ('chaseshot', 32, 14),
    'elevatorshot': ('elevatorshot', 32, 8), 'volcanoball': ('volcanoball', 16, 16), 'mine': ('mine', 24, 24), 'spike1': ('spike1', 16, 17), 'spike2': ('spike2', 16, 17),
    'shield': ('shield', 56, 34), 'powerups': ('powerups', 20, 20), 'star': ('star', 72, 72), 'blob': ('blob1', 12, 12),
    'pu_oneup': ('pu_oneup', 20, 20), 'pu_bounce': ('pu_bounce', 20, 20), 'pu_shield': ('pu_shield', 20, 20), 'pu_line': ('pu_line', 20, 20),
    'pu_spread': ('pu_spread', 20, 20), 'pu_laser': ('pu_laser', 20, 20), 'pu_rocket': ('pu_rocket', 20, 20),
    'hudtop': ('hud-oben', 640, 16), 'ws': ('ws', 7, 10), 'hudbottom': ('hud-unten', 640, 48), 'energy': ('player-energy', 56, 9),
    'font': ('font', 10, 14), 'font2': ('font2', 8, 10), 'bigfont': ('bigfont', 32, 32),
    'title': ('title', 640, 480), 'getready': ('getready', 329, 56), 'gameover': ('gameover', 429, 56), 'logo': ('logo', 640, 140),
    'intro': ('intro', 619, 371), 'intro2': ('intro2', 497, 52), 'pl': ('pl', 494, 75), 'backside': ('backside', 640, 170),
    'creditstile': ('creditstile', 80, 80), 'creditslogo': ('CreditsLogo', 160, 100), 'volume': ('volume', 192, 128),
    'volumebar': ('volumebar', 100, 16),
    'endscreen': ('Endscreen', 640, 480), 'fadeleft': ('fadeleft', 120, 480), 'faderight': ('faderight', 120, 480), 'menu': ('menu', 224, 64), 'rahmen': ('rahmen', 32, 32), 'loading': ('loading', 280, 146),
    # enemies by type
    'e0': ('asteroid', 64, 54), 'e1': ('Razorback', 52, 32), 'e2': ('spinner', 56, 46), 'e9': ('container', 36, 46),
    'e10': ('turret-floor', 44, 41), 'e11': ('turret-ceiling', 44, 41), 'e12': ('walker', 43, 54), 'e13': ('circuit', 32, 32),
    'e14': ('bulldozer', 80, 47), 'e15': ('VoltCare', 49, 34), 'e16': ('magnet', 32, 32), 'e17': ('faller', 32, 64),
    'e18': ('block1', 16, 16), 'e19': ('block2', 16, 16), 'e20': ('block3', 16, 16), 'e21': ('block4', 16, 16),
    'e22': ('arnold', 71, 17), 'e23': ('Kraftfeld', 71, 64), 'e24': ('x6502', 84, 47), 'e25': ('elevator', 56, 68),
    'e26': ('presse1', 64, 256), 'e27': ('presse2', 64, 256), 'e28': ('spikeball', 72, 72), 'e29': ('volcano', 80, 36),
    'e30': ('bumper', 40, 40), 'e31': ('timebomb', 48, 48), 'e32': ('sharpshooter', 32, 32), 'e33': ('containerfake', 36, 61),
    'dragontail': ('dragontail', 40, 40), 'drive': ('drive', 16, 16), 'rail': ('rail', 11, 32),
}
NOKEY = {'title', 'endscreen', 'loading', 'ws', 'pl', 'backside', 'intro', 'intro2', 'menu', 'volume', 'volumebar', 'rahmen',
         'hudtop', 'hudbottom', 'beamload', 'creditstile', 'rail', 'energy'}

data = {'sprites': {}, 'themes': {}, 'levels': [], 'sounds': {}}
for k, (f, fw, fh) in SPRITES.items():
    data['sprites'][k] = gfx(f, fw, fh, key=k not in NOKEY)

for t in range(1, 7):
    n = f'{t:02d}'
    data['themes'][t] = {
        'tsa': img_b64(os.path.join(EX, 'Level', f'{n}.tsa'))[2],
        'tsb': img_b64(os.path.join(EX, 'Level', f'{n}.tsb'))[2],
        'stc': img_b64(os.path.join(EX, 'Level', f'{n}.stc'), key=False)[2]}

stage = [("1-1", "Warm Up !"), ("1-2", "Little more speed !"), ("2-1", "Don't try to collect crystals!"), ("2-2", "Jam the brakes !"),
         ("3-1", "Danger! Mines ahaed !!!"), ("3-2", "Stupid enemies"), ("4-1", "Sorry, no goodies!"), ("4-2", "Get magnified !"),
         ("5-1", "Crazy Volcanos may help you! (hint)"), ("5-2", "Hot Lava!"), ("6-1", "Watch the spikeballs!"), ("6-2", "Prepare for the Brain!")]
for i in range(1, 13):
    lv = Level(os.path.join(EX, 'Level', f'{i:02d}.lvl'))
    scr = level_screens(lv)
    wa = layer_a_width(scr)
    A, B = lv.split_layers(wa)
    # in the order of the file: the enemy array is processed in this order (0x42bdb0)
    objs = [[o['type'], o['x'], (o['y'] - 2**32 if o['y'] >= 2**31 else o['y']), o['param'], o['flag']] for o in lv.objects]
    data['levels'].append({'stage': stage[i - 1][0], 'hint': stage[i - 1][1], 'theme': (i + 1) // 2, 'screens': scr,
                           'speed': level_speed(lv), 'wa': wa, 'wb': scr * 20,
                           'A': base64.b64encode(b''.join(A)).decode(), 'B': base64.b64encode(b''.join(B)).decode(), 'objects': objs})

SOUNDS = {'explosion': 'Explosion', 'bigexplosion': 'bigexplosion', 'spread': 'Spread', 'laser': 'Laser', 'laser2': 'Laser2', 'hit': 'Hit',
          'shield': 'Shield', 'rocket': 'Rocket', 'bounce': 'Bounce', 'beam': 'Beam', 'bigshot': 'BigShot', 'trigger': 'Trigger',
          'powerline': 'powerline', 'morph': 'morph', 'klippikloppi': 'klippikloppi'}
for k, f in SOUNDS.items():
    data['sounds'][k] = 'data:audio/wav;base64,' + base64.b64encode(wav_bytes(os.path.join(EX, 'Sfx', f + '.sfx'))).decode()
SPEECH = {'intro': 'Intro', 'cheat': 'cheat', 'online': 'online', 'oneup': '1up', 'spread': 'spread', 'laser': 'laser', 'bounce': 'bounce', 'shield': 'shield', 'homing': 'homing', 'line': 'line', 'bigone': 'bigone'}
for k, f in SPEECH.items():
    data['sounds']['v_' + k] = 'data:audio/wav;base64,' + base64.b64encode(wav_bytes(os.path.join(EX, 'Speech', f + '.spc'))).decode()


# movement pattern table from Takatis.exe (.data at 0x4856c0, 64 entries x 0x140 bytes):
# list of (dx, dy, count) triples; count>0 = frames, -1/-2 = hold velocity forever, -3 = loop, -4 = teleport+restart
import pefile
_pe = pefile.PE(os.path.join(EX, 'Takatis.exe'))
_img = _pe.get_memory_mapped_image()
_o = 0x4856c0 - _pe.OPTIONAL_HEADER.ImageBase
paths = []
for e in range(64):
    ints = struct.unpack('<80i', _img[_o + e * 0x140:_o + (e + 1) * 0x140])
    segs = []
    for k in range(0, 78, 3):
        dx, dy, n = ints[k], ints[k + 1], ints[k + 2]
        segs.append([dx, dy, n])
        if n < 0:
            break
    paths.append(segs)
data['paths'] = paths

# enemy init function 0x40c760: per type a block "cmp [ebp+8], type" followed by constant stores into the enemy
# record. +0x20 energy, +0x18/+0x1c size, +0x3c frames, +0x44 frame delay, +0x48 sheet columns,
# +0x38 ping-pong animation, +0x64 points.
import capstone
_md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_32)
_md.detail = True
_FIELDS = {0x20: 'hp', 0x18: 'w', 0x1c: 'h', 0x3c: 'frames', 0x44: 'delay', 0x48: 'cols', 0x38: 'pp', 0x64: 'pts'}
_code = _img[0x40c760 - _pe.OPTIONAL_HEADER.ImageBase:0x40d860 - _pe.OPTIONAL_HEADER.ImageBase]
enemies, cur = {}, None
for ins in _md.disasm(_code, 0x40c760):
    ops = ins.operands
    if ins.mnemonic == 'cmp' and len(ops) == 2 and ops[0].type == capstone.x86.X86_OP_MEM \
            and ops[0].mem.base == capstone.x86.X86_REG_EBP and ops[0].mem.disp == 8 and ops[1].type == capstone.x86.X86_OP_IMM:
        cur = ops[1].imm
        enemies.setdefault(cur, {})
    elif ins.mnemonic == 'mov' and cur is not None and len(ops) == 2 and ops[0].type == capstone.x86.X86_OP_MEM \
            and ops[1].type == capstone.x86.X86_OP_IMM and ops[0].mem.disp in _FIELDS and ops[0].mem.base != capstone.x86.X86_REG_EBP:
        enemies[cur][_FIELDS[ops[0].mem.disp]] = ops[1].imm
# the container block covers types 3..9 ("cmp 3 / cmp 9" range check)
for t_ in range(3, 9):
    enemies[t_] = dict(enemies[9])
data['enemyInit'] = {k: v for k, v in enemies.items() if 'hp' in v}

# stage intro (0x416301): per level three centered lines "y, text, colour row" (text function 0x40e540)
def _cstr(a):
    o = a - _pe.OPTIONAL_HEADER.ImageBase
    return _img[o:_img.index(b'\0', o)].decode('latin-1')
data['intro'] = [[] for _ in range(12)]
_lvl, _push = None, []
for ins in _md.disasm(_img[0x4163ea - _pe.OPTIONAL_HEADER.ImageBase:0x416a12 - _pe.OPTIONAL_HEADER.ImageBase], 0x4163ea):
    ops = ins.operands
    if ins.mnemonic == 'cmp' and len(ops) == 2 and ops[0].type == capstone.x86.X86_OP_MEM and ops[0].mem.disp == 0x495154:
        _lvl = ops[1].imm
    elif ins.mnemonic == 'push' and ops[0].type == capstone.x86.X86_OP_IMM:
        _push.append(ops[0].imm)
    elif ins.mnemonic == 'call':
        if ops[0].type == capstone.x86.X86_OP_IMM and ops[0].imm == 0x401217:
            data['intro'][_lvl].append([_push[-1], _cstr(_push[-2]), _push[-3]])
        _push = []
assert all(len(x) == 3 for x in data['intro'])
# proportional font (0x40e2a0, width 0x40e0e0): advance = width[c]+1, a space adds 10
data['fontW'] = list(struct.unpack('<128i', _img[0x484820 - _pe.OPTIONAL_HEADER.ImageBase:0x484a20 - _pe.OPTIONAL_HEADER.ImageBase]))
# help pages (0x40e6e0): 5 pages of 30 lines of 100 characters at 0x480e0c
_hb = 0x480e0c - _pe.OPTIONAL_HEADER.ImageBase
data['helpText'] = [[_img[_hb + p * 3000 + l * 100:_hb + p * 3000 + l * 100 + 100].split(b'\0')[0].decode('latin-1')
                     for l in range(30)] for p in range(5)]
# credits (state 9): 0x426ba0 fills the line table 0x494184 one entry after the other
_cred, _ci = {}, 0
for ins in _md.disasm(_img[0x426bb8 - _pe.OPTIONAL_HEADER.ImageBase:0x42a250 - _pe.OPTIONAL_HEADER.ImageBase], 0x426bb8):
    ops = ins.operands
    if ins.mnemonic == 'ret':
        break
    if ins.mnemonic == 'mov' and ops[0].type == capstone.x86.X86_OP_MEM and ops[0].mem.disp == 0x494184:
        _cred[_ci] = _cstr(ops[1].imm)
    elif ins.mnemonic == 'add' and ops[0].type == capstone.x86.X86_OP_REG and ops[1].type == capstone.x86.X86_OP_IMM and ops[1].imm == 1:
        _ci += 1
data['credits'] = [_cred.get(i, '') for i in range(max(_cred) + 1)]
assert len(data['credits']) == 351 and data['credits'][23].startswith('-* Takatis')
# jukebox titles (options, 0x4211b8): 15 characters each from 0x480d60
data['songs'] = [_cstr(0x480d60 + 15 * i) for i in range(11)]

# the end (0x42a250): Level/ot.lvl is an enemy parade whose foreground tiles come from bigfont.gfx; below it runs
# the text at 0x4766d8
_lv = Level(os.path.join(EX, 'Level', 'ot.lvl'))
_scr = level_screens(_lv)
_wa = layer_a_width(_scr)
_A, _B = _lv.split_layers(_wa)
data['outro'] = {'stage': '', 'hint': '', 'theme': 7, 'screens': _scr, 'speed': level_speed(_lv), 'wa': _wa, 'wb': _scr * 20,
                 'A': base64.b64encode(b''.join(_A)).decode(), 'B': base64.b64encode(b''.join(_B)).decode(),
                 'objects': [[o['type'], o['x'], (o['y'] - 2**32 if o['y'] >= 2**31 else o['y']), o['param'], o['flag']] for o in _lv.objects],
                 'text': _cstr(0x4766d8)}

# 3D bosses: DirectX .x meshes as triangle lists in object space (per corner: position, normal, uv). The game scales
# the vertices (CD3DFile::Scale) and applies the frame matrix and the world matrix at render time.
# The DX7 file loader (0x42ec30) uses a normal list only when it has exactly one normal per vertex (normal i for
# vertex i, the face indices of MeshNormals are ignored) and computes smooth normals otherwise; only b06 qualifies.
from xfile import parse_x, triangulate, d3dfile_normals
data['meshes'] = {}
for part in ['a01', 'b01', 'c01', 'a02', 'b02', '003', '004', '005', 'a06', 'b06']:
    x = parse_x(os.path.join(EX, '3D', 'endboss.' + part))
    v, uv = x['verts'], x['uvs'] if x['uvs'] and len(x['uvs']) == len(x['verts']) else [(0, 0)] * len(x['verts'])
    tris = triangulate(x['faces'])
    nrm = x['normals_raw'] if x['normals_raw'] and len(x['normals_raw']) == len(v) else d3dfile_normals(v, tris)
    P, N, U = [], [], []
    for tri in tris:
        for vi in tri:
            P += [round(q, 3) for q in v[vi]]
            N += [round(q, 4) for q in nrm[vi]]
            U += [round(q, 4) for q in uv[vi]]
    data['meshes'][part] = {'p': P, 'n': N, 'uv': U, 'm': x['matrix'] or [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1],
                            'tex': os.path.splitext(x['texture'] or '')[0].lower(), 'color': x['color'][:3]}

# the end-boss routine runs as translated code; it needs the constants and variables of .rdata/.data
import bossvm
data['bossMem'] = []
for sec in _pe.sections:
    if sec.Name.rstrip(b'\0') in (b'.rdata', b'.data'):
        va = sec.VirtualAddress
        data['bossMem'].append([va + _pe.OPTIONAL_HEADER.ImageBase, base64.b64encode(_img[va:va + sec.Misc_VirtualSize]).decode()])
BOSS_JS = bossvm.translate(_img, _pe.OPTIONAL_HEADER.ImageBase)


def bmp_any_png(path):
    d = open(path, 'rb').read()
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    bpp = struct.unpack_from('<H', d, 28)[0]
    h = abs(h)
    rows = []
    if bpp == 8:
        pal = [q565(tuple(d[54 + i * 4:54 + i * 4 + 3][::-1])) for i in range(256)]
        stride = (w + 3) & ~3
        raw = [d[off + y * stride:off + y * stride + w] for y in range(h)][::-1]
        for r in raw:
            rows.append(b''.join(bytes(pal[i]) + b'\xff' for i in r))
    else:
        stride = (w * 3 + 3) & ~3
        raw = [d[off + y * stride:off + y * stride + w * 3] for y in range(h)][::-1]
        for r in raw:
            rows.append(b''.join(bytes(q565((r[i + 2], r[i + 1], r[i]))) + b'\xff' for i in range(0, w * 3, 3)))
    return 'data:image/png;base64,' + base64.b64encode(png_bytes(w, h, rows)).decode()


data['skins'] = {}
for f in os.listdir(os.path.join(EX, '3D')):
    if f.lower().endswith('.bmp'):
        data['skins'][f.lower()[:-4]] = bmp_any_png(os.path.join(EX, '3D', f))
SPRITES_EXTRA = {'bosshud': ('bosshud', 270, 26), 'bossenergy': ('bossenergy', 200, 24)}
for k, (f, fw, fh) in SPRITES_EXTRA.items():
    data['sprites'][k] = gfx(f, fw, fh)

MUSIC = {'title': 'tl', 'level1': '1', 'level2': '2', 'level3': '3', 'level4': '4', 'level5': '5', 'level6': '6',
         'clear': 'sc', 'highscore': 'hs', 'end': 'es', 'boss': 'eb', 'credits': 'cr'}
data['music'] = {}
for k, f in MUSIC.items():
    fp = os.path.join(EX, 'Sfx', f + '.trk')   # the .trk files are plain Impulse Tracker modules
    data['music'][k] = 'data:application/octet-stream;base64,' + base64.b64encode(open(fp, 'rb').read()).decode()
js = json.dumps(data, separators=(',', ':'))
t = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
assert t.count('/*DATA*/') == 1
out = os.path.join(HERE, 'takatis.html')
lib = open(os.path.join(ROOT, 'lib', 'libopenmpt.js'), encoding='utf-8', errors='ignore').read()
assert t.count('/*LIBOPENMPT*/') == 1 and t.count('/*WASM_B64*/') == 1 and t.count('/*BOSSASM*/') == 1
wasm_b64 = base64.b64encode(open(os.path.join(ROOT, 'lib', 'libopenmpt.wasm'), 'rb').read()).decode()
notice = open(os.path.join(ROOT, 'lib', 'LICENSE-libopenmpt.txt'), encoding='utf-8').read().replace('--', '- -')
t = t.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n<!--\n' + notice + '-->', 1)
# which build this is: the commit and its date, shown under the credits
import subprocess
try:
    rev, day = subprocess.run(['git', 'log', '-1', '--format=%h %cs'], cwd=ROOT, capture_output=True, text=True, check=True).stdout.split()
    y, m, d = day.split('-')
    build = 'Build %s · %s.%s.%s' % (rev, d, m, y)
except Exception:
    build = 'lokaler Build'
t = t.replace('/*BUILD*/', build)
html = t.replace('/*BOSSASM*/', BOSS_JS).replace('/*DATA*/', js).replace('/*LIBOPENMPT*/', lib).replace('/*WASM_B64*/', wasm_b64)
open(out, 'w', encoding='utf-8').write(html)
site = os.path.join(ROOT, 'dist')   # the same page as dist/index.html, ready for a static host
os.makedirs(site, exist_ok=True)
open(os.path.join(site, 'index.html'), 'w', encoding='utf-8').write(html)
print('wrote', out, os.path.getsize(out) // 1024, 'KB')
