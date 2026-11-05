"""Replay the current fixed-driver qualification without compiler or emulator."""
from pathlib import Path, PurePosixPath
import configparser
import hashlib
import importlib.machinery
import io
import json
import re
import statistics
import stat
import struct
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUAL = ROOT / 'tools/CPPACK/QUALIFY.JSN'
PROFILES = {'colorplus32016': (320, 'plantronics', 'CP3216', 'XTE'),
            'yamaha160-b800': (160, 'v6355d', 'YMB800', 'XTC')}
# Required repository-owned producer and replay inputs. External DDK/C6 inputs
# are supplied to FULL.PY separately; its final byte-equality gate remains required.
SOURCE_INPUTS = {'experiments/DGSCOPY/' + n for n in (
    'BUILD.PY', 'COPYFAST.PY', 'DGFAR.ASM', 'FULL.PY', 'GENDECO.H', 'GENDRAW.H',
    'GENFAR.H', 'GENSPAN.H', 'GENTRY.H', 'MODECHK.PY', 'N160BASE.C', 'N320BASE.C',
    'OMFFIX.PY', 'PACK.PY', 'PEN16/DISPLAY.INC', 'PEN16/ROBJECT.ASM', 'SPAN.C',
    'TEST.PY', 'TESTPKG.PY', 'TESTVFY.PY', 'VERIFY.PY', 'YAMCUR.PY', 'YAMCUROR.PY')}
SOURCE_INPUTS |= {'experiments/DGSCOPY/' + profile + '/' + name
                  for profile in ('N16016', 'N32016')
                  for name in ('ADRAW.ASM', 'GENDECO.C', 'GENDRAW.C', 'TCURSOR.ASM',
                               'TSOFT.ASM', 'TSOFT.DEF', 'TSOFT.LNK')}
SOURCE_INPUTS |= {'src/tandysw/' + n for n in (
    'build.py', 'BUILDCOPY.PY', 'AUDIT88.PY', 'PORT8086.PY', 'PORTDIB.PY',
    'MODEPROF.PY', 'REPCOPY88.PY', 'BYTECOL.PY', 'CURKEEP.PY', 'OUTROWS.PY',
    'WIDESCAN.PY', 'V1.ASM', 'TCURSOR.ASM', 'TSOFT.DEF', 'TSOFT.LNK',
    'BLDCOR.BAT', 'BLDCUR.BAT', 'BLDRES.BAT', 'PACKRES.PY', 'RLE88.ASM', 'SDIB88.ASM')}
SOURCE_INPUTS |= {'src/pcp/CPCMP.PY', 'src/rrect/RRCMP.PY',
                  'tools/YAMPACK/PACK.PY', 'tools/YAMPACK/TEST.PY'}
SOURCE_INPUTS |= {'experiments/DGSCOPY/PROBES/' + n for n in (
    'ELLIPSE/BUILD.BAT', 'ELLIPSE/PROBE.C', 'ELLIPSE/PROBE.DEF', 'ELLIPSE/PROBE.RSP',
    'MODE/MODEBLD.BAT', 'MODE/MODETEST.C', 'MODE/MODETEST.DEF', 'MODE/MODETEST.RSP',
    'MODE/PROBEASM.ASM', 'RLETEST.C', 'RRECT/BUILD.BAT', 'RRECT/RRBENCH.C',
    'RRECT/RRBENCH.DEF', 'RRECT/RRBENCH.RSP')}
PROBES = {
    'ellipse': ('PROBE.EXE', {'bytes': 8319, 'sha256': '188150f5156ca9f7de34c382810b1f1452ffec2b8fba99fa2e4b2705be03d550'}),
    'colorplus32016': ('RRBENCH.EXE', {'bytes': 14367, 'sha256': 'd1409021a8afa7a1a9c85fedbd75f0bee2d4bc6807ce7728ae8efe429b12b433'}),
    'yamaha160-b800': ('RRBENCH.EXE', {'bytes': 11887, 'sha256': 'b6d0c339e6be2d549dc9b4fc63c600d1918947f08b923701dabb9c66250c71a4'}),
    'mode': ('MODETEST.EXE', {'bytes': 15583, 'sha256': 'd8fc1d6a6cb294d6b1c5d8a9cc6405f9780792976177031fd0ff125c593e51b6'})}


