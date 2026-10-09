"""Prepare/run bounded private Win16 tests. NEVER auto-allocate an emulator.

prepare performs only host copies/config generation. run requires a human
allocation, an explicit bound, and exclusive existing lock ownership.
"""
import argparse
import csv
import datetime
import hashlib
import io
import json
import shutil
import struct
import subprocess
import time
from pathlib import Path
from BUILD import textfile

HERE = Path(__file__).resolve().parent
MODES = {'C160': ('TR51616.DRV', 'CGA', 8, 160),
         'C320': ('TR53204.DRV', 'CGA', 4, 320),
         'E320': ('TR53216.DRV', 'EGA', 9, 320),
         'C6404': ('TR56404.DRV', 'CGA', 10, 640),
         'C6402': ('TR56402.DRV', 'CGA', 6, 640)}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def config(mounts, commands, working, runtime=False):
    memory = ('memsize=0\nmemsizekb=640\nallow more than 640kb base memory=false'
              if runtime else 'memsize=16')
    return ('[sdl]\nfullscreen=false\noutput=surface\n'
            '[dosbox]\nmachine=tandy\n' + memory + '\n'
            '[cpu]\ncore=normal\ncputype=8086_prefetch\n'
            'cycles=fixed 200000\nfpu=false\n[render]\nscaler=none\n'
            'doublescan=false\naspect=false\n[dos]\nxms=false\n'
            'ems=false\numb=false\n[mixer]\nnosound=true\n[autoexec]\n'
            '@echo off\n' + ''.join('MOUNT %s "%s"\n' % (letter, root)
                                     for letter, root in mounts) + commands)


def prepare(args):
    out = args.out.resolve()
    if out.exists():
        raise ValueError('Choose a new --out directory')
    compiler, fixture, fonts = args.compiler.resolve(), args.guest.resolve(), args.fonts.resolve()
    repo = HERE.parent.parent
    needed = ['BIN/CL.EXE', 'BIN/C1.EXE', 'BIN/C2.EXE', 'BIN/C3.EXE',
              'BIN/LINK4.EXE', 'LIB/SLIBCEW.LIB', 'LIB/LIBW.LIB',
              'DDK/286/INC/WINDOWS.H', 'INCLUDE/STRING.H']
    for relative in needed:
        if not (compiler / relative).is_file():
            raise ValueError('Missing approved toolchain input: ' + relative)
    if not (fixture / 'WINDOWS/SYSTEM.INI').is_file():
        raise ValueError('Expected private fixture GUEST/WINDOWS')
    out.mkdir(parents=True)
    nativebuild = out / 'BUILD'
    nativebuild.mkdir()
    for name in ('FONTPRB.C', 'FONTPRB.DEF'):
        shutil.copyfile(HERE / name, nativebuild / name)
    batch = ('@ECHO OFF\nPATH=T:\\BIN\n'
             'SET INCLUDE=T:\\DDK\\286\\INC;T:\\INCLUDE\nSET LIB=T:\\LIB\n'
             'CL /nologo /c /G0 /Gw /AS /W3 /Od FONTPRB.C > BUILD.LOG\n'
             'IF ERRORLEVEL 1 GOTO FAIL\n'
             'LINK4 /NOE /NOD FONTPRB.OBJ,FONTPRB.EXE,FONTPRB.MAP,'
             'T:\\LIB\\SLIBCEW.LIB T:\\LIB\\LIBW.LIB,FONTPRB.DEF; >> BUILD.LOG\n'
             'IF ERRORLEVEL 1 GOTO FAIL\nECHO PASS>DONE.TXT\nGOTO END\n'
             ':FAIL\nECHO FAIL>DONE.TXT\n:END\nEXIT\n')
    textfile(nativebuild / 'BUILD.BAT', batch)
    textfile(nativebuild / 'BUILD.CNF', config(
        [('T', compiler), ('D', nativebuild)], 'D:\nBUILD.BAT\n', nativebuild))
    report = {'kind': 'PREPARED ONLY; no emulator launched',
              'compiler': str(compiler), 'dosbox': str(args.dosbox.resolve()),
              'fixture': str(fixture), 'fonts': str(fonts),
              'toolchain': {r: sha(compiler / r) for r in needed}, 'modes': {}}
    # Only the working Windows fixture and reservation helper are copied.
    for mode, (driver, family, bios, width) in MODES.items():
        guest = out / mode / 'GUEST'
        guest.mkdir(parents=True)
        shutil.copytree(fixture / 'WINDOWS', guest / 'WINDOWS')
        target = guest / 'WINDOWS/SYSTEM'
        for name in ('CGASYS', 'CGAFIX', 'CGAOEM', 'EGASYS', 'EGAFIX', 'EGAOEM', 'TXTSYS'):
            shutil.copyfile(fonts / (name + '.FON'), target / (name + '.FON'))
        shutil.copyfile(repo / 'distributions/WINXT' / driver, target / driver)
        shutil.copyfile(repo / 'distributions/WINXT/RESERVE.COM', guest / 'RESERVE.COM')
        ini = guest / 'WINDOWS/SYSTEM.INI'
        text = ini.read_text('latin1')
        import re
        for key, value in [('display.drv', driver), ('fonts.fon', family + 'SYS.FON'),
                           ('fixedfon.fon', family + 'FIX.FON'),
                           ('oemfonts.fon', family + 'OEM.FON'),
                           ('shell', 'C:\\FONTPRB.EXE')]:
            section, count, lines = '', 0, []
            for line in text.splitlines():
                if line.strip().startswith('['):
                    section = line.strip().lower()
                if section == '[boot]' and re.match(
                        r'^' + re.escape(key) + r'=', line, re.I):
                    line, count = key + '=' + value, count + 1
                lines.append(line)
            text = '\n'.join(lines) + '\n'
            if count != 1:
                raise ValueError('Missing/duplicate fixture key: ' + key)
        ini.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))
        textfile(guest / 'START.BAT', '@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\'
            '\nSET TEMP=C:\\WINDOWS\\TEMP\nC:\nRESERVE > RESERVE.LOG\n'
            'IF ERRORLEVEL 1 GOTO FAIL\nCD \\WINDOWS\nWIN /R > C:\\WIN.LOG\n'
            'ECHO RETURNED>C:\\RETURN.OK\nGOTO END\n:FAIL\n'
            'ECHO RESERVATION_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n')
        textfile(out / mode / 'RUN.CNF', config([('C', guest)], 'C:\nSTART.BAT\n', guest, True))
        report['modes'][mode] = {'driver': driver, 'family': family,
            'bios': bios, 'width': width, 'driver_sha256': sha(target / driver),
            'font_sha256': {n: sha(target / n) for n in (family + 'SYS.FON',
                  family + 'FIX.FON', family + 'OEM.FON')},
            'source_windows_sha256': {str(p.relative_to(fixture)): sha(p)
                for p in (fixture / 'WINDOWS').rglob('*') if p.is_file()}}
    textfile(out / 'INPUTS.JSON', json.dumps(report, indent=2) + '\n')
    print('PREPARED ONLY:', out)


