#!/usr/bin/env python3
"""Read-only art/UI checks; Pillow is a modern-host dependency, never runtime.

Run with --require-runtime after all three fresh emulator runs. Missing VRAM
captures are explicitly skipped by default. This script never runs an emulator
or modifies sources, assets, evidence, or a user's Windows installation.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import re
import sys
import textwrap

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
PALETTE = [(0, 0, 0), (0, 0, 170), (0, 170, 0), (0, 170, 170),
           (170, 0, 0), (170, 0, 170), (170, 85, 0), (170, 170, 170),
           (85, 85, 85), (85, 85, 255), (85, 255, 85), (85, 255, 255),
           (255, 85, 85), (255, 85, 255), (255, 255, 85), (255, 255, 255)]
# Independently recorded hashes of the two supplied original sheets.
SOURCE_HASHES = {
    'CABINET.PNG': '960fb2033e3aeaa7c0d550e228e8fcf69cdad6dace8a13571a9b5f068bf5251b',
    'PARTS.PNG': '6ae9d955e6feaf6bd0585e82fd7ed5cda6b743b929913fede5ac0cb951ebbcb1',
}
MODES = {'320x200x16': (320, 16, 4, 160),
         '640x200x2': (640, 2, 2, 80),
         '640x200x4': (640, 4, 4, 160)}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def match(pattern, source):
    result = re.search(pattern, source, re.S)
    require(result is not None, 'Source invariant not found: ' + pattern)
    return result


def c_array(source, name, length):
    found = match(r'\b' + name + r'\[\s*(\d+)\s*\]\s*=\s*\{([^}]+)\}', source)
    require(int(found[1]) == length, name + ' has unexpected declared length')
    require(re.fullmatch(r'[\d,\s]+', found[2]) is not None,
            name + ' no longer contains a plain integer initializer')
    values = [int(value) for value in re.findall(r'\d+', found[2])]
    require(len(values) == length, name + ' initializer length mismatch')
    return values


def read_image(path):
    with Image.open(path) as image:
        return image.convert('RGB')


def check_sources(manifest):
    require(manifest['source_sha256'] == SOURCE_HASHES,
            'Manifest does not identify the independently recorded original art')
    for name, expected in SOURCE_HASHES.items():
        actual = hashlib.sha256((ROOT / 'art' / name).read_bytes()).hexdigest()
        require(actual == expected, name + ' does not match its original hash')
    return {'original_sheets': len(SOURCE_HASHES), 'hashes': SOURCE_HASHES}


def check_crops(manifest, atlas):
    require(list(atlas.size) == manifest['atlas_size'], 'Atlas dimensions changed')
    reconstructed = Image.new('RGB', atlas.size, (0, 0, 0))
    occupied = set()
    for crop in manifest['crops']:
        source = read_image(ROOT / 'art' / crop['source'])
        left, top, right, bottom = crop['source_rectangle']
        x, y = crop['atlas_xy']
        require(0 <= left < right <= source.width and
                0 <= top < bottom <= source.height, 'Invalid source crop: ' + crop['name'])
        width, height = right - left, bottom - top
        require(0 <= x and x + width <= atlas.width and
                0 <= y and y + height <= atlas.height, 'Crop leaves atlas: ' + crop['name'])
        rectangle = set(itertools.product(range(x, x + width), range(y, y + height)))
        require(not (occupied & rectangle), 'Overlapping manifest crop: ' + crop['name'])
        occupied.update(rectangle)
        expected = source.crop((left, top, right, bottom))
        actual = atlas.crop((x, y, x + width, y + height))
        require(actual.tobytes() == expected.tobytes(), 'Non-native pixels in ' + crop['name'])
        reconstructed.paste(expected, (x, y))
    require(reconstructed.tobytes() == atlas.tobytes(),
            'Atlas contains altered crop pixels or non-black unmanifested padding')
    allowed = set(PALETTE)
    require(all(pixel in allowed for pixel in zip(*[iter(atlas.tobytes())] * 3)),
            'Atlas contains colors outside the exact native RGBI palette')
    return {'pixel_exact_crops': len(manifest['crops']), 'atlas_size': list(atlas.size)}


def check_packed_atlas(manifest, atlas):
    source = (ROOT / 'src' / 'ART.H').read_text()
    width = int(match(r'#define\s+ART_W\s+(\d+)', source)[1])
    height = int(match(r'#define\s+ART_H\s+(\d+)', source)[1])
    require((width, height) == atlas.size, 'ART.H dimensions differ from ATLAS.PNG')
    stride = ((width * 4 + 31) // 32) * 4
    bits = c_array(source, 'artbits', stride * height)
    require(all(0 <= value <= 255 for value in bits), 'DIB initializer is not byte-valued')
    require(len(bits) == manifest['dib_bytes'], 'Manifest DIB size mismatch')
    decoded = bytearray()
    for y in range(height):
        for x in range(width):
            value = bits[(height - 1 - y) * stride + x // 2]
            index = value >> 4 if not x % 2 else value & 15
            decoded.extend(PALETTE[index])
    require(bytes(decoded) == atlas.tobytes(), 'Bottom-up 4bpp DIB differs from atlas')
    return {'decoded_bytes': len(bits), 'row_stride': stride, 'pixel_exact': True}


def check_ticket(source):
    compact = re.sub(r'\s+', '', source)
    left = int(match(r'panelleft\(void\)\{return(\d+)\*sx;\}', compact)[1])
    inset = int(match(r'r\.left=left\+(\d+)\*sx;', compact)[1])
    right = int(match(r'r\.right=screenw-(\d+)\*sx;', compact)[1])
    top = int(match(r'r\.top=y\+(\d+);', compact)[1])
    bottom = int(match(r'r\.bottom=y\+h-(\d+);', compact)[1])
    require('GetStockObject(SYSTEM_FIXED_FONT)' in compact, 'Fixed-font UI assumption changed')
    # CGAFIX.FON's fixed font is 8x8 in the qualified Windows test profile.
    columns = (320 - right - left - inset) // 8
    require(columns >= 26, '320-mode ticket cannot fit the compiler\'s 26-column words')
    heights = {field: int(match(r'ticket\(dc,' + field + r',\d+,(\d+)\)', compact)[1])
               for field in ('question', 'name')}
    rows = {field: (height - top - bottom) // 8 for field, height in heights.items()}
    data = json.loads((ROOT / 'data' / 'STARTER.JSON').read_text())
    counts = {}
    for field, items, key in [('question', data['questions'], 'text'),
                              ('name', data['characters'], 'name')]:
        most = 0
        for item in items:
            value = item[key]
            lines = textwrap.wrap(value, width=columns, break_long_words=False,
                                  break_on_hyphens=False)
            require(all(len(line) <= columns for line in lines),
                    field + ' clips horizontally: ' + value)
            require(len(lines) <= rows[field], field + ' clips vertically: ' + value)
            most = max(most, len(lines))
        counts[field] = {'strings': len(items), 'max_lines': most, 'available_rows': rows[field]}
    # Keep the compiler's accepted exact-limit fixture representable as well.
    limit_question = 'Q' * 25 + ' ' + 'R' * 26 + ' ' + 'S' * 26
    require(len(textwrap.wrap(limit_question, width=columns)) <= rows['question'],
            'Maximum supported question fixture does not fit')
    return {'narrowest_columns': columns, 'font_assumption': 'qualified CGAFIX 8x8',
            'content': counts}


def check_pupils(source, atlas):
    body = match(r'static void eyes\(HDC dc\)\{(.*?)\n\}', source)[1]
    compact = re.sub(r'\s+', '', body)
    patches = [tuple(map(int, row)) for row in re.findall(
        r'box\(dc,x\+(\d+)\*sx,y\+(\d+),(\d+)\*sx,(\d+),RGB\(255,255,255\)\)', compact)]
    pupils = [tuple(map(int, row)) for row in re.findall(
        r'sprite\(dc,x\+\((\d+)\+lookx\)\*sx,y\+(\d+)\+looky,(\d+),(\d+),(\d+),(\d+)\)', compact)]
    require(len(patches) == len(pupils) == 2, 'Expected exactly two native pupil patches')
    look = re.sub(r'\s+', '', match(r'static void look\(int x,int y\)\{(.*?)\n\}', source)[1])
    for axis in ('nx', 'ny'):
        require('if(' + axis + '>1)' + axis + '=1;' in look and
                'if(' + axis + '<-1)' + axis + '=-1;' in look,
                'Nine-position pupil clamp changed for ' + axis)
    native = atlas.crop((0, 0, 96, 120))
    placements = 0
    for dx, dy in itertools.product((-1, 0, 1), repeat=2):
        redraw = native.copy()
        for (px, py, pw, ph), (x, y, width, height, ax, ay) in zip(patches, pupils):
            for sx in (1, 2):
                require(px * sx <= (x + dx) * sx and
                        (x + dx + width) * sx <= (px + pw) * sx and
                        py <= y + dy and y + dy + height <= py + ph,
                        'Pupil leaves native white patch at ' + repr((dx, dy, sx)))
            require(0 <= ax < ax + width <= atlas.width and
                    0 <= ay < ay + height <= atlas.height, 'Pupil source leaves atlas')
            redraw.paste((255, 255, 255), (px, py, px + pw, py + ph))
            redraw.paste(atlas.crop((ax, ay, ax + width, ay + height)), (x + dx, y + dy))
        if dx == dy == 0:
            require(redraw.tobytes() == native.tobytes(),
                    'Centered eyes erase or alter original native pupil/shadow pixels')
        for y in range(native.height):
            for x in range(native.width):
                if native.getpixel((x, y)) != redraw.getpixel((x, y)):
                    require(any(px <= x < px + pw and py <= y < py + ph
                                for px, py, pw, ph in patches), 'Eye changes leave bounded patches')
        placements += 1
    return {'native_positions': placements, 'horizontal_scales': [1, 2],
            'centered_pixels_exact': True, 'patches': patches}


def decode_vram(raw, mode):
    require(len(raw) == 32768, 'Expected the full 32KB B800 video-memory capture')
    width, colors, banks, pitch = MODES[mode]
    frame = bytearray(width * 200)
    for y in range(200):
        base = y % banks * 8192 + y // banks * pitch
        for x in range(width):
            if colors == 16:
                value = raw[base + x // 2]
                value = value >> 4 if not x % 2 else value & 15
            elif colors == 2:
                value = (raw[base + x // 8] >> (7 - x % 8)) & 1
            else:
                address = base + 2 * (x // 8)
                value = ((raw[address] >> (7 - x % 8)) & 1) | (
                    ((raw[address + 1] >> (7 - x % 8)) & 1) << 1)
            frame[y * width + x] = value
    return frame


def check_runtime(mode, source, atlas):
    directory = ROOT / 'evidence' / ('art-' + mode)
    frame = decode_vram((directory / 'guest' / 'NATIVE.BIN').read_bytes(), mode)
    width, colors, _, _ = MODES[mode]
    sx = 1 if width == 320 else 2
    if colors == 16:
        mapping = list(range(16))
    else:
        name = 'monomap' if colors == 2 else 'lowmap'
        logical = c_array(source, name, 16)
        # Qualified TNDY6404 hardware palette: 0 black, 1 light red,
        # 2 light green, 3 white. It is not the CGA cyan/magenta palette.
        hardware = {0: 0, 15: 1} if colors == 2 else {0: 0, 12: 1, 10: 2, 15: 3}
        require(set(logical) <= set(hardware), 'Unexpected logical entries in ' + name)
        mapping = [hardware[value] for value in logical]
    mismatches = []
    total = 0
    for y in range(120):
        for x in range(96):
            expected = mapping[PALETTE.index(atlas.getpixel((x, y)))]
            for duplicate in range(sx):
                screenx, screeny = (6 + x) * sx + duplicate, 43 + y
                actual = frame[screeny * width + screenx]
                if actual != expected:
                    total += 1
                    if len(mismatches) < 8:
                        mismatches.append({'xy': [screenx, screeny], 'actual': actual,
                                           'expected': expected})
    require(not total, '%s cabinet mismatches: %d; first: %s' %
            (mode, total, json.dumps(mismatches)))
    report_path = directory / 'RESULT.JSON'
    bound_to_exe = False
    if report_path.exists():
        report = json.loads(report_path.read_text())
        current = hashlib.sha256((ROOT / 'src' / 'TANDI.EXE').read_bytes()).hexdigest()
        require(report['exe_sha256'] == current, mode + ' capture belongs to an older EXE')
        bound_to_exe = True
    return {'compared_pixels': 96 * sx * 120, 'exact_hardware_indices': True,
            'x_scale': sx, 'result_matches_current_exe': bound_to_exe,
            'hardware_palette': 'black/red/green/white' if colors == 4 else str(colors) + ' colors'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--require-runtime', action='store_true',
                        help='Fail rather than skip if any NATIVE.BIN capture is missing')
    args = parser.parse_args()
    results = []
    manifest = json.loads((ROOT / 'art' / 'MANIFEST.JSON').read_text())
    atlas = read_image(ROOT / 'art' / 'ATLAS.PNG')
    source = (ROOT / 'src' / 'TANDI.C').read_text()

    def test(name, callback):
        try:
            results.append({'name': name, 'status': 'passed', 'detail': callback()})
        except Exception as error:
            results.append({'name': name, 'status': 'FAILED', 'error': str(error)})

    test('immutable original source hashes', lambda: check_sources(manifest))
    test('all native crops and black padding', lambda: check_crops(manifest, atlas))
    test('generated DIB decodes to exact atlas', lambda: check_packed_atlas(manifest, atlas))
    test('26-column starter questions and names fit', lambda: check_ticket(source))
    test('nine bounded native pupil positions', lambda: check_pupils(source, atlas))
    for mode in MODES:
        capture = ROOT / 'evidence' / ('art-' + mode) / 'guest' / 'NATIVE.BIN'
        name = 'native framebuffer fidelity ' + mode
        if not capture.exists() and not args.require_runtime:
            results.append({'name': name, 'status': 'skipped', 'reason': 'NATIVE.BIN not present'})
        else:
            test(name, lambda mode=mode: check_runtime(mode, source, atlas))
    report = {'passed': sum(row['status'] == 'passed' for row in results),
              'failed': sum(row['status'] == 'FAILED' for row in results),
              'skipped': sum(row['status'] == 'skipped' for row in results),
              'tests': results}
    print(json.dumps(report, indent=2))
    return bool(report['failed'])


if __name__ == '__main__':
    sys.exit(main())
