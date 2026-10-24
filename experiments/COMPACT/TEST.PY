"""Focused offline integrity, typography and rollback checks. No emulator.

Specimens are host FNT decodes, never Windows screenshot evidence.
"""
import argparse
import hashlib
import io
import json
import struct
import tempfile
import zipfile
from pathlib import Path
from PIL import Image, ImageDraw
import BUILD
import FONT
import PREP
import UI

INSPECT = FONT.load('compact_inspect', FONT.ROOT / 'tools/XTFONTS/INSPECT.PY')


def strike(data):
    module, resources = INSPECT.resources(data)
    font = next(data[o:o + n] for t, i, f, o, n in resources if t == 0x8008)
    return font[:struct.unpack_from('<I', font, 2)[0]]


def pixels(font, code):
    first, last = font[95:97]
    if not first <= code <= last:
        code = first + font[97]
    width, off = struct.unpack_from('<HH', font, 118 + (code - first) * 4)
    h = struct.unpack_from('<H', font, 88)[0]
    return [[(font[off + x // 8 * h + y] >> (7 - x % 8)) & 1 for x in range(width)] for y in range(h)]


def extent(font, text):
    return sum(len(pixels(font, c)[0]) for c in text.encode('cp1252'))


def bitmap(data):
    header = struct.unpack_from('<I', data)[0]
    colors = 6 if header == 12 else 8
    bmp = struct.pack('<2sIHHI', b'BM', 14 + len(data), 0, 0, 14 + header + colors) + data
    return Image.open(io.BytesIO(bmp)).convert('RGB')


def tree(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


def refusal(action):
    try:
        action()
    except (ValueError, KeyError, struct.error, IndexError):
        return
    raise AssertionError('expected refusal')


def run(out, dialog_helper=None):
    out.mkdir(parents=True, exist_ok=False)
    metrics, checks = {}, []
    protected = [FONT.ROOT / 'src/tandysw/MODEPROF.PY', FONT.ROOT / 'src/text80/T80UI.PY']
    protected += list((FONT.ROOT / 'distributions/WINXT').glob('*.DRV'))
    protected += list((FONT.ROOT / 'distributions/WINXT').glob('*.FON'))
    before = {str(p): BUILD.SHA(p.read_bytes()) for p in protected}
    with tempfile.TemporaryDirectory(prefix='compact160-') as scratch:
        scratch = Path(scratch)
        for target, t in BUILD.TARGETS.items():
            packet, again = scratch / target, scratch / (target + '-again')
            BUILD.build(target, packet)
            BUILD.build(target, again)
            assert tree(packet) == tree(again), 'nondeterministic build'
            with zipfile.ZipFile(FONT.ROOT / 'downloads/experimental/yamaha-candidate03' / t['archive']) as z:
                original = z.read(t['input'])
                baseline_font = strike(z.read('XTCSYS.FON'))
            candidate = (packet / t['output']).read_bytes()
            oldres = {(a, b): d for a, b, c, d in BUILD.PACKRES.inspect_ne(original)}
            newres = {(a, b): d for a, b, c, d in BUILD.PACKRES.inspect_ne(candidate)}
            assert oldres.keys() == newres.keys()
            desc, shift = BUILD.descriptors(original)
            allowed = {i for key in json.loads((packet / 'BUILD.JSN').read_text())['resource_edits']
                       for i in range(desc[tuple(key)][0], desc[tuple(key)][0] + 4)}
            assert all(a == b or i in allowed for i, (a, b) in enumerate(zip(original, candidate)))
            # This covers every code/data segment and relocation byte, all NE
            # entry/import/name/device tuples, framebuffer and BIOS instructions.
            assert len(candidate) > len(original)
            assert struct.unpack_from('<9H', newres[(0x7006, 1)]) == (8, 6, 2, 4, 1, 2, 0, 1, 1)
            assert newres[(0x7006, 1)][4:12] == oldres[(0x7006, 1)][4:12], 'icon/cursor compression changed'
            for key in oldres:
                if key not in [(2, i) for i in UI.bitmaps()] + [(0x7006, 1), (0x7006, 3)]:
                    assert oldres[key] == newres[key], key
            changed = bytearray(original)
            struct.pack_into('<H', changed, desc[(2, 32749)][0], 0xffff)
            refusal(lambda: BUILD.overlay(changed))
            refusal(lambda: BUILD.overlay(b'not NE'))
            refusal(lambda: BUILD.build(target, packet))
            checks += [target + ': deterministic build and all original non-resource bytes preserved',
                       target + ': malformed NE and existing output refused']

            # Synthetic private clone: no Windows binaries/media included.
            clone = scratch / (target + '-clone')
            (clone / 'SYSTEM').mkdir(parents=True)
            (clone / 'SYSTEM' / t['input']).write_bytes(original)
            (clone / 'SYSTEM.INI').write_bytes(('[boot]\r\ndisplay.drv=' + t['input'] +
                '\r\nfonts.fon=XTCSYS.FON\r\nfixedfon.fon=XTCFIX.FON\r\noemfonts.fon=XTCOEM.FON\r\nshell=PROGMAN.EXE\r\n; keep this\r\n').encode())
            (clone / 'PROGMAN.INI').write_bytes(b'[Settings]\r\nWindow=64 20 576 160 1\r\nSaveSettings=1\r\n')
            (clone / 'WIN.INI').write_bytes(b'[windows]\r\nload=KEEP.EXE\r\nBorderWidth=3\r\n[fonts]\r\nExisting=OWN.FON\r\n[other]\r\nkept=yes\r\n')
            original_tree = tree(clone)
            wrong = 'pc1-b000' if target == 'yamaha-b800' else 'yamaha-b800'
            refusal(lambda: PREP.install(clone, packet, wrong))
            assert tree(clone) == original_tree
            PREP.install(clone, packet, target)
            assert PREP.ini((clone / 'PROGMAN.INI').read_bytes(), 'Settings', 'Window') == '64 20 576 160 3'
            assert b'load=KEEP.EXE\r\n' in (clone / 'WIN.INI').read_bytes()
            assert b'Existing=OWN.FON\r\n' in (clone / 'WIN.INI').read_bytes()
            refusal(lambda: PREP.install(clone, packet, target))
            modified = (clone / 'WIN.INI').read_bytes()
            (clone / 'WIN.INI').write_bytes(modified + b'; user edit\r\n')
            dirty = tree(clone)
            refusal(lambda: PREP.rollback(clone))
            assert tree(clone) == dirty
            (clone / 'WIN.INI').write_bytes(modified)
            PREP.rollback(clone)
            restored = tree(clone)
            assert restored.pop('C16STATE.JSN')
            assert restored == original_tree
            refusal(lambda: PREP.safe(clone, '../outside'))
            refusal(lambda: PREP.ini(b'[x]\r\na=1\r\na=2\r\n', 'x', 'a', '3'))
            checks += [target + ': wrong-target and repeated install refused before mutation',
                       target + ': exact rollback; intervening user edits preserved/refused']

            # Completed evidence is archived only after full baseline validation.
            journal = (clone / 'C16STATE.JSN').read_bytes()
            (clone / 'C16H0001.JSN').write_bytes(b'older evidence; never overwrite')
            saved = tree(clone)
            refusal(lambda: PREP.rollback(clone))
            assert tree(clone) == saved
            for change in ('status', 'schema', 'target', 'hash', 'duplicate', 'missing', 'unsafe'):
                state = json.loads(journal)
                if change == 'status': state['status'] = 'INSTALLED'
                elif change == 'schema': state['schema'] = True
                elif change == 'target': state['target'] = []
                elif change == 'hash': state['entries'][0]['before_sha256'] = '0' * 64
                elif change == 'duplicate': state['entries'].append(state['entries'][0])
                elif change == 'missing': state['entries'].pop(0)
                else: state['entries'][0]['path'] = '../outside'
                (clone / 'C16STATE.JSN').write_text(json.dumps(state))
                bad_tree = tree(clone)
                refusal(lambda: PREP.install(clone, packet, target))
                assert tree(clone) == bad_tree
            (clone / 'C16STATE.JSN').write_bytes(journal)
            f = clone / 'WIN.INI'
            f.write_bytes(original_tree['WIN.INI'] + b'; changed baseline')
            saved = tree(clone)
            refusal(lambda: PREP.install(clone, packet, target))
            assert tree(clone) == saved
            f.write_bytes(original_tree['WIN.INI'])
            # Interrupt between archival and the next PREPARED journal. No file
            # has changed; retained history permits a fresh retry.
            original_atomic = PREP.atomic
            def before_prepared(path, data):
                raise OSError('intentional interruption after archival')
            PREP.atomic = before_prepared
            try:
                try: PREP.install(clone, packet, target)
                except OSError: pass
                else: raise AssertionError('interruption did not fire')
            finally: PREP.atomic = original_atomic
            assert not (clone / 'C16STATE.JSN').exists()
            assert (clone / 'C16H0002.JSN').read_bytes() == journal
            for cycle in range(2):
                PREP.install(clone, packet, target)
                PREP.rollback(clone)
            restored = tree(clone)
            assert restored.pop('C16STATE.JSN') == journal
            assert restored.pop('C16H0001.JSN') == b'older evidence; never overwrite'
            assert restored.pop('C16H0002.JSN') == journal
            assert restored.pop('C16H0003.JSN') == journal
            assert restored == original_tree
            checks += [target + ': on/off/on/off exact restoration and immutable numbered history',
                       target + ': corrupt, active and inconsistent completed journals refused unchanged',
                       target + ': interruption after archival safely retries without payload mutation']

            # A failed archive flush leaves the active journal recoverable and
            # retains the incomplete history slot; retry must never overwrite it.
            archive_clone = scratch / (target + '-archive-interrupted')
            (archive_clone / 'SYSTEM').mkdir(parents=True)
            for name, data in original_tree.items():
                (archive_clone / name).write_bytes(data)
            (archive_clone / 'C16STATE.JSN').write_bytes(journal)
            original_fsync = PREP.os.fsync
            def fail_flush(fd):
                raise OSError('intentional archive flush interruption')
            PREP.os.fsync = fail_flush
            try:
                try: PREP.install(archive_clone, packet, target)
                except OSError: pass
                else: raise AssertionError('archive interruption did not fire')
            finally: PREP.os.fsync = original_fsync
            saved = tree(archive_clone)
            assert saved.pop('C16STATE.JSN') == journal
            assert saved.pop('C16H0001.JSN') == journal
            assert saved == original_tree
            PREP.install(archive_clone, packet, target)
            PREP.rollback(archive_clone)
            restored = tree(archive_clone)
            assert restored.pop('C16STATE.JSN') == journal
            assert restored.pop('C16H0001.JSN') == journal
            assert restored.pop('C16H0002.JSN') == journal
            assert restored == original_tree
            checks += [target + ': failed archive flush retains journal/history and safely retries']

            # Recover a prepared journal after only one payload was replaced.
            # This is file-transaction interruption, not an emulator crash test.
            interrupted = scratch / (target + '-interrupted')
            (interrupted / 'SYSTEM').mkdir(parents=True)
            for name, data in original_tree.items():
                (interrupted / name).write_bytes(data)
            original_atomic, calls = PREP.atomic, [0]
            def injected(path, data):
                calls[0] += 1
                if calls[0] == 3:
                    raise OSError('intentional transaction interruption')
                original_atomic(path, data)
            PREP.atomic = injected
            try:
                try:
                    PREP.install(interrupted, packet, target)
                except OSError:
                    pass
                else:
                    raise AssertionError('interruption did not fire')
            finally:
                PREP.atomic = original_atomic
            assert json.loads((interrupted / 'C16STATE.JSN').read_text())['status'] == 'PREPARED'
            PREP.rollback(interrupted)
            restored = tree(interrupted)
            restored.pop('C16STATE.JSN')
            assert restored == original_tree
            checks += [target + ': recovery of partially applied prepared transaction']

            for label, shell, placement in [('custom-shell', 'OWN.EXE', '64 20 576 160 1'),
                                             ('unknown-placement', 'PROGMAN.EXE', 'unrecognized placement')]:
                guarded = scratch / (target + '-' + label)
                (guarded / 'SYSTEM').mkdir(parents=True)
                for name, data in original_tree.items():
                    (guarded / name).write_bytes(data)
                f = guarded / 'SYSTEM.INI'
                f.write_bytes(PREP.ini(f.read_bytes(), 'boot', 'shell', shell))
                f = guarded / 'PROGMAN.INI'
                f.write_bytes(PREP.ini(f.read_bytes(), 'Settings', 'Window', placement))
                expected = tree(guarded)
                PREP.install(guarded, packet, target)
                assert (guarded / 'PROGMAN.INI').read_bytes() == expected['PROGMAN.INI']
                PREP.rollback(guarded)
                restored = tree(guarded)
                restored.pop('C16STATE.JSN')
                assert restored == expected
            checks += [target + ': custom shell and unknown Program Manager placement preserved']

            if dialog_helper is not None:
                helper_clone = scratch / (target + '-helper')
                (helper_clone / 'SYSTEM').mkdir(parents=True)
                for name, data in original_tree.items():
                    (helper_clone / name).write_bytes(data)
                bad = scratch / 'BAD.EXE'
                bad.write_bytes(b'not the pinned original helper')
                refusal(lambda: PREP.install(helper_clone, packet, target, bad))
                assert tree(helper_clone) == original_tree
                PREP.install(helper_clone, packet, target, dialog_helper)
                assert (helper_clone / 'C16VIEW.EXE').read_bytes() == Path(dialog_helper).read_bytes()
                assert PREP.ini((helper_clone / 'WIN.INI').read_bytes(), 'windows', 'load') == 'KEEP.EXE C16VIEW.EXE'
                installed = (helper_clone / 'C16VIEW.EXE').read_bytes()
                (helper_clone / 'C16VIEW.EXE').write_bytes(installed + b'changed')
                dirty = tree(helper_clone)
                refusal(lambda: PREP.rollback(helper_clone))
                assert tree(helper_clone) == dirty
                (helper_clone / 'C16VIEW.EXE').write_bytes(installed)
                PREP.rollback(helper_clone)
                restored = tree(helper_clone)
                restored.pop('C16STATE.JSN')
                assert restored == original_tree
                checks += [target + ': pinned optional focus helper startup, refusal, exact rollback']

        packet = scratch / 'yamaha-b800'
        for name in FONT.FACES:
            font = strike((packet / name).read_bytes())
            h = INSPECT.fontinfo(font)
            assert (h['height'], h['ascent'], h['avg_width']) == (8, 7, 4)
            assert (h['horiz_res'], h['vert_res']) == (96, 48)
            assert h['width_bytes'] % 2 == 0
            for code in range(h['first'], h['last'] + 2):
                width, off = struct.unpack_from('<HH', font, 118 + (code - h['first']) * 4)
                assert off >= 118 + (h['last'] - h['first'] + 2) * 4
                assert off + ((width + 7) // 8) * 8 <= struct.unpack_from('<I', font, 105)[0]
                rows = pixels(font, min(code, h['last']))
                assert len(rows) == 8 and 1 <= width <= h['max_width']
                if h['pix_width']:
                    assert width == 4
            for char in 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789':
                assert any(map(any, pixels(font, ord(char))))
            assert pixels(font, ord('0')) != pixels(font, ord('O'))
            # Fixed/OEM remain distinct letters in their independently authored
            # four-column variants; no nearest-neighbor raster shrink is used.
            assert pixels(font, ord('M')) != pixels(font, ord('W'))
            metrics[name] = {k: v for k, v in h.items() if k != 'widths'}
        record = json.loads((packet / 'BUILD.JSN').read_text())
        assert record['fonts']['fonts']['C16OEM.FON']['fallback_codes'] == []
        for n in ('C16SYS.FON', 'C16FIX.FON', 'C16HELV.FON', 'C16COUR.FON'):
            assert record['fonts']['fonts'][n]['fallback_codes'] == [127, 128, 129, 141, 142, 143, 144, 157, 158]
        compact_font = strike((packet / 'C16SYS.FON').read_bytes())
        text = ['File Options Window Help', 'File Edit Search Help', 'Program Manager',
                'Save changes before exit?', 'Cancel', 'C:\\WINDOWS\\NOTEPAD.TXT']
        metrics['advance_comparison'] = [{'text': t, 'baseline': extent(baseline_font, t),
            'compact': extent(compact_font, t)} for t in text]
        metrics['native_metrics'] = 'NOT_TESTED; FNT fields/bitmap dimensions are offline measurements'
        metrics['geometry'] = {'caption_button': [6, 7], 'scroll_arrow': [6, 8],
            'thumb_minimum_config': [6, 8], 'checkbox_radio_tile': [6, 8],
            'icon_compression': [2, 4], 'icon_compression_source': 'inherited unchanged; Y=4 is not newly introduced',
            'native_icon_dimensions_and_rendering': 'NOT_TESTED', 'BorderWidth_ini': 1,
            'baseline_caption_button': [27, 14], 'baseline_scroll_up': [18, 11],
            'native_hit_rectangles': 'NOT_TESTED'}
        metrics['reference_presentation'] = {'file': 'docs/yamaha/YAMAHA03.JPG', 'size': [960, 600],
            'native_mode': [160, 200], 'inferred_pixel_scale': [6, 3],
            'reference_pixel_aspect': '2:1', '4_3_monitor_pixel_aspect': '5:3',
            'inference': 'dimension-derived; not a hardware timing measurement'}
        # Only decode original first-party font pixels; this is explicitly a
        # host typography specimen, not a reconstruction of Windows chrome.
        specimen = Image.new('RGB', (160, 200), 'white')
        y = 2
        lines = ['HOST FONT DECODE', 'COMPACT160 - NOT WIN3', '', 'File Options Window Help',
                 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz', '0123456789',
                 'Save changes before exit?', 'OK   Cancel   &Help', 'C:\\WINDOWS\\NOTEPAD.TXT',
                 'M W m w   0 O   1 l I', 'CP437 original narrow:']
        for line in lines:
            x = 2
            for c in line.encode('cp1252'):
                rows = pixels(compact_font, c)
                for gy, row in enumerate(rows):
                    for gx, ink in enumerate(row):
                        if ink and x + gx < 160 and y + gy < 200:
                            specimen.putpixel((x + gx, y + gy), (0, 0, 0))
                x += len(rows[0])
            y += 10
        oem = strike((packet / 'C16OEM.FON').read_bytes())
        for index, code in enumerate(range(1, 255)):
            x, y = 2 + index % 32 * 4, 124 + index // 32 * 9
            for gy, row in enumerate(pixels(oem, code)):
                for gx, ink in enumerate(row):
                    if ink and y + gy < 200:
                        specimen.putpixel((x + gx, y + gy), (0, 0, 0))
        specimen.save(out / 'HOST160.PNG')
        specimen.resize((960, 600), Image.Resampling.NEAREST).save(out / 'HOSTWIDE.PNG')
        # Atlas state dimensions and original pressed/unpressed differences.
        controls = UI.bitmaps()
        atlas = bitmap(controls[32759])
        assert atlas.size == (24, 24)
        tiles = [atlas.crop((x * 6, y * 8, (x + 1) * 6, (y + 1) * 8)).tobytes()
                 for y in range(3) for x in range(4)]
        assert len(set(tiles)) == 12, 'state collision'
        atlas.resize((480, 240), Image.Resampling.NEAREST).save(out / 'HOSTCTL.PNG')
        for a, b in ((32749, 32746), (32748, 32745), (32747, 32744),
                     (32753, 32743), (32752, 32742), (32750, 32740), (32751, 32741)):
            assert controls[a] != controls[b]
            assert bitmap(controls[a]).size == bitmap(controls[b]).size
        checks += ['five FNT/FON structures, bounds, metrics and ASCII strikes',
                   'all advertised CP437 codes drawn; ANSI reserved bytes visibly fall back',
                   '12 distinct checkbox/radio/three-state tiles; seven pressed pairs',
                   '160x200 host specimens clearly distinguished from native screenshots']
    assert before == {str(p): BUILD.SHA(p.read_bytes()) for p in protected}
    checks += ['320/640 shipped driver/font bytes and existing profile sources unchanged']
    result = dict(status='PASS', scope='OFFLINE ONLY', checks=checks, metrics=metrics,
                  native_runtime='NOT_TESTED', remaining='See README native acceptance matrix',
                  optional_helper_sha256=BUILD.SHA(Path(dialog_helper).read_bytes()) if dialog_helper is not None else None)
    FONT.XT.textfile(out / 'RESULT.JSN', json.dumps(result, ensure_ascii=True, indent=2) + '\n')
    print(json.dumps(dict(status='PASS', checks=len(checks), native_runtime='NOT_TESTED', out=str(out))))
    return result


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--dialog-helper', type=Path)
    a = p.parse_args()
    run(a.out.resolve(), a.dialog_helper)
