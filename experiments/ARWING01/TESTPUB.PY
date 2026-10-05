#!/usr/bin/env python3
"""Read-only publication inventory checks. No installation or runtime launch."""
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile

ROOT=Path(__file__).resolve().parent
RUNTIME={
 'ARWING01/RUN/STARFLD.EXE':(31599,'2ff451a01c55c1a87ed29d8b24f57ed2d1f0c0885bcf227c9f0008196965aeeb'),
 'ARWING01/RUN/TSHELL.EXE':(68979,'703383a6944c9c22a0533f15d2e2ff7794edfd57ed0ebced125eca67129a7403'),
}

def digest(data):return hashlib.sha256(data).hexdigest()

def main():
 for name,pin in json.loads((ROOT/'SHA256.JSN').read_text()).items():
  data=(ROOT/name).read_bytes()
  assert len(data)==pin['bytes'] and digest(data)==pin['sha256'],name
 with zipfile.ZipFile(ROOT/'ARWING01.ZIP') as archive:
  names=archive.namelist();assert len(names)==len(set(names))==136
  assert archive.testzip() is None
  actual_exes=[]
  for name in names:
   p=PurePosixPath(name);data=archive.read(name)
   assert not p.is_absolute() and '..' not in p.parts and name.startswith('ARWING01/')
   assert not any(x.lower() in {'windows','guest','ddk','include','lib','.git','library-helpers'} for x in p.parts)
   assert p.suffix.lower() not in {'.drv','.dll','.com','.sys','.fon','.obj','.lib','.zip'}
   assert data[:4]!=b'\x7fELF'
   if data[:2]==b'MZ' or p.suffix.lower()=='.exe':actual_exes.append(name)
  assert set(actual_exes)==set(RUNTIME)
  rows=archive.read('ARWING01/SHA256.TXT').decode().splitlines()
  assert len(rows)==135
  for row in rows:
   expected,name=row.split(None,1)
   assert digest(archive.read('ARWING01/'+name.strip()))==expected,name
  for name,(size,expected) in RUNTIME.items():
   data=archive.read(name);assert len(data)==size and digest(data)==expected
  for local,inside in [('NOTICE.TXT','NOTICE.TXT'),('TESTS.MD','TESTS.MD'),
                       ('KITGUIDE.MD','README.MD'),('COLOR16.PNG','SHOTS/COLOR16.PNG'),
                       ('OPTIONS.PNG','SHOTS/OPTION16.PNG'),('CALIB.PNG','SHOTS/CALIB.PNG')]:
   assert (ROOT/local).read_bytes()==archive.read('ARWING01/'+inside),local
 print('PASS: artifact hashes, 136 ZIP entries, 135 internal hashes, both runtime pins, docs/screenshots and platform exclusions')

if __name__=='__main__':main()
