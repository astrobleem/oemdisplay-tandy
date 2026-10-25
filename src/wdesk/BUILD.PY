#!/usr/bin/env python3
"""BUILD.PY - developer-only build and check driver for the WDESK core.

Not shipped.  Python 3.8+, standard library only, no network, no emulator.
Everything is written under --out, which must not exist or be empty.
Nothing is ever deleted.

Steps (each prints PASS/FAIL/SKIPPED; exit status is nonzero on any FAIL):
  1 HOST    WDTEST.C + WDCORE.C through the managed GCC launcher; the test
            exe must exit 0.
  2 NEG     the same build with -DWD_FAULT_OWNER, -DWD_FAULT_REUSE and
            -DWD_FAULT_PIN on WDCORE.C; each test exe must exit nonzero.
  3 WIN16   Open Watcom wcc for WDCORE.C, WDWIN.C, WDSTUB.C; no warnings
            or errors allowed.
  4 LINK    wlink WDSTUB.EXE from the three OBJ files.
  5 SIZES   map file and sizeof report (no performance claims).
  6 NE      NE header checks on WDSTUB.EXE.
  7 IMPORT  stub imports checked against a real Windows 3.00 system dir.

Evidence classes: HOST CHECKS (steps 1-2) and WIN16 COMPILE/LINK (3-7).
Native Win16 runtime behaviour of WDWIN is never exercised (NOT RUN).

Usage:
  python -B src/wdesk/BUILD.PY --out FRESH_DIR [--win30-system DIR]
                               [--watcom ROOT] [--skip-win16]
"""

import argparse
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LAUNCHER = os.path.expandvars(
    r'%USERPROFILE%\Documents\Codex\toolchains\gcc-ucrt64.py')
HOST_FLAGS = ['-x', 'c', '-std=c89', '-pedantic', '-Wall', '-Wextra',
              '-Wconversion', '-Wshadow', '-Wstrict-prototypes', '-Werror']
FAULTS = ('WD_FAULT_OWNER', 'WD_FAULT_REUSE', 'WD_FAULT_PIN')
WIN16_FLAGS = ['-bt=windows', '-ms', '-0', '-os', '-zq', '-w4', '-we', '-zw']
WIN16_SRC = ('WDCORE', 'WDWIN', 'WDSTUB')
DEFAULT_WATCOM = r'C:\WATCOM'
SZDD_SIG = b'SZDD'
EV_HOST = 'HOST CHECKS'
EV_WIN16 = 'WIN16 COMPILE/LINK'
PASS = 'PASS'
FAIL = 'FAIL'
SKIP = 'SKIPPED'
NE_DATA_MASK = 0x0003
NE_RELOC_FLAG = 0x0100


class UsageError(Exception):
    """Refused arguments, for example a non-empty --out directory."""


class NEError(Exception):
    """A file that is not a readable NE image."""


class Log(object):
    """One row per step; each row is echoed as it is added."""

    def __init__(self):
        self.rows = []

    def add(self, num, name, status, evidence, detail=''):
        self.rows.append((num, name, status, evidence, detail))
        line = '%-7s step %d %s' % (status, num, name)
        if detail:
            line += ': ' + detail
        print(line)


class Ctx(object):
    """Shared state for one run."""

    def __init__(self, args, out):
        self.out = out
        self.src = HERE
        self.log = Log()
        self.watcom = watcom_root(args.watcom)
        self.win30 = args.win30_system
        self.skip_win16 = args.skip_win16
        self.test_text = ''


# ----------------------------------------------------------------- utilities

def parse_args(argv):
    parser = argparse.ArgumentParser(
        description='Developer-only build and check driver for WDESK core.')
    parser.add_argument('--out', required=True, metavar='FRESH_DIR',
                        help='output directory; must not exist or be empty')
    parser.add_argument('--win30-system', metavar='DIR',
                        help='real Windows 3.00 SYSTEM dir for step 7')
    parser.add_argument('--watcom', metavar='ROOT',
                        help='Open Watcom root (default: env WATCOM, '
                             'else C:\\WATCOM)')
    parser.add_argument('--skip-win16', action='store_true',
                        help='run host steps 1-2 only')
    return parser.parse_args(argv)


