#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,zipfile
p=Path(__file__).resolve().parent
manifest=json.loads((p/'SHA256.JSN').read_text())
for name,digest in manifest.items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
with zipfile.ZipFile(p/'VISPART2.ZIP') as z:
 assert z.testzip() is None
 names=z.namelist();assert all(n.startswith('VISPART2/') and '..' not in Path(n).parts for n in names)
 inside=json.loads(z.read('VISPART2/SHA256.JSN'))
 assert sorted(n for n in names if n.upper().endswith('.EXE'))==['VISPART2/RUN/MAZE.EXE','VISPART2/RUN/STARFLD.EXE']
 assert not any(n.upper().endswith(('.DRV','.FON','.DLL','.IMG','.ISO','.OBJ','.SO')) for n in names)
 for name,digest in inside.items():assert hashlib.sha256(z.read('VISPART2/'+name)).hexdigest()==digest,name
 assert len(names)==len(inside)+1
 for app in ['MZLIFE','STLIFE']:
  text=z.read('VISPART2/EVIDENCE/'+app+'.LOG').decode('ascii')
  assert text.count('changed_units=0 active_ok=1')==16 and 'QA DONE' in text and 'INPUT LEAK' not in text and 'FAIL' not in text
 for tag in ['AR160','AR320','AR640','PL160','PL320','PL640']:
  text=z.read('VISPART2/EVIDENCE/'+tag+'.LOG').decode('ascii');assert text.count('mismatched_bytes=0')==40
 a=z.read('VISPART2/EVIDENCE/MZQUIET0.LOG').decode('ascii');b=z.read('VISPART2/EVIDENCE/MZQUIET1.LOG').decode('ascii')
 assert 'PROFILE visible_first_ms=1648' in a and 'PROFILE visible_first_ms=3240' in b
 assert 'setup_ms=2581' in b
 assert 'steady ray_ms=55 fills_ms=4119 copy_ms=5438' in b
 assert json.loads(z.read('VISPART2/EVIDENCE/DRIVER.JSN'))['sha256']=='f922f12168de69ec2f8a761ce7fce2cbe2080b9e3fcfb06e3a3dac4faba6d502'
print('PASS sealed Maze/Starfield kit, scope, lifecycle/scene checks and corrected matched-boundary timing evidence.')
