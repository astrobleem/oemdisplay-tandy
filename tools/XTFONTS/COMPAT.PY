"""Retain narrow M/W while restoring Windows 3.0 System dialog units.

Add one real blank advance column to I, J, C, E and S. Every bitmap,
resource offset and header byte remains unchanged. Historical System
fonts and the earlier two-letter correction are separate frozen inputs.
"""
import argparse
import hashlib
import importlib.machinery
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
N = importlib.machinery.SourceFileLoader('compat_narrow', str(HERE / 'NARROW.PY')).load_module()
INPUT_SHA256 = '4a66e2f7fd26f9575fb26766e630c0805bfee60f51d27adaf08975678bcbca76'
SPACING = (('I', 4, 5), ('J', 7, 8), ('C', 9, 10), ('E', 9, 10), ('S', 9, 10))


def raw_font(data):
    entries = [e for e in N.I.resources(data)[1] if e[0] == 0x8008]
    if len(entries) != 1:
        raise ValueError('Expected exactly one XTCSYS font resource')
    base = entries[0][3]
    return data[base:base + N.I.dword(data, base + 2)], base


def glyph(raw, code):
    code = code if raw[95] <= code <= raw[96] else raw[95] + raw[97]
    width, offset = struct.unpack_from('<HH', raw, 118 + (code - raw[95]) * 4)
    height = N.I.word(raw, 88)
    return [[(raw[offset + (x // 8) * height + y] >> (7 - x % 8)) & 1
             for x in range(width)] for y in range(height)]


def compatible(data):
    # Reject unrelated fonts, edited inputs and repeated application. This
    # identifies the existing source asset; no private path is required.
    if hashlib.sha256(data).hexdigest() != INPUT_SHA256:
        raise ValueError('Expected the unchanged narrow XTCSYS source asset')
    raw, base = raw_font(data)
    info = N.I.fontinfo(raw)
    if (info['face'], info['height'], info['charset'], info['pix_width'],
            info['pitch_family'], info['avg_width'], info['first'], info['last']) != (
            'System', 8, 0, 0, 0x21, 7, 32, 255):
        raise ValueError('Unexpected variable-pitch System metadata')
    for char in 'MW':
        rows = glyph(raw, ord(char))
        if (len(rows[0]) != 9 or any(row[0] or row[-1] for row in rows) or
                [''.join('#' if p else '.' for p in row[1:8]) for row in rows] != N.G[char]):
            raise ValueError('Unexpected narrow M/W drawing or advance')
    result = bytearray(data)
    for char, before, after in SPACING:
        at = 118 + (ord(char) - info['first']) * 4
        width, offset = struct.unpack_from('<HH', raw, at)
        if width != before or (before + 7) // 8 != (after + 7) // 8:
            raise ValueError('Unexpected glyph advance or storage boundary')
        for y in range(info['height']):
            if raw[offset + (before // 8) * info['height'] + y] & (128 >> (before % 8)):
                raise ValueError('The added spacing column is not blank')
        struct.pack_into('<H', result, base + at, after)
    return bytes(result)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=HERE / 'NARROW/XTCSYS.FON')
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise SystemExit('Choose a fresh output; no accepted font is overwritten.')
    result = compatible(a.input.read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_bytes(result)
    print('XTCSYS: M/W remain 9; I/J/C/E/S gain one blank advance column.')


if __name__ == '__main__':
    main()
