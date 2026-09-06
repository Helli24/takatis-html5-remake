"""Takatis (Poke53280, 2002) file-format toolkit.

Formats handled:
  * NitroSetup 1.4 installer payload (LZSS variant)   -> extract_installer()
  * .gfx/.stc/.tsa/.tsb  = plain 8-bit Windows BMPs    -> load_bmp8()
  * .sfx/.spc            = RIFF WAV with renamed chunks -> fix_wav()
  * .trk                 = Impulse Tracker module (.it)
  * .lvl                 = level: header (u8 screens, u8 start scroll speed),
                           layer A = parallax background, 13 rows x (screens*10+10) cols,
                                     drawn at half scroll speed with tileset NN.tsb,
                           layer B = foreground/collision, 13 rows x (screens*20) cols,
                                     drawn with tileset NN.tsa,
                           u32 object count, 20-byte object records
                           (type u32, x u32 level px, y i32 screen px, param u32
                           = index into a 64-entry movement pattern table, flag u8 =
                           minimum difficulty 0/1/2, 3 bytes 0xCC padding)
  * pure-python PNG writer for viewing (no PIL needed)
"""
import os
import struct
import zlib

ROWS = 13          # visible tile rows (416 px / 32)
TILE = 32
TILESET_COLS = 10  # 320x320 tileset => 10x10 tiles


# ---------------------------------------------------------------- installer
def lzss_decode(comp: bytes, usz: int) -> bytes:
    """NitroSetup LZSS: flag byte (MSB first, 1 = back-reference),
    reference = 16-bit big-endian, distance = v >> 4, length = (v & 15) + 2."""
    out = bytearray()
    i = 0
    n = len(comp)
    while len(out) < usz and i < n:
        flags = comp[i]
        i += 1
        for b in range(8):
            if len(out) >= usz or i >= n:
                break
            if (flags >> (7 - b)) & 1:
                v = (comp[i] << 8) | comp[i + 1]
                i += 2
                dist, ln = v >> 4, (v & 15) + 2
                for _ in range(ln):
                    out.append(out[-dist])
            else:
                out.append(comp[i])
                i += 1
    return bytes(out)


def extract_installer(setup_path: str, out_dir: str):
    """Extract every file from 'Takatis Setup V1_2.exe' into out_dir."""
    d = open(setup_path, 'rb').read()
    pe = struct.unpack_from('<I', d, 0x3c)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    optsz = struct.unpack_from('<H', d, pe + 20)[0]
    sec = pe + 24 + optsz
    overlay = 0
    for i in range(nsec):
        rsz, ro = struct.unpack_from('<II', d, sec + i * 40 + 16)
        overlay = max(overlay, ro + rsz)
    p = overlay
    for _ in range(2):                      # title, description
        p = d.index(b'\0', p) + 1
    p += 4                                  # ff ff ff ff
    sz = struct.unpack_from('<I', d, p)[0]  # uninstaller stub (raw PE)
    p += 4 + sz
    usz, _, csz = struct.unpack_from('<III', d, p)
    p += 12 + csz                           # licence text block
    p += 8                                  # entry count, total size
    cur = out_dir
    os.makedirs(out_dir, exist_ok=True)
    n = 0
    while p < len(d) - 32:
        a, t, b, c = struct.unpack_from('<IIII', d, p)
        q = p + 16
        e = d.find(b'\0', q, q + 300)
        if e < 0 or t not in (1, 2):
            break
        name = d[q:e].decode('cp1252')
        p = e + 1
        if t == 1:                          # directory
            cur = out_dir if n == 0 else os.path.join(out_dir, name)
            os.makedirs(cur, exist_ok=True)
        else:                               # file
            if b == 1:
                cur = out_dir
            ts, usz, csz = struct.unpack_from('<III', d, p)
            p += 12
            data = lzss_decode(d[p:p + csz], usz)
            p += csz
            assert len(data) == usz, name
            fp = os.path.join(cur, name)
            open(fp, 'wb').write(data)
            os.utime(fp, (ts, ts))
        n += 1
    return n


# ---------------------------------------------------------------- bitmaps
_PERM_TABLE = None


