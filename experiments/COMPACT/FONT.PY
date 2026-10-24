"""Generate original compact Win3 FNT/FON files without private inputs.

Reuse XT Pixels' original grids, character mapping, cell algorithms and NE
writer. No installed fonts, ROM, Microsoft bitmaps, or image resizing.
"""
import hashlib
import importlib.machinery
import json
import struct
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def load(name, path):
    return importlib.machinery.SourceFileLoader(name, str(path)).load_module()


ORIGINAL = load('GLYPHS', ROOT / 'tools/XTFONTS/GLYPHS.PY')
sys.modules['GLYPHS'] = ORIGINAL
XT = load('compact_xtbuild', ROOT / 'tools/XTFONTS/BUILD.PY')
GRID = load('compact_grid', HERE / 'GRID.PY')

# Keep Win3 stock font identities, FONTDIR and charset conventions. Separate
# filenames make Setup's choice opt-in; existing XTC*/XTE* files stay intact.
FACES = {
    'C16SYS.FON': ('System', 'FONTS', 27, 0, False, 700, 0x21, 1, 0),
    'C16FIX.FON': ('FixedSys', 'FIXFONTS', 27, 0, True, 400, 0x30, 0, 1),
    'C16OEM.FON': ('Terminal', 'OEMFONTS', 29, 255, True, 400, 0x30, 0, 0),
    'C16HELV.FON': ('Helv', 'C16HELV', 27, 0, False, 700, 0x21, 1, 0),
    'C16COUR.FON': ('Courier', 'C16COUR', 27, 0, True, 400, 0x30, 0, 1),
}


def glyph(char, fixed=False):
    """Return ink rows and provenance. Never remove authored columns/rows."""
    if fixed:
        cell = XT.cell_glyph(char, 4, 8) if char else None
        if cell is not None:
            return cell, 'original XT cell algorithm'
    source = GRID.FIXED.get(char, GRID.G.get(char)) if fixed else GRID.G.get(char)
    origin = 'compact authored grid'
    if source is None:
        source = GRID.accented(char)
        origin = 'compact authored accent recipe'
    if source is None:
        source = ORIGINAL.G.get(char)
        origin = 'original XT grid at authored width'
    if source is None or fixed and len(source[0]) > 3:
        source = GRID.G['\u25a1']
        origin = 'visible fallback'
    width = 4 if fixed else len(source[0]) + 1
    # Left bearing zero, one blank advance column; one-pixel wide letters
    # remain distinct. Descenders occupy row 7 without vertical resampling.
    return [[int(c == '#') for c in row] + [0] * (width - len(row)) for row in source], origin


def fnt(face, charset, fixed, weight, family, internal, external):
    first, last = (1, 254) if charset == 255 else (32, 255)
    table_start = 118 + (last - first + 2) * 4
    offsets, widths, bits, coverage = [], [], bytearray(), []
    for code in range(first, last + 2):
        char = XT.decode_code(code, charset) if code <= last else ' '
        rows, origin = glyph(char, fixed)
        width = len(rows[0])
        offsets.append(table_start + len(bits))
        widths.append(width)
        for column in range((width + 7) // 8):
            for row in rows:
                bits.append(sum(row[x] << (7 - x % 8) for x in range(column * 8, min(width, column * 8 + 8))))
        if code <= last:
            coverage.append(dict(code=code, char=char, source=origin, width=width))
    stride = len(bits) // 8
    stride += stride % 2
    bits += bytes(stride * 8 - len(bits))
    faceoff = table_start + len(bits)
    facebytes = face.encode('ascii') + b'\0'
    header = bytearray(118)
    struct.pack_into('<HI', header, 0, 0x200, faceoff + len(facebytes))
    notice = b'XT Pixels Compact (c) 2026 contributors; MIT'
    header[6:6 + len(notice)] = notice
    for offset, value in ((66, 0), (68, 6), (70, 48), (72, 96), (74, 7),
                          (76, internal), (78, external), (83, weight),
                          (86, 4 if fixed else 0), (88, 8), (91, 4),
                          (93, max(widths)), (99, stride)):
        struct.pack_into('<H', header, offset, value)
    for offset, value in ((85, charset), (90, family), (95, first), (96, last),
                          (97, 32 - first if charset == 255 else 0x80 - first), (98, 32 - first)):
        header[offset] = value
    struct.pack_into('<I', header, 105, faceoff)
    struct.pack_into('<I', header, 113, table_start)
    table = b''.join(struct.pack('<HH', w, o) for w, o in zip(widths, offsets))
    return bytes(header) + table + bits + facebytes, coverage


def write(out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    record = {'runtime': 'NOT_TESTED', 'font_height': 8, 'average_width': 4, 'fonts': {}}
    for name, (face, module, rid, charset, fixed, weight, family, internal, external) in FACES.items():
        font, coverage = fnt(face, charset, fixed, weight, family, internal, external)
        data = XT.fon(font, module, rid, 'XT Pixels Compact 160 experimental ' + face)
        (out / name).write_bytes(data)
        record['fonts'][name] = dict(face=face, charset=charset, weight=weight,
            sha256=hashlib.sha256(data).hexdigest(), bytes=len(data),
            fallback_codes=[c['code'] for c in coverage if c['source'] == 'visible fallback'],
            coverage=coverage)
    return record


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    if a.out.exists():
        p.error('choose a fresh output directory')
    result = write(a.out)
    XT.textfile(a.out / 'FONTS.JSN', json.dumps(result, ensure_ascii=True, indent=2) + '\n')
    print('Generated five original compact fonts; Windows runtime NOT_TESTED')
