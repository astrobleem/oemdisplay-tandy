#!/usr/bin/env python3
"""Independent cursor-only checks for reconstructed Yamaha MODETEST cases120..124.
Print JSON to stdout only. Preserve MODECHK's independent87 noncursor checks.
Example: python YAMCUROR.PY GUEST --driver YAM160.DRV
Use --resource-source current for a diagnostic with the actual driver's artwork;
resource-identity failure still fails the accepted cursor contract.
Default capture model is the verified86Box fixture: two mirrored views of one16KB aperture.
Nonuniform compression blocks fail closed: the loader's shrink rule is unknown.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
ACCEPTED = ROOT / 'accepted-regression-inputs-20261105/YAM160.DRV'
ACCEPTED_SHA = 'a3d339a3f1e831bd8499fb2b0a28c683bf08f9fbeb0e96689dc3f6ef9a627c8a'
W, H, RAW = 160, 200, 32768
IDS = tuple(range(120, 125))
REQUESTS = ((0, 0), (159, 199), (80, 100), (-20, -20), (180, 220))
ALL_IDS = [0, 1, 2] + list(range(10, 22)) + list(range(30, 36)) + list(range(40, 96)) + list(range(100, 109)) + [110] + list(IDS)


def require(ok, message):
    if not ok:
        raise ValueError(message)


def u16(b, at):
    return struct.unpack_from('<H', b, at)[0]


def ne_records(b):
    require(len(b) >= 64 and b[:2] == b'MZ', 'Not an MZ executable')
    n = struct.unpack_from('<I', b, 60)[0]
    require(b[n:n + 2] == b'NE', 'Not an NE executable')
    start, stop = n + u16(b, n + 36), n + u16(b, n + 38)
    require(start + 4 <= stop <= len(b), 'Invalid NE resource-table bounds')
    shift, at, result = u16(b, start), start + 2, {}
    require(shift <= 16, 'Invalid resource alignment')
    while True:
        require(at + 2 <= stop, 'Missing resource-table terminator')
        typ = u16(b, at)
        if not typ:
            break
        require(at + 8 <= stop and typ & 0x8000, 'Unsupported resource type')
        count = u16(b, at + 2)
        at += 8
        for unused in range(count):
            require(at + 12 <= stop, 'Truncated resource record')
            off, size, flags, ident, handle, usage = struct.unpack_from('<6H', b, at)
            at += 12
            require(ident & 0x8000, 'Unsupported string resource identifier')
            lo, hi = off << shift, (off + size) << shift
            require(lo < hi <= len(b), 'Resource outside executable')
            key = (typ & 0x7fff, ident & 0x7fff)
            require(key not in result, 'Duplicate resource identifier')
            result[key] = b[lo:hi]
    return result


def cursor_resources(driver, pinned=False):
    b = Path(driver).read_bytes()
    if pinned:
        require(hashlib.sha256(b).hexdigest() == ACCEPTED_SHA,
                'Accepted reference is not the recorded candidate03 YAM160.DRV')
    records = ne_records(b)
    config = records[0x7006, 1]
    require(len(config) >= 12, 'Truncated OEM configuration')
    compression = struct.unpack_from('<HH', config, 8)
    require(all(1 <= v <= 32 for v in compression), 'Invalid cursor compression')
    cursors = {}
    for (typ, ident), group in records.items():
        if typ != 12:
            continue
        require(len(group) >= 20 and struct.unpack_from('<HHH', group) == (0, 2, 1),
                'Only single-image monochrome cursor groups are supported')
        width, height, planes, bits, size, image_id = struct.unpack_from('<HHHHIH', group, 6)
        require(planes == bits == 1, 'Cursor group is not monochrome')
        payload = records[1, image_id]
        require(44 <= size <= len(payload), 'Invalid cursor payload size')
        payload = payload[:size]
        hot = struct.unpack_from('<HH', payload)
        dib = payload[4:]
        header, dw, dh, dp, db, encoding = struct.unpack_from('<IiiHHI', dib)
        require(header == 40 and dw == width and dh == height and dh > 0 and dh % 2 == 0,
                'Unsupported cursor DIB dimensions')
        require(dp == db == 1 and encoding == 0, 'Unsupported cursor DIB encoding')
        height //= 2
        stride = ((width + 31) // 32) * 4
        require(len(dib) == 48 + 2 * stride * height, 'Unexpected cursor plane length')
        require(dib[40:48] == bytes((0, 0, 0, 0, 255, 255, 255, 0)), 'Unexpected monochrome palette')
        require(0 <= hot[0] < width and 0 <= hot[1] < height, 'Invalid cursor hotspot')
        def plane(offset):
            return tuple(tuple((dib[offset + (height - 1 - y) * stride + x // 8] >> (7 - x % 8)) & 1
                               for x in range(width)) for y in range(height))
        cursors[ident] = {'width': width, 'height': height, 'hotspot': hot,
                         'and': plane(48 + stride * height), 'xor': plane(48),
                         'payload': payload, 'group': group[:20]}
    require(32512 in cursors, 'NORMAL OEM cursor group32512 missing')
    return compression, cursors


def identity(reference, observed):
    rc, rr = reference
    oc, oo = observed
    different = [n for n in sorted(set(rr) | set(oo))
                 if n not in rr or n not in oo or rr[n]['group'] != oo[n]['group'] or rr[n]['payload'] != oo[n]['payload']]
    return {'pass': rc == oc and not different, 'compression_equal': rc == oc,
            'changed_cursor_groups': different, 'accepted_group_count': len(rr), 'current_group_count': len(oo)}


def compress_cursor(resource, compression):
    hx, vy = compression
    w, h = resource['width'], resource['height']
    hotx, hoty = resource['hotspot']
    require(w % hx == h % vy == hotx % hx == hoty % vy == 0,
            'Nonintegral cursor dimensions/hotspot compression')
    out = {'width': w // hx, 'height': h // vy, 'hotspot': (hotx // hx, hoty // vy)}
    ambiguous = 0
    for kind in ('and', 'xor'):
        rows = []
        for y in range(h // vy):
            row = []
            for x in range(w // hx):
                block = {resource[kind][y * vy + yy][x * hx + xx] for yy in range(vy) for xx in range(hx)}
                ambiguous += len(block) != 1
                row.append(next(iter(block)))
            rows.append(tuple(row))
        out[kind] = tuple(rows)
    require(not ambiguous, '%d nonuniform AND/XOR compression blocks; loader shrink semantics unverified' % ambiguous)
    return out


def address(x, y):
    return (y & 1) * 8192 + (y // 2) * 80 + x // 2


USED = frozenset(address(x, y) for y in range(H) for x in range(W))
PADDING = tuple(i for i in range(16384) if i not in USED)
UNUSED = tuple(i for i in range(RAW) if i not in USED)
MIRROR_PADDING = PADDING + tuple(i + 16384 for i in PADDING)


def untouched_offsets(capture_model):
    require(capture_model in ('mirrored16k', 'independent32k'), 'Unknown capture model')
    return MIRROR_PADDING if capture_model == 'mirrored16k' else UNUSED


def pixels(raw):
    require(len(raw) == RAW, 'Capture must contain32768 bytes')
    return [(raw[address(x, y)] >> (0 if x & 1 else 4)) & 15 for y in range(H) for x in range(W)]


def grid():
    # Exact public MODETEST.strips(dc,1):16 columns,10 rows, (i+j*3)&15.
    return [(x // 10 + (y // 20) * 3) & 15 for y in range(H) for x in range(W)]


def visible_frame(before, cursor, cx, cy, capture_model='mirrored16k'):
    require(len(before) == RAW, 'Capture must contain32768 bytes')
    untouched_offsets(capture_model)
    if capture_model == 'mirrored16k':
        require(before[:16384] == before[16384:], 'Before capture violates16KB mirror contract')
    out = bytearray(before)
    ox, oy = cx - cursor['hotspot'][0], cy - cursor['hotspot'][1]
    for ly in range(cursor['height']):
        y = oy + ly
        if not 0 <= y < H:
            continue
        for lx in range(cursor['width']):
            x = ox + lx
            if not 0 <= x < W:
                continue
            at, shift = address(x, y), 0 if x & 1 else 4
            old = (out[at] >> shift) & 15
            value = (old & (15 if cursor['and'][ly][lx] else 0)) ^ (15 if cursor['xor'][ly][lx] else 0)
            out[at] = (out[at] & ~(15 << shift)) | (value << shift)
    if capture_model == 'mirrored16k':
        out[16384:] = out[:16384]
    return bytes(out)


def read_log(path):
    values, cases, active = {}, [], None
    for line in Path(path).read_text().splitlines():
        if '=' not in line:
            continue
        key, text = line.split('=', 1)
        number = int(text)
        values.setdefault(key, []).append(number)
        if key == 'CASE':
            require(active is None, 'Case began before previous ENDCASE')
            active = {}
            cases.append(active)
        if active is not None:
            active.setdefault(key, []).append(number)
            if key == 'ENDCASE':
                require(active['CASE'] == [number], 'Mismatched ENDCASE')
                active = None
    require(active is None, 'Unfinished case')
    return values, cases


def differences(a, b):
    require(len(a) == len(b), 'Different comparison lengths')
    changed = [i for i in range(len(a)) if a[i] != b[i]]
    return {'count': len(changed), 'first_offsets': changed[:16]}


def analyze(guest, driver, accepted, source='accepted', capture_model='mirrored16k'):
    untouched = untouched_offsets(capture_model)
    reference, observed = cursor_resources(accepted, True), cursor_resources(driver)
    identities = identity(reference, observed)
    selected = reference if source == 'accepted' else observed
    model, model_error = None, None
    try:
        model = compress_cursor(selected[1][32512], selected[0])
    except ValueError as exc:
        model_error = str(exc)
    values, all_cases = read_log(guest / 'MODETEST.LOG')
    checks = {}
    for key, wanted in [('VERSION', 2), ('PHASES', 15), ('PALETTE_KIND', 0), ('HORZRES', W), ('VERTRES', H),
                        ('BITSPIXEL', 1), ('PLANES', 4), ('NUMCOLORS', 16), ('BIOS', 4), ('COMPLETE', 1), ('CURSOR_LOADED', 1)]:
        checks[key] = values.get(key) == [wanted]
    checks['92_case_sequence'] = [c.get('CASE') for c in all_cases] == [[n] for n in ALL_IDS]
    checks['no_probe_errors'] = not any(key in values for key in ('WRONG_DISPLAY', 'DUMP_ERROR', 'BRUSH_ERROR', 'ALIASES_WRONG_PROFILE'))
    cases = [c for c in all_cases if c.get('CASE', [None])[0] in IDS]
    checks['five_cursor_cases'] = [c.get('CASE') for c in cases] == [[n] for n in IDS]
    alias_frames, alias_failures = 0, []
    if capture_model == 'mirrored16k':
        names = ['M%s%03d.BIN' % (k, n) for n in ALL_IDS for k in 'BD'] + ['MV%03d.BIN' % n for n in IDS]
        for name in names:
            try:
                raw = (guest / name).read_bytes()
                require(len(raw) == RAW, 'Capture size is not32768')
                alias_frames += 1
                if raw[:16384] != raw[16384:]:
                    alias_failures.append({'file': name, 'mirror_mismatches': differences(raw[:16384], raw[16384:])})
            except (OSError, ValueError) as exc:
                alias_failures.append({'file': name, 'error': str(exc)})
        checks['all189_capture_aliases'] = alias_frames == 189 and not alias_failures
    results = []
    want_background = grid()
    for c in cases:
        n = c['CASE'][0]
        row = {'case': n}
        try:
            rx, ry = REQUESTS[n - 120]
            cx, cy = max(0, min(W - 1, rx)), max(0, min(H - 1, ry))
            required = {'KIND': 10, 'ENDCASE': n, 'CURSOR_REQ_X': rx, 'CURSOR_REQ_Y': ry, 'CURSOR_X': cx, 'CURSOR_Y': cy}
            row['log_fields'] = all(c.get(k) == [v] for k, v in required.items())
            shown, hidden = c.get('CURSOR_SHOW_COUNT', []), c.get('CURSOR_HIDE_COUNT', [])
            row['show_hide_counts'] = len(shown) == len(hidden) == 1 and shown[0] >= 0 and hidden[0] == shown[0] - 1 and hidden[0] < 0
            before, visible, after = (guest / ('M%s%03d.BIN' % (kind, n)) for kind in 'BVD')
            before, visible, after = before.read_bytes(), visible.read_bytes(), after.read_bytes()
            require(len(before) == len(visible) == len(after) == RAW, 'Capture size is not32768')
            row['before_background'] = differences(want_background, pixels(before))
            row['restored_background'] = differences(want_background, pixels(after))
            row['restore_raw'] = differences(before, after)
            row['visible_padding_changes'] = [i for i in PADDING if visible[i] != before[i]]
            row['visible_unused_changes'] = [i for i in untouched if visible[i] != before[i]]
            row['restore_unused_changes'] = [i for i in untouched if after[i] != before[i]]
            if model is not None:
                wanted = visible_frame(before, model, cx, cy, capture_model)
                row['visible_raw'] = differences(wanted, visible)
                row['visible_pixels'] = differences(pixels(wanted), pixels(visible))
                row['visible_pixels_compared'] = W * H
            else:
                row['visible_raw'] = None
                row['visible_pixels'] = None
                row['visible_pixels_compared'] = 0
            row['restoration_and_padding_pass'] = row['log_fields'] and row['show_hide_counts'] and all(row[k]['count'] == 0 for k in ('before_background', 'restored_background', 'restore_raw')) and not row['visible_unused_changes'] and not row['restore_unused_changes']
            row['raster_pass'] = None if model is None else row['restoration_and_padding_pass'] and row['visible_raw']['count'] == 0
        except (OSError, ValueError, KeyError, IndexError, struct.error) as exc:
            row.update(error=str(exc), restoration_and_padding_pass=False, raster_pass=False)
        results.append(row)
    metadata = all(checks.values())
    raster = None if model is None else metadata and len(results) == 5 and all(r.get('raster_pass') is True for r in results)
    return {'scope': 'Five cursor cases only; other87 cases still require the independent MODECHK result',
            'resource_source': source, 'resource_identity': identities, 'compression': selected[0],
            'capture_model': {'name': capture_model, 'physical_bytes': 16384 if capture_model == 'mirrored16k' else 32768,
                              'captured_bytes': RAW, 'unused_capture_offsets_checked': len(untouched),
                              'basis': 'Explicit fixture model:32KB window aliases the same16KB aperture twice; verified against every input frame' if capture_model == 'mirrored16k' else 'Independent32KB window; upper16KB must remain unchanged',
                              'alias_frames_checked': alias_frames, 'alias_failures': alias_failures},
            'source_hotspot': selected[1][32512]['hotspot'], 'logical_hotspot': model['hotspot'] if model else None,
            'logged_cursor_metrics': [values.get('CURSOR_WIDTH'), values.get('CURSOR_HEIGHT')],
            'model_error': model_error, 'metadata_checks': checks, 'metadata_pass': metadata,
            'cases': results, 'visible_pixels_compared': sum(r.get('visible_pixels_compared', 0) for r in results),
            'raster_pass': raster, 'accepted_cursor_contract_pass': identities['pass'] and raster is True}


def selftest(accepted, driver=None):
    reference = cursor_resources(accepted, True)
    require(reference[0] == (1, 2) and len(reference[1]) == 11, 'Wrong accepted resources')
    model = compress_cursor(reference[1][32512], reference[0])
    require((model['width'], model['height'], model['hotspot']) == (32, 16, (2, 2)), 'Wrong accepted shape dimensions')
    counts = Counter(zip(sum(model['and'], ()), sum(model['xor'], ())))
    require(counts == {(1, 0): 456, (0, 1): 28, (0, 0): 28}, 'Wrong accepted mask counts')
    require(len(USED) == 16000 and len(PADDING) == 384 and len(UNUSED) == 16768, 'Incorrect160x200 banking')
    before = bytearray([0xa5] * RAW)
    # Independent row-wise bank writer, separate from address().
    expected = grid()
    for y in range(H):
        start = (8192 if y % 2 else 0) + (y // 2) * 80
        for pair in range(80):
            before[start + pair] = (expected[y * W + pair * 2] << 4) | expected[y * W + pair * 2 + 1]
    before[16384:] = before[:16384]
    require(pixels(before) == expected, 'Independent160x200 bank roundtrip failed')
    checks = 0
    for rx, ry in REQUESTS:
        cx, cy = max(0, min(W - 1, rx)), max(0, min(H - 1, ry))
        rendered = visible_frame(before, model, cx, cy)
        want = expected.copy()
        # Pixel-centric independent equation, not renderer iteration/order.
        for y in range(H):
            for x in range(W):
                lx, ly = x - cx + 2, y - cy + 2
                if 0 <= lx < 32 and 0 <= ly < 16:
                    a, b = model['and'][ly][lx], model['xor'][ly][lx]
                    old = want[y * W + x]
                    want[y * W + x] = ((old if a else 0) ^ (15 if b else 0))
        require(pixels(rendered) == want, 'Independent cursor pixel equation failed')
        require(all(rendered[i] == before[i] for i in MIRROR_PADDING), 'Cursor changed physical bank padding')
        require(rendered[:16384] == rendered[16384:], 'Predicted mirrored capture differs between halves')
        for at in (address(cx, cy), 16384 + address(cx, cy)):
            broken = bytearray(rendered)
            broken[at] ^= 1
            require(broken != rendered and broken[:16384] != broken[16384:], 'Single-half corruption not detected')
        checks += W * H
    if driver is not None:
        actual = cursor_resources(driver)
        require(not identity(reference, actual)['pass'], 'Expected changed-current resources in diagnostic selftest')
        try:
            compress_cursor(actual[1][32512], actual[0])
        except ValueError:
            pass
        else:
            raise ValueError('Expected current stock compression ambiguity was not rejected')
    return {'selftest': 'PASS', 'synthetic_cursor_pixels': checks, 'known_compact_masks': dict((str(k), v) for k, v in counts.items()),
            'bank_padding_bytes': len(PADDING), 'unused_mirrored_offsets': len(MIRROR_PADDING), 'capture_model': 'mirrored16k', 'independent_half_corruptions_rejected': 10, 'native_execution': 'NOT_RUN'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('guest', type=Path, nargs='?')
    parser.add_argument('--driver', type=Path, help='Actual installed driver, required for guest checks')
    parser.add_argument('--accepted-driver', type=Path, default=ACCEPTED)
    parser.add_argument('--resource-source', choices=('accepted', 'current'), default='accepted')
    parser.add_argument('--capture-model', choices=('mirrored16k', 'independent32k'), default='mirrored16k')
    parser.add_argument('--selftest', action='store_true')
    args = parser.parse_args()
    try:
        if args.selftest:
            report = selftest(args.accepted_driver, args.driver)
            ok = True
        else:
            if args.guest is None or args.driver is None:
                parser.error('guest and --driver are required for guest checks')
            report = analyze(args.guest, args.driver, args.accepted_driver, args.resource_source, args.capture_model)
            ok = report['accepted_cursor_contract_pass']
    except (OSError, ValueError, KeyError, IndexError, struct.error) as exc:
        report, ok = {'accepted_cursor_contract_pass': False, 'error': str(exc)}, False
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
