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
print('PASS sealed Maze/Starfield kit, file hashes, CRC, 32 lifecycle cases, 240 scene comparisons and payload scope.')
