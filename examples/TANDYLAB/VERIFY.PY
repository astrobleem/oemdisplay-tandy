#!/usr/bin/env python3
"""Read-only validation of the TANDYLAB copy pack; Python 3.8+, modern host."""
import argparse, hashlib, io, json, re, zipfile
from pathlib import Path, PurePosixPath

def sha(data):
    return hashlib.sha256(data).hexdigest()

def members(data):
    z = zipfile.ZipFile(io.BytesIO(data))
    assert z.testzip() is None, "ZIP CRC failure"
    names = [i.filename for i in z.infolist() if not i.is_dir()]
    assert len(names) == len(set(names)), "Duplicate ZIP path"
    for name in names:
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts, name
        assert '\\' not in name, name
    return {name: z.read(name) for name in names}

def verify_manifest(files, name, prefix=''):
    seen = set()
    for line in files[name].decode('ascii').splitlines():
        digest, rel = line.split('  ', 1)
        assert re.fullmatch('[0-9a-f]{64}', digest), line
        path = prefix + rel
        assert path not in seen, path
        assert path in files and sha(files[path]) == digest, path
        seen.add(path)
    return seen

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('zip', nargs='?', type=Path, default=Path(__file__).with_name('TANDYLAB.ZIP'))
    a = p.parse_args()
    data = a.zip.read_bytes()
    files = members(data)
    pat = re.compile(r'^[A-Z0-9_]{1,8}(\.[A-Z0-9_]{1,3})?$')
    for name, content in files.items():
        assert name.startswith('TANDYLAB/'), name
        assert all(pat.fullmatch(part) for part in PurePosixPath(name).parts), name
        base = PurePosixPath(name).name
        assert base not in {'WIN.COM', 'SETUP.EXE', 'SYSTEM.INI', 'WIN.INI',
            'CONFIG.SYS', 'AUTOEXEC.BAT', 'SOUND.DRV', 'TSOUND.DRV', 'TXTMODE.DRV'}, name
        assert PurePosixPath(name).suffix not in {'.FON', '.LGO', '.GR2', '.LIB', '.OBJ'}, name
        if name.endswith(('.TXT', '.SHA')):
            assert not re.search(b'(?<!\r)\n|\r(?!\n)', content), name
    manifest = 'TANDYLAB/MANIFEST.SHA'
    checked = verify_manifest(files, manifest, 'TANDYLAB/')
    assert checked == set(files) - {manifest}, 'Unexpected/unlisted member'
    toolkit = members(files['TANDYLAB/DRIVERS/T88TOOLS.ZIP'])
    toolkit_checked = verify_manifest(toolkit, 'DISK1/MANIFEST.SHA', 'DISK1/')
    assert toolkit_checked == {n for n in toolkit if n.startswith('DISK1/')} - {'DISK1/MANIFEST.SHA'}
    assert not any(n.endswith(('.FON', '.LGO', '.GR2', '.LIB', '.OBJ')) for n in toolkit)
    helper = members(files['TANDYLAB/EXPER/CDLG/SOURCE.ZIP'])
    helper_checked = verify_manifest(helper, 'MANIFEST.SHA')
    assert helper_checked == set(helper) - {'MANIFEST.SHA'}
    assert helper['CDSTART.EXE'] == files['TANDYLAB/EXPER/CDLG/CDSTART.EXE']
    assert sha(helper['CDSTART.EXE']) == 'c2cf986d1cd5d44ed02a31a4c327601b4b7b4b6a4dceb94fa41f8909d8136eac'
    assert 'TANDYLAB/FLYSWAT/SWAT.EXE' in files, 'Final game missing'
    print(json.dumps({'zip_bytes': len(data), 'zip_sha256': sha(data),
        'pack_members_verified': len(checked), 'toolkit_members_verified': len(toolkit_checked),
        'helper_members_verified': len(helper_checked), 'dos83_paths': True,
        'game_sha256': sha(files['TANDYLAB/FLYSWAT/SWAT.EXE']),
        'result': 'PASS: archive structure and hashes only; not a runtime or hardware test'}, indent=2))

if __name__ == '__main__':
    main()
