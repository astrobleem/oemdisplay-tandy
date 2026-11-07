"""Correct XTCSYS capital M/W without changing other glyphs or stock metrics.

The original 7-column drawings were stretched to 10/12 ink columns by the
compatibility advances. Keep those drawings at their natural width, with
one blank column at each side: both advances become 9 pixels. Existing
resource offsets, identities, System metrics and all other bytes survive.
Historical R10 files and contracts are intentionally not rewritten. Native
Win3 dialog base units change from 8x8 to 7x8; qualify affected dialogs when
installing this as the System font. Other glyphs and header metrics stay intact.
"""
import argparse
import importlib.machinery
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
I = importlib.machinery.SourceFileLoader('narrow_inspect', str(HERE/'INSPECT.PY')).load_module()
G = importlib.machinery.SourceFileLoader('narrow_glyphs', str(HERE/'GLYPHS.PY')).load_module().G


def narrow(data):
    result = bytearray(data)
    entries = [e for e in I.resources(data)[1] if e[0] == 0x8008]
    if len(entries) != 1:
        raise ValueError('Expected one XTCSYS resource')
    base = entries[0][3]
    raw = data[base:base + I.dword(data,base+2)]
    h = I.fontinfo(raw)
    if (h['face'],h['height'],h['charset'],h['pix_width'],h['first'],h['last']) != ('System',8,0,0,32,255):
        raise ValueError('Expected XTCSYS 8-row ANSI System')
    for char,before in (('M',12),('W',14)):
        at = base + 118 + (ord(char)-h['first'])*4
        width,offset = struct.unpack_from('<HH',result,at)
        if width != before:
            raise ValueError('Unexpected original '+char+' advance')
        # 9-pixel advances still occupy two byte-columns, just like 12/14.
        # Their storage boundaries and every later glyph offset stay valid.
        rows = G[char]
        if len(rows) != 8 or any(len(row) != 7 for row in rows):
            raise ValueError('Original 7-column M/W drawings changed')
        # Refuse an unrelated or already edited System font.
        expected_rows = [[0] + [int(row[x*7//(before-2)] == '#')
                         for x in range(before-2)] + [0] for row in rows]
        expected = bytes(sum(row[x] << (7-x%8)
                         for x in range(col*8,min(before,col*8+8)))
                         for col in range(2) for row in expected_rows)
        if data[base+offset:base+offset+16] != expected:
            raise ValueError('Unexpected original '+char+' bitmap')
        struct.pack_into('<H',result,at,9)
        for y,row in enumerate(rows):
            result[base+offset+y] = sum((pixel == '#') << (6-x) for x,pixel in enumerate(row))
            result[base+offset+8+y] = 0
    return bytes(result)


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',type=Path,default=HERE.parents[1]/'distributions/WINXT/XTCSYS.FON')
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists():
        raise SystemExit('Choose a fresh output; no accepted font is overwritten.')
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_bytes(narrow(a.input.read_bytes()))
    print('XTCSYS: M advance 12 -> 9; W advance 14 -> 9; all other glyphs unchanged.')