def _perm_table():
    """Levelinfos.tsf is NOT level info: it is a triangular table of row
    permutations. Row k (k = 1..480) holds a permutation of 1..k and is used to
    scramble the scanlines of every bitmap with height k."""
    global _PERM_TABLE
    if _PERM_TABLE is None:
        here = os.path.dirname(os.path.abspath(__file__))
        for cand in (os.path.join(here, '..', 'extracted', 'Level', 'Levelinfos.tsf'),
                     os.path.join(here, 'Levelinfos.tsf'),
                     'Levelinfos.tsf'):
            if os.path.exists(cand):
                _PERM_TABLE = open(cand, 'rb').read()
                break
        else:
            raise FileNotFoundError('Levelinfos.tsf (row permutation table) not found')
    return _PERM_TABLE


def row_permutation(h: int):
    t = _perm_table()
    o = h * (h - 1) // 2
    return struct.unpack_from('<%dH' % h, t, o * 2)


def unscramble_rows(rows_top_down):
    """rows_top_down: scanlines as stored (already flipped to top-down).
    Returns the real image, top-down."""
    h = len(rows_top_down)
    P = row_permutation(h)
    out = [None] * h
    for y in range(h):
        out[P[y] - 1] = rows_top_down[y][::-1]   # scanlines are also stored mirrored
    return out[::-1]


def load_bmp8(path: str, unscramble=True):
    """Return (width, height, palette[256] of (r,g,b), pixels top-down bytes).
    Game bitmaps (.gfx/.stc/.tsa/.tsb) have scrambled scanlines; unscramble=True
    restores them via the permutation table."""
    d = open(path, 'rb').read()
    assert d[:2] == b'BM', path
    off = struct.unpack_from('<I', d, 10)[0]
    w, h = struct.unpack_from('<ii', d, 18)
    bpp = struct.unpack_from('<H', d, 28)[0]
    assert bpp == 8, (path, bpp)
    pal = [tuple(d[54 + i * 4:54 + i * 4 + 3][::-1]) for i in range(256)]
    stride = (w + 3) & ~3
    flip = h > 0
    h = abs(h)
    rows = [d[off + y * stride: off + y * stride + w] for y in range(h)]
    if flip:
        rows.reverse()
    if unscramble:
        rows = unscramble_rows(rows)
    return w, h, pal, b''.join(rows)


def scramble_rows(rows_top_down):
    """Inverse of unscramble_rows: turn a real image into the on-disk row order
    (top-down), so modified/new graphics can be fed back to the original game."""
    h = len(rows_top_down)
    P = row_permutation(h)
    rev = rows_top_down[::-1]
    return [rev[P[y] - 1][::-1] for y in range(h)]


def write_png(path: str, w: int, h: int, rgba_rows):
    """rgba_rows: iterable of h bytes-objects, each w*4 bytes (RGBA)."""
    raw = b''.join(b'\0' + r for r in rgba_rows)

    def chunk(tag, data):
        c = tag + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0))
    png += chunk(b'IDAT', zlib.compress(raw, 6)) + chunk(b'IEND', b'')
    open(path, 'wb').write(png)


def bmp8_to_png(src: str, dst: str, transparent_index=None):
    w, h, pal, px = load_bmp8(src)
    rows = []
    for y in range(h):
        row = bytearray()
        for x in range(w):
            i = px[y * w + x]
            r, g, b = pal[i]
            a = 0 if i == transparent_index else 255
            row += bytes((r, g, b, a))
        rows.append(bytes(row))
    write_png(dst, w, h, rows)


# ---------------------------------------------------------------- wav
def fix_wav(src: str, dst: str):
    d = bytearray(open(src, 'rb').read())
    assert d[8:16] == b'LOSTsfx ', src
    d[8:16] = b'WAVEfmt '
    p = 20 + struct.unpack_from('<I', d, 16)[0]
    assert d[p:p + 4] == b'twew', src
    d[p:p + 4] = b'data'
    open(dst, 'wb').write(d)