def prepare_out(path):
    out = os.path.abspath(path)
    if os.path.exists(out):
        if not os.path.isdir(out):
            raise UsageError('--out %s exists and is not a directory' % out)
        if os.listdir(out):
            raise UsageError('--out %s is not empty; refusing (nothing is '
                             'deleted)' % out)
    else:
        os.makedirs(out)
    return out


def watcom_root(arg):
    if arg:
        return os.path.abspath(arg)
    return os.environ.get('WATCOM') or DEFAULT_WATCOM


def watcom_env(root):
    env = dict(os.environ)
    env['WATCOM'] = root
    env['PATH'] = (os.path.join(root, 'binnt') + os.pathsep +
                   os.environ.get('PATH', ''))
    env['INCLUDE'] = (os.path.join(root, 'h', 'win') + os.pathsep +
                      os.path.join(root, 'h'))
    return env


def run_cmd(cmd, cwd, env=None, timeout=300):
    """Run a command with stderr merged.  Returns (rc, text); rc is None
    when the command could not start or timed out."""
    try:
        proc = subprocess.run(cmd, cwd=cwd, env=env,
                              stdin=subprocess.DEVNULL,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout)
    except OSError as exc:
        return None, 'cannot start %s: %s' % (cmd[0], exc)
    except subprocess.TimeoutExpired:
        return None, 'timed out after %d s' % timeout
    return proc.returncode, proc.stdout.decode('latin-1')


def save_text(path, text):
    with open(path, 'w', encoding='latin-1', newline='') as fh:
        fh.write(text)


def append_text(path, text):
    with open(path, 'a', encoding='latin-1', newline='') as fh:
        fh.write(text)


def first_lines(text, count=6):
    return ' | '.join(text.strip().splitlines()[:count])


def gcc_cmd(args):
    """Every host compile goes through the managed launcher; raw gcc is
    never invoked."""
    return [sys.executable, LAUNCHER, '--'] + args


def u16(data, off):
    return struct.unpack_from('<H', data, off)[0]


def u32(data, off):
    return struct.unpack_from('<I', data, off)[0]


def pascal(data, off):
    n = data[off]
    return data[off + 1:off + 1 + n].decode('latin-1'), off + 1 + n


# ---------------------------------------------------------- host steps 1-2

def host_build(ctx, tag, fault=None):
    """Compile WDCORE.C (with -D<fault> when given) and WDTEST.C, then
    link a static exe under --out.  Returns (exe, '') or (None, reason)."""
    out = ctx.out
    core_flags = ['-D' + fault] if fault else []
    core_o = os.path.join(out, 'wdcore_%s.o' % tag)
    test_o = os.path.join(out, 'wdtest_%s.o' % tag)
    exe = os.path.join(out, 'wdtest_%s.exe' % tag)
    jobs = (
        ('compile WDCORE.C', HOST_FLAGS + core_flags +
         ['-c', os.path.join(ctx.src, 'WDCORE.C'), '-o', core_o]),
        ('compile WDTEST.C', HOST_FLAGS +
         ['-c', os.path.join(ctx.src, 'WDTEST.C'), '-o', test_o]),
        ('link', ['-static', '-o', exe, core_o, test_o]),
    )
    log_path = os.path.join(out, 'build_%s.txt' % tag)
    for label, args in jobs:
        rc, text = run_cmd(gcc_cmd(args), out)
        append_text(log_path, '== %s (rc %s)\n%s\n' % (label, rc, text))
        if rc != 0:
            return None, '%s failed (rc %s): %s' % (
                label, rc, first_lines(text))
    return exe, ''


def run_exe(ctx, exe, log_name):
    rc, text = run_cmd([exe], ctx.out, timeout=60)
    save_text(os.path.join(ctx.out, log_name), text)
    return rc, text


