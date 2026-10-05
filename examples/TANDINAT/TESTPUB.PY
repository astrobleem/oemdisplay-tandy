#!/usr/bin/env python3
"""Read-only exact artifact/publication check; never installs or runs TANDI."""
from pathlib import Path, PurePosixPath
import hashlib
import zipfile

ROOT=Path(__file__).resolve().parent
PINS={
    'RUN/TANDI.EXE':'addccc4271aee92a95ca5c53c18679a7c2c7019a1b96fcb471e2b6ba33bfeeca',
    'RUN/TANDY.DAT':'8af110b129698f054ee9349b0fe84b5401b2b595852862e84f2c240fa4c4377d',
    'SOURCE/art/CABINET.PNG':'960fb2033e3aeaa7c0d550e228e8fcf69cdad6dace8a13571a9b5f068bf5251b',
    'SOURCE/art/PARTS.PNG':'6ae9d955e6feaf6bd0585e82fd7ed5cda6b743b929913fede5ac0cb951ebbcb1',
}

def sha(data):
    return hashlib.sha256(data).hexdigest()

def main():
    payload=(ROOT/'TANDI02.ZIP').read_bytes()
    assert len(payload)==1285196
    assert sha(payload)=='4b7da3fc7c9141c66dd43e8c84a4b177bc2cdf2b93cbad4d24f2cf83c6fbdb4c'
    with zipfile.ZipFile(ROOT/'TANDI02.ZIP') as archive:
        names=archive.namelist()
        assert len(names)==len(set(names))==201 and archive.testzip() is None
        for name in names:
            p=PurePosixPath(name)
            assert not p.is_absolute() and '..' not in p.parts
            assert name.startswith('TANDI02/')
            assert not any(x.lower() in {'windows','guest','ddk','include','lib',
                                        '.git','library-helpers'} for x in p.parts)
            assert p.suffix.lower() not in {'.drv','.dll','.sys','.fon','.obj','.lib'}
            if p.suffix.lower()=='.exe':
                assert name=='TANDI02/RUN/TANDI.EXE'
        rows=archive.read('TANDI02/SHA256.TXT').decode().splitlines()
        assert len(rows)==200
        for line in rows:
            expected,name=line.split(None,1)
            assert sha(archive.read('TANDI02/'+name.strip()))==expected,name
        for name,expected in PINS.items():
            assert sha(archive.read('TANDI02/'+name))==expected,name
        count=0
        for folder in ['SOURCE','RUN','EVIDENCE']:
            for local in (ROOT/folder).rglob('*'):
                if local.is_file():
                    rel=local.relative_to(ROOT).as_posix()
                    assert local.read_bytes()==archive.read('TANDI02/'+rel),rel
                    count+=1
    print('PASS: 201 archive entries, 200 manifest hashes, runtime/art pins, '+
          str(count)+' browsable-file identities and platform exclusions')

if __name__=='__main__':
    main()
