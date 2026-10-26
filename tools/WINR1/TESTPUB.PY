"""Negative checks for the rc.7 release boundary. MIT, Windows XT contributors."""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

loader = importlib.machinery.SourceFileLoader('r1pub', str(Path(__file__).with_name('PUBLISH.PY')))
spec = importlib.util.spec_from_loader(loader.name, loader)
pub = importlib.util.module_from_spec(spec)
loader.exec_module(pub)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--release', type=Path, required=True)
    args = ap.parse_args()
    pub.verify(args.release)
    checks = 0
    with tempfile.TemporaryDirectory(prefix='winxt-r1-guards-') as td:
        def refusal(change):
            nonlocal checks
            target = Path(td) / str(checks)
            shutil.copytree(args.release, target)
            change(target)
            try:
                pub.verify(target)
            except (ValueError, KeyError, json.JSONDecodeError):
                checks += 1
            else:
                raise AssertionError('Accepted invalid release')
        refusal(lambda p: (p / 'WIN.CNF').write_bytes(b'owned resource'))
        refusal(lambda p: (p / 'CL.EXE').write_bytes(b'external tool'))
        for name in pub.PINS:
            refusal(lambda p, name=name: (p / name).write_bytes(b'changed archive'))
        for name in ('START-HERE.TXT', 'QUALIFY.JSON', 'RELEASE.JSON', 'SHA256SUMS'):
            refusal(lambda p, name=name: (p / name).write_bytes(b'changed metadata'))
        for field, value in [('standalone_installer', True),
                             ('final_R1_and_new_WHEEL_physical_hardware_tested', True),
                             ('Microsoft_media_included', True)]:
            def alter(p, field=field, value=value):
                path = p / 'QUALIFY.JSON'
                q = json.loads(path.read_bytes())
                q[field] = value
                path.write_bytes(pub.encoded(q))
                (p / 'SHA256SUMS').write_bytes(''.join(pub.sha(pub.raw(p / n)) + '  ' + n + '\n'
                    for n in sorted(pub.ASSETS - {'SHA256SUMS'})).encode('ascii'))
            refusal(alter)
        try:
            pub.verify(args.release, 'f' * 40)
        except ValueError:
            checks += 1
        else:
            raise AssertionError('Accepted wrong commit')
        for name in ('../escape', '/absolute', 'a\\WIN.CNF', 'C:bad'):
            try:
                pub.safe_name(name)
            except ValueError:
                checks += 1
            else:
                raise AssertionError('Accepted unsafe archive path')
    print('PASS rc.7 publication negatives:', checks)

if __name__ == '__main__':
    main()