def step_host(ctx):
    if not os.path.isfile(LAUNCHER):
        ctx.log.add(1, 'HOST', FAIL, EV_HOST,
                    'GCC launcher missing: %s (raw gcc is never used)'
                    % LAUNCHER)
        return False
    for name in ('WDTEST.C', 'WDCORE.C'):
        path = os.path.join(ctx.src, name)
        if not os.path.isfile(path) or os.path.getsize(path) == 0:
            ctx.log.add(1, 'HOST', FAIL, EV_HOST,
                        '%s missing or empty' % path)
            return False
    exe, err = host_build(ctx, 'clean')
    if exe is None:
        ctx.log.add(1, 'HOST', FAIL, EV_HOST, err)
        return False
    rc, text = run_exe(ctx, exe, 'test_clean.txt')
    ctx.test_text = text
    if rc != 0:
        ctx.log.add(1, 'HOST', FAIL, EV_HOST,
                    'test exit %s, must be 0' % rc)
        return False
    ctx.log.add(1, 'HOST', PASS, EV_HOST,
                'WDTEST exit 0; output in test_clean.txt')
    return True


def step_neg(ctx):
    results = []
    all_ok = True
    for fault in FAULTS:
        tag = fault.split('_')[-1].lower()
        exe, err = host_build(ctx, tag, fault)
        if exe is None:
            all_ok = False
            results.append('%s build failed (%s)' % (tag, err))
            continue
        rc, _ = run_exe(ctx, exe, 'test_%s.txt' % tag)
        if rc is None or rc == 0:
            all_ok = False
            results.append('%s NOT DETECTED (exit %s)' % (tag, rc))
        else:
            results.append('%s detected (exit %s)' % (tag, rc))
    ctx.log.add(2, 'NEG', PASS if all_ok else FAIL, EV_HOST,
                '; '.join(results))


# ------------------------------------------------------------ Win16 steps

def step_wcc(ctx):
    root = ctx.watcom
    wcc = os.path.join(root, 'binnt', 'wcc.exe')
    if not os.path.isfile(wcc):
        ctx.log.add(3, 'WIN16', FAIL, EV_WIN16,
                    'Open Watcom wcc not found at %s (use --skip-win16 for '
                    'host-only runs)' % wcc)
        return False
    env = watcom_env(root)
    bad = []
    for name in WIN16_SRC:
        src = os.path.join(ctx.src, name + '.C')
        obj = os.path.join(ctx.out, name + '.OBJ')
        rc, text = run_cmd([wcc] + WIN16_FLAGS + ['-fo=' + obj, src],
                           ctx.out, env)
        save_text(os.path.join(ctx.out, 'wcc_%s.txt' % name), text)
        diag = re.search(r'warning|error', text, re.IGNORECASE)
        if rc != 0 or diag or not os.path.isfile(obj):
            bad.append('%s rc=%s %s' % (name, rc,
                                        first_lines(text, 3)))
    if bad:
        ctx.log.add(3, 'WIN16', FAIL, EV_WIN16, '; '.join(bad))
        return False
    ctx.log.add(3, 'WIN16', PASS, EV_WIN16,
                'wcc clean for %s (0 warnings, 0 errors)'
                % ', '.join(WIN16_SRC))
    return True


def write_lnk(ctx):
    root = ctx.watcom
    out = ctx.out
    lines = ['system windows',
             'name %s' % os.path.join(out, 'WDSTUB.EXE')]
    for name in WIN16_SRC:
        lines.append('file %s' % os.path.join(out, name + '.OBJ'))
    for sub in (('lib286', 'win'), ('lib286',)):
        path = os.path.join(root, *sub)
        if os.path.isdir(path):
            lines.append('libpath %s' % path)
    lines += ['option map=%s' % os.path.join(out, 'WDSTUB.MAP'),
              'option stack=5120',
              'option heapsize=1024',
              'option stub=%s' % os.path.join(root, 'binw', 'wstub.exe'),
              'option quiet']
    path = os.path.join(out, 'WDSTUB.LNK')
    save_text(path, '\n'.join(lines) + '\n')
    return path


