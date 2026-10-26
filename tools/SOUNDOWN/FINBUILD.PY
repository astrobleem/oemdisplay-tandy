"""Rebuild current XR1 finisher using external C6 and the shared lease."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
from importlib.machinery import SourceFileLoader
import json
import shutil

HERE = Path(__file__).resolve().parent
SOURCES = ('FIXXT.C', 'FIXXT.RSP', 'BLDFIX.BAT', 'SOUNDID.H', 'HPXYID.H')


def identity(path):
    data = path.read_bytes()
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dosbox', required=True, type=Path)
    parser.add_argument('--toolchain', required=True, type=Path)
    parser.add_argument('--lease', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    tool, out = args.toolchain.resolve(), args.out.resolve()
    for name in ('BIN/CL.EXE', 'BIN/LINK4.EXE', 'LIB/SLIBCE.LIB'):
        if not (tool / name).is_file():
            parser.error('Missing external toolchain file: ' + name)
    out.mkdir(parents=True, exist_ok=False)
    for name in SOURCES:
        source = HERE.parent/'DOSINST'/name if name in ('FIXXT.C', 'SOUNDID.H', 'HPXYID.H') else HERE/name
        shutil.copyfile(source, out/name)
    config = f'''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
memsize=1
working directory option=force
working directory default={out}
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
[midi]
mididevice=none
[autoexec]
@echo off
mount C "{tool}" -ro
mount D "{out}"
D:
BLDFIX.BAT
exit
'''
    (out / 'BUILD.CNF').write_text(config)
    runpath = HERE / 'RUNDOS.PY'
    spec = importlib.util.spec_from_loader('setup_rundos',
        SourceFileLoader('setup_rundos', str(runpath)))
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    runner.run(args.dosbox, out / 'BUILD.CNF', args.lease, 60)
    log = (out / 'BUILD.LOG').read_text(errors='replace')
    if 'PASS' not in log or 'FAIL' in log:
        raise RuntimeError('Installer build failed; inspect BUILD.LOG')
    names = SOURCES
    record = {'target': 'DOS3+, MSC6 /G0 /AS, LINK4, 8086, 8KB stack',
              'sources': {name: identity(out / name) for name in names},
              'runtime': identity(out / 'FIXXT.EXE')}
    (out / 'BUILD.JSON').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(record, indent=2))


if __name__ == '__main__':
    main()
