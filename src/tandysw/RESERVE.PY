#!/usr/bin/env python3
"""Build and exercise RESERVE.COM with actual DOS allocations in DOSBox-X.

No Windows/media or expanded base memory needed. Every case has its own DOS
boot. Logs are bounded to 64KiB and each emulator invocation has a timeout.
"""
from pathlib import Path
import argparse
import hashlib
import json
import os
import re
import selectors
import shutil
import struct
import subprocess
import time

HERE = Path(__file__).resolve().parent
FIELDS = ('bda_kb first_mcb last_mcb arena_end last_owner last_size last_type '
          'strategy block_count probe_psp alloc_segment alloc_size alloc_end '
          'alias_verified mcb_verified owner_open_handles').split()


def dos_text(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def run_dos(dosbox, repo, directory, batch, machine='tandy', expanded=False, version='3.30', cpu='8086'):
    config = directory / 'RUN.CONF'
    dos_text(config, f'''[sdl]
fullscreen=false
output=surface
[dosbox]
machine={machine}
allow more than 640kb base memory={'true' if expanded else 'false'}
memsize=16
working directory option=force
working directory default={directory}
[cpu]
core=normal
cputype={cpu}
cycles=fixed 30000
[mixer]
nosound=true
[midi]
mididevice=none
[dos]
xms=false
ems=false
umb=false
ver={version}
[autoexec]
@echo off
mount C "{repo}"
mount R "{directory}"
R:
{batch}
''')
    env = dict(os.environ, SDL_VIDEODRIVER='dummy', SDL_AUDIODRIVER='dummy')
    process = subprocess.Popen([str(dosbox), '-nopromptfolder', '-conf', str(config)],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env)
    assert process.stdout is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    deadline = time.monotonic() + 60
    total = 0
    try:
        with (directory / 'HOST.LOG').open('wb') as log:
            while selector.get_map():
                if time.monotonic() > deadline:
                    raise TimeoutError(f'DOSBox timed out in {directory}')
                for key, _ in selector.select(0.25):
                    data = os.read(key.fileobj.fileno(), 8192)
                    if not data:
                        selector.unregister(key.fileobj)
                        break
                    if total < 65536:
                        log.write(data[:65536-total])
                    total += len(data)
        if process.wait(timeout=2):
            raise RuntimeError(f'DOSBox failed in {directory}')
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        selector.close()
        process.stdout.close()
    host = (directory / 'HOST.LOG').read_text(errors='replace')
    if '8086 cpu type' not in host or 'is not a valid value' in host:
        raise RuntimeError(f'8086 CPU configuration not confirmed in {directory}')


def captured(command, label):
    return (f'{command} > {label}.TXT\nIF ERRORLEVEL 1 GOTO E{label}\n'
            f'ECHO 0> {label}.RET\nGOTO N{label}\n:E{label}\n'
            f'ECHO 1> {label}.RET\n:N{label}\n')


def snapshot(label):
    return captured('RESERVET S', label) + f'COPY SNAP.BIN {label}.BIN > NUL\n'


def report(directory, label):
    data = (directory / (label + '.BIN')).read_bytes()
    return dict(zip(FIELDS, struct.unpack('<16H', data)))


def returned(directory, label):
    return int((directory / (label + '.RET')).read_text().strip())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=HERE.parents[1])
    parser.add_argument('--dosbox', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cpu', choices=('8086', '8086_prefetch'), default='8086')
    args = parser.parse_args()
    repo, dosbox, out = args.repo.resolve(), args.dosbox.resolve(), args.out.resolve()
    if out.exists():
        parser.error('--out must name a new directory')
    if shutil.disk_usage(out.parent).free < 32 * 1024 * 1024:
        raise RuntimeError('Need at least 32MB free space')
    out.mkdir(parents=True)
    for name in ('RESERVE.ASM', 'RESERVET.ASM'):
        shutil.copyfile(HERE / name, out / name)
    commands = '@ECHO OFF\n'
    for name in ('RESERVE', 'RESERVET'):
        commands += (f'C:\\BIN\\MASM {name}.ASM,{name}.OBJ,{name}.LST; >> BUILD.LOG\n'
                     f'C:\\BIN\\LINK {name}.OBJ,{name}.EXE,{name}.MAP; >> BUILD.LOG\n'
                     f'C:\\DDK\\TOOLS\\EXE2BIN {name}.EXE {name}.COM >> BUILD.LOG\n')
    dos_text(out / 'BUILD.BAT', commands + 'EXIT\n')
    run_dos(dosbox, repo, out, 'BUILD.BAT', cpu=args.cpu)
    log = (out / 'BUILD.LOG').read_text(errors='replace')
    severe = re.findall(r'(\d+)\s+Severe\s+Errors', log)
    if severe != ['0', '0'] or re.search(r'error [AL]\d+|fatal error', log, re.I):
        raise RuntimeError('Assembly/link failed; inspect BUILD.LOG')
    for name in ('RESERVE', 'RESERVET'):
        if not (out / (name + '.COM')).is_file():
            raise RuntimeError('Missing ' + name + '.COM')

    checks = []
    details = {}

    def check(name, condition):
        if not condition:
            raise AssertionError(name)
        checks.append(name)

    def case(name, commands, **settings):
        directory = out / name
        directory.mkdir()
        for binary in ('RESERVE.COM', 'RESERVET.COM'):
            shutil.copyfile(out / binary, directory / binary)
        dos_text(directory / 'TEST.BAT', '@ECHO OFF\n' + commands + 'EXIT\n')
        run_dos(dosbox, repo, directory, 'TEST.BAT', cpu=args.cpu, **settings)
        return directory

    normal = case('normal', snapshot('BEFORE') + captured('RESERVE', 'INSTALL') +
                  snapshot('AFTER') + captured('RESERVE', 'AGAIN') + snapshot('TWICE') +
                  captured('RESERVET P', 'PROBE') + 'COPY SNAP.BIN PROBE.BIN > NUL\n' +
                  captured('RESERVE', 'POSTVID') + snapshot('FINAL'))
    before, after, twice, probe, final = [report(normal, x) for x in
                                        ('BEFORE', 'AFTER', 'TWICE', 'PROBE', 'FINAL')]
    details['normal'] = dict(before=before, after=after, twice=twice, probe=probe, final=final)
    check('normal 640K installs successfully', returned(normal, 'INSTALL') == 0)
    check('BIOS 624K remains unchanged', before['bda_kb'] == after['bda_kb'] == 624)
    check('real conventional DOS arena ends at 9C00h', before['arena_end'] == after['arena_end'] == 0x9c00)
    check('video allocation has safe 97FFh MCB and 0400h paragraphs',
          after['last_mcb'] == 0x97ff and after['last_size'] == 0x400 and
          after['last_type'] & 255 == ord('Z') and after['last_owner'] != 0)
    check('resident closes inherited handles including redirected stdout', after['owner_open_handles'] == 0)
    check('repeated invocation succeeds without a second TSR',
          returned(normal, 'AGAIN') == 0 and after == twice and
          'already installed' in (normal / 'AGAIN.TXT').read_text())
    check('maximum real DOS allocation ends below video and its MCB',
          returned(normal, 'PROBE') == 0 and probe['alloc_end'] == 0x97ff)
    check('mode 09 full 32KB write really aliases physical 9800h', probe['alias_verified'] == 1)
    check('DOS allocation guard and video MCB survive video overwrite', probe['mcb_verified'] == 1)
    check('reservation survives return to text mode and re-invocation',
          returned(normal, 'POSTVID') == 0 and after == final)

    for strategy in (0, 1, 2):
        directory = case('strategy' + str(strategy),
                         captured('RESERVET ' + str(strategy + 1), 'SET') +
                         captured('RESERVE', 'INSTALL') + snapshot('AFTER') +
                         captured('RESERVET P', 'PROBE') + 'COPY SNAP.BIN PROBE.BIN > NUL\n')
        state = report(directory, 'AFTER')
        details['strategy' + str(strategy)] = state
        check(f'preserve allocation strategy {strategy}', returned(directory, 'INSTALL') == 0 and
              state['strategy'] == strategy and state['last_mcb'] == 0x97ff)
        check(f'video and DOS allocation survive with strategy {strategy}', returned(directory, 'PROBE') == 0)

    for name, setup in (('occupied', 'RESERVET O'), ('occupied_exact', 'RESERVET T')):
        directory = case(name, captured(setup, 'SETUP') + snapshot('BEFORE') +
                         captured('RESERVE', 'INSTALL') + snapshot('AFTER'))
        before, after = report(directory, 'BEFORE'), report(directory, 'AFTER')
        details[name] = dict(before=before, after=after)
        stable = ('last_mcb', 'last_owner', 'last_size', 'arena_end', 'bda_kb', 'strategy')
        check(name + ' fails without taking another owner\'s memory', returned(directory, 'SETUP') == 0 and
              returned(directory, 'INSTALL') == 1 and
              all(before[k] == after[k] for k in stable) and
              'already occupied' in (directory / 'INSTALL.TXT').read_text())

    for name, setup, settings in (
            ('short_arena', 'RESERVET A\n', {}),
            ('wrong_bda', 'RESERVET B\n', {}),
            ('wrong_mode', 'RESERVET M\n', {}),
            ('expanded', '', dict(expanded=True)),
            ('cga', '', dict(machine='cga')),
            ('dos2', '', dict(version='2.11'))):
        directory = case(name, setup + captured('RESERVE', 'INSTALL') + snapshot('AFTER'), **settings)
        state = report(directory, 'AFTER')
        details[name] = state
        check(name + ' fails closed', returned(directory, 'INSTALL') == 1 and
              state['last_owner'] == 0 and 'No reservation' in (directory / 'INSTALL.TXT').read_text())

    result = dict(status='PASS', tests=len(checks), checks=checks, details=details,
                  cpu=f'DOSBox-X cputype={args.cpu}, configured core=normal; not cycle-accurate hardware',
                  normal_memory='640K physical, BIOS 624K, expanded base memory disabled',
                  reserve_bytes=(out / 'RESERVE.COM').stat().st_size,
                  reserve_sha256=hashlib.sha256((out / 'RESERVE.COM').read_bytes()).hexdigest())
    (out / 'RESULT.JSON').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: result[k] for k in ('status', 'tests', 'reserve_bytes', 'reserve_sha256')}))


if __name__ == '__main__':
    main()
