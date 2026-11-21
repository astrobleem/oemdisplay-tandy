"""Derive the reviewed System strike for the 640x200 IBM CGA profile."""
from pathlib import Path
import importlib.machinery as M
import struct

ROOT = Path(__file__).resolve().parents[2]
I = M.SourceFileLoader('tight640_fon', str(ROOT/'tools/XTFONTS/INSPECT.PY')).load_module()
FONT = 'XTCLITE.FON'
ADVANCES = {' ': (4, 3), 'i': (4, 3), 'l': (4, 3), '!': (4, 3),
            '.': (4, 3), "'": (4, 3), '|': (4, 3), 'm': (12, 9),
            'n': (8, 7), 'w': (10, 9)}


def build(base):
    """Keep original resources/metrics except the reviewed widths and E stem."""
    _, resources = I.resources(base)
    [(start, size)] = [(off, count) for kind, _, _, off, count in resources
                       if kind == 0x8008]
    raw = base[start:start + size]
    info = I.fontinfo(raw)
    if (info['height'], info['ascent'], info['type'] & 1, info['charset'],
            info['pix_width'], info['first'], info['last']) != (8, 7, 0, 0, 0, 32, 255):
        raise ValueError('Expected the original 8-row proportional XTC System strike')

    def glyph(char):
        entry = 118 + 4 * (ord(char) - info['first'])
        width, offset = struct.unpack_from('<HH', raw, entry)
        if offset + ((width + 7) // 8) * 8 > len(raw):
            raise ValueError('XTC glyph is outside the font resource')
        return entry, width, offset

    result = bytearray(base)
    for char, (original, advance) in ADVANCES.items():
        entry, width, offset = glyph(char)
        if width != original or (width + 7) // 8 != (advance + 7) // 8:
            raise ValueError('Unexpected original XTC advance: ' + repr(char))
        for x in range(advance, width):
            if any(raw[offset + (x // 8) * 8 + y] & (0x80 >> (x % 8)) for y in range(8)):
                raise ValueError('New XTC advance would clip ink: ' + repr(char))
        struct.pack_into('<H', result, start + entry, advance)

    _, width, offset = glyph('E')
    if width != 10:
        raise ValueError('Expected a 10-pixel XTC capital E')
    for y in (1, 2, 4, 5):
        if (raw[offset + y], raw[offset + y + 8]) != (0x60, 0):
            raise ValueError('Unexpected XTC capital E stem')
        result[start + offset + y] = 0x40
    return bytes(result)
