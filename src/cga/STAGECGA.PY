#!/usr/bin/env python3
"""Host-only CGA source staging. Never launches a compiler or emulator.

Normal CGA profiles reuse BUILD88's complete, pinned TR5 pipeline. CGA100
is an opt-in final adapter of its 160x200 profile, not a new raster engine.
Supply a commit-pinned display source view (tools/BUILDDEPS/README.MD).
"""
import argparse
import hashlib
import importlib.machinery
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE.parent / 'tandysw'
MODES = {'160x100x16': ('160x200x16', 'CGA100.DRV'),
         '320x200x4': ('320x200x4', 'CGA320.DRV'),
         '640x200x2': ('640x200x2', 'CGA640.DRV')}


def module(name):
    return importlib.machinery.SourceFileLoader('cga_' + name.lower(), str(BASE / (name + '.PY'))).load_module()


def read(path):
    return path.read_bytes().replace(b'\r\n', b'\n').decode('latin1')


def write(path, value):
    path.write_bytes(value.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))


def once(text, old, new, count=1):
    found = text.count(old)
    if found != count:
        raise ValueError('CGA anchor %r: %d, expected %d' % (old, found, count))
    return text.replace(old, new)


def pipeline(repo, out, mode):
    """Exactly the BUILD88 staging order; every upstream source pin stays on."""
    sys.path.insert(0, str(BASE))
    import build
    renderer, resources = build.prepare(repo, out)
    audits = {}
    for name in ('PORT8086', 'PORTDIB'):
        audits[name] = module(name).port(renderer, repo)
    base = MODES[mode][0]
    audits['MODEPROF'] = module('MODEPROF').port(renderer, resources, repo, base)
    for name in ('REPCOPY88', 'BYTECOL', 'CURKEEP', 'OUTROWS', 'WIDESCAN'):
        kwargs = {'combined': True} if name == 'CURKEEP' else {}
        audits[name] = module(name).port(renderer, base, **kwargs)
    return renderer, resources, audits


def stage(repo, out, mode):
    renderer, resources, audits = pipeline(repo, out, mode)
    # The normal-mode source and resource bytes remain exactly the upstream
    # staged result. IBM CGA qualification is separate from Tandy evidence.
    if mode == '160x100x16':
        patch = importlib.machinery.SourceFileLoader('cga100', str(HERE / 'CGA100.PY')).load_module()
        audits['CGA100'] = patch.stage(renderer, resources)
    paths = [p for root in (renderer, resources) for p in root.rglob('*') if p.is_file()]
    return dict(mode=mode, driver=MODES[mode][1], base_profile=MODES[mode][0],
                build='NOT_RUN', runtime='NOT_TESTED', audits=audits,
                staged_sha256={p.relative_to(out).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in sorted(paths)})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo', type=Path, required=True)
    ap.add_argument('--out', type=Path, required=True)
    ap.add_argument('--mode', choices=tuple(MODES), required=True)
    args = ap.parse_args()
    if args.out.exists():
        raise SystemExit('Choose a fresh --out')
    args.out.mkdir(parents=True)
    report = stage(args.repo.resolve(), args.out.resolve(), args.mode)
    write(args.out / 'CGASTAGE.JSN', json.dumps(report, indent=2) + '\n')
    print('CGA host staging PASS: ' + args.mode + '; no native build/runtime claim')


if __name__ == '__main__':
    main()