SOURCE_INPUTS |= {'tools/CPPACK/CURRENT.PY', 'tools/CPPACK/TESTCUR.PY',
                  'src/pcp/CPVERIFY.PY', 'tools/CURRENT/BUNDLE.PY'}
EVIDENCE_PREFIX = 'docs/pcp/OUTPUT/OPTIMIZED/'
_evidence_cache = {}

def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def module(name, path):
    return importlib.machinery.SourceFileLoader(name, str(ROOT / path)).load_module()


def relative_name(name):
    require(isinstance(name, str) and name and '\\' not in name and ':' not in name and '\0' not in name,
            'Unsafe qualification path')
    path = PurePosixPath(name)
    require(not path.is_absolute() and '..' not in path.parts and path.as_posix() == name and name != '.',
            'Unsafe qualification path')
    return name


def evidence_members(q):
    """Derive the exact ZIP inventory from existing logical evidence bindings."""
    expected = {}
    def add(path, pin):
        relative_name(path)
        require(path.startswith(EVIDENCE_PREFIX), 'Evidence binding is outside optimized prefix')
        name = relative_name(path[len(EVIDENCE_PREFIX):])
        require(set(pin) == {'bytes', 'sha256'} and type(pin['bytes']) is int and pin['bytes'] >= 0 and
                re.fullmatch(r'[0-9a-f]{64}', pin['sha256']) is not None, 'Invalid evidence member identity')
        require(name not in expected or expected[name] == pin, 'Conflicting evidence member binding: ' + name)
        expected[name] = pin
    def run(row):
        require(row['files'].get('EXECUTED.DRV') == row['driver'], 'Stopped-image driver readback differs: unbound evidence')
        folder = relative_name(row['folder'])
        for name, pin in row['files'].items():
            add(folder + '/' + relative_name(name), pin)
    require(set(q['profiles']) == set(PROFILES), 'Evidence profile inventory differs')
    for profile, p in q['profiles'].items():
        for kind in ('ellipse', 'rounded') + (('mode',) if profile == 'yamaha160-b800' else ()):
            pair = p[kind]
            require(set(pair) == {'baseline', 'candidate'}, 'Evidence run-pair inventory differs')
            for row in pair.values():
                run(row)
        run(p['setup'])
        add(p['control_driver']['path'], p['control_driver']['identity'])
        for row in p['build']['logs']:
            add(row['path'], row['identity'])
    for name in expected:
        require(not any(parent.as_posix() in expected for parent in PurePosixPath(name).parents),
                'Conflicting evidence file/directory paths')
    return expected


