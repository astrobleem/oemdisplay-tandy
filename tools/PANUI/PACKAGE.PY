"""Build the current native-install panning ZIPs; no SFX or host prerequisite."""
from pathlib import Path
import argparse
import importlib.machinery
import io
import json
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
S = importlib.machinery.SourceFileLoader(
    'current_softpan_payload', str(ROOT / 'tools/SPPACK/PACKAGE.PY')).load_module()


def stored(files):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            z.writestr(info, data)
    return out.getvalue()


def outputs():
    spec = json.loads((ROOT / 'tools/SPPACK/PUBLIC.JSN').read_bytes())
    baseline = json.loads((HERE / 'BASE.JSN').read_bytes())
    files = {}
    for kind in ('JRPAN', 'CPPAN'):
        body = S.payload(kind, spec)
        before = baseline[kind]
        if set(body) != set(before):
            raise ValueError('Panning support inventory changed: ' + kind)
        changed = {n for n, b in body.items() if S.identity(b) != before[n]}
        if changed != {'XTPAN.EXE', 'PANCFG.EXE', 'INSTALL.TXT'}:
            raise ValueError('Unexpected driver/support changes: ' + kind)
        if kind == 'JRPAN':
            files[kind + '.ZIP'] = S.archive(kind, body)
        else:
            body['INSTALL.TXT'] = (ROOT / 'tools/CURRENT/GUIDES/CPPAN.TXT').read_bytes()
            body['OWATCOM.TXT'] = (ROOT / 'tools/XR1PACK/OWATCOM.TXT').read_bytes()
            native = json.loads((ROOT / 'tools/DRVSET/NATIVE.JSN').read_bytes())
            original = native['runtime']['ColorPlus']
            if not native['complete'] or not all(native['checks'].values()):
                raise ValueError('Original native ColorPlus installer incomplete')
            if set(body) != set(original) or any(S.identity(b) != original[n]
                    for n, b in body.items() if n not in changed):
                raise ValueError('Native ColorPlus installation/support changed')
            files[kind + '.ZIP'] = stored(body)
    return files


def verify(files):
    expected = outputs()
    if {n: files[n] for n in expected} != expected:
        raise ValueError('Current native-qualified panning packet differs')
    return {n: S.identity(b) for n, b in expected.items()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    files = outputs()
    args.out.mkdir(parents=True, exist_ok=False)
    for name, data in files.items():
        (args.out / name).write_bytes(data)
    print(json.dumps(verify(files), indent=2))
