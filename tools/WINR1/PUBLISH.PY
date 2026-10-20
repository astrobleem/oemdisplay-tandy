"""Fail-closed rc.7 publication of the qualified, redistributable R1 subset.

MIT, Copyright (c) 2026 Windows XT contributors.
No private Windows files, compiler, emulator, native run or media access.
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import zipfile

ROOT = Path(__file__).resolve().parents[2]
HERE = ROOT / 'tools/WINR1'
TAG = 'v0.1.0-rc.7'
PINS = {
    'WINXT-REDISTRIBUTABLE-OVERLAY-R1.zip':
        (49235, '53b9cd81d49825ad21d91490d8e741e8b5715f4f99b57368e43a34ad1dd260ed'),
    'WINXT-FIRST-PARTY-R1.zip':
        (65989, '1631e02735289b8f7f897a9c3d53d796db8411017437950d0d8e48f9f3eeae5b'),
}
ASSETS = set(PINS) | {'START-HERE.TXT', 'QUALIFY.JSON', 'RELEASE.JSON', 'SHA256SUMS'}
DRIVER = '84df334cfc34af2dc8785676e92cfe428e0288cb21e2c6e94dbc16baba6d12f0'
RECORD = '0355523532636e20daa7be1769d36ea66026679c53defae8213b8937554da746'
FINAL_RUN = '59e08544551f42a18848856e5761cc61'

def check(value, message):
    if not value:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def raw(path):
    check(path.is_file() and not path.is_symlink() and
          path.stat().st_size < 67108864, 'Missing/linked/oversized file: ' + str(path))
    return path.read_bytes()

def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\r\n').encode('utf-8')

def safe_name(name):
    p = PurePosixPath(name)
    check(bool(name) and not p.is_absolute() and '..' not in p.parts and
          '\\' not in name and ':' not in name, 'Unsafe archive path: ' + name)

def members(path):
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        check(len(names) == len(set(names)), 'Duplicate archive member')
        for item in z.infolist():
            safe_name(item.filename)
            check(not item.is_dir() and item.file_size < 2097152 and
                  ((item.external_attr >> 16) & 0o170000) != 0o120000,
                  'Unexpected archive member: ' + item.filename)
        check(z.testzip() is None, 'Archive CRC failure')
        files = {name: z.read(name) for name in names}
    manifest = json.loads(files['MANIFEST.json'])
    records = manifest['files']
    if isinstance(records, dict):
        check(all(isinstance(v, dict) and set(v) == {'bytes', 'sha256'}
                  for v in records.values()), 'Unexpected keyed manifest record')
        records = [dict(value, path=name) for name, value in records.items()]
    check(isinstance(records, list) and all(isinstance(x, dict) and
          set(x) == {'path', 'bytes', 'sha256'} for x in records),
          'Unexpected manifest record')
    check(len(records) == len({x['path'] for x in records}), 'Duplicate manifest path')
    check({x['path'] for x in records} == set(files) - {'MANIFEST.json'},
          'Manifest member set differs')
    for item in records:
        data = files[item['path']]
        check(len(data) == item['bytes'] and sha(data) == item['sha256'],
              'Manifest hash differs: ' + item['path'])
    return files

def sources():
    archives = {}
    for name, (length, digest) in PINS.items():
        path = ROOT / 'downloads/R1' / name
        data = raw(path)
        check(len(data) == length and sha(data) == digest, 'Sealed asset changed: ' + name)
        archives[name] = members(path)
    kit = archives['WINXT-FIRST-PARTY-R1.zip']
    check(len(kit) == 38 and sha(kit['mouse/WHEEL.DRV']) == DRIVER,
          'Qualified first-party driver changed')
    tracked = {p.relative_to(HERE / 'KIT').as_posix(): raw(p)
               for p in (HERE / 'KIT').rglob('*') if p.is_file() and
               '__pycache__' not in p.parts and p.suffix != '.pyc'}
    check(tracked == kit, 'Visible component source/runtime differs from sealed kit')
    binary_names = {name for name in kit if PurePosixPath(name).suffix.lower()
                    in {'.exe', '.com', '.dll', '.drv', '.fon', '.rom', '.img', '.zip'}}
    check(binary_names == {'mouse/WHEEL.DRV', 'fonts/XTCFIX.FON',
          'fonts/XTCOEM.FON', 'fonts/XTCSYS.FON'}, 'Unexpected component binary')
    for name in ('mouse/LICENSE', 'fonts/LICENSE'):
        check(b'MIT License' in kit[name] and b'Permission is hereby granted' in kit[name],
              'Component license missing')
    overlay = archives['WINXT-REDISTRIBUTABLE-OVERLAY-R1.zip']
    check(len(overlay) == 21, 'Overlay member count changed')
    binaries = {'DOS-CROOT/' + folder + '/WHEEL.DRV': kit['mouse/WHEEL.DRV']
                for folder in ('W30', 'WINXT', 'WINXT/FILES')}
    for name in ('XTCFIX.FON', 'XTCOEM.FON', 'XTCSYS.FON'):
        for folder in ('WINXT', 'WINXT/FILES'):
            binaries['DOS-CROOT/' + folder + '/' + name] = kit['fonts/' + name]
    actual = {name: data for name, data in overlay.items() if name.startswith('DOS-CROOT/')}
    check(actual == binaries, 'Overlay contains unexpected/private runtime bytes')
    req = json.loads(overlay['LOCAL-REQUIREMENTS.json'])
    check(req['contains_dependency_bytes'] is False and req['external_file_count'] == 370
          and req['complete_assembled_file_count'] == 379, 'Local dependency boundary changed')
    check(sha(kit['QUALIFICATION.json']) == RECORD and
          kit['QUALIFICATION.json'] == overlay['QUALIFICATION.json'],
          'Original native record changed')
    native = json.loads(kit['QUALIFICATION.json'])
    check(native['status'] == 'PASS_WITH_STATED_SCOPE' and
          native['driver_sha256'] == DRIVER and native['clean_room_claim'] is False and
          native['integration']['run_id'] == FINAL_RUN and
          native['integration']['exact_frames'] == 8 and
          native['integration']['clean_dos_returns'] == 2,
          'Accepted integration/source identity changed')
    check(native['target']['hz'] == 7159092 and native['target']['ram_kb'] == 640
          and native['target']['original_8088_core'] is True,
          'Emulator qualification scope changed')
    return native

def qualification(commit):
    check(commit == 'working-tree' or re.fullmatch(r'[0-9a-f]{40}', commit),
          'Require exact publication commit')
    native = sources()
    return {'schema': 'winxt-rc7-redistributable-r1-v1', 'release_tag': TAG,
            'publication_commit': commit, 'publication_allowed': True,
            'standalone_installer': False, 'Microsoft_media_included': False,
            'private_project_executables_included': False,
            'separately_supplied_local_files': 370, 'assembled_file_count': 379,
            'native_record_sha256': RECORD, 'native_record': native,
            'final_R1_and_new_WHEEL_physical_hardware_tested': False,
            'earlier_physical_XR1': {
                'status': 'SEPARATE_PRIOR_USER_ACCEPTANCE',
                'scope': 'Earlier HPXY R1 panning/drawing on real Tandy 1000 EX; 54 pans, 53 hardware operations, software/home cleanup, Windows exit 0.',
                'source': 'README.md#panning-on-real-tandy-hardware',
                'qualifies_final_R1_or_new_first_party_WHEEL': False},
            'release_preparation_native_run': False, 'CF_access': False,
            'new_features_added_during_release_preparation': False}

def contents(commit):
    files = {name: raw(ROOT / 'downloads/R1' / name) for name in PINS}
    files['START-HERE.TXT'] = raw(HERE / 'START-HERE.TXT')
    files['QUALIFY.JSON'] = encoded(qualification(commit))
    files['RELEASE.JSON'] = encoded({
        'schema': 'winxt-rc7-public-assets-v1', 'release_tag': TAG,
        'publication_commit': commit, 'publication_allowed': True,
        'standalone_installer': False, 'Windows_support_included': False,
        'unresolved_private_executables_included': False,
        'assets_sha256': {name: sha(data) for name, data in sorted(files.items())}})
    files['SHA256SUMS'] = ''.join(sha(data) + '  ' + name + '\n'
                                for name, data in sorted(files.items())).encode('ascii')
    return files

def verify(folder, commit=None):
    check({p.name for p in folder.iterdir()} == ASSETS, 'Release asset allowlist differs')
    release = json.loads(raw(folder / 'RELEASE.JSON'))
    selected = release['publication_commit']
    if commit is not None:
        check(selected == commit, 'Publication commit differs')
    expected = contents(selected)
    check(all(raw(folder / name) == data for name, data in expected.items()),
          'Release source/qualification/asset bytes differ')
    print('PASS rc.7: exact MIT sources, 9-copy overlay, no Windows/private executables; 6 bound assets')

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', type=Path)
    ap.add_argument('--verify', type=Path)
    ap.add_argument('--commit', default=None)
    args = ap.parse_args()
    if args.verify:
        verify(args.verify, args.commit)
    else:
        if not args.out:
            ap.error('--out or --verify is required')
        files = contents(args.commit or 'working-tree')
        args.out.mkdir(parents=True, exist_ok=False)
        for name, data in files.items():
            (args.out / name).write_bytes(data)
        verify(args.out, args.commit)

if __name__ == '__main__':
    main()