# ---------------------------------------------------------------- levels
class Level:
    def __init__(self, path: str):
        d = open(path, 'rb').read()
        self.path = path
        self.header = struct.unpack_from('<H', d, 0)[0]
        # locate object table: last u32 count before 20-byte records at file end
        # records: (type u32, x u32, y u32, param u32, flag u8, pad 3x 0xCC)
        # find count by scanning from the end
        n_end = len(d)
        for count in range(0, 2000):
            pos = n_end - count * 20 - 4
            if pos < 2:
                break
            if struct.unpack_from('<I', d, pos)[0] == count and \
               all(d[pos + 4 + k * 20 + 17: pos + 4 + k * 20 + 20] == b'\xcc\xcc\xcc' for k in range(count)):
                self.obj_offset = pos
                self.count = count
                break
        else:
            raise ValueError('object table not found')
        map_len = self.obj_offset - 2
        assert map_len % ROWS == 0, (path, map_len)
        self.total_cols = map_len // ROWS
        self.map_raw = d[2:self.obj_offset]
        self.objects = []
        p = self.obj_offset + 4
        for _ in range(self.count):
            t, x, y, prm, flag = struct.unpack_from('<IIIIB', d, p)
            self.objects.append(dict(type=t, x=x, y=y, param=prm, flag=flag))
            p += 20

    def split_layers(self, width_a: int):
        """Layer A (parallax background) has width_a columns, layer B the rest."""
        wa = width_a
        wb = self.total_cols - wa
        a = self.map_raw[:wa * ROWS]
        b = self.map_raw[wa * ROWS:]
        A = [a[r * wa:(r + 1) * wa] for r in range(ROWS)]
        B = [b[r * wb:(r + 1) * wb] for r in range(ROWS)]
        return A, B


def guess_layer_width(level: Level):
    """Find width of layer A by maximising vertical tileset coherence (tile+10 below)."""
    raw = level.map_raw
    best = (0, 0)
    for wa in range(40, level.total_cols - 40):
        sc = 0
        # score the first 13 rows region only
        lim = min(len(raw) - wa, wa * (ROWS - 1))
        for i in range(lim):
            if raw[i] and raw[i + wa] == raw[i] + 10:
                sc += 1
        if sc > best[0]:
            best = (sc, wa)
    return best[1]


def render_layer(rows, tileset_path: str, transparent_index=0):
    w, h, pal, px = load_bmp8(tileset_path)
    cols = len(rows[0])
    W, H = cols * TILE, ROWS * TILE
    out = [bytearray(W * 4) for _ in range(H)]
    for r, row in enumerate(rows):
        for c, t in enumerate(row):
            if t == 0:
                continue
            tx, ty = (t % TILESET_COLS) * TILE, (t // TILESET_COLS) * TILE
            for yy in range(TILE):
                src = px[(ty + yy) * w + tx:(ty + yy) * w + tx + TILE]
                dst = out[r * TILE + yy]
                base = c * TILE * 4
                for xx, i in enumerate(src):
                    if i == transparent_index:
                        continue
                    rr, gg, bb = pal[i]
                    o = base + xx * 4
                    dst[o] = rr; dst[o + 1] = gg; dst[o + 2] = bb; dst[o + 3] = 255
    return W, H, [bytes(r) for r in out]


# ---------------------------------------------------------------- level writer
def layer_a_width(screens: int) -> int:
    """Width of the parallax layer as computed by the game: screens*20/2 + 10."""
    return (screens * 20) // 2 + 10


def write_level(path: str, screens: int, speed: int, layer_a, layer_b, objects):
    """Write a .lvl file the original game can load.
    layer_a: 13 rows x layer_a_width(screens) tile bytes, layer_b: 13 rows x screens*20.
    objects: list of dicts with type, x, y, param, flag."""
    wa, wb = layer_a_width(screens), screens * 20
    assert len(layer_a) == ROWS and all(len(r) == wa for r in layer_a), 'layer A size'
    assert len(layer_b) == ROWS and all(len(r) == wb for r in layer_b), 'layer B size'
    out = bytearray(struct.pack('<BB', screens, speed))
    for r in layer_a:
        out += bytes(r)
    for r in layer_b:
        out += bytes(r)
    out += struct.pack('<I', len(objects))
    for o in objects:
        out += struct.pack('<IIiIB', o['type'], o['x'], o['y'], o['param'], o['flag']) + b'\xcc\xcc\xcc'
    open(path, 'wb').write(out)


def level_screens(level: Level) -> int:
    return level.header & 0xff


def level_speed(level: Level) -> int:
    return level.header >> 8
