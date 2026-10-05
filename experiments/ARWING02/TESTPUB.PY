#!/usr/bin/env python3
"""Read-only horizon-laser publication inventory; never installs or runs EXEs."""
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
def sha(data):return hashlib.sha256(data).hexdigest()
def main():
 pins=json.loads((ROOT/'SHA256.JSN').read_text())
 for name in ['ARWING02.ZIP','DEMO.GIF']:
  p=pins.pop(name);data=(ROOT/name).read_bytes()
  assert len(data)==p['bytes'] and sha(data)==p['sha256'],name
 with zipfile.ZipFile(ROOT/'ARWING02.ZIP') as z:
  names=z.namelist();assert len(names)==len(set(names))==124 and z.testzip() is None
  exes=set()
  for name in names:
   p=PurePosixPath(name);b=z.read(name)
   assert name.startswith('ARWING02/') and not p.is_absolute() and '..' not in p.parts
   assert not any(x.lower() in {'windows','guest','ddk','include','lib','.git','library-helpers'} for x in p.parts)
   assert p.suffix.lower() not in {'.drv','.dll','.com','.sys','.fon','.obj','.lib','.zip'}
   assert b[:4]!=b'\x7fELF'
   if b[:2]==b'MZ' or p.suffix.lower()=='.exe':exes.add(name)
  assert exes=={'ARWING02/RUN/STARFLD.EXE','ARWING02/RUN/TSHELL.EXE'}
  rows=z.read('ARWING02/SHA256.TXT').decode().splitlines();assert len(rows)==123
  for row in rows:
   h,name=row.split(None,1);assert sha(z.read('ARWING02/'+name.strip()))==h,name
  for name,p in pins.items():
   b=z.read('ARWING02/'+name);assert len(b)==p['bytes'] and sha(b)==p['sha256'],name
  c=json.loads(z.read('ARWING02/EVIDENCE/CHANGES.JSN'))
  for row in c['production_changes']:
   assert sha(z.read('ARWING02/SOURCE/STARFLD/SOURCE/'+row['file']))==row['sha256']
  for name,h in c['unchanged_components'].items():
   assert sha(z.read('ARWING02/SOURCE/STARFLD/SOURCE/'+name))==h,name
  assert sha(z.read('ARWING02/RUN/TSHELL.EXE'))==c['tshell_sha256']
  for local,inside in [('NOTICE.TXT','NOTICE.TXT'),('TESTS.MD','TESTS.MD'),
                       ('BASELINE.TXT','BASELINE.TXT'),('KITGUIDE.MD','README.MD')]:
   assert (ROOT/local).read_bytes()==z.read('ARWING02/'+inside),local
  for p in (ROOT/'EVIDENCE').iterdir():
   assert p.read_bytes()==z.read('ARWING02/EVIDENCE/'+p.name),p.name
 print('PASS: ZIP/GIF hashes, 124 entries, 123 internal hashes, runtime/source pins and public evidence identities')
if __name__=='__main__':main()
