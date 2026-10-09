"""Verify saved genuine framebuffer pixels/metrics; launches no emulator."""
import argparse
import json
import struct
from pathlib import Path
from PIL import Image
from BUILD import read_glyph, textfile

HERE = Path(__file__).resolve().parent


def pattern(font, codes):
    glyphs = [read_glyph(font, code) for code in codes]
    return [bytes(v for glyph in glyphs for v in glyph[y])
            for y in range(struct.unpack_from('<H', font, 88)[0])]


def exact(image, rows, x, y):
    width, height, pixels = image
    return (x >= 0 and y >= 0 and x + len(rows[0]) <= width and
            y + len(rows) <= height and all(
                pixels[(y + dy) * width + x:(y + dy) * width + x + len(row)] == row
                for dy, row in enumerate(rows)))


def metrics(text):
    rows, current = {}, None
    for line in text.splitlines():
        key, _, value = line.partition('=')
        if key == 'STOCK':
            current = {}
            rows[int(value)] = current
        elif current is not None and key in ('HEIGHT', 'ASCENT', 'INTERNAL', 'EXTERNAL',
                'AVERAGE', 'MAXIMUM', 'FIRST', 'LAST', 'DEFAULT', 'CHARSET'):
            current[key] = int(value)
    return rows


def main(args):
    inputs = json.loads((args.native / 'INPUTS.JSON').read_text())
    contracts = {item['filename']: next(r['font'] for r in item['resources'] if 'font' in r)
                 for item in json.loads((HERE / 'CONTRACT.JSON').read_text())}
    report = {'kind': 'Saved genuine Win3 framebuffer/stock metrics verification',
              'native_ui_slice_passed': True, 'native_package_qualified': False,
              'full_native_encoding_pixels_qualified': False,
              'system_fixed_native_pixels_qualified': False,
              'oem_out_of_range_native_behavior_qualified': False,
              'txtsys_native_renderer_qualified': False, 'modes': {}}
    keymap = {'HEIGHT': 'height', 'ASCENT': 'ascent', 'INTERNAL': 'internal',
              'EXTERNAL': 'external', 'AVERAGE': 'avg_width', 'MAXIMUM': 'max_width',
              'FIRST': 'first', 'LAST': 'last', 'CHARSET': 'charset'}
    for mode, entry in inputs['modes'].items():
        folder = args.native / mode
        log = (folder / 'FONT.LOG').read_text()
        if 'DONE=1' not in log:
            raise ValueError('Native probe incomplete: ' + mode)
        found = metrics(log)
        for stock, family in ((13, 'SYS'), (16, 'FIX'), (10, 'OEM')):
            contract = contracts[entry['family'] + family + '.FON']
            for key, field in keymap.items():
                if found[stock][key] != contract[field]:
                    raise ValueError('Native metric changed: %s %d %s' % (mode, stock, key))
            if found[stock]['DEFAULT'] != contract['first'] + contract['default']:
                raise ValueError('Native default metric changed: ' + mode)
        advances = list(struct.unpack('<224H', (folder / 'GUEST/WIDTHS.BIN').read_bytes()))
        if advances != contracts[entry['family'] + 'SYS.FON']['widths']:
            raise ValueError('Native advances changed: ' + mode)
        im = Image.open(folder / 'NORMAL.PNG').convert('RGB')
        image = (*im.size, bytes(int(c == (0, 0, 0)) for c in im.getdata()))
        system = (args.fonts / (entry['family'] + 'SYS.FNT')).read_bytes()
        oem = (args.fonts / (entry['family'] + 'OEM.FNT')).read_bytes()
        first = pattern(system, b'XT Pixels / Win3')
        anchors = [(x, y) for y in range(30, 90) for x in range(2, 15)
                   if exact(image, first, x, y)]
        if len(anchors) != 1:
            raise ValueError('Native glyph anchor not unique: ' + mode + str(anchors))
        x, y = anchors[0]
        cases = [(system, b'XT Pixels / Win3', 0),
                 (system, b'File Edit View Help', 16),
                 (system, b'Il1 O0 rn m ; !?', 32),
                 (system, bytes([0x7f, 0x80, 0x81, 0xff]), 48)]
        cases += [(oem, bytes(range(176 + row * 16, 192 + row * 16)), 68 + row * 10)
                  for row in range(4)]
        for font, codes, dy in cases:
            if not exact(image, pattern(font, codes), x, y + dy):
                raise ValueError('Native emitted-glyph pixels differ: %s at %d' % (mode, dy))
        values = {key: int(value) for key, value in (l.split('=', 1)
                  for l in log.splitlines() if '=' in l) if key in
                  ('DIALOG_LEFT', 'DIALOG_RIGHT', 'DIALOG_BOTTOM', 'DIALOG_SCREEN_OVERFLOW',
                   'CANCEL_TEXT_WIDTH', 'CANCEL_CLIENT_WIDTH', 'DIALOG_BASE')}
        if values['CANCEL_TEXT_WIDTH'] > values['CANCEL_CLIENT_WIDTH']:
            raise ValueError('Cancel label exceeds its logical control: ' + mode)
        report['modes'][mode] = {'stock_metrics': found, 'all_system_advances_preserved': True,
            'pixel_anchor': [x, y], 'exact_native_system_runs': 4,
            'exact_native_oem_codes': 'B0..EF (64 codes)',
            'direct_ansi_reserved_codes_tested': ['7F', '80', '81'],
            'native_capture_size': list(im.size), 'dialog': values,
            'native_image_visual_review_required': True}
    textfile(args.native / 'QUALIFY.JSON', json.dumps(report, indent=2) + '\n')
    print('PASS: five graphics profiles; stock metrics, all System advances,')
    print('normal System/ANSI fallback runs and 64 OEM glyphs match emitted originals.')
    print('Installer/full encoding/fixed rendering/text renderer remain separate gates.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--fonts', type=Path, required=True)
    main(parser.parse_args())
