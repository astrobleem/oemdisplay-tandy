"""Deterministic, host-only original FNT 2.x and resource-only NE writer.

No private Windows file, installed font, Pillow font, compiler, or emulator
is used by this builder. Specimens decode the emitted FNT bytes.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from GLYPHS import G
import unicodedata

HERE = Path(__file__).resolve().parent

# OEM control-code pictures are Unicode identities, not control operations.
CONTROLS = '\u0000\u263a\u263b\u2665\u2666\u2663\u2660\u2022\u25d8\u25cb\u25d9\u2642\u2640\u266a\u266b\u263c\u25ba\u25c4\u2195\u203c\u00b6\u00a7\u25ac\u21a8\u2191\u2193\u2192\u2190\u221f\u2194\u25b2\u25bc'


def cell_glyph(char, width, height):
    if char is None:
        return None
    name = unicodedata.name(char or '', '') if char else ''
    rows = [[0] * width for _ in range(height)]
    if name.startswith('BOX DRAWINGS'):
        # Directional tracks reach cell edges; mixed single/double strokes
        # join through a center hub. The design is algorithmic and original.
        directions = {s for s in ('LEFT', 'RIGHT', 'UP', 'DOWN') if s in name}
        if 'HORIZONTAL' in name:
            directions |= {'LEFT', 'RIGHT'}
        if 'VERTICAL' in name:
            directions |= {'UP', 'DOWN'}
        double = 'DOUBLE' in name
        xs = [width // 3, width * 2 // 3] if double else [width // 2]
        ys = [height // 3, height * 2 // 3] if double else [height // 2]
        # CP437 mixed forms distinguish their horizontal/vertical tracks.
        if 'SINGLE' in name and double:
            parts = name.split(' AND ')
            xs = [width // 2] if any('SINGLE' in p and any(
                d in p for d in ('VERTICAL', 'UP', 'DOWN')) for p in parts) else xs
            ys = [height // 2] if any('SINGLE' in p and any(
                d in p for d in ('HORIZONTAL', 'LEFT', 'RIGHT')) for p in parts) else ys
        for y in ys:
            for x in range(width):
                if ('LEFT' in directions and x <= max(xs)) or (
                        'RIGHT' in directions and x >= min(xs)):
                    rows[y][x] = 1
        for x in xs:
            for y in range(height):
                if ('UP' in directions and y <= max(ys)) or (
                        'DOWN' in directions and y >= min(ys)):
                    rows[y][x] = 1
        return rows
    if char in '\u2591\u2592\u2593':
        threshold = {'\u2591': 1, '\u2592': 2, '\u2593': 3}[char]
        return [[int((x + 2 * y) % 4 < threshold) for x in range(width)]
                for y in range(height)]
    if char in '\u2588\u2580\u2584\u258c\u2590':
        for y in range(height):
            for x in range(width):
                rows[y][x] = int(char == '\u2588' or
                    char == '\u2580' and y < height // 2 or
                    char == '\u2584' and y >= height // 2 or
                    char == '\u258c' and x < width // 2 or
                    char == '\u2590' and x >= width // 2)
        return rows
    return None


def textfile(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def glyph(char, width, height, fixed=False):
    cell = cell_glyph(char, width, height) if fixed else None
    if cell is not None:
        return cell
    source = G.get(char, G['\u25a1'])
    sw = len(source[0])
    target = min(width - 1, max(1, sw)) if fixed else (
        min(width - 1, sw) if sw < 5 else max(1, width - 2))
    target = max(1, target)
    left = (width - target) // 2
    rows = [[0] * width for _ in range(height)]
    if height == 8:
        ymap = list(range(8))
    elif height == 10:
        ymap = [None] + [min(6, y * 7 // 8) for y in range(8)] + [7]
    elif height == 12:
        ymap = [None] + [min(6, y * 7 // 9) for y in range(9)] + [7, 7]
    else:
        raise ValueError('Unsupported hand-tuned strike height')
    for y, sy in enumerate(ymap):
        if sy is not None:
            for x in range(target):
                rows[y][left + x] = int(source[sy][min(sw - 1, x * sw // target)] == '#')
    return rows


def decode_code(code, charset):
    if charset == 255:
        if code < 32:
            return CONTROLS[code]
        if code == 127:
            return '\u2302'
        return bytes([code]).decode('cp437')
    # Windows 3.0 ANSI has no Euro at 80h. Unassigned controls are fallback.
    if code in range(0x7f, 0xa0):
        if code in (0x80, 0x81, 0x8d, 0x8e, 0x8f, 0x90, 0x9d, 0x9e):
            return None
        return bytes([code]).decode('cp1252')
    return chr(code)


def fnt(contract, face=None):
    h = contract
    first, last, height = h['first'], h['last'], h['height']
    # Every inspected strike advertises an eight-pixel absolute blank entry.
    widths = h['widths'] + [8]
    bitstart = 118 + len(widths) * 4
    if bitstart % 2:
        bitstart += 1
    offsets, bits, coverage = [], bytearray(), []
    for code, width in zip(range(first, last + 2), widths):
        char = decode_code(code, h['charset']) if code <= last else ' '
        known = char in G or bool(h['pix_width']) and cell_glyph(char, width, height) is not None
        coverage.append({'code': code, 'unicode': ord(char) if char else None,
                         'status': 'drawn' if known else 'fallback'})
        rows = glyph(char, width, height, bool(h['pix_width']))
        offsets.append(bitstart + len(bits))
        for column in range((width + 7) // 8):
            for row in rows:
                bits.append(sum((row[x] << (7 - x % 8))
                                for x in range(column * 8, min(width, column * 8 + 8))))
    # dfWidthBytes describes the combined padded byte-column bitmap.
    # Use an even stride per the SDK; original fixtures used odd strides.
    widthbytes = len(bits) // height
    widthbytes += widthbytes % 2
    bits.extend(bytes(widthbytes * height - len(bits)))
    facebytes = (face or h['face']).encode('ascii') + b'\0'
    faceoff = bitstart + len(bits)
    header = bytearray(118)
    struct.pack_into('<HI', header, 0, 0x200, faceoff + len(facebytes))
    copy = b'XT Pixels (c) 2026 Windows XT contributors; MIT'
    header[6:6 + len(copy)] = copy
    for at, key in ((66, 'type'), (68, 'points'), (70, 'vert_res'),
                    (72, 'horiz_res'), (74, 'ascent'), (76, 'internal'),
                    (78, 'external'), (83, 'weight'), (86, 'pix_width'),
                    (88, 'height'), (91, 'avg_width'), (93, 'max_width')):
        struct.pack_into('<H', header, at, h[key])
    for at, key in ((80, 'italic'), (81, 'underline'), (82, 'strikeout'),
                    (85, 'charset'), (90, 'pitch_family'), (95, 'first'),
                    (96, 'last'), (97, 'default'), (98, 'break')):
        header[at] = h[key]
    struct.pack_into('<H', header, 99, widthbytes)
    struct.pack_into('<I', header, 105, faceoff)
    struct.pack_into('<I', header, 113, bitstart)
    table = b''.join(struct.pack('<HH', w, o) for w, o in zip(widths, offsets))
    return bytes(header) + table + bytes(bitstart - 118 - len(table)) + bits + facebytes, coverage[:-1]


def pascal(text, ordinal=0):
    raw = text.encode('ascii')
    return bytes([len(raw)]) + raw + struct.pack('<H', ordinal)


def fon(font, module, rid, description='XT Pixels original bitmap font'):
    # FONTDIR contains the common 109-byte prefix, four reserved zero bytes,
    # device name, face name. Offsets there are not live FNT pointers.
    prefix = bytearray(font[:109])
    # Retain the FNT-relative face offset used by the inspected FONTDIR.
    # Host GDI tolerated zero; this revised Win16 container is unqualified.
    faceoff = struct.unpack_from('<I', font, 105)[0]
    face = font[faceoff:font.index(0, faceoff) + 1]
    directory = struct.pack('<HH', 1, rid) + prefix + bytes(4) + b'\0' + face
    # Win16 name-table alias: numeric FONTDIR 1 is discoverable as FONTDIR.
    nametable = struct.pack('<HHH', 15, 7, 0x8001) + b'\0FONTDIR\0' + b'\0\0'
    payloads = [(0x8007, 0x8001, 0x0c50, directory),
                (0x8008, rid | 0x8000, 0x1c30, font),
                (0x800f, 0x8001, 0x1c30, nametable)]
    neoff = 1024
    # The resource table is the first NE table, followed by names and entries.
    restable_size = 2 + sum(8 + 12 for _ in payloads) + 2
    resident = pascal(module) + b'\0'
    nonresident = pascal(description) + b'\0'
    resoff = 64
    residentoff = resoff + restable_size
    entryoff = residentoff + len(resident)
    # No imported modules/names: both tables must point to an empty byte.
    # Reuse the empty entry table, as the verified Win3 containers do.
    # Pointing past it accidentally exposed the nonresident description as
    # an import-name string. Modern GDI tolerated that; Win16 is unqualified.
    importoff = entryoff
    nonresidentoff = neoff + entryoff + 2
    datastart = (nonresidentoff + len(nonresident) + 15) & ~15
    table = bytearray(struct.pack('<H', 4))
    data = bytearray()
    for typ, ident, flags, raw in payloads:
        off = datastart + len(data)
        size = (len(raw) + 15) & ~15
        table.extend(struct.pack('<HHI', typ, 1, 0))
        table.extend(struct.pack('<HHHHHH', off >> 4, size >> 4,
                                 flags, ident, 0, 0))
        data.extend(raw + bytes(size - len(raw)))
    table.extend(b'\0\0')
    ne = bytearray(64)
    ne[:4] = b'NE\x05\x01'
    struct.pack_into('<HH', ne, 4, entryoff, 2)
    struct.pack_into('<H', ne, 12, 0x8300)
    struct.pack_into('<H', ne, 32, len(nonresident))
    struct.pack_into('<HHHHH', ne, 34, resoff, resoff,
                     residentoff, importoff, importoff)
    struct.pack_into('<I', ne, 44, nonresidentoff)
    struct.pack_into('<H', ne, 50, 4)
    ne[54] = 2  # Windows
    struct.pack_into('<H', ne, 62, 0x300)
    mz = bytearray(neoff)
    mz[:2] = b'MZ'
    # MZ size declares the authored DOS stub, not the full appended font
    # image. The private inputs use a different historical DOS stub.
    struct.pack_into('<HHHHHH', mz, 2, neoff % 512, (neoff + 511) // 512,
                     0, 4, 0, 0xffff)
    struct.pack_into('<H', mz, 16, 0x100)
    struct.pack_into('<H', mz, 24, 0x40)
    struct.pack_into('<I', mz, 60, neoff)
    # Original five-byte DOS stub: MOV AX,4C01h; INT 21h. No copied stub.
    mz[64:69] = b'\xb8\x01\x4c\xcd\x21'
    prefix = bytes(mz) + bytes(ne) + table + resident + b'\0\0'
    assert len(prefix) == nonresidentoff
    prefix += nonresident
    return prefix + bytes(datastart - len(prefix)) + data


def read_glyph(data, code):
    from INSPECT import fontinfo, word
    info = fontinfo(data)
    if not info['first'] <= code <= info['last']:
        code = info['first'] + info['default']
    width, off = struct.unpack_from('<HH', data, 118 + (code - info['first']) * 4)
    return [[(data[off + x // 8 * info['height'] + y] >> (7 - x % 8)) & 1
             for x in range(width)] for y in range(info['height'])]


def specimen(font, path, width, height=200):
    from PIL import Image, ImageDraw
    image = Image.new('RGB', (width, height), '#c0c0c0')
    draw = ImageDraw.Draw(image)
    lines = ['XT Pixels - HOST RENDER', 'File  Edit  View  Help',
             'Open a document', 'C:\\WINXT\\README.TXT',
             'Aa Bb Cc Dd Ee Ff Gg', 'Hh Ii Jj Kk Ll Mm Nn',
             'Oo Pp Qq Rr Ss Tt Uu', 'Vv Ww Xx Yy Zz 0123',
             'Il1 O0 rn m; :., !?', 'Save changes?', '[ OK ]  [ Cancel ]']
    y = 4
    fh = struct.unpack_from('<H', font, 88)[0]
    for index, line in enumerate(lines):
        if y + fh >= height:
            break
        x = 4
        if index == 0:
            draw.rectangle((0, y - 2, width - 1, y + fh + 1), fill='#000080')
        for char in line:
            rows = read_glyph(font, ord(char))
            if x + len(rows[0]) > width - 4:
                # Explicit host clipping, not reflowing a Win3 dialog claim.
                draw.line((width - 2, y, width - 2, y + fh - 1), fill='#ff0000')
                break
            for gy, row in enumerate(rows):
                for gx, ink in enumerate(row):
                    if ink:
                        image.putpixel((x + gx, y + gy), (255, 255, 255) if index == 0 else (0, 0, 0))
            x += len(rows[0])
        y += fh + 7
    image.save(path)


def atlas(font, path):
    from PIL import Image
    first, last, height = font[95], font[96], struct.unpack_from('<H', font, 88)[0]
    # 16 columns of separated glyph cells, not a Windows screenshot.
    image = Image.new('RGB', (320, ((last - first + 16) // 16) * (height + 4)), 'white')
    for code in range(first, last + 1):
        x, y = (code - first) % 16 * 20 + 2, (code - first) // 16 * (height + 4) + 2
        for gy, row in enumerate(read_glyph(font, code)):
            for gx, ink in enumerate(row):
                if ink:
                    image.putpixel((x + gx, y + gy), (0, 0, 0))
    image.save(path)


def build(out):
    if out.exists():
        raise ValueError('Output exists; choose a fresh directory')
    out.mkdir(parents=True)
    contracts = json.loads((HERE / 'CONTRACT.JSON').read_text('ascii'))
    report = {'schema': 1, 'native_qualified': False, 'fonts': {}}
    for item in contracts:
        resource = next(r for r in item['resources'] if r['type'] == 0x8008)
        font, coverage = fnt(resource['font'])
        name = item['filename']
        binary = fon(font, item['module'], resource['id'])
        (out / name).write_bytes(binary)
        (out / name.replace('.FON', '.FNT')).write_bytes(font)
        atlas(font, out / name.replace('.FON', '.PNG'))
        report['fonts'][name] = {'size': len(binary), 'sha256': hashlib.sha256(binary).hexdigest(),
                                 'coverage': coverage}
    fixed = next(item for item in contracts if item['filename'] == 'CGAFIX.FON')
    resource = next(r for r in fixed['resources'] if r['type'] == 0x8008)
    font, _ = fnt(resource['font'])
    (out / 'TXTSYS.FON').write_bytes(fon(font, 'FONTS', 27))
    for name in ('CGASYS', 'EGASYS'):
        for width in (160, 320, 640):
            specimen((out / (name + '.FNT')).read_bytes(),
                     out / ('S%d%s.PNG' % (width, 'CGA' if name == 'CGASYS' else 'EGA')), width)
    auditfont, _ = fnt(next(r['font'] for item in contracts if item['filename'] == 'CGASYS.FON'
                           for r in item['resources'] if 'font' in r), 'XT Pixels UI')
    (out / 'XTAUDIT.FON').write_bytes(fon(auditfont, 'XTAUDIT', 27))
    textfile(out / 'BUILD.JSON', json.dumps(report, indent=2) + '\n')
    missing = {name: [c for c in row['coverage'] if c['status'] != 'drawn']
               for name, row in report['fonts'].items()}
    textfile(out / 'MISSING.JSON', json.dumps(missing, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    report = build(args.out)
    for name, entry in report['fonts'].items():
        print(name, entry['size'], entry['sha256'])
