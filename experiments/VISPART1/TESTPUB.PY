#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,zipfile
p=Path(__file__).resolve().parent
manifest=json.loads((p/'SHA256.JSN').read_text())
for name,digest in manifest.items():assert hashlib.sha256((p/name).read_bytes()).hexdigest()==digest,name
with zipfile.ZipFile(p/'VISPART1.ZIP') as z:
 assert z.testzip() is None
 names=z.namelist();assert all(n.startswith('VISPART1/') and '..' not in Path(n).parts for n in names)
 inside=json.loads(z.read('VISPART1/SHA256.JSN'))
 assert sorted(n for n in names if n.upper().endswith('.EXE'))==['VISPART1/RUN/MATRIX.EXE','VISPART1/RUN/XTEYES.EXE']
 assert not any(n.upper().endswith(('.DRV','.FON','.DLL','.IMG','.ISO','.OBJ','.SO')) for n in names)
 for name,digest in inside.items():assert hashlib.sha256(z.read('VISPART1/'+name)).hexdigest()==digest,name
 assert len(names)==len(inside)+1
print('PASS sealed Matrix/XTEyes kit, every file hash, CRC, scope, and no OS/toolchain payload.')