def evidence_root(q=None):
    if q is None:
        q = json.loads(QUAL.read_bytes())['optimized']
    row = q.get('evidence_archive')
    require(isinstance(row, dict) and set(row) == {'path', 'identity'}, 'Missing bound optimized evidence archive')
    path = relative_name(row['path'])
    require(not path.startswith(EVIDENCE_PREFIX) and path != EVIDENCE_PREFIX.rstrip('/'),
            'Evidence archive must be outside its logical extraction prefix')
    expected = evidence_members(q)
    try:
        data = (ROOT / path).read_bytes()
    except OSError as error:
        raise ValueError('Bound evidence archive unavailable; no raw-folder fallback') from error
    require(identity(data) == row['identity'], 'Evidence archive identity differs')
    key = (str(ROOT.resolve()), json.dumps({'archive': row, 'members': expected}, sort_keys=True))
    if key in _evidence_cache:
        return Path(_evidence_cache[key].name)
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as zipped:
            infos = zipped.infolist()
            names = [info.filename for info in infos]
            require(len(names) == len(set(names)), 'Duplicate evidence archive member')
            for info in infos:
                relative_name(info.filename)
                require(not info.is_dir() and not info.flag_bits & 1 and
                        stat.S_IFMT(info.external_attr >> 16) in (0, stat.S_IFREG),
                        'Nonregular or encrypted evidence archive member')
            require(set(names) == set(expected), 'Evidence archive member inventory differs')
            payloads = {}
            for info in infos:
                require(info.file_size == expected[info.filename]['bytes'], 'Evidence archive member size differs')
                body = zipped.read(info)
                require(identity(body) == expected[info.filename], 'Evidence archive member identity differs: ' + info.filename)
                payloads[info.filename] = body
    except (OSError, zipfile.BadZipFile, RuntimeError, NotImplementedError) as error:
        raise ValueError('Unreadable bound evidence archive') from error
    # Only after every member is verified, write regular files into a private
    # temporary tree. Never extract archive paths or links directly.
    temp = tempfile.TemporaryDirectory(prefix='fixed-driver-evidence-')
    try:
        for name, body in payloads.items():
            target = Path(temp.name) / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(body)
    except BaseException:
        temp.cleanup()
        raise
    _evidence_cache[key] = temp
    return Path(temp.name)


def local(name):
    relative_name(name)
    if name.startswith(EVIDENCE_PREFIX):
        return evidence_root() / name[len(EVIDENCE_PREFIX):]
    if name == EVIDENCE_PREFIX.rstrip('/'):
        return evidence_root()
    return ROOT / name


def exact(row):
    data = local(row['path']).read_bytes()
    require(identity(data) == row['identity'], 'Qualified bytes differ: ' + row['path'])
    return data


def values(text, key):
    return [int(x) for x in re.findall(r'(?m)^' + re.escape(key) + r'=(\d+)\r?$', text)]


def probe(folder, kind):
    name, pin = PROBES[kind]
    require(identity((folder / name).read_bytes()) == pin, 'Executed native probe differs: ' + name)


def read_run(row, profile, candidate):
    folder = local(row['folder'])
    actual = {p.relative_to(folder).as_posix(): identity(p.read_bytes())
              for p in folder.rglob('*') if p.is_file()}
    require(actual == row['files'], 'Native evidence closure differs: ' + row['folder'])
    require(all(row.get(k) is True for k in ('complete', 'lease_acquired', 'owned_stopped', 'lease_released')),
            'Native run/cleanup incomplete: ' + row['folder'])
    if candidate:
        require(row.get('nonempty_lease_marker_checked') is True, 'Candidate marker check absent')
    require(identity((folder / 'EXECUTED.DRV').read_bytes()) == row['driver'],
            'Stopped-image driver readback differs')
    cfg = configparser.ConfigParser(strict=False, interpolation=None)
    cfg.read_string((folder / 'PROFILE.CFG').read_text())
    for key, wanted in {'machine': 'ibmxt86', 'cpu_family': '8088', 'cpu_speed': '4772728',
                        'cpu_multi': '1', 'mem_size': '640', 'cpu_use_dynarec': '0',
                        'time_sync': 'disabled'}.items():
        require(cfg['Machine'].get(key) == wanted, 'Unmatched native profile: ' + key)
    require(cfg['Video']['gfxcard'] == PROFILES[profile][1], 'Wrong video adapter')
    if profile == 'yamaha160-b800':
        require(dict(cfg['Yamaha V6355D #1']) == {'display_type': '2', 'double_type': '0'},
                'Wrong Yamaha B800 fixture')
    return folder


def raw_pair(a, b, names):
    for name in names:
        x, y = (a / name).read_bytes(), (b / name).read_bytes()
        require(len(x) == len(y) == 32768 and x == y, 'Full raw frame differs: ' + name)


