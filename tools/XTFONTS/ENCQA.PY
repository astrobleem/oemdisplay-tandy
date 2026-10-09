"""Validate saved original-font complete-byte pages; no emulator launch.

Never run on a privately owned Microsoft font atlas. Baseline UI geometry
comparison uses FONTPRB's menus/dialog only, separately from this tool.
"""
import argparse
import hashlib
import json
import struct
from pathlib import Path
from PIL import Image
from BUILD import read_glyph, textfile
from INSPECT import resources, fontinfo, dword
from NATIVEQA import metrics


def decode(raw, width, bios, area):
    if len(raw) != 32768:
        raise ValueError('Short framebuffer')
    pixels = []; colors = []
    for y in range(200):
        for x in range(width):
            if bios == 6:
                at = y % 2 * 8192 + y // 2 * 80 + x // 8
                color = raw[at] >> (7 - x % 8) & 1
            elif bios == 9:
                at = y % 4 * 8192 + y // 4 * 160 + x // 2
                color = raw[at] >> ((1 - x % 2) * 4) & 15
            else:
                raise ValueError('Full glyph proof currently uses BIOS 6/9 only')
            if area[0] <= x < area[0]+128 and area[1] <= y < area[1]+128 and color not in ((0, 1) if bios == 6 else (0, 15)):
                raise ValueError('Unexpected color in monochrome glyph page')
            pixels.append(int(color == 0)); colors.append(color if bios == 9 else color * 15)
    return bytes(pixels), colors


def emitted(fonts, name):
    data = (fonts / name).read_bytes()
    _, entries = resources(data)
    off = next(off for kind, rid, flags, off, size in entries if kind == 0x8008)
    return data[off:off + dword(data, off + 2)]


def validate(folder, fonts, family, bios, width):
    log = (folder / 'FONENC.LOG').read_text()
    if 'DONE=1' not in log or log.count('WIDTH_QUERY=1') != 3:
        raise ValueError('Incomplete native complete-byte probe')
    fields = dict(line.split('=', 1) for line in log.splitlines() if '=' in line)
    if int(fields['SCREEN_WIDTH']) != width or int(fields['SCREEN_HEIGHT']) != 200:
        raise ValueError('Unexpected screen geometry')
    x, y = int(fields['CLIENT_X']) + 2, int(fields['CLIENT_Y']) + 2
    if int(fields['CLIENT_WIDTH']) < 128 or int(fields['CLIENT_HEIGHT']) < 128:
        raise ValueError('Atlas would clip')
    found = metrics(log)
    report = {'kind': 'Genuine native complete-byte rendering', 'family': family,
              'native_glyph_pages_verified': True, 'pixel_origin': [x, y], 'fonts': {}}
    mapping = {'HEIGHT': 'height', 'ASCENT': 'ascent', 'INTERNAL': 'internal',
               'EXTERNAL': 'external', 'AVERAGE': 'avg_width', 'MAXIMUM': 'max_width',
               'FIRST': 'first', 'LAST': 'last', 'CHARSET': 'charset'}
    for initial, stock, suffix in (('S', 13, 'SYS'), ('F', 16, 'FIX'), ('O', 10, 'OEM')):
        name = 'TXTSYS.FON' if family == 'TXT' and suffix == 'SYS' else (
            ('CGA' if family == 'TXT' else family) + suffix + '.FON')
        rawfont = emitted(fonts, name)
        info = fontinfo(rawfont)
        for key, field in mapping.items():
            if found[stock][key] != info[field]:
                raise ValueError('Native stock metric mismatch: ' + name + ' ' + key)
        default = info['first'] + info['default']
        if found[stock]['DEFAULT'] != default:
            raise ValueError('Wrong native default character: ' + name)
        wanted = [info['widths'][(code if info['first'] <= code <= info['last'] else default) - info['first']]
                  for code in range(256)]
        widths = list(struct.unpack('<256H', (folder / (initial + 'WIDTH.BIN')).read_bytes()))
        if widths[info['first']:info['last'] + 1] != wanted[info['first']:info['last'] + 1]:
            raise ValueError('Native in-range advances differ: ' + name)
        captures = {}
        outside_differences = []
        for page in range(4):
            path = folder / (initial + str(page) + '.BIN')
            raw = path.read_bytes()
            bits, colors = decode(raw, width, bios, (x, y))
            for slot in range(64):
                code = page * 64 + slot
                glyph = read_glyph(rawfont, code)
                gx, gy = x + slot % 8 * 16, y + slot // 8 * 16
                different = 0
                for dy in range(16):
                    for dx in range(16):
                        expected = glyph[dy][dx] if dy < len(glyph) and dx < len(glyph[0]) else 0
                        if bits[(gy + dy) * width + gx + dx] != expected:
                            different += 1
                if different:
                    if info['first'] <= code <= info['last']:
                        raise ValueError('Native in-range glyph pixel mismatch %s %02X: %d pixels' % (name, code, different))
                    outside_differences.append({'code': code, 'pixels_different_from_fnt_default': different})
            image = Image.new('RGB', (width, 200))
            palette = [(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
            image.putdata([palette[color] for color in colors])
            image.save(folder / (initial + str(page) + '.PNG'))
            captures[path.name] = hashlib.sha256(raw).hexdigest()
        report['fonts'][name] = {'all_256_bytes_exact': not outside_differences,
            'all_in_range_pixels_and_advances_exact': True, 'in_range': [info['first'], info['last']],
            'out_of_range_default': default, 'font_sha256': hashlib.sha256((fonts / name).read_bytes()).hexdigest(),
            'outside_range_width_observations': {str(code): widths[code] for code in range(256)
                                                if not info['first'] <= code <= info['last']},
            'outside_range_pixel_differences': outside_differences, 'capture_sha256': captures}
    textfile(folder / 'ENCQA.JSON', json.dumps(report, indent=2) + '\n')
    print('PASS', family, ': stock SYS/FIX/OEM metrics and every in-range glyph; out-of-range observations recorded')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--guest', type=Path, required=True)
    parser.add_argument('--fonts', type=Path, required=True)
    parser.add_argument('--family', choices=('CGA', 'EGA', 'TXT'), required=True)
    args = parser.parse_args()
    validate(args.guest, args.fonts, args.family, 9 if args.family == 'EGA' else 6,
             320 if args.family == 'EGA' else 640)
