#!/usr/bin/env python3
"""Stage all five pinned source pipelines; no guest code or emulator runs."""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import json
import tempfile

HERE = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=HERE.parents[1])
    parser.add_argument('--pins', type=Path)
    args = parser.parse_args()
    repo = args.repo.resolve()
    source = repo / 'src/tandysw'
    pinfile = args.pins or repo / 'docs/TRIAL4/BUILDS.JSN'
    pins = json.loads(pinfile.read_text())
    modules = {}
    for name in ('build', 'PORT8086', 'PORTDIB', 'MODEPROF', 'REPCOPY88',
                 'BYTECOL', 'CURKEEP', 'OUTROWS'):
        suffix = '.py' if name == 'build' else '.PY'
        loader = importlib.machinery.SourceFileLoader('chain_' + name,
                                                     str(source / (name + suffix)))
        modules[name] = loader.load_module()
    for rel, expected in pins['source_files'].items():
        assert hashlib.sha256((repo / rel).read_bytes()).hexdigest() == expected, rel
    rows = []
    with tempfile.TemporaryDirectory(prefix='tandy-chain-') as temp:
        for mode, expected in pins['profiles'].items():
            out = Path(temp) / mode
            renderer, resources = modules['build'].prepare(repo, out)
            modules['PORT8086'].port(renderer, repo)
            modules['PORTDIB'].port(renderer, repo)
            modules['MODEPROF'].port(renderer, resources, repo, mode)
            modules['REPCOPY88'].port(renderer, mode)
            modules['BYTECOL'].port(renderer, mode)
            modules['CURKEEP'].port(renderer, mode, combined=True)
            modules['OUTROWS'].port(renderer, mode)
            for name, digest in expected['staged_source_sha256'].items():
                payload = (renderer / 'EGA' / name).read_bytes()
                assert hashlib.sha256(payload).hexdigest() == digest, (mode, name)
                assert b'\n' not in payload.replace(b'\r\n', b''), (mode, name)
            before = (renderer / 'EGA/TSOFT.ASM').read_bytes()
            try:
                modules['OUTROWS'].port(renderer, mode)
            except RuntimeError:
                pass
            else:
                raise AssertionError('Repeated Output-row pass was accepted')
            assert (renderer / 'EGA/TSOFT.ASM').read_bytes() == before
            rows.append({'mode': mode, 'result': 'PASS'})
    print(json.dumps({'result': 'PASS', 'profiles': rows,
                      'scope': 'Source hashes, exact staged assembly, CRLF and repeated-pass rejection; no runtime or binary claim'}, indent=2))

if __name__ == '__main__':
    main()
