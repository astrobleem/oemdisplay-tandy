"""Stage the qualified HPXY runtime in the single normal package producer."""
from pathlib import Path
import hashlib
import importlib.machinery
import json
import shutil
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration'
HERE = ROOT / 'tools/DOSINST'
QUAL = ROOT / 'docs/QUAL/HPXY'


def identity(data):
    return dict(bytes=len(data), sha256=hashlib.sha256(data).hexdigest())


def save(path, value):
    path.write_bytes((json.dumps(value, indent=2) + '\n').replace('\n', '\r\n').encode('ascii'))


def module(name):
    return importlib.machinery.SourceFileLoader(name, str(HERE / (name + '.PY'))).load_module()


def runtime():
    QUAL.mkdir(parents=True, exist_ok=True)
    integration = json.loads((OUT / 'INTEGRATION.JSN').read_bytes())
    shutil.copyfile(OUT / 'candidate-build/HPXY.DRV', HERE / 'BIN/HPXY.DRV')
    save(QUAL / 'BUILD.JSN', integration['builds']['candidate']['receipt'])
    with zipfile.ZipFile(QUAL / 'WINDOWS.ZIP', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for leaf in ('INTEGRATION.JSN', 'BUILD-COMPARISON.JSN', 'MOVEMENTS.CSV'):
            z.writestr(leaf, (OUT / leaf).read_bytes())
        for case in ('baseline', 'candidate', 'baseline-qual', 'candidate-qual'):
            folder = OUT / ('windows-' + case)
            for path in sorted(folder.iterdir()):
                if path.suffix in ('.BIN',) or path.name in (
                        'PANQA.LOG', 'LEASE.JSN', 'RESULT.JSN', 'VERIFIED.JSN', 'PREPARE.JSN'):
                    z.writestr(case + '/' + path.name, path.read_bytes())
    save(HERE / 'HPXY.JSN', dict(status=integration['status'],
        physical_hardware=False, source_base=integration['source_base'],
        sources=integration['source'], driver=identity((HERE / 'BIN/HPXY.DRV').read_bytes()),
        evidence={str(p.relative_to(ROOT)).replace('\\', '/'): identity(p.read_bytes())
                  for p in (QUAL / 'BUILD.JSN', QUAL / 'WINDOWS.ZIP')},
        project_budget=dict(gross_NE_bytes=126883, ceiling=127531, margin=648,
            interpretation='Sum of NE segment minimum allocations; not free conventional RAM'),
        measured_windows_memory=dict(additional_allocated_bytes=1472,
            free_warm_bytes=154592, largest_free_block=149280),
        verified_frames=152, compared_packed_bytes=4864000))


def bindfix(build):
    shutil.copyfile(build / 'FIXXT.EXE', HERE / 'BIN/FIXXT.EXE')
    save(HERE / 'FIXBUILD.JSN', json.loads((build / 'BUILD.JSON').read_bytes()))
    q = json.loads((HERE / 'RCNATIVE.JSN').read_bytes())
    f = q['companions']['FIXXT.EXE']
    for name in ('source', 'binary', 'build_record'):
        f[name + '_identity'] = identity((ROOT / f[name]).read_bytes())
    f['source_dependencies']['tools/DOSINST/HPXYID.H'] = identity((HERE / 'HPXYID.H').read_bytes())
    save(HERE / 'RCNATIVE.JSN', q)
    for name, data in module('MAKESET').generate().items():
        (HERE / name).write_bytes(data)


def bindsetup(build):
    shutil.copyfile(build / 'SETUP.EXE', HERE / 'BIN/SETUP.EXE')
    q = json.loads((HERE / 'SETNAT.JSN').read_bytes())
    q['binary'] = identity((HERE / 'BIN/SETUP.EXE').read_bytes())
    q['sources'] = {n: identity((HERE / n).read_bytes()) for n in q['sources']}
    for name in ('HPXY.PY', 'HPXY.JSN', 'HPXYID.H'):
        q['sources'][name] = identity((HERE / name).read_bytes())
    save(HERE / 'SETNAT.JSN', q)
    entries = module('RCPUB').expanded_entries()
    stage = OUT / 'canonical-stage'
    stage.mkdir(exist_ok=False)
    for name, data in entries.items():
        dest = stage / name
        dest.parent.mkdir(exist_ok=True)
        dest.write_bytes(data)
    (OUT / 'CANONICAL.ZIP').write_bytes(module('RCPUB').pub.zip_bytes(entries))
    print('Staged normal expanded package:', stage)


if __name__ == '__main__':
    if sys.argv[1] == 'runtime':
        runtime()
    elif sys.argv[1] == 'fix':
        bindfix(Path(sys.argv[2]))
    elif sys.argv[1] == 'setup':
        bindsetup(Path(sys.argv[2]))
    else:
        raise SystemExit('runtime | fix BUILD | setup BUILD')
