#!/usr/bin/env python3
"""Verify the isolated AUDIT05 kit and its exact evidence bindings."""
from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha((P/'TANDI05.ZIP').read_bytes())=='e81841c245a5af04f85675c1eadb1ef5e211625ae5d079d0b637da8649a94c87','Kit hash mismatch'
with zipfile.ZipFile(P/'TANDI05.ZIP') as z:
 assert z.testzip() is None
 names=z.namelist();assert len(names)==len(set(names))
 assert all(n.startswith('TANDI05/') and '..' not in Path(n).parts for n in names)
 entries=z.read('TANDI05/SHA256.TXT').decode().splitlines()
 expected=set()
 for row in entries:
  h,n=row.split('  ',1);expected.add('TANDI05/'+n);assert sha(z.read('TANDI05/'+n))==h,n
 assert expected==set(names)-{'TANDI05/SHA256.TXT'}
 for n,h in {'RUN/TANDI.EXE':'7b3e1260ae259d6bfa9bc248d92de60c6e79ec5d031652aa76c23385af0ccbb9','RUN/TANDY.DAT':'c952b6c4d5f7b12c469ce73bf8fe9a18fa0c560cac03f339df74779b22ae455f','SOURCE/data/STARTER.JSON':'9b6455a7bde9c015e378be8faac0aa2b73e834c8b961d477b35f4a2203aaa341','SOURCE/data/BEFORE05.JSON':'dc46b91ef521711f97326d82e32aa766c01d6951572a20c873e8ec608424f8ce','SOURCE/evidence/FACTAUDIT.FIXTURE.JSON':'1129d0eb2b464b08f0453105628f03128d7290fa70c719169a313cf81112d8bb'}.items():assert sha(z.read('TANDI05/'+n))==h,n
 audit=json.loads(z.read('TANDI05/SOURCE/data/AUDIT05.JSON'))
 assert len(audit['questions'])==130 and len(audit['cell_changes'])==32
 for n in ['QTEST05.JSON','UITEST05.JSON']:assert json.loads(z.read('TANDI05/EVIDENCE/'+n))['status']=='passed'
 art=json.loads(z.read('TANDI05/EVIDENCE/ART05.JSON'));assert art['passed']==8 and art['failed']==art['skipped']==0
 for mode in ['320x200x16','640x200x2','640x200x4']:
  r=json.loads(z.read('TANDI05/EVIDENCE/'+mode+'/RESULT.JSON'))
  assert r['exe_sha256']==sha(z.read('TANDI05/RUN/TANDI.EXE'))
  assert r['database_sha256']==sha(z.read('TANDI05/RUN/TANDY.DAT'))
  assert 'ERRORS=0\n' in r['log'] and 'COMPLETE=1\n' in r['log'] and 'WRAP_FAILURES=0\n' in r['log']
  assert r['partial_repaint_exact'] and r['border_expose_exact'] and r['focus_restore_exact']
  assert r['eyes']['only_eye_rectangles_changed'] and r['eyes']['changed_pixels']>0
print('AUDIT05 exact kit, 32-cell source delta, preserved independent fixture and three-mode captured evidence verified.')
print('Replay is not factual-accuracy qualification; physical hardware and human testing remain pending.')
