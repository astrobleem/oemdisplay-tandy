"""Prepare and run the next explicitly allocated private font sequence.

Preparation launches nothing. run needs an explicit bounded allocation,
refuses a busy shared lock, owns only its process, and releases in finally.
"""
import argparse
import datetime
import hashlib
import json
import re
import shutil
import struct
import subprocess
import time
from pathlib import Path
from BUILD import textfile
from NATIVE import config, conflicts
from ENCQA import validate as encoding_validate, emitted
from INSPECT import fontinfo
from NATIVEQA import metrics
from PINBUILD import main as pin_build

HERE = Path(__file__).resolve().parent


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}


def boot_key(ini, key, value):
    text = ini.read_text('latin1'); section = ''; count = 0; lines = []
    for line in text.splitlines():
        if line.strip().startswith('['):
            section = line.strip().lower()
        if section == '[boot]' and line.lower().startswith(key.lower() + '='):
            line = key + '=' + value; count += 1
        lines.append(line)
    if count != 1:
        raise ValueError('Missing/duplicate boot key: ' + key)
    ini.write_bytes(('\r\n'.join(lines) + '\r\n').encode('latin1'))


def prepare(args):
    out = args.out.resolve()
    if out.exists():
        raise ValueError('Choose a fresh private test directory')
    candidate, fonts = args.candidate.resolve(), args.fonts.resolve()
    sourceguest, installwin = args.fixture.resolve(), args.install_windows.resolve()
    compiler = args.compiler.resolve()
    out.mkdir(parents=True); build = out / 'BUILD'; build.mkdir()
    for name in ('FONENC.C', 'FONENC.DEF', 'FONTPRB.C', 'FONTPRB.DEF'):
        shutil.copyfile(HERE / name, build / name)
    for name in ('PREPXT.C', 'XTPINS.H', 'PACKPINS.H', 'SZSTREAM.H'):
        shutil.copyfile(candidate / 'tools/FLASHDISK' / name, build / name)
    shutil.copyfile(candidate / 'src/tandysw/TINST.C', build / 'TINST.C')
    batch = ['@ECHO OFF', r'PATH=T:\BIN', r'SET INCLUDE=T:\INCLUDE', r'SET LIB=T:\LIB']
    for src, output, flags in [('TINST', 'TINST', ''), ('TINST', 'TINSTD', '/DINSTALL_DIAGNOSTICS'),
                                ('PREPXT', 'PREPXT', ''), ('PREPXT', 'PREPD', '/DINSTALL_DIAGNOSTICS')]:
        batch += ['CL /nologo /c /G0 /AS /Od /W3 %s /Fo%s.OBJ %s.C >> BUILD.LOG' % (flags, output, src),
                  'IF ERRORLEVEL 1 GOTO FAIL',
                  r'LINK4 /NOE /NOD /ST:4096 %s.OBJ,%s.EXE,%s.MAP,T:\LIB\SLIBCE.LIB; >> BUILD.LOG' % (output, output, output),
                  'IF ERRORLEVEL 1 GOTO FAIL']
    batch += [r'SET INCLUDE=T:\DDK\286\INC;T:\INCLUDE']
    for name in ('FONENC', 'FONTPRB'):
        batch += ['CL /nologo /c /G0 /Gw /AS /Od /W3 %s.C >> BUILD.LOG' % name,
                  'IF ERRORLEVEL 1 GOTO FAIL',
                  r'LINK4 /NOE /NOD %s.OBJ,%s.EXE,%s.MAP,T:\LIB\SLIBCEW.LIB T:\LIB\LIBW.LIB,%s.DEF; >> BUILD.LOG' % (name, name, name, name),
                  'IF ERRORLEVEL 1 GOTO FAIL']
    batch += ['ECHO SUCCESS>>BUILD.LOG', 'GOTO END', ':FAIL', 'ECHO FAILED>>BUILD.LOG', ':END', 'EXIT']
    textfile(build / 'BUILD.BAT', '\n'.join(batch) + '\n')
    rebuild = ['@ECHO OFF', r'PATH=T:\BIN', r'SET INCLUDE=T:\INCLUDE', r'SET LIB=T:\LIB']
    for output, flags in [('PREPXT', ''), ('PREPD', '/DINSTALL_DIAGNOSTICS')]:
        rebuild += ['CL /nologo /c /G0 /AS /Od /W3 %s /Fo%s.OBJ PREPXT.C >> REBUILD.LOG' % (flags, output),
                    'IF ERRORLEVEL 1 GOTO FAIL',
                    r'LINK4 /NOE /NOD /ST:4096 %s.OBJ,%s.EXE,%s.MAP,T:\LIB\SLIBCE.LIB; >> REBUILD.LOG' % (output, output, output),
                    'IF ERRORLEVEL 1 GOTO FAIL']
    rebuild += ['ECHO SUCCESS>>REBUILD.LOG', 'GOTO END', ':FAIL', 'ECHO FAILED>>REBUILD.LOG', ':END', 'EXIT']
    textfile(build / 'REBUILD.BAT', '\n'.join(rebuild) + '\n')
    for name in ('BUILD', 'REBUILD'):
        textfile(build / (name + '.CNF'), config([('T', compiler), ('D', build)], 'D:\n' + name + '.BAT\n', build))
    cases = {'CGA': ('TR56402.DRV', 'CGA', 'FONENC', 6, 640),
             'EGA': ('TR53216.DRV', 'EGA', 'FONENC', 9, 320),
             'TXFONT': ('TR56402.DRV', 'TXT', 'FONENC', 6, 640),
             'B160': ('TR51616.DRV', 'CGA', 'FONTPRB', 8, 160),
             'TXMODE': ('TXTMODE.DRV', 'TXT', 'FONENC', 3, 640)}
    report = {'kind': 'Prepared private next sequence; no guest launched', 'candidate': str(candidate),
              'fonts': str(fonts), 'compiler': str(compiler), 'dosbox': str(args.dosbox.resolve()), 'cases': {}}
    needed = ['BIN/CL.EXE', 'BIN/C1.EXE', 'BIN/C2.EXE', 'BIN/C3.EXE', 'BIN/LINK4.EXE',
              'LIB/SLIBCE.LIB', 'LIB/SLIBCEW.LIB', 'LIB/LIBW.LIB', 'DDK/286/INC/WINDOWS.H', 'INCLUDE/STRING.H']
    report['compiler_sha256'] = {n: sha(compiler / n) for n in needed}
    for name, (driver, family, probe, bios, width) in cases.items():
        case = out / name; guest = case / 'GUEST'; guest.mkdir(parents=True)
        shutil.copytree(sourceguest / 'WINDOWS', guest / 'WINDOWS')
        target = guest / 'WINDOWS/SYSTEM'
        for font in ('CGASYS', 'CGAFIX', 'CGAOEM', 'EGASYS', 'EGAFIX', 'EGAOEM', 'TXTSYS'):
            shutil.copyfile(fonts / (font + '.FON'), target / (font + '.FON'))
        if name == 'B160':
            # This case deliberately produces only UI/geometry, not an atlas
            # of Microsoft glyphs. Original font media never enters output kit.
            for font in ('CGASYS', 'CGAFIX', 'CGAOEM'):
                shutil.copyfile(sourceguest / 'WINDOWS/SYSTEM' / (font + '.FON'), target / (font + '.FON'))
        shutil.copyfile(candidate / 'distributions/WINXT' / driver, target / driver)
        shutil.copyfile(candidate / 'distributions/WINXT/RESERVE.COM', guest / 'RESERVE.COM')
        ini = guest / 'WINDOWS/SYSTEM.INI'
        for key, value in [('display.drv', driver), ('fonts.fon', 'TXTSYS.FON' if family == 'TXT' else family + 'SYS.FON'),
                           ('fixedfon.fon', ('CGA' if family == 'TXT' else family) + 'FIX.FON'),
                           ('oemfonts.fon', ('CGA' if family == 'TXT' else family) + 'OEM.FON'),
                           ('shell', 'C:\\' + probe + '.EXE')]:
            boot_key(ini, key, value)
        # Only copies are changed. Clear copied probe artifacts if present.
        for p in guest.iterdir():
            if p.is_file() and p.name in ('FONT.LOG', 'RETURN.OK', 'FONENC.LOG', 'NORMAL.BIN', 'DIALOG.BIN'):
                p.unlink()
        textfile(guest / 'START.BAT', '@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\n'
                 'SET TEMP=C:\\WINDOWS\\TEMP\nC:\nRESERVE > C:\\RESERVE.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
                 'CD \\WINDOWS\nWIN /R > C:\\WIN.LOG\nECHO RETURNED>C:\\RETURN.OK\nGOTO END\n'
                 ':FAIL\nECHO RESERVATION_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n')
        textfile(case / 'RUN.CNF', config([('C', guest)], 'C:\nSTART.BAT\n', guest, True))
        report['cases'][name] = {'driver': driver, 'family': family, 'probe': probe, 'bios': bios, 'width': width}
    # A fresh clean Windows installation fixture for actual DOS Setup and rollback.
    guest = out / 'INSTALL/GUEST'; guest.mkdir(parents=True)
    shutil.copytree(installwin, guest / 'WINDOWS')
    boot_key(guest / 'WINDOWS/SYSTEM.INI', 'shell', 'C:\\FONTPRB.EXE')
    (guest / 'MEDIA').mkdir(); (guest / 'SOURCEOS/SYSTEM').mkdir(parents=True)
    # PREPXT receives a directory with NO Windows font files, only empty SYSTEM.
    for name in ('CGA.GR2', 'CGALOGO.LGO'):
        shutil.copyfile(guest / 'WINDOWS/SYSTEM' / name, guest / 'MEDIA' / name)
    textfile(guest / 'YES.TXT', 'Y\n')
    textfile(guest / 'CONFIG.SYS', 'FILES=30\nBUFFERS=20\n')
    textfile(guest / 'AUTOEXEC.BAT', '@ECHO OFF\n')
    original = args.autotype_from.read_text('ascii')
    autotype = next(line for line in original.splitlines() if line.startswith('AUTOTYPE '))
    start = ('@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nC:\n'
             'D:\\PREPD A:\\WINXT C:\\SOURCEOS C:\\MEDIA < C:\\YES.TXT > C:\\PREP.LOG\n'
             'IF ERRORLEVEL 1 GOTO FAIL\nIF NOT EXIST C:\\WINXT\\INSTALL.BAT GOTO FAIL\n'
             'ECHO PREPARATION_COMMITTED>C:\\PREP.OK\nCD \\WINXT\n'
             'D:\\TINSTD C:\\WINDOWS > C:\\INSTALL.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
             'IF NOT EXIST C:\\WINXT\\READY.TAG GOTO FAIL\nECHO INSTALLER_COMMITTED>C:\\INST.OK\n'
             + autotype + '\nCD \\WINDOWS\nCOMMAND.COM /C C:\\WINXT\\WINXT.BAT SETUP > C:\\SETUP.LOG\n'
             'ECHO SETUP_RETURNED>C:\\SETUP.OK\nCOMMAND.COM /C C:\\WINXT\\WINXT.BAT > C:\\WIN.LOG\n'
             'IF NOT EXIST C:\\FONT.LOG GOTO FAIL\nECHO COLD_GUI_RETURNED>C:\\GUI.OK\n'
             'COMMAND.COM /C C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES > C:\\ROLLBACK.LOG\n'
             'IF ERRORLEVEL 1 GOTO FAIL\nECHO ROLLBACK_RETURNED>C:\\ROLL.OK\n'
             'ECHO COMPLETE>C:\\DONE.OK\nGOTO END\n:FAIL\nECHO INSTALL_SEQUENCE>C:\\FAIL.TXT\n:END\nEXIT\n')
    textfile(guest / 'START.BAT', start)
    report['install_original_windows_sha256'] = files(guest / 'WINDOWS')
    report['install_original_boot_sha256'] = {n: sha(guest / n) for n in ('CONFIG.SYS', 'AUTOEXEC.BAT')}
    # IMAGE is filled only after reviewed compiler output and host package checks.
    cfg = config([('C', guest), ('D', build)], '', guest, True)
    cfg += 'IMGMOUNT A "' + str(out / 'PACKAGE/WINXT720.IMG') + '" -T FLOPPY\nC:\nSTART.BAT\n'
    textfile(out / 'INSTALL/RUN.CNF', cfg)
    textfile(out / 'INPUTS.JSON', json.dumps(report, indent=2) + '\n')
    print('PREPARED ONLY:', out)


