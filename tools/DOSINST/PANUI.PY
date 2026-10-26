"""Bind the current expanded installer to native-qualified panning helpers.

The original OS gathering, ordinary OEM descriptor and driver receipts stay
frozen. This update checks their unchanged members and the exact new helper,
catalog/finisher builds and native preparation/installed-helper results.
"""
from pathlib import Path
import hashlib
import importlib.machinery
import io
import json
import re
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def helpers():
    m = importlib.machinery.SourceFileLoader(
        'qualified_panui', str(ROOT / 'src/panui/VERIFY.PY')).load_module()
    return m.verify()


def runtimes():
    _, binaries = helpers()
    spec = json.loads((HERE / 'RCNATIVE.JSN').read_bytes())
    fix = spec['companions']['FIXXT.EXE']
    for name in ('source', 'binary', 'build_record'):
        require(identity((ROOT / fix[name]).read_bytes()) ==
                fix[name + '_identity'], 'Finisher binding differs: ' + name)
    for name, pin in fix['source_dependencies'].items():
        require(identity((ROOT / name).read_bytes()) == pin,
                'Finisher dependency differs: ' + name)
    return {'XYCTL.EXE': binaries['XYCTL.EXE'],
            'FIXXT.EXE': (HERE / 'BIN/FIXXT.EXE').read_bytes()}


def aliases(pins, files):
    for name, data in runtimes().items():
        row = ('{"%s","%s",%dUL,0,0x%08xUL}' %
               (name, hashlib.sha256(data).hexdigest(), len(data),
                zlib.crc32(data))).encode('ascii')
        pattern = rb'\{"' + name.encode().replace(b'.', rb'\.') + rb'","[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL\}'
        pins, count = re.subn(pattern, lambda _: row, pins)
        require(count == 1, 'Current runtime pin missing: ' + name)
        pattern = rb'(,"' + name.encode().replace(b'.', rb'\.') + rb'",)\d+UL(,0\})'
        files, count = re.subn(pattern, lambda m: m[1] +
                              str(len(data)).encode() + b'UL' + m[2], files)
        require(count == 2, 'Current runtime recipe differs: ' + name)
    return pins, files


def qualify(entries, archive, baseline):
    helpers()
    path = ROOT / 'docs/QUAL/WDESK/PACKAGE.JSN'
    q = json.loads(path.read_bytes())
    require(q['status'] == 'PASS_NATIVE_PACKAGE' and
            q['physical_qualification'] is False, 'Panning package incomplete')
    require(q['baseline_expanded'] == identity(
        (ROOT / 'docs/QUAL/DOSINST/EXPAND.JSN').read_bytes()),
        'Expanded baseline receipt differs')
    require(baseline['status'] == 'PASS_EXPANDED_NATIVE' and
            baseline['physical_test'] is False, 'Expanded baseline incomplete')
    for name in ('fresh', 'update', 'drivers_only', 'negative'):
        row = baseline[name]
        require(row['complete'] and row['owned_stopped'] and
                row['lease_released'] and not row.get('error'),
                'Expanded baseline case incomplete: ' + name)
    for name, pin in baseline['evidence'].items():
        require(identity((ROOT / 'docs/QUAL/DOSINST' / name).read_bytes()) == pin,
                'Expanded baseline evidence differs: ' + name)
    require(q['helper_qualification'] == identity(
        (ROOT / 'docs/QUAL/WDESK/NATIVE.JSN').read_bytes()),
        'Different settings qualification used')
    require(q['archive'] == identity(archive) and q['files'] ==
            {n: identity(b) for n, b in sorted(entries.items())},
            'Current package differs from native inputs')
    require(set(q['files']) == set(baseline['files']),
            'Expanded source inventory changed')
    changed = {n for n, pin in q['files'].items()
               if pin != baseline['files'][n]}
    require(changed == {'SETUP.EXE', 'README.TXT', 'WINXT/FIXXT.EXE',
                        'WINXT/XYCTL.EXE'}, 'Unexpected package changes')
    for name, data in runtimes().items():
        require(entries['WINXT/' + name] == data,
                'Different installed runtime: ' + name)
    ordinary = json.loads((ROOT / 'tools/XROEM/NATIVE.JSN').read_bytes())
    require(ordinary['packet'] == baseline['archive'] and ordinary['complete']
            and all(ordinary['checks'].values()), 'Ordinary OEM baseline incomplete')
    for name, pin in ordinary['sources'].items():
        require(identity(entries['WINXT/' + name]) == pin,
                'Ordinary OEM source changed: ' + name)
    for name, pin in ordinary['evidence'].items():
        require(identity((ROOT / 'tools/XROEM/QA' / name).read_bytes()) == pin,
                'Ordinary OEM evidence changed: ' + name)
    require(set(q['native']) == {'fresh', 'update', 'finisher'},
            'Current native cases incomplete')
    for name, row in q['native'].items():
        require(row['complete'] and row['owned_stopped'] and
                row['lease_released'] and not row.get('error'),
                'Current native case incomplete: ' + name)
        require(row['archive'] == q['archive'] and
                row['helper'] == q['files']['SETUP.EXE'],
                'Different packet/Setup tested: ' + name)
        if name != 'finisher':
            require(row['prepared_comparison'] ==
                    {'count': 370 if name == 'fresh' else 83, 'different': []},
                    'Prepared current files differ: ' + name)
        else:
            require(row['finisher'] == q['files']['WINXT/FIXXT.EXE'] and
                    row['input_runtime'] == q['files']['WINXT/XYCTL.EXE'] and
                    row['installed_helper'] == q['files']['WINXT/XYCTL.EXE']
                    and row['guarded_windows_return'],
                    'Installed helper/Windows return not verified')
    require(set(q['evidence']) == {'docs/QUAL/WDESK/INSTALL.ZIP'},
            'Native package evidence inventory differs')
    for name, pin in q['evidence'].items():
        data = (ROOT / name).read_bytes()
        require(identity(data) == pin,
                'Changed native package evidence: ' + name)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(len(z.namelist()) == len(set(z.namelist())) and
                    z.testzip() is None, 'Corrupt native package evidence')
            require(json.loads(z.read('RESULT.JSN')) == q['native'],
                    'Native package result differs from raw receipt')
    return q
