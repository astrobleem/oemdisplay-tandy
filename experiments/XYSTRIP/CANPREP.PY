"""Bounded normal SETUP fresh/update preparation and full finisher acceptance."""
from pathlib import Path
import importlib.machinery
import hashlib
import json
import re
import shutil
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration'
OLD = Path(r'C:\Users\chad\Documents\Codex\2026-10-24\task\wdesk-install-native-02')
MEDIA = Path(r'C:\Users\chad\Documents\Codex\2026-10-24\task\panui-install-native-01\MEDIA')
STAGE = OUT / 'canonical-stage'
LEASE = Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock')
DOSBOX = Path(r'C:\Program Files\DOSBox-X\dosbox-x.exe')


def run(case):
    archive_before = (OUT / 'CANONICAL.ZIP').read_bytes()
    archive_pin = dict(bytes=len(archive_before), sha256=hashlib.sha256(archive_before).hexdigest())
    tested = {}
    for name in ('SETUP.EXE', 'WINXT/FIXXT.EXE', 'WINXT/HPXY.DRV'):
        data = (STAGE / name).read_bytes()
        tested[name] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    out = OUT / ('canonical-' + case)
    out.mkdir(exist_ok=False)
    croot = out / 'CROOT'
    croot.mkdir()
    if case == 'update':
        shutil.copytree(OLD / 'UPDATE/CROOT/WINDOWS', croot / 'WINDOWS')
    target = 'E:\\' if case == 'fresh' else 'C:\\WINDOWS'
    batch = ('@ECHO OFF\nD:\\SETUP ' + case.upper() + ' ' + target +
             ' /PREP > C:\\PREP.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n')
    if case == 'update':
        batch += ('C:\\WINXT\\FIXXT INSTALL C:\\WINDOWS C:\\WINXT /XR1 /VERIFY > C:\\FINISH.LOG\n'
                  'IF ERRORLEVEL 1 GOTO FAIL\n'
                  'C:\\WINXT\\CPSET APPLY C:\\WINDOWS /VERIFY >> C:\\FINISH.LOG\n'
                  'IF ERRORLEVEL 1 GOTO FAIL\n'
                  'C:\\WINXT\\FIXXT CHECK C:\\WINDOWS C:\\WINXT /VERIFY >> C:\\FINISH.LOG\n'
                  'IF ERRORLEVEL 1 GOTO FAIL\n')
    batch += ('ECHO PASS > C:\\ACCEPT.OK\nGOTO DONE\n:FAIL\n'
              'ECHO FAIL > C:\\ACCEPT.ERR\n:DONE\nEXIT\n')
    (out / 'RUN.BAT').write_bytes(batch.replace('\n', '\r\n').encode('ascii'))
    config = '''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=1
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 200000
fpu=false
[dos]
xms=false
ems=false
umb=false
[mixer]
nosound=true
[autoexec]
@ECHO OFF
MOUNT C "{croot}"
MOUNT D "{stage}" -ro
MOUNT E "{media}" -ro
MOUNT F "{out}" -ro
C:
F:\RUN.BAT
'''.format(croot=croot, stage=STAGE, media=MEDIA, out=out)
    (out / 'RUN.CNF').write_bytes(config.replace('\n', '\r\n').encode('ascii'))
    runner = importlib.machinery.SourceFileLoader('canon_rundos',
        str(ROOT / 'tools/SOUNDOWN/RUNDOS.PY')).load_module()
    p = runner.run(DOSBOX, out / 'RUN.CNF', LEASE, 120)
    assert (croot / 'ACCEPT.OK').is_file() and not (croot / 'ACCEPT.ERR').exists(), 'Inspect retained guest logs'
    rows = re.findall(r'\{"([^"\n]+)","([^"\n]+)",(\d+)UL,(\d+)\}',
                      (ROOT / 'tools/DOSINST/SETFILES.H').read_text())
    differences = []
    count = 0
    for path, source, size, kind in rows:
        if case == 'update' and path.startswith('W30\\'):
            continue
        path = path.replace('\\\\', '/')
        actual = (croot / path).read_bytes()
        expected = ((STAGE / 'WINXT' / source).read_bytes() if kind == '0' else
                    (OLD / 'FRESH/CROOT' / path).read_bytes())
        if actual != expected or len(actual) != int(size):
            differences.append(path)
        count += 1
    assert count == (370 if case == 'fresh' else 83) and not differences, differences
    if case == 'update':
        assert (croot / 'WINDOWS/SYSTEM/HPXY.DRV').read_bytes() == (STAGE / 'WINXT/HPXY.DRV').read_bytes()
        assert (croot / 'WINXT/XYCTL.EXE').read_bytes() == (STAGE / 'WINXT/XYCTL.EXE').read_bytes()
    result = dict(complete=True, owned_stopped=p['owned_child_stopped'],
        lease_released=p['lease_released'], process=p,
        prepared_comparison=dict(count=count, different=differences),
        scope='DOSBox native preparation' + (' plus full INSTALL/CPSET/CHECK finisher' if case == 'update' else ''),
        full_finisher_complete=case == 'update', physical_hardware=False)
    assert (OUT / 'CANONICAL.ZIP').read_bytes() == archive_before
    for name, pin in tested.items():
        data = (STAGE / name).read_bytes()
        assert dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest()) == pin
    result.update(archive=archive_pin, tested_inputs=tested)
    if case == 'update':
        for key, name in (('installed_driver', 'WINDOWS/SYSTEM/HPXY.DRV'), ('installed_helper', 'WINXT/XYCTL.EXE')):
            data = (croot / name).read_bytes()
            result[key] = dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    (out / 'RESULT.JSN').write_bytes((json.dumps(result, indent=2) + '\r\n').encode('ascii'))
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    run(sys.argv[1])
