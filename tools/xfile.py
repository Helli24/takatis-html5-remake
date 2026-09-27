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
    # Material { faceColor RGBA; power; specular RGB; emissive RGB; [TextureFilename] }, the numbers separated by ',' or
    # ';'; the DX7 loader (0x42e929) takes faceColor as diffuse and ambient colour
    m = re.search(r'(?<![\w])Material(?!List)\s*[\w\-]*\s*\{([^{}]*)', txt)
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
    # per-face-corner normals (MeshNormals: normal list plus one index list per face)
    normals = None
    out['normals_raw'] = None
    m = re.search(r'MeshNormals\s*[\w]*\s*\{\s*(\d+)\s*;', txt)
    if m:
        nn = int(m.group(1))
        q = m.end()
        nv = re.compile(r'\s*(-?[\d.eE+-]+)\s*;\s*(-?[\d.eE+-]+)\s*;\s*(-?[\d.eE+-]+)\s*;[,;]')
        nl = []
        for _ in range(nn):
            mm = nv.match(txt, q)
            nl.append((float(mm.group(1)), float(mm.group(2)), float(mm.group(3))))
            q = mm.end()
        out['normals_raw'] = nl
        fm = re.match(r'\s*(\d+)\s*;', txt[q:])
        q += fm.end()
        normals = []
        for _ in range(int(fm.group(1))):
            mm = facem.match(txt, q)
            normals.append([nl[int(v)] for v in mm.group(2).split(',')])
            q = mm.end()
    out['verts'] = verts
    out['faces'] = faces
    out['uvs'] = uvs
    out['normals'] = normals
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


def d3dfile_normals(verts, tris):
    """Vertex normals as CD3DFileObject::ComputeNormals (DX7 d3dfile.cpp, 0x42e5d1 in Takatis.exe) makes them: per
    triangle the normalised (P1-P0) x (P2-P1) is added to its three vertices, then every sum is normalised; sums
    shorter than 0.1 become (0,0,1)."""
    import math
    n = [[0.0, 0.0, 0.0] for _ in verts]
    for a, b, c in tris:
        p0, p1, p2 = verts[a], verts[b], verts[c]
        u = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        v = (p2[0] - p1[0], p2[1] - p1[1], p2[2] - p1[2])
        x, y, z = u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]
        l = math.sqrt(x * x + y * y + z * z)
        if l == 0:
            continue   # the original divides by zero here; a degenerate triangle adds nothing usable
        for i in (a, b, c):
            n[i][0] += x / l; n[i][1] += y / l; n[i][2] += z / l
    out = []
    for x, y, z in n:
        l = math.sqrt(x * x + y * y + z * z)
        if l < 0.1:
            x, y, z, l = 0.0, 0.0, 1.0, 1.0
        out.append((x / l, y / l, z / l))
    return out