def step_link(ctx):
    wlink = os.path.join(ctx.watcom, 'binnt', 'wlink.exe')
    if not os.path.isfile(wlink):
        ctx.log.add(4, 'LINK', FAIL, EV_WIN16,
                    'wlink not found at %s' % wlink)
        return False
    write_lnk(ctx)
    rc, text = run_cmd([wlink, '@WDSTUB.LNK'], ctx.out,
                       watcom_env(ctx.watcom))
    save_text(os.path.join(ctx.out, 'wlink.txt'), text)
    exe = os.path.join(ctx.out, 'WDSTUB.EXE')
    if rc != 0 or re.search(r'error', text, re.IGNORECASE) or \
            not os.path.isfile(exe):
        ctx.log.add(4, 'LINK', FAIL, EV_WIN16,
                    'wlink rc=%s %s' % (rc, first_lines(text, 4)))
        return False
    ctx.log.add(4, 'LINK', PASS, EV_WIN16,
                'WDSTUB.EXE, %d bytes' % os.path.getsize(exe))
    return True


# Segment rows: name class [group] seg:off size (hex).
MAP_SEG_RE = re.compile(
    r'^\s*(\w+)\s+(\w+)\s+(?:(\w+)\s+)?[0-9A-Fa-f]{4}:[0-9A-Fa-f]{4,8}'
    r'\s+([0-9A-Fa-f]{4,8})\s*$')
MAP_MOD_RE = re.compile(r'^\s*Module:\s*([^\s(]+)', re.IGNORECASE)


def parse_map(path):
    """Return (segments, modules).  segments is a list of (name, class,
    size) from the table before the first Module: header; modules maps a
    lower-case module file name to a list of (class, size)."""
    segs = []
    mods = {}
    cur = None
    with open(path, 'r', encoding='latin-1') as fh:
        for line in fh:
            mod = MAP_MOD_RE.match(line)
            if mod:
                cur = os.path.basename(mod.group(1)).lower()
                mods.setdefault(cur, [])
                continue
            seg = MAP_SEG_RE.match(line)
            if not seg:
                continue
            size = int(seg.group(4), 16)
            if cur is None:
                segs.append((seg.group(1), seg.group(2), size))
            else:
                mods[cur].append((seg.group(2), size))
    return segs, mods


def find_sizeof(text, name):
    match = re.search(r'sizeof\s*\(?\s*%s\s*\)?[^0-9A-Za-z\n]*(\d+)' % name,
                      text, re.IGNORECASE)
    return int(match.group(1)) if match else None


def read_maxwin(src):
    with open(os.path.join(src, 'WDCORE.H'), 'r', encoding='latin-1') as fh:
        match = re.search(r'#\s*define\s+WD_MAXWIN\s+(\d+)', fh.read())
    return int(match.group(1)) if match else None


def is_code(cls):
    return cls.upper().endswith('CODE')


def step_sizes(ctx, exe, mapf):
    try:
        segs, mods = parse_map(mapf)
    except (IOError, OSError) as exc:
        ctx.log.add(5, 'SIZES', FAIL, EV_WIN16, 'map unreadable: %s' % exc)
        return False
    if not segs and not mods:
        ctx.log.add(5, 'SIZES', FAIL, EV_WIN16,
                    'no segment rows parsed from WDSTUB.MAP')
        return False
    print('  segments (name class size):')
    for name, cls, size in segs:
        print('    %-12s %-10s %6d' % (name, cls, size))
    code = sum(s for _, c, s in segs if is_code(c))
    data = sum(s for _, c, s in segs if not is_code(c))
    print('  segment totals: code %d B, data+stack %d B' % (code, data))
    if mods:
        # Watcom module sections list symbol addresses, not sizes, so
        # per-module byte counts cannot be derived from this map.
        print('  per module: byte sizes not in map (symbol addresses '
              'only); modules: %s' % ', '.join(sorted(mods)))
    else:
        print('  per module: no Module: sections in map')
    total = os.path.getsize(exe)
    print('  WDSTUB.EXE file size: %d B' % total)
    wdent = find_sizeof(ctx.test_text, 'WDENT')
    whole = find_sizeof(ctx.test_text, 'WD')
    maxwin = read_maxwin(ctx.src)
    if wdent is None or maxwin is None:
        ctx.log.add(5, 'SIZES', FAIL, EV_WIN16,
                    'sizeof(WDENT) line in test output or WD_MAXWIN in '
                    'WDCORE.H not found')
        return False
    cost = wdent * maxwin
    detail = ('sizeof(WDENT)=%d B per window; WD_MAXWIN=%d; window-limit '
              'cost=%d B; sizeof(WD)=%s B; exe=%d B'
              % (wdent, maxwin, cost,
                 whole if whole is not None else 'not printed', total))
    print('  ' + detail)
    ctx.log.add(5, 'SIZES', PASS, EV_WIN16, detail)
    return True