def run(args):
    import msvcrt
    out = args.out.resolve(); inputs = json.loads((out / 'INPUTS.JSON').read_text())
    for name, expected in inputs['compiler_sha256'].items():
        if sha(Path(inputs['compiler']) / name) != expected:
            raise ValueError('Approved compiler input changed: ' + name)
    if conflicts():
        raise ValueError('Another emulator is running')
    lock = args.lock.open('rb'); held = False; process = None
    status = {'allocation_seconds': args.allocated_seconds, 'runs': [], 'native_package_qualified': False}
    def save():
        textfile(out / 'STATUS.JSON', json.dumps(status, indent=2) + '\n')
        print(json.dumps(status), flush=True)
    def stop():
        nonlocal process
        if process is not None and process.poll() is None:
            process.terminate()
            try: process.wait(timeout=2)
            except subprocess.TimeoutExpired: process.kill(); process.wait(timeout=2)
        process = None
    def launch(name, cfg, cwd, seconds):
        nonlocal process
        if conflicts(): raise ValueError('Conflict before ' + name)
        if deadline - time.monotonic() < 10: raise ValueError('Allocation exhausted before ' + name)
        start = time.monotonic(); bound = min(deadline - 3, start + seconds)
        si = subprocess.STARTUPINFO(); si.dwFlags |= subprocess.STARTF_USESHOWWINDOW; si.wShowWindow = 0
        with (out / (name + '.HOST.LOG')).open('wb') as log:
            process = subprocess.Popen([inputs['dosbox'], '-nopromptfolder', '-conf', str(cfg)], cwd=cwd,
                stdout=log, stderr=subprocess.STDOUT, startupinfo=si, creationflags=subprocess.CREATE_NO_WINDOW)
            status['active'] = name; status['active_pid'] = process.pid; save(); beat = start
            while process.poll() is None and time.monotonic() < bound:
                if time.monotonic() - beat > 15: save(); beat = time.monotonic()
                time.sleep(.2)
            result = {'name': name, 'exit_code': process.poll(), 'seconds': round(time.monotonic() - start, 3)}
            stop()
        status['runs'].append(result); save()
        if result['exit_code'] != 0: raise ValueError('Failed or exceeded bound: ' + name)
    try:
        msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1); held = True
        began = time.monotonic(); deadline = began + args.allocated_seconds
        if args.deadline_utc:
            absolute = datetime.datetime.fromisoformat(args.deadline_utc)
            deadline = min(deadline, began + (absolute - datetime.datetime.now(datetime.timezone.utc)).total_seconds())
        status['acquired_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat(); save()
        build = out / 'BUILD'; candidate = Path(inputs['candidate'])
        if not args.skip_build: launch('BUILD', build / 'BUILD.CNF', build, 70)
        pin_build(argparse.Namespace(candidate=candidate, build=build))
        if not (candidate / 'tools/FLASHDISK/HELPER.SHA').exists():
            shutil.copyfile(candidate / 'tools/FLASHDISK/XTPINS.H', build / 'XTPINS.H')
            launch('REBUILD', build / 'REBUILD.CNF', build, 25)
            # The full log establishes all other builds; include second build's diagnostics.
            with (build / 'BUILD.LOG').open('ab') as log: log.write((build / 'REBUILD.LOG').read_bytes())
            pin_build(argparse.Namespace(candidate=candidate, build=build))
        for name in ('FONENC', 'FONTPRB'):
            binary = bytearray((build / (name + '.EXE')).read_bytes()); ne = struct.unpack_from('<I', binary, 60)[0]
            if binary[ne:ne + 2] != b'NE' or struct.unpack_from('<H', binary, ne + 12)[0] & 8:
                raise ValueError('Probe is not a real-mode-capable NE')
            struct.pack_into('<H', binary, ne + 62, 0x300)
            (build / (name + '.EXE')).write_bytes(binary)
        for name, entry in inputs['cases'].items():
            guest = out / name / 'GUEST'
            shutil.copyfile(build / (entry['probe'] + '.EXE'), guest / (entry['probe'] + '.EXE'))
            launch(name, out / name / 'RUN.CNF', guest, 45)
            if name == 'B160':
                baseline = (guest / 'FONT.LOG').read_text('latin1')
                prior = args.prior_native / 'C160/FONT.LOG'
                previous = prior.read_text('latin1')
                fields = ('DIALOG_BASE', 'DIALOG_LEFT', 'DIALOG_RIGHT', 'DIALOG_BOTTOM', 'DIALOG_SCREEN_OVERFLOW',
                          'CANCEL_TEXT_WIDTH', 'CANCEL_CLIENT_WIDTH')
                def geometry(text):
                    values = dict(l.split('=', 1) for l in text.splitlines() if '=' in l)
                    return {k: int(values[k]) for k in fields}
                comparison = {'baseline': geometry(baseline), 'original_font_candidate': geometry(previous),
                              'stock_metric_match': metrics(baseline) == metrics(previous)}
                comparison['same_geometry'] = comparison['baseline'] == comparison['original_font_candidate']
                if 'DONE=1' not in baseline or not comparison['same_geometry'] or not comparison['stock_metric_match']:
                    raise ValueError('Baseline 160 geometry differs; investigate before accepting')
                textfile(out / 'BASE160.JSON', json.dumps(comparison, indent=2) + '\n')
            elif name == 'TXMODE':
                log = (guest / 'FONENC.LOG').read_text('latin1')
                if 'DONE=1' not in log or log.count('WIDTH_QUERY=1') != 3:
                    raise ValueError('Experimental text-mode font probe incomplete')
                textfile(out / 'TXMODE.JSON', json.dumps({'font_probe_completed': True,
                    'native_text_renderer_pixels_qualified': False,
                    'reason': 'Hardware text renderer uses BIOS cells; inspect semantic cells separately from FON bitmaps',
                    'stock_metrics': metrics(log)}, indent=2) + '\n')
            else:
                encoding_validate(guest, Path(inputs['fonts']), entry['family'], entry['bios'], entry['width'])
        # Host package work between guests stays within the same allocation.
        package = out / 'PACKAGE'
        command = ['python', str(candidate / 'tools/FLASHDISK/MAKEIMG.PY'), '--runtime',
                   str(candidate / 'distributions/WINXT'), '--out', str(package)]
        result = subprocess.run(command, capture_output=True, text=True, timeout=min(60, max(1, deadline - time.monotonic() - 3)))
        textfile(out / 'PACKAGE.LOG', result.stdout + result.stderr)
        if result.returncode: raise ValueError('Host package build failed: ' + result.stderr)
        status['host_image_built'] = True; save()
        guest = out / 'INSTALL/GUEST'
        shutil.copyfile(build / 'FONTPRB.EXE', guest / 'FONTPRB.EXE')
        launch('INSTALL', out / 'INSTALL/RUN.CNF', guest, 160)
        if (guest / 'FAIL.TXT').exists() or not all((guest / n).exists() for n in
                ('PREP.OK', 'INST.OK', 'SETUP.OK', 'GUI.OK', 'ROLL.OK', 'DONE.OK')):
            raise ValueError('Incomplete preparation/Setup/GUI/rollback sequence')
        # Every pre-existing Windows resource and both boot files must restore exactly.
        changed = [n for n, h in inputs['install_original_windows_sha256'].items()
                   if not (guest / 'WINDOWS' / n).is_file() or sha(guest / 'WINDOWS' / n) != h]
        if changed: raise ValueError('Rollback changed originals: ' + str(changed))
        for name, h in inputs['install_original_boot_sha256'].items():
            if sha(guest / name) != h: raise ValueError('Boot configuration changed')
        prep = (guest / 'PREP.LOG').read_text('latin1'); install = (guest / 'INSTALL.LOG').read_text('latin1')
        if not re.search(r'SHA blocks=0', prep) or 'compared=0' not in install:
            raise ValueError('Default diagnostic counters do not prove zero deep work')
        status['installation_sequence_and_original_rollback_passed'] = True
        status['status'] = 'COMPLETED; inspect Setup-selected font/driver and cold GUI evidence before acceptance'
    except Exception as error:
        status['status'] = 'STOPPED: ' + repr(error); raise
    finally:
        stop()
        if held:
            lock.seek(0); msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            status['held_seconds'] = round(time.monotonic() - began, 3)
            status['released_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
        lock.close(); status['active_pid'] = None; status['remaining_conflicts'] = conflicts(); save()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); actions = p.add_subparsers(dest='action', required=True)
    prep = actions.add_parser('prepare')
    for option in ('out', 'candidate', 'fonts', 'fixture', 'install-windows', 'compiler', 'dosbox', 'autotype-from'):
        prep.add_argument('--' + option, type=Path, required=True)
    execute = actions.add_parser('run')
    execute.add_argument('--out', type=Path, required=True); execute.add_argument('--lock', type=Path, required=True)
    execute.add_argument('--prior-native', type=Path, required=True)
    execute.add_argument('--skip-build', action='store_true')
    execute.add_argument('--deadline-utc')
    execute.add_argument('--allocated-seconds', type=int, choices=range(60, 481), required=True)
    args = p.parse_args(); prepare(args) if args.action == 'prepare' else run(args)
