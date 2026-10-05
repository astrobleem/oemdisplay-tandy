#!/usr/bin/env python3
"""Verify immutable publication archives; no install or guest execution."""
from pathlib import Path, PurePosixPath
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parent

def digest(data):
    return hashlib.sha256(data).hexdigest()

def names(archive, prefix):
    result = archive.namelist()
    assert len(result) == len(set(result)), 'duplicate archive names'
    for name in result:
        path = PurePosixPath(name)
        assert not path.is_absolute() and '..' not in path.parts
        assert name.startswith(prefix + '/')
        assert not any(p.lower() in {'guest', 'windows', 'ddk', 'include',
                                    'lib', '.git', 'library-helpers'}
                       for p in path.parts)
    assert archive.testzip() is None
    return result

def main():
    for filename, record in json.loads((ROOT/'SHA256.JSN').read_text()).items():
        payload = (ROOT/filename).read_bytes()
        assert len(payload) == record['bytes']
        assert digest(payload) == record['sha256'], filename
    with zipfile.ZipFile(ROOT/'TRIAL7.ZIP') as archive:
        runtime = names(archive, 'TRIAL7')
        assert len(runtime) == 20
        manifest = archive.read('TRIAL7/MANIFEST.SHA').decode()
        count = 0
        for line in manifest.splitlines():
            if not line.strip():
                continue
            expected, filename = line.split(None, 1)
            filename = filename.strip().lstrip('*').replace('\\', '/')
            assert digest(archive.read('TRIAL7/' + filename)) == expected
            count += 1
        assert count == 19
        frozen = json.loads((ROOT/'EVIDENCE/FROZEN-BUILDS.json').read_text())
        modes = {'160x200x16':'TR51616.DRV', '320x200x16':'TR53216.DRV',
                 '320x200x4':'TR53204.DRV', '640x200x4':'TR56404.DRV',
                 '640x200x2':'TR56402.DRV'}
        for mode, filename in modes.items():
            data = archive.read('TRIAL7/NEW/' + filename)
            assert digest(data) == frozen['profiles'][mode]['sha256']
            assert len(data) == frozen['profiles'][mode]['bytes']
        for filename in ['BUILD.BAT', 'PINS.H', 'T7SAFE.C']:
            assert archive.read('TRIAL7/SOURCE/'+filename) == (ROOT/'GUARD'/filename).read_bytes()
        for filename in ['README.TXT','TESTS.TXT','MANIFEST.SHA']:
            assert archive.read('TRIAL7/'+filename) == (ROOT/'RUNTIME'/filename).read_bytes()
    with zipfile.ZipFile(ROOT/'SOURCEQA.ZIP') as archive:
        evidence = names(archive, 'TRIAL7-SOURCE-RESULTS')
        assert len(evidence) == 1875
        records = json.loads(archive.read('TRIAL7-SOURCE-RESULTS/CONTENTS-SHA256.json'))
        assert len(records) == 1874
        for filename, expected in records.items():
            assert digest(archive.read('TRIAL7-SOURCE-RESULTS/'+filename)) == expected, filename
        excluded = {'.exe','.drv','.dll','.com','.fon','.obj','.lst','.lib','.sys'}
        assert not any(PurePosixPath(n).suffix.lower() in excluded for n in evidence)
        for local in (ROOT/'SOURCE/src/tandysw').iterdir():
            assert local.read_bytes() == archive.read('TRIAL7-SOURCE-RESULTS/source/src/tandysw/'+local.name)
    print('PASS: archive hashes, 19 runtime pins, five TR7 drivers, 1,874 source/evidence hashes, source identity and excluded-file checks')

if __name__ == '__main__':
    main()
