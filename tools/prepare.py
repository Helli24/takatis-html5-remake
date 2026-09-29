"""Unpack 'Takatis Setup V1_2.exe' into extracted/ and write extracted/Takatis_patched.exe.

The build (game/build.py) calls this on its own when extracted/ is missing. Everything the remake needs is read from
the unpacked files; nothing else has to be prepared by hand.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from takatis import extract_installer  # noqa: E402

SETUP = os.path.join(ROOT, 'Takatis Setup V1_2.exe')
EX = os.path.join(ROOT, 'extracted')

# Takatis.exe asks for DDSCAPS_VIDEOMEMORY (0x4000) in four surface descriptions; on Windows 11 creating the scroll
# surface then fails. Clearing that bit lets the original run again.
PATCH = [(0x1152f, 0x40, 0x00), (0x115c4, 0x40, 0x00), (0x117e3, 0x60, 0x20), (0x128f7, 0x40, 0x00)]


def patch_exe():
    d = bytearray(open(os.path.join(EX, 'Takatis.exe'), 'rb').read())
    for off, old, new in PATCH:
        assert d[off] == old, hex(off)
        d[off] = new
    open(os.path.join(EX, 'Takatis_patched.exe'), 'wb').write(d)


def prepare():
    n = extract_installer(SETUP, EX)
    patch_exe()
    return n


if __name__ == '__main__':
    print('unpacked', prepare(), 'entries to', EX)
