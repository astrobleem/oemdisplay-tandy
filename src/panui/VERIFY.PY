"""Check exact helper builds and saved Windows 3.0 settings evidence."""
from pathlib import Path
import hashlib
import io
import json
import zipfile

ROOT = Path(__file__).resolve().parents[2]
QUAL = ROOT / 'docs/QUAL/WDESK/NATIVE.JSN'
SOURCES = ('src/panui/PANSET.C', 'src/panui/PANSET.H',
           'src/panui/PANDLG.C', 'src/panui/PANDLG.H',
           'src/xtpan/XTPAN.C', 'src/xtpan/XTPAN.DEF', 'src/xtpan/XTPAN.RSP',
           'src/softpan/PANCFG.C', 'src/softpan/PANCFG.DEF',
           'src/softpan/PANCFG.RSP', 'src/softpan/BUILDAPP.PY',
           'src/softpan/BLDTEST.BAT', 'experiments/XYOVERVIEW/XYCTL.C',
           'experiments/XYOVERVIEW/XYCTL.LNK',
           'src/wdesk/WDCORE.C', 'src/wdesk/WDCORE.H',
           'src/wdesk/WDWIN.C', 'src/wdesk/WDWIN.H',
           'src/wdesk/PLACE/WTPLACE.C', 'src/wdesk/PLACE/WTPLACE.H')


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def require(test, message):
    if not test:
        raise ValueError(message)


def exact(name, pin):
    path = Path(name)
    require(not path.is_absolute() and '..' not in path.parts,
            'Unsafe qualification path: ' + name)
    data = (ROOT / path).read_bytes()
    require(identity(data) == pin, 'Changed qualified input: ' + name)
    return data


def verify():
    q = json.loads(QUAL.read_bytes())
    require(q['status'] == 'PASS_NATIVE_SETTINGS' and
            q['physical_qualification'] is False, 'Native settings incomplete')
    require(set(q['helpers']) == {'XTPAN.EXE', 'PANCFG.EXE', 'XYCTL.EXE'},
            'Helper inventory differs')
    binaries = {}
    for name, row in q['helpers'].items():
        binaries[name] = exact(row['path'], row['identity'])
    require(set(q['sources']) == set(SOURCES), 'Compiled source inventory differs')
    for name, pin in q['sources'].items():
        exact(name, pin)
    for name, pin in q['build_evidence'].items():
        exact(name, pin)
    window = q['window_backend']
    with zipfile.ZipFile(io.BytesIO(exact(window['path'], window['identity']))) as z:
        require(len(z.namelist()) == len(set(z.namelist())) and
                z.testzip() is None, 'Corrupt window workspace evidence')
        require({n: identity(z.read(n)) for n in z.namelist()} ==
                window['members'], 'Window evidence inventory differs')
        for helper, data in binaries.items():
            require(z.read('CANDIDATE/' + helper) == data,
                    'Different window helper tested: ' + helper)
        for name in ('WDCORE.C', 'WDCORE.H', 'WDWIN.C', 'WDWIN.H'):
            require(z.read('SHARED/' + name) ==
                    (ROOT / 'src/wdesk' / name).read_bytes(),
                    'Different workspace source tested: ' + name)
        for name in ('WTPLACE.C', 'WTPLACE.H'):
            require(z.read('SHARED/' + name) ==
                    (ROOT / 'src/wdesk/PLACE' / name).read_bytes(),
                    'Different placement source tested: ' + name)
        for case in ('PCJR', 'CGA-MAX'):
            result = json.loads(z.read('EVIDENCE/' + case + '/RESULT.JSON'))
            lease = json.loads(z.read('EVIDENCE/' + case + '/LEASE.JSON'))
            require(result['status'] == 'PASS' and lease['status'] == 'PASS'
                    and lease['lease_acquired'] and lease['lease_released']
                    and not lease['inventory_after'] and
                    all(c['stopped'] for c in lease['children']),
                    'Window recovery case incomplete: ' + case)
            if case == 'PCJR':
                for helper in binaries:
                    require(result['binaries'][helper] == identity(binaries[helper]),
                            'Window run used different helper: ' + helper)
    shared = json.loads((ROOT / 'src/wdesk/PLACE/SOURCE.JSN').read_bytes())
    require(shared['repository'] == 'astrobleem/libwintandy' and
            len(shared['commit']) == 40, 'Canonical placement source missing')
    for name, pin in shared['files'].items():
        exact('src/wdesk/PLACE/' + name, pin)
    require(set(q['cases']) == {'PCJR', 'COLORPLUS', 'TANDYXY'},
            'Native settings adapter inventory differs')
    for name, case in q['cases'].items():
        data = exact(case['path'], case['identity'])
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(len(z.namelist()) == len(set(z.namelist())) and
                    z.testzip() is None, 'Corrupt evidence: ' + name)
            require({n: identity(z.read(n)) for n in z.namelist()} ==
                    case['members'], 'Evidence inventory differs: ' + name)
            result = json.loads(z.read(case['result']))
            lease = json.loads(z.read(case['lease']))
            require(result['status'] == 'PASS', 'UI case did not pass: ' + name)
            require(lease['status'] == 'PASS' and lease['lease_acquired'] and
                    lease['lease_released'] and not lease['inventory_after'] and
                    all(c['stopped'] for c in lease['children']),
                    'Owned session cleanup incomplete: ' + name)
            require(case['normal_dos_return'] and case['return_evidence'] in
                    z.namelist(), 'DOS return evidence missing: ' + name)
            labels = {e['label'] for e in result['events']}
            require(set(case['required_snapshots']) <= labels,
                    'Native UI snapshots incomplete: ' + name)
            for label in case['required_snapshots']:
                state = z.read(label + '.TXT').decode('ascii')
                require(state.startswith('STATE ') and 'PROFILE ' in state,
                        'Incomplete snapshot: ' + label)
                if case['live_fat_bridge']:
                    require(state.rstrip().endswith('UI_COMPLETE'),
                            'Incomplete FAT snapshot: ' + label)
            for helper in case['helpers']:
                require(case['loaded_files'][helper] ==
                        q['helpers'][helper]['identity'],
                        'Different helper tested: ' + name + '/' + helper)
            exact(case['driver']['path'], case['driver']['identity'])
            require(case['loaded_files']['driver'] == case['driver']['identity'],
                    'Different driver tested: ' + name)
    return q, binaries


if __name__ == '__main__':
    record, _ = verify()
    print(json.dumps({'status': record['status'],
                      'helpers': record['helpers'],
                      'adapters': list(record['cases'])}, indent=2))
