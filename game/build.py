"""Build game/takatis.html from game/template.html + original game data."""
import os, sys, json, base64, struct, zlib
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from takatis import Level, level_screens, level_speed, layer_a_width, load_bmp8

EX = os.path.join(ROOT, 'extracted')


def png_bytes(w, h, rows):
    raw = b''.join(b'\0' + r for r in rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))


def img_b64(path, key=True):
    w, h, pal, px = load_bmp8(path)
    keyidx = {i for i, c in enumerate(pal) if c == (0, 255, 0)} if key else set()
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
    'player': ('player', 49, 34), 'player2': ('player2', 49, 34),
    'spread': ('spreadshot', 18, 17), 'laser': ('laser', 24, 12),
    'bounce1': ('bounce1', 24, 24), 'bounce2': ('bounce2', 18, 18), 'bounce3': ('bounce3', 12, 12),
    'rocket': ('rocket', 16, 16), 'powerline': ('powerline', 16, 32),
    'beammini': ('beammini', 16, 8), 'beamsmall': ('beamsmall', 32, 16), 'beammed': ('beammed', 48, 24), 'beambig': ('beambig', 64, 32),
    'beamload': ('beam-load', 248, 24), 'beamexplode': ('beamexplode', 50, 50),
    'explosion': ('explosion', 60, 50), 'explosion2': ('explosion2', 48, 48), 'smallexpl': ('small_explosion', 16, 16),
    'smoke': ('smoke', 16, 16), 'lasersmoke': ('lasersmoke', 16, 16), 'shieldflare': ('shieldflare', 16, 16),
    'debris1': ('debris1', 16, 16), 'debris2': ('debris2', 16, 16), 'debris3': ('Debris3', 16, 16),
    'bullet': ('turret-bullet', 8, 8), 'walkershot': ('walkershot', 24, 24), 'bullspread': ('bullspread', 18, 13), 'chaseshot': ('chaseshot', 32, 14),
    'elevatorshot': ('elevatorshot', 32, 8), 'volcanoball': ('volcanoball', 16, 16), 'mine': ('mine', 24, 24), 'spike1': ('spike1', 16, 17), 'spike2': ('spike2', 16, 17),
    'shield': ('shield', 56, 34), 'powerups': ('powerups', 20, 20), 'star': ('star', 72, 72), 'blob': ('blob1', 12, 12),
    'pu_oneup': ('pu_oneup', 20, 20), 'pu_bounce': ('pu_bounce', 20, 20), 'pu_shield': ('pu_shield', 20, 20), 'pu_line': ('pu_line', 20, 20),
    'pu_spread': ('pu_spread', 20, 20), 'pu_laser': ('pu_laser', 20, 20), 'pu_rocket': ('pu_rocket', 20, 20),
    'hudtop': ('hud-oben', 640, 16), 'hudbottom': ('hud-unten', 640, 48), 'energy': ('player-energy', 56, 9),
    'font': ('font', 10, 14), 'font2': ('font2', 8, 10), 'bigfont': ('bigfont', 32, 32),
    'title': ('title', 640, 480), 'getready': ('getready', 329, 56), 'gameover': ('gameover', 429, 56), 'logo': ('logo', 640, 140),
    'endscreen': ('Endscreen', 640, 480), 'menu': ('menu', 224, 64), 'rahmen': ('rahmen', 32, 32), 'loading': ('loading', 280, 146),
    # enemies by type
    'e0': ('asteroid', 64, 54), 'e1': ('Razorback', 52, 32), 'e2': ('spinner', 56, 46), 'e9': ('container', 36, 46),
    'e10': ('turret-floor', 44, 41), 'e11': ('turret-ceiling', 44, 41), 'e12': ('walker', 43, 54), 'e13': ('magnet', 32, 32),
    'e14': ('bulldozer', 80, 47), 'e15': ('VoltCare', 49, 34), 'e16': ('circuit', 32, 32), 'e17': ('faller', 32, 64),
    'e18': ('block1', 16, 16), 'e19': ('block2', 16, 16), 'e20': ('block3', 16, 16), 'e21': ('block4', 16, 16),
    'e22': ('arnold', 71, 17), 'e23': ('Kraftfeld', 71, 64), 'e24': ('x6502', 84, 47), 'e25': ('elevator', 56, 68),
    'e26': ('presse1', 64, 256), 'e27': ('presse2', 64, 256), 'e28': ('spikeball', 72, 72), 'e29': ('volcano', 80, 36),
    'e30': ('bumper', 40, 40), 'e31': ('timebomb', 48, 48), 'e32': ('sharpshooter', 32, 32), 'e33': ('containerfake', 36, 61),
    'dragontail': ('dragontail', 40, 40), 'drive': ('drive', 16, 16), 'rail': ('rail', 11, 32),
}
NOKEY = {'title', 'endscreen', 'loading'}

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
    objs = [[o['type'], o['x'], (o['y'] - 2**32 if o['y'] >= 2**31 else o['y']), o['param'], o['flag']] for o in lv.objects]
    objs.sort(key=lambda o: o[1])
    data['levels'].append({'stage': stage[i - 1][0], 'hint': stage[i - 1][1], 'theme': (i + 1) // 2, 'screens': scr,
                           'speed': level_speed(lv), 'wa': wa, 'wb': scr * 20,
                           'A': base64.b64encode(b''.join(A)).decode(), 'B': base64.b64encode(b''.join(B)).decode(), 'objects': objs})