def ne_offset(data):
    if len(data) < 0x40 or data[:2] != b'MZ':
        raise NEError('not an MZ file')
    ne = u32(data, 0x3C)
    if ne + 0x40 > len(data) or data[ne:ne + 2] != b'NE':
        raise NEError('no NE header at offset 0x%X' % ne)
    return ne


def check_ne(data):
    """Print NE header fields and return a list of problems."""
    ne = ne_offset(data)
    flags = u16(data, ne + 0x0C)
    auto_seg = u16(data, ne + 0x0E)
    win_ver = u16(data, ne + 0x3E)
    target_os = data[ne + 0x36]
    os2_flags = data[ne + 0x37]
    print('  NE header at 0x%X' % ne)
    print('  flags=0x%04X (data type bits=0x%X) autodata_seg=%d'
          % (flags, flags & NE_DATA_MASK, auto_seg))
    print('  expected Windows version word=0x%04X (%d.%02d)'
          % (win_ver, win_ver >> 8, win_ver & 0xFF))
    print('  target OS=%d  OS/2 flags=0x%02X (printed only)'
          % (target_os, os2_flags))
    problems = []
    if win_ver != 0x0300:
        problems.append('expected Windows version 0x0300, got 0x%04X'
                        % win_ver)
    if target_os != 2:
        problems.append('target OS %d, need 2 (Windows)' % target_os)
    if auto_seg == 0 or (flags & NE_DATA_MASK) == 0:
        problems.append('autodata not set (seg=%d, data bits=0x%X)'
                        % (auto_seg, flags & NE_DATA_MASK))
    return problems


def step_ne(ctx, exe):
    try:
        with open(exe, 'rb') as fh:
            problems = check_ne(fh.read())
    except (NEError, IOError, OSError, struct.error) as exc:
        ctx.log.add(6, 'NE', FAIL, EV_WIN16, 'cannot parse NE: %s' % exc)
        return False
    if problems:
        ctx.log.add(6, 'NE', FAIL, EV_WIN16, '; '.join(problems))
        return False
    ctx.log.add(6, 'NE', PASS, EV_WIN16,
                'NE 3.00, target OS 2, autodata present')
    return True


def ne_imports(data):
    """List (module, 'name'|'ord', value) for every import fixup in every
    segment of an NE image."""
    ne = ne_offset(data)
    mod_count = u16(data, ne + 0x1E)
    mod_tab = ne + u16(data, ne + 0x28)
    name_tab = ne + u16(data, ne + 0x2A)
    seg_count = u16(data, ne + 0x1C)
    seg_tab = ne + u16(data, ne + 0x22)
    shift = u16(data, ne + 0x32) or 9
    modules = []
    for i in range(mod_count):
        name, _ = pascal(data, name_tab + u16(data, mod_tab + 2 * i))
        modules.append(name)
    refs = []
    for seg in range(seg_count):
        ent = seg_tab + 8 * seg
        sector = u16(data, ent)
        length = u16(data, ent + 2) or 0x10000
        flags = u16(data, ent + 4)
        if sector == 0 or not (flags & NE_RELOC_FLAG):
            continue
        rel = (sector << shift) + length
        count = u16(data, rel)
        pos = rel + 2
        for _ in range(count):
            kind = data[pos + 1] & 3
            if kind in (1, 2):
                idx = u16(data, pos + 4)
                if not 1 <= idx <= len(modules):
                    raise NEError('fixup module index %d out of range'
                                  % idx)
                mod = modules[idx - 1]
                if kind == 1:
                    refs.append((mod, 'ord', u16(data, pos + 6)))
                else:
                    refs.append((mod, 'name', pascal(
                        data, name_tab + u16(data, pos + 6))[0]))
            pos += 8
    return sorted(set(refs))


