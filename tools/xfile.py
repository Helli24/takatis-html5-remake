"""Minimal DirectX .x (text) parser for the Takatis boss meshes."""
import re


def _nums(s):
    return [float(v) for v in re.findall(r'-?\d+\.?\d*(?:[eE][-+]?\d+)?', s)]


def parse_x(path):
    txt = open(path, encoding='latin-1').read()
    txt = re.sub(r'//.*', '', txt)
    out = {'texture': None, 'color': [1, 1, 1, 1], 'matrix': None}
    m = re.search(r'TextureFilename\s*\{\s*"([^"]+)"', txt, re.I)
    if m:
        out['texture'] = m.group(1).split('/')[-1].lower()
    m = re.search(r'Material\s+[\w\-]*\s*\{\s*([^;]+;;)', txt)
    if m:
        out['color'] = _nums(m.group(1))[:4]
    m = re.search(r'FrameTransformMatrix\s*\{([^}]*)\}', txt)
    if m:
        out['matrix'] = _nums(m.group(1))[:16]
    # Mesh block: nVertices; vertices; nFaces; faces
    m = re.search(r'\bMesh\s+[\w\-]*\s*\{\s*(\d+)\s*;', txt)
    n = int(m.group(1))
    pos = m.end()
    verts = []
    rest = txt[pos:]
    vm = re.compile(r'\s*(-?[\d.eE+-]+)\s*;\s*(-?[\d.eE+-]+)\s*;\s*(-?[\d.eE+-]+)\s*;[,;]')
    p = 0
    for _ in range(n):
        mm = vm.match(rest, p)
        verts.append((float(mm.group(1)), float(mm.group(2)), float(mm.group(3))))
        p = mm.end()
    fm = re.match(r'\s*(\d+)\s*;', rest[p:])
    nf = int(fm.group(1))
    p += fm.end()
    faces = []
    facem = re.compile(r'\s*(\d+)\s*;\s*([\d,\s]+?)\s*;[,;]')
    for _ in range(nf):
        mm = facem.match(rest, p)
        idx = [int(v) for v in mm.group(2).split(',')]
        faces.append(idx)
        p += mm.end() - p if False else 0
        p = mm.end()
    # texture coords
    uvs = None
    m = re.search(r'MeshTextureCoords\s*[\w]*\s*\{\s*(\d+)\s*;', txt)
    if m:
        nt = int(m.group(1))
        q = m.end()
        uvm = re.compile(r'\s*(-?[\d.eE+-]+)\s*;\s*(-?[\d.eE+-]+)\s*;[,;]')
        uvs = []
        for _ in range(nt):
            mm = uvm.match(txt, q)
            uvs.append((float(mm.group(1)), float(mm.group(2))))
            q = mm.end()
    out['verts'] = verts
    out['faces'] = faces
    out['uvs'] = uvs
    return out


def transform(verts, mat):
    if not mat:
        return verts
    m = mat
    res = []
    for x, y, z in verts:
        res.append((x * m[0] + y * m[4] + z * m[8] + m[12], x * m[1] + y * m[5] + z * m[9] + m[13], x * m[2] + y * m[6] + z * m[10] + m[14]))
    return res


def triangulate(faces):
    tris = []
    for f in faces:
        for i in range(1, len(f) - 1):
            tris.append((f[0], f[i], f[i + 1]))
    return tris


def vertex_normals(verts, tris):
    import math
    n = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        ax, ay, az = verts[a]; bx, by, bz = verts[b]; cx, cy, cz = verts[c]
        ux, uy, uz = bx - ax, by - ay, bz - az
        vx, vy, vz = cx - ax, cy - ay, cz - az
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        for i in (a, b, c):
            n[i][0] += nx; n[i][1] += ny; n[i][2] += nz
    res = []
    for v in n:
        l = math.sqrt(v[0] ** 2 + v[1] ** 2 + v[2] ** 2) or 1.0
        res.append((v[0] / l, v[1] / l, v[2] / l))
    return res
