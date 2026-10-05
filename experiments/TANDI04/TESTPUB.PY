#!/usr/bin/env python3
"""Read-only exact UI04 package/evidence verification; no installation."""
from pathlib import Path,PurePosixPath
import hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
PINNED={
 'SOURCE/src/TANDI.C':'f5fe677f478efb0d7c22424b462d7a167e76ec610c596dd9158af4b51d50ac39',
 'SOURCE/src/ENGINE.C':'970f9ff2c1750f71aa392d36e801067a1aca7709fbc64837dfaee4fa86ed4b99',
 'SOURCE/src/DB.C':'e3f078fc5d9534b78b30e102390da98324dce345ec2a3261393a1ae0ebf4a788',
 'SOURCE/src/ART.H':'be14f7ca4c2963c8feae8332e6ec286845a94af9873fb4f731e3bed4ee72c07f',
 'SOURCE/data/STARTER.JSON':'dc46b91ef521711f97326d82e32aa766c01d6951572a20c873e8ec608424f8ce',
 'SOURCE/build/BASE128.EXE':'addccc4271aee92a95ca5c53c18679a7c2c7019a1b96fcb471e2b6ba33bfeeca',
 'SOURCE/build/BASE128.DAT':'8af110b129698f054ee9349b0fe84b5401b2b595852862e84f2c240fa4c4377d',
 'SOURCE/art/CABINET.PNG':'960fb2033e3aeaa7c0d550e228e8fcf69cdad6dace8a13571a9b5f068bf5251b',
 'SOURCE/art/PARTS.PNG':'6ae9d955e6feaf6bd0585e82fd7ed5cda6b743b929913fede5ac0cb951ebbcb1',
}
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
 pins=json.loads((ROOT/'SHA256.JSN').read_text())
 for n in ['TANDI04.ZIP','BASELINE.PNG','PREVIEW.PNG']:
  p=pins.pop(n);b=(ROOT/n).read_bytes()
  assert len(b)==p['bytes'] and sha(b)==p['sha256'],n
 with zipfile.ZipFile(ROOT/'TANDI04.ZIP') as z:
  names=z.namelist();assert len(names)==len(set(names))==129 and z.testzip() is None
  exes=set()
  for n in names:
   p=PurePosixPath(n);b=z.read(n)
   assert n.startswith('TANDI04/') and not p.is_absolute() and '..' not in p.parts
   assert not any(x.lower() in {'windows','guest','ddk','include','lib','.git','library-helpers'} for x in p.parts)
   assert p.suffix.lower() not in {'.drv','.dll','.com','.sys','.fon','.obj','.lib','.zip'}
   assert b[:4]!=b'\x7fELF'
   if b[:2]==b'MZ' or p.suffix.lower()=='.exe':exes.add(n)
  assert exes=={'TANDI04/RUN/TANDI.EXE','TANDI04/SOURCE/build/BASE128.EXE'}
  rows=z.read('TANDI04/SHA256.TXT').decode().splitlines();assert len(rows)==128
  for row in rows:
   h,n=row.split(None,1);assert sha(z.read('TANDI04/'+n.strip()))==h,n
  for n,p in pins.items():
   b=z.read('TANDI04/'+n);assert len(b)==p['bytes'] and sha(b)==p['sha256'],n
  for n,h in PINNED.items():assert sha(z.read('TANDI04/'+n))==h,n
  source=z.read('TANDI04/SOURCE/src/TANDI.C')
  assert b'\n' not in source.replace(b'\r\n',b'')
  for n in ['UI04.TXT','NOTICE.TXT','EVIDENCE/UITEST.JSON','EVIDENCE/ARTUI04.JSON']:
   assert (ROOT/n).read_bytes()==z.read('TANDI04/'+n),n
  ui=json.loads(z.read('TANDI04/EVIDENCE/UITEST.JSON'))
  assert ui['status']=='passed' and ui['exe_sha256']==pins['RUN/TANDI.EXE']['sha256']
  assert ui['database_sha256']==pins['RUN/TANDY.DAT']['sha256']
  assert len(ui['runs'])==3
  for r in ui['runs']:
   assert (r['question_count'],r['name_count'],r['keys'],r['mouse_corners'])==(130,256,5,10)
   assert r['outside_click_ignored'] and r['redraws_exact'] and r['moving_eyes_preserved']
  art=json.loads(z.read('TANDI04/EVIDENCE/ARTUI04.JSON'))
  assert art['passed']==8 and art['failed']==art['skipped']==0
 print('PASS: artifact hashes, 129 entries, 128 internal hashes, new UI/source pins, unchanged core/data/art/fallback and exact three-mode evidence')
if __name__=='__main__':main()