def entry_ordinals(data, ne):
    """Ordinals that have a real entry in the NE entry table."""
    pos = ne + u16(data, ne + 0x04)
    end = pos + u16(data, ne + 0x06)
    ords = set()
    ordinal = 1
    while pos < end and pos < len(data):
        count = data[pos]
        if count == 0:
            break
        ind = data[pos + 1]
        if ind == 0:
            ordinal += count
            pos += 2
            continue
        size = 6 if ind == 0xFF else 3
        for _ in range(count):
            ords.add(ordinal)
            ordinal += 1
        pos += 2 + size * count
    return ords


def name_table(data, start, mod):
    """Walk one name table; the first entry (module/description) has
    ordinal 0 and is skipped."""
    pos = start
    first = True
    while pos < len(data):
        n = data[pos]
        if n == 0:
            break
        name = data[pos + 1:pos + 1 + n].decode('latin-1')
        ordv = u16(data, pos + 1 + n)
        if not first:
            mod.names.setdefault(name, ordv)
            mod.by_ord.setdefault(ordv, name)
        first = False
        pos += n + 3


class RealModule(object):
    """Export data of a real NE module: entry ordinals and name tables."""

    def __init__(self, path):
        with open(path, 'rb') as fh:
            data = fh.read()
        if data[:4] == SZDD_SIG:
            raise NEError('SZDD-compressed (MS LZ-Expand); expand it first, '
                          'this script does not guess')
        ne = ne_offset(data)
        self.entries = entry_ordinals(data, ne)
        self.names = {}
        self.by_ord = {}
        name_table(data, ne + u16(data, ne + 0x26), self)
        name_table(data, u32(data, ne + 0x2C), self)


def step_import(ctx, exe, linked):
    if not ctx.win30:
        if ctx.skip_win16:
            reason = 'Win16 evidence MISSING (--skip-win16)'
        else:
            reason = 'no --win30-system DIR given; imports not checked'
        ctx.log.add(7, 'IMPORT', SKIP, EV_WIN16, reason)
        return
    if not linked:
        ctx.log.add(7, 'IMPORT', FAIL, EV_WIN16, 'not run: link failed')
        return
    if not os.path.isdir(ctx.win30):
        ctx.log.add(7, 'IMPORT', FAIL, EV_WIN16,
                    '--win30-system %s is not a directory' % ctx.win30)
        return
    try:
        with open(exe, 'rb') as fh:
            imports = ne_imports(fh.read())
    except (NEError, IOError, OSError, struct.error, IndexError) as exc:
        ctx.log.add(7, 'IMPORT', FAIL, EV_WIN16,
                    'cannot parse stub imports: %s' % exc)
        return
    cache = {}
    lines = []
    missing = 0
    for mod, kind, val in imports:
        if mod not in cache:
            path = os.path.join(ctx.win30, mod + '.EXE')
            try:
                cache[mod] = RealModule(path)
            except (NEError, IOError, OSError, struct.error,
                    IndexError) as exc:
                cache[mod] = exc
        real = cache[mod]
        if isinstance(real, Exception):
            ok, shown = False, '%s' % real
        elif kind == 'name':
            ordv = real.names.get(val)
            ok = ordv is not None and ordv in real.entries
            shown = val
        else:
            ok = val in real.entries
            shown = '#%d (%s)' % (val, real.by_ord.get(val, 'no name'))
        if not ok:
            missing += 1
        lines.append('  %-8s %-40s %s' % (
            mod, shown, 'OK' if ok else 'NOT EXPORTED'))
    for mod in sorted(cache):
        real = cache[mod]
        if not isinstance(real, Exception):
            lines.append('  %s.EXE: %d entries, %d named exports'
                         % (mod, len(real.entries), len(real.names)))
    text = '\n'.join(lines) + '\n'
    save_text(os.path.join(ctx.out, 'imports.txt'), text)
    print(text, end='')
    if missing or not imports:
        ctx.log.add(7, 'IMPORT', FAIL, EV_WIN16,
                    '%d of %d imports not exported by Windows 3.00'
                    % (missing, len(imports)))
        return
    ctx.log.add(7, 'IMPORT', PASS, EV_WIN16,
                '%d imports from %d modules, all exported by the real '
                'Windows 3.00 modules' % (len(imports), len(cache)))