def pixels(profile, raw):
    require(len(raw) == 32768, 'Truncated raw frame')
    width = PROFILES[profile][0]
    out = bytearray(width * 200)
    for y in range(200):
        for x in range(width):
            if width == 160:
                at = (y & 1) * 8192 + (y // 2) * 80 + x // 2
                color = (raw[at] >> (0 if x & 1 else 4)) & 15
            else:
                at = (y & 1) * 8192 + (y // 2) * 80 + x // 4
                shift = 6 - 2 * (x & 3)
                lo, hi = (raw[at] >> shift) & 3, (raw[at + 16384] >> shift) & 3
                color = ((lo & 2) << 1) | ((lo & 1) << 1) | ((hi & 2) >> 1) | ((hi & 1) << 3)
            out[y * width + x] = color
    return out


def ellipse(profile, pair):
    width = PROFILES[profile][0]
    folders = [read_run(pair[k], profile, k == 'candidate') for k in ('baseline', 'candidate')]
    logs = []
    for folder in folders:
        probe(folder, 'ellipse')
        text = (folder / 'PROBE.LOG').read_text()
        logs.append(text)
        for key, wanted in [('COUNTER_FOUND', 1), ('REAL_MODE', 1), ('WIDTH', width),
                            ('HEIGHT', 200), ('COLORS', 16), ('CURVECAPS', 8),
                            ('PROFILE', 1 if profile == 'colorplus32016' else 3), ('MEMORY_BLIT', 1),
                            ('ELLIPSE_DONE', 1), ('COMPLETE', 1)]:
            require(values(text, key) == [wanted], 'Ellipse contract: ' + key)
        require(text.rstrip().endswith('COMPLETE=1') and values(text, 'SEQ') == list(range(58)),
                'Incomplete ellipse sequence')
        require(values(text, 'EXT_NATIVE') == [1] * 32 and values(text, 'EXT_PEN_PRESERVED') == [1] * 32,
                'COPY admission/16-byte pen contract failed')
        require(values(text, 'REJECT_NATIVE') == [1, 0, 0, 0], 'Ellipse fallback contract changed')
        require(not values(text, 'WRITE_ERROR'), 'Ellipse capture write error')
        for key in ('K_BLACK_ADMIT', 'K_GREEN_ADMIT'):
            require(values(text, key) == [16] * 3, 'Ellipse kernel admission count')
        expected = bytes([0, 12, 10, 9, 14, 13, 11, 15][min(7, x * 8 // width)]
                         for y in range(200) for x in range(width))
        require(pixels(profile, (folder / 'F00.BIN').read_bytes()) == expected, 'Independent color chart failed')
        require((folder / 'F05.BIN').read_bytes() == (folder / 'F07.BIN').read_bytes(), 'XOR erase failed')
        require(values(text, 'CUBE_EXEC') == [3], 'Unexpected historical Cube result; requalify scope')
    raw_pair(*folders, ['F%02d.BIN' % n for n in range(58)])
    timing = {}
    for key in ('K_BLACK_MS', 'K_GREEN_MS'):
        samples = [values(text, key) for text in logs]
        require(all(len(x) == 3 for x in samples), 'Missing ellipse timing samples')
        timing[key] = [statistics.median(x) for x in samples]
    require(timing['K_BLACK_MS'][1] < timing['K_BLACK_MS'][0], 'No measured COPY gain')
    require(timing['K_GREEN_MS'][1] <= timing['K_GREEN_MS'][0] + 55, 'XOR timing regressed')
    return {'frames': 58, 'timing_medians': timing, 'cube_execution_qualified': False}


def rounded(profile, pair):
    a, b = [read_run(pair[k], profile, k == 'candidate') for k in ('baseline', 'candidate')]
    for folder in (a, b):
        probe(folder, profile)
    if profile == 'colorplus32016':
        cmp = module('copy_cp_frames', 'src/pcp/CPCMP.PY')
        ha, sa, fa, ba = cmp.validate(a)
        hb, sb, fb, bb = cmp.validate(b)
        require(not ba and not bb, 'Incomplete ColorPlus historical suite')
        require(set(fa) == set(fb) and len(fa) == 48, 'Wrong ColorPlus capture closure')
        count = 48
    else:
        cmp = module('copy_yam_roundrect', 'src/rrect/RRCMP.PY')
        ta, tb = (a / 'RRBENCH.LOG').read_text(), (b / 'RRBENCH.LOG').read_text()
        ia, ba = cmp.validate(ta)
        ib, bb = cmp.validate(tb)
        require(not ba and not bb and ia == ib and ia['screen'] == (['160'], ['200']),
                'Incomplete Yamaha RoundRect/app suite')
        ha, _ = cmp.parse(ta)
        hb, _ = cmp.parse(tb)
        sa, sb = cmp.stages(ta), cmp.stages(tb)
        fa = {p.name: None for p in a.glob('R*.BIN')}
        fb = {p.name: None for p in b.glob('R*.BIN')}
        require(set(fa) == set(fb) and len(fa) == 28, 'Wrong Yamaha RoundRect capture closure')
        count = 28
    require(ha.get('CURVECAPS') == ['0'] and hb.get('CURVECAPS') == ['8'], 'Ellipse capability change differs')
    allowed = {'CURVECAPS', 'FREE_BEFORE_PROBE'}
    require({k: v for k, v in ha.items() if k not in allowed} ==
            {k: v for k, v in hb.items() if k not in allowed}, 'Unapproved GDI metadata change')
    require(set(sa) == set(sb), 'Stage inventory differs')
    for n in sa:
        for key in ('name', 'count', 'api_successes', 'app_found', 'title', 'step_dumps'):
            require(sa[n].get(key) == sb[n].get(key), 'GDI/app result differs: ' + str(n) + ' ' + key)
    raw_pair(a, b, sorted(fa))
    for label, folder in [('baseline', a), ('candidate', b)]:
        wanted = b'RETURNED\r\n' if label == 'candidate' else (folder / 'DONE.TXT').read_bytes()
        require(wanted in (b'RETURNED\r\n', b'RETURNED \r\n') and
                (folder / 'DONE.TXT').read_bytes() == wanted, 'Missing DOS return')
    result = {'frames': count, 'metadata_change': 'CURVECAPS 0 -> 8'}
    if profile == 'colorplus32016':
        times = {x['name']: (x['elapsed_ms'], sb[n]['elapsed_ms'])
                 for n, x in sa.items() if x.get('name') in ('scan_full', 'scan_narrow')}
        require(times['scan_full'][1] <= times['scan_full'][0] + 55, 'Original full-width timing budget exceeded')
        require(times['scan_narrow'][1] - times['scan_narrow'][0] == 110,
                'Disclosed narrow-Output residual no longer describes evidence')
        result['timings'] = times
    return result


def setup(profile, row):
    folder = read_run(row, profile, True)
    width, card, packet, font = PROFILES[profile]
    cfg = configparser.ConfigParser(strict=False, interpolation=None)
    cfg.read_string((folder / 'SYSTEM.INI').read_text())
    require(cfg['boot']['display.drv'].upper() == packet + '.DRV' and
            cfg['boot']['shell'].upper() == 'C:\\RLETEST.EXE' and
            cfg['boot']['286grabber'].upper() == 'CGA.GR2', 'Setup selection differs')
    for key, suffix in [('fonts.fon', 'SYS'), ('fixedfon.fon', 'FIX'), ('oemfonts.fon', 'OEM')]:
        require(cfg['boot'][key].upper() == font + suffix + '.FON', 'Setup font differs')
    require((folder / 'INSTALLED' / (packet + '.DRV')).read_bytes() ==
            (folder / 'EXECUTED.DRV').read_bytes(), 'Setup installed driver differs')
    support = module('copy_selected_support', 'experiments/DGSCOPY/PACK.PY').SUPPORT
    for name in ['CGA.GR2', 'XTSTATIC.LGO', 'WXTSPL01.RLE'] + [font + x + '.FON' for x in ('SYS', 'FIX', 'OEM')]:
        require(identity((folder / 'INSTALLED' / name).read_bytes())['sha256'] == support[name],
                'Installed support bytes differ: ' + name)
    require(identity((folder / 'INSTALLED/RLETEST.EXE').read_bytes()) ==
            {'bytes': 5103, 'sha256': '38a8b842e03d2626b7b0e68384b34db872275e991b7e31343d0d52e2f665f131'},
            'Executed RLE probe differs')
    text = (folder / 'RLETEST.LOG').read_text()
    for key, wanted in [('SCREEN_LINES', 8), ('MEMORY_LINES', 8), ('MEMORY_BLIT', 1),
                        ('ALLOC_70K', 1), ('START_OFFSET', 65520), ('CROSS_LINES', 8), ('RLE_DONE', 1)]:
        require(values(text, key) == [wanted], 'RLE contract differs: ' + key)
    expected = bytearray([15]) * (width * 200)
    for number, x, y in ((0, 10, 10), (1, 22, 22), (2, 40, 40)):
        for line in range(8):
            color = [0, 9, 10, 11, 12, 13, 14, 15][(8 - line) & 7]
            expected[(y + line) * width + x:(y + line) * width + x + 8] = bytes([color]) * 8
        require(pixels(profile, (folder / ('R%02d.BIN' % number)).read_bytes()) == expected,
                'Independent RLE frame oracle failed')
    raw_pair(folder / 'REFERENCE', folder, ['R%02d.BIN' % n for n in range(3)])
    return {'frames': 3, 'pixels_checked': width * 200 * 3, 'shutdown_qualified': False}


def cursor_slots(data):
    ne = struct.unpack_from('<I', data, 60)[0]
    at = ne + struct.unpack_from('<H', data, ne + 36)[0]
    shift = struct.unpack_from('<H', data, at)[0]
    at += 2
    slots = {}
    while True:
        typ, count = struct.unpack_from('<HH', data, at)
        if not typ:
            break
        at += 8
        for unused in range(count):
            offset, size, flags, ident = struct.unpack_from('<4H', data, at)
            at += 12
            if typ & 0x7fff in (1, 12):
                key = (typ & 0x7fff, ident & 0x7fff)
                require(key not in slots, 'Duplicate cursor slot')
                slots[key] = (flags, data[offset << shift:(offset + size) << shift])
    require(len(slots) == 22, 'Expected11 cursor images and11 groups')
    return slots


def verify_profile(profile):
    require(profile in PROFILES, 'Unknown fixed profile')
    q = json.loads(QUAL.read_bytes())['optimized']
    require(q.get('schema') == 1 and q.get('physical_hardware_qualified') is False and
            q.get('cube_execution_qualified') is False,
            'Current fixed-driver qualification incomplete')
    require(SOURCE_INPUTS <= set(q['sources']), 'Missing required fixed-driver source bindings: ' +
            ', '.join(sorted(SOURCE_INPUTS - set(q['sources']))))
    for name, pin in q['sources'].items():
        require(identity(local(name).read_bytes()) == pin, 'Qualified source differs: ' + name)
    p = q['profiles'][profile]
    if profile == 'yamaha160-b800':
        require(p['mode']['baseline']['driver'] == p['control_driver']['identity'] and
                p['mode']['candidate']['driver'] == p['driver']['identity'],
                'MODE control/candidate driver binding differs')
    driver, control = exact(p['driver']), exact(p['control_driver'])
    require(p['build']['modules'] == 31 and p['build']['assembly_listings'] == 29 and
            p['build'].get('private_reference_used') is False and
            all(p['build'].get(k) is True for k in ('complete', 'owned_stopped', 'lease_released',
                 'all_modules_fresh', 'isa_8086_pass', 'rep_prefix_pass', 'exact_reproduction')),
            'Complete source reproduction is unqualified')
    logs = {Path(row['path']).name: exact(row).decode('latin1') for row in p['build']['logs']}
    require(logs['MREADY.TXT'].strip() == 'MODULES_OK' and logs['LREADY.TXT'].strip() == 'LINK_OK',
            'Native build completion markers differ')
    require(logs['C6.LOG'].split() == ['GENDRAW.C', 'GENDECO.C'], 'Native C6 build log differs')
    linked = re.findall(r'\b[A-Z0-9_]+\.OBJ\b', logs['LINK.LOG'].split('Run File', 1)[0])
    source_profile = 'N32016' if profile == 'colorplus32016' else 'N16016'
    expected_objects = re.findall(r'\b[A-Z0-9_]+\.OBJ\b',
                                 (HERE / source_profile / 'TSOFT.LNK').read_text().upper())
    require(len(expected_objects) == len(set(expected_objects)) == 31 and linked == expected_objects,
            'Native link differs from exact31-module source response')
    require(not re.search(r'(?i)fatal error|error [AL]\d+', logs['MODULES.LOG'] + logs['C6.LOG'] + logs['LINK.LOG']),
            'Native compiler/link error recorded')
    # Terse MASM suppresses successful summaries for some modules. FULL.PY
    # separately audits all 29 listings; these logs contain 12 emitted totals.
    require([int(n) for n in re.findall(r'(\d+)\s+Severe\s+Errors', logs['MODULES.LOG'])] == [0] * 12,
            'Recorded assembler error totals differ')
    report = {'driver': identity(driver), 'ellipse': ellipse(profile, p['ellipse']),
              'rounded': rounded(profile, p['rounded']), 'setup': setup(profile, p['setup']),
              'physical_hardware_qualified': False}
    require(p['ellipse']['candidate']['driver'] == p['rounded']['candidate']['driver'] ==
            p['setup']['driver'] == identity(driver), 'Executed driver binding differs')
    require(p['rounded']['baseline']['driver'] == identity(control), 'Shipped control binding differs')
    if profile == 'yamaha160-b800':
        require(identity(control)['sha256'] == 'a3d339a3f1e831bd8499fb2b0a28c683bf08f9fbeb0e96689dc3f6ef9a627c8a',
                'Wrong accepted Yamaha control')
        require(cursor_slots(driver) == cursor_slots(control), 'Accepted cursor flags/padded payloads differ')
        require(p['mode']['baseline']['driver'] == identity(control) and
                p['mode']['candidate']['driver'] == identity(driver), 'MODE control/candidate driver binding differs')
        folders = [read_run(p['mode'][k], profile, k == 'candidate') for k in ('baseline', 'candidate')]
        oracle = module('copy_yamaha_mode', 'experiments/DGSCOPY/MODECHK.PY')
        cursor = module('copy_yamaha_cursor', 'experiments/DGSCOPY/YAMCUROR.PY')
        for folder in folders:
            probe(folder, 'mode')
            result = oracle.analyze(folder, '160x200x16', 15)
            require(result['case_count'] == 92 and all(x['pass'] for x in result['assertions']) and
                    all(x['pass'] for x in result['results'] if x['case'] < 120),
                    'Yamaha independent 87 noncursor cases failed')
            current = local(p['driver']['path']) if folder == folders[1] else local(p['control_driver']['path'])
            checked = cursor.analyze(folder, current, local(p['control_driver']['path']))
            require(checked['accepted_cursor_contract_pass'] is True and checked['visible_pixels_compared'] == 160000,
                    'Yamaha accepted cursor contract failed')
        names = ['M%s%03d.BIN' % (kind, n) for n in cursor.ALL_IDS for kind in 'BD']
        names += ['MV%03d.BIN' % n for n in cursor.IDS]
        raw_pair(*folders, names)
        report['mode'] = {'cases': 92, 'raw_frames': 189, 'cursor_pixels': 160000}
    else:
        require(identity(control) == json.loads(QUAL.read_bytes())['driver'], 'Historical ColorPlus control differs')
    return report


if __name__ == '__main__':
    print(json.dumps({p: verify_profile(p) for p in PROFILES}, indent=2))