def conflicts():
    raw = subprocess.check_output(['tasklist.exe', '/FO', 'CSV', '/NH'], text=True)
    return [row[:2] for row in csv.reader(io.StringIO(raw))
            if row and any(name in row[0].lower() for name in
                           ('dosbox', '86box', 'pcem', 'tandybox'))]


def run(args):
    import msvcrt
    out = args.out.resolve()
    inputs = json.loads((out / 'INPUTS.JSON').read_text())
    for path, expected in inputs['toolchain'].items():
        if sha(Path(inputs['compiler']) / path) != expected:
            raise ValueError('Compiler input changed')
    if conflicts():
        raise ValueError('Emulator already active; allocation refused')
    status = {'allocation_seconds': args.allocated_seconds,
              'cpu': '8086_prefetch', 'core': 'normal',
              'cycles': 'fixed 200000', 'runtime_kb': 640,
              'xms': False, 'ems': False, 'umb': False, 'runs': [],
              'native_qualified': False}
    lock = Path(args.lock)
    lease = lock.open('rb')
    process = None
    held = False
    def save():
        textfile(out / 'STATUS.JSON', json.dumps(status, indent=2) + '\n')
        print(json.dumps(status), flush=True)
    def stop():
        nonlocal process
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        process = None
    def launch(name, cfg, cwd, bound):
        nonlocal process
        if conflicts():
            raise ValueError('Conflicting emulator before ' + name)
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        start = time.monotonic()
        with (out / (name + '.LOG')).open('wb') as logfile:
            process = subprocess.Popen([inputs['dosbox'], '-nopromptfolder',
                '-conf', str(cfg)], cwd=cwd, stdout=logfile,
                stderr=subprocess.STDOUT, startupinfo=si,
                creationflags=subprocess.CREATE_NO_WINDOW)
            status['active'] = name
            status['active_pid'] = process.pid
            save()
            heartbeat = start
            while process.poll() is None and time.monotonic() < bound - 2:
                if time.monotonic() - heartbeat >= 15:
                    status['active'] = name
                    save()
                    heartbeat = time.monotonic()
                time.sleep(.2)
            result = {'name': name, 'exit_code': process.poll(),
                      'seconds': round(time.monotonic() - start, 3)}
            stop()
        status['runs'].append(result)
        save()
        if result['exit_code'] != 0:
            raise ValueError('Failed or exceeded bound: ' + name)
    try:
        lease.seek(0)
        msvcrt.locking(lease.fileno(), msvcrt.LK_NBLCK, 1)
        held = True
        start = time.monotonic()
        deadline = start + args.allocated_seconds
        status['acquired_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        save()
        builddir = out / 'BUILD'
        launch('BUILD', builddir / 'BUILD.CNF', builddir, min(deadline, start + 45))
        if (builddir / 'DONE.TXT').read_text().strip() != 'PASS':
            raise ValueError('Native compile failed; inspect BUILD.LOG')
        if any('warning' in line.lower() or 'error' in line.lower()
               for line in (builddir / 'BUILD.LOG').read_text().splitlines()):
            raise ValueError('Native compiler warnings/errors require repair')
        binary = bytearray((builddir / 'FONTPRB.EXE').read_bytes())
        ne = struct.unpack_from('<I', binary, 60)[0]
        if binary[ne:ne + 2] != b'NE' or struct.unpack_from('<H', binary, ne + 12)[0] & 8:
            raise ValueError('Not a real-mode-capable Win16 module')
        struct.pack_into('<H', binary, ne + 62, 0x300)
        for mode, entry in inputs['modes'].items():
            guest = out / mode / 'GUEST'
            (guest / 'FONTPRB.EXE').write_bytes(binary)
            launch(mode, out / mode / 'RUN.CNF', guest,
                   min(deadline, time.monotonic() + 35))
            if not (guest / 'RETURN.OK').exists():
                raise ValueError('No DOS return marker: ' + mode)
            log = (guest / 'FONT.LOG').read_text('latin1')
            if 'DONE=1' not in log:
                raise ValueError('Win16 probe incomplete: ' + mode)
            expected = next(r['font']['widths'] for item in json.loads(
                (HERE / 'CONTRACT.JSON').read_text()) if item['filename'] ==
                entry['family'] + 'SYS.FON' for r in item['resources'] if 'font' in r)
            widths = list(struct.unpack('<224H', (guest / 'WIDTHS.BIN').read_bytes()))
            if widths != expected:
                raise ValueError('Native character advances changed: ' + mode)
            textfile(out / mode / 'FONT.LOG', log)
            # Raw VRAM is a genuine emulator framebuffer. Decode through the
            # established BIOS bank formulas, label separately from host art.
            from PIL import Image
            syswidth = entry['width']
            modebios = entry['bios']
            palette = [(0,0,0), (0,0,170), (0,170,0), (0,170,170),
                (170,0,0), (170,0,170), (170,85,0), (170,170,170),
                (85,85,85), (85,85,255), (85,255,85), (85,255,255),
                (255,85,85), (255,85,255), (255,255,85), (255,255,255)]
            colorids = [0,12,10,15] if modebios == 10 else (
                [0,3,5,15] if modebios == 4 else [0,15])
            for snap in ('NORMAL', 'DIALOG'):
                raw = (guest / (snap + '.BIN')).read_bytes()
                pixels = []
                for y in range(200):
                    for x in range(syswidth):
                        if modebios == 10:
                            a = y % 4 * 8192 + y // 4 * 160 + x // 8 * 2
                            color = (raw[a] >> (7 - x % 8) & 1) | (
                                (raw[a + 1] >> (7 - x % 8) & 1) << 1)
                        else:
                            bits = 1 if modebios == 6 else 2 if modebios == 4 else 4
                            a = (y % (4 if modebios == 9 else 2) * 8192 +
                                y // (4 if modebios == 9 else 2) *
                                (160 if modebios == 9 else 80) + x // (8 // bits))
                            color = raw[a] >> ((8 // bits - 1 - x % (8 // bits)) * bits) & ((1 << bits) - 1)
                        pixels.append(palette[color if modebios in (8, 9) else colorids[color]])
                image = Image.new('RGB', (syswidth, 200))
                image.putdata(pixels)
                image.save(out / mode / (snap + '.PNG'))
        # This runner confirms completion, advances and saves screenshots.
        # Acceptance still needs native metric/glyph/menu/dialog review.
        status['status'] = 'COMPLETED; REVIEW METRICS/PIXELS/CLIPPING BEFORE ACCEPTANCE'
    except Exception as error:
        status['status'] = 'STOPPED: ' + repr(error)
        raise
    finally:
        stop()
        if held:
            lease.seek(0)
            msvcrt.locking(lease.fileno(), msvcrt.LK_UNLCK, 1)
            status['lease_seconds'] = round(time.monotonic() - start, 3)
            status['released_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        lease.close()
        status['remaining_conflicts'] = conflicts()
        status['active_pid'] = None
        save()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest='action', required=True)
    prep = sub.add_parser('prepare')
    for option in ('out', 'compiler', 'guest', 'fonts', 'dosbox'):
        prep.add_argument('--' + option, type=Path, required=True)
    execute = sub.add_parser('run')
    execute.add_argument('--out', type=Path, required=True)
    execute.add_argument('--lock', type=Path, required=True)
    execute.add_argument('--allocated-seconds', type=int, choices=range(60, 481), required=True)
    args = parser.parse_args()
    prepare(args) if args.action == 'prepare' else run(args)