def run_win16(ctx):
    if step_wcc(ctx):
        linked = step_link(ctx)
    else:
        ctx.log.add(4, 'LINK', FAIL, EV_WIN16, 'not run: step 3 failed')
        linked = False
    exe = os.path.join(ctx.out, 'WDSTUB.EXE')
    mapf = os.path.join(ctx.out, 'WDSTUB.MAP')
    if linked:
        step_sizes(ctx, exe, mapf)
        step_ne(ctx, exe)
    else:
        ctx.log.add(5, 'SIZES', FAIL, EV_WIN16, 'not run: link failed')
        ctx.log.add(6, 'NE', FAIL, EV_WIN16, 'not run: link failed')
    step_import(ctx, exe, linked)


def skip_win16(ctx):
    for num, name in ((3, 'WIN16'), (4, 'LINK'), (5, 'SIZES'),
                      (6, 'NE'), (7, 'IMPORT')):
        ctx.log.add(num, name, SKIP, EV_WIN16,
                    'Win16 evidence MISSING (--skip-win16)')


# ---------------------------------------------------------------- summary

def group_text(rows):
    if not rows:
        return 'NOT RUN'
    return ' '.join('%d=%s' % (row[0], row[2]) for row in rows)


def print_summary(ctx):
    rows = ctx.log.rows
    lines = ['', 'SUMMARY',
             '%-5s %-7s %-8s %-19s %s' % ('STEP', 'NAME', 'STATUS',
                                          'EVIDENCE', 'DETAIL')]
    for num, name, status, evid, detail in rows:
        lines.append('%-5d %-7s %-8s %-19s %s'
                     % (num, name, status, evid, detail))
    host = [r for r in rows if r[3] == EV_HOST]
    win = [r for r in rows if r[3] == EV_WIN16]
    lines += ['', 'EVIDENCE CLASSES',
              '  HOST CHECKS        : %s' % group_text(host)]
    if ctx.skip_win16:
        lines.append('  WIN16 COMPILE/LINK : MISSING (--skip-win16 given)')
    else:
        lines.append('  WIN16 COMPILE/LINK : %s' % group_text(win))
    lines.append('  NOT RUN            : native Win16 runtime of WDWIN/'
                 'WDSTUB (no Windows 3.0 or emulator run)')
    failed = [r for r in rows if r[2] == FAIL]
    lines.append('')
    lines.append('OVERALL: %s (%d failed step(s))'
                 % ('FAIL' if failed else 'PASS', len(failed)))
    text = '\n'.join(lines) + '\n'
    save_text(os.path.join(ctx.out, 'summary.txt'), text)
    print(text, end='')


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        out = prepare_out(args.out)
    except UsageError as exc:
        print('BUILD refused: %s' % exc, file=sys.stderr)
        return 2
    ctx = Ctx(args, out)
    print('output directory: %s' % out)
    step_host(ctx)
    step_neg(ctx)
    if ctx.skip_win16:
        skip_win16(ctx)
    else:
        run_win16(ctx)
    print_summary(ctx)
    failed = [r for r in ctx.log.rows if r[2] == FAIL]
    return 1 if failed else 0


if __name__ == '__main__':
    sys.exit(main())