SOUNDS = {'explosion': 'Explosion', 'bigexplosion': 'bigexplosion', 'spread': 'Spread', 'laser': 'Laser', 'laser2': 'Laser2', 'hit': 'Hit',
          'shield': 'Shield', 'rocket': 'Rocket', 'bounce': 'Bounce', 'beam': 'Beam', 'bigshot': 'BigShot', 'trigger': 'Trigger',
          'powerline': 'powerline', 'morph': 'morph', 'klippikloppi': 'klippikloppi'}
for k, f in SOUNDS.items():
    p = os.path.join(ROOT, 'assets', 'Sfx', f + '.wav')
    data['sounds'][k] = 'data:audio/wav;base64,' + base64.b64encode(open(p, 'rb').read()).decode()
SPEECH = {'online': 'online', 'oneup': '1up', 'spread': 'spread', 'laser': 'laser', 'bounce': 'bounce', 'shield': 'shield', 'homing': 'homing', 'line': 'line', 'bigone': 'bigone'}
for k, f in SPEECH.items():
    p = os.path.join(ROOT, 'assets', 'Speech', f + '.wav')
    data['sounds']['v_' + k] = 'data:audio/wav;base64,' + base64.b64encode(open(p, 'rb').read()).decode()


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
            rows.append(b''.join(bytes(pal[i]) + b'\xff' for i in r))
    else:
        stride = (w * 3 + 3) & ~3
        raw = [d[off + y * stride:off + y * stride + w * 3] for y in range(h)][::-1]
        for r in raw:
            rows.append(b''.join(bytes((r[i + 2], r[i + 1], r[i])) + b'\xff' for i in range(0, w * 3, 3)))
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
    fp = os.path.join(ROOT, 'assets', 'Sfx', f + '.it')
    data['music'][k] = 'data:application/octet-stream;base64,' + base64.b64encode(open(fp, 'rb').read()).decode()
js = json.dumps(data, separators=(',', ':'))
t = open(os.path.join(HERE, 'template.html'), encoding='utf-8').read()
assert t.count('/*DATA*/') == 1
out = os.path.join(HERE, 'takatis.html')
lib = open(os.path.join(ROOT, 'libopenmpt.js'), encoding='utf-8', errors='ignore').read()
assert t.count('/*LIBOPENMPT*/') == 1 and t.count('/*WASM_B64*/') == 1
wasm_b64 = base64.b64encode(open(os.path.join(ROOT, 'libopenmpt.wasm'), 'rb').read()).decode()
html = t.replace('/*DATA*/', js).replace('/*LIBOPENMPT*/', lib).replace('/*WASM_B64*/', wasm_b64)
open(out, 'w', encoding='utf-8').write(html)
print('wrote', out, os.path.getsize(out) // 1024, 'KB')
