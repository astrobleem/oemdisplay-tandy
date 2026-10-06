#!/usr/bin/env python3
"""Read-only exact publication check for the standalone TANDI07 trial."""
from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
package=json.loads((P/'PACKAGE.JSON').read_text())
assert sha((P/'TANDI07.ZIP').read_bytes())==package['sha256']=='4d1998d6536c1e4b297635f8fd382f85520716f6a8ea3038c42bd8ad55a6ba3f'
assert sha((P/'PREVIEW.PNG').read_bytes())==package['preview_sha256']=='1b5549b6a2583998dd399340056a0fdc99679bebaec833561d8c4d41af12e62b'
assert sha((P/'SOURCE.DIF').read_bytes())==package['source_diff_sha256']
with zipfile.ZipFile(P/'TANDI07.ZIP') as z:
 assert z.testzip() is None
 names=z.namelist();assert len(names)==len(set(names))==835
 assert all(n.startswith('TANDI07/') and '..' not in Path(n).parts for n in names)
 expected=set()
 for row in z.read('TANDI07/SHA256.TXT').decode().splitlines():
  h,n=row.split('  ',1);expected.add('TANDI07/'+n);assert sha(z.read('TANDI07/'+n))==h,n
 assert expected==set(names)-{'TANDI07/SHA256.TXT'}
 assert not any('/WINDOWS/' in n.upper() or Path(n).suffix.upper() in ['.DRV','.DLL','.COM','.OBJ'] for n in names)
 for n in names:
  if (n.startswith('TANDI07/SOURCE/tests/') or n.startswith('TANDI07/SOURCE/src/')) and Path(n).suffix.upper() in ['.C','.H','.TXT','.PY']:
   data=z.read(n);data.decode('ascii');assert b'\n' not in data.replace(b'\r\n',b''),n
 assert {n for n in names if n.upper().endswith('.EXE')}=={'TANDI07/RUN/TANDI.EXE','TANDI07/SOURCE/src/TANDI.EXE'}
 pins={'RUN/TANDI.EXE':'b7cc1627f973ab266873223c8d8b3968393bb5db349f6f49f2fc42a68db07249',
 'RUN/TANDY.DAT':'c952b6c4d5f7b12c469ce73bf8fe9a18fa0c560cac03f339df74779b22ae455f',
 'SOURCE/src/ENGINE.C':'970f9ff2c1750f71aa392d36e801067a1aca7709fbc64837dfaee4fa86ed4b99',
 'SOURCE/src/DB.C':'e3f078fc5d9534b78b30e102390da98324dce345ec2a3261393a1ae0ebf4a788',
 'SOURCE/data/STARTER.JSON':'9b6455a7bde9c015e378be8faac0aa2b73e834c8b961d477b35f4a2203aaa341',
 'SOURCE/art/CABINET.PNG':'960fb2033e3aeaa7c0d550e228e8fcf69cdad6dace8a13571a9b5f068bf5251b',
 'SOURCE/art/PARTS.PNG':'6ae9d955e6feaf6bd0585e82fd7ed5cda6b743b929913fede5ac0cb951ebbcb1'}
 for n,h in pins.items():assert sha(z.read('TANDI07/'+n))==h,n
 assert sha(z.read('TANDI07/SOURCE/src/TANDI.EXE'))==pins['RUN/TANDI.EXE']
 assert json.loads(z.read('TANDI07/EVIDENCE/QTEST06.JSON'))['status']=='passed'
 assert json.loads(z.read('TANDI07/EVIDENCE/UITEST.JSON'))['status']=='passed'
 art=json.loads(z.read('TANDI07/EVIDENCE/ARTTEST.JSON'));assert art['passed']==8 and art['failed']==art['skipped']==0
 assert len(json.loads(z.read('TANDI07/EVIDENCE/ANIMTEST.JSON')))==3
 assert '36 checks, 0 failures' in z.read('TANDI07/EVIDENCE/UIGUARD.TXT').decode()
 assert z.read('TANDI07/EVIDENCE/SOUNDHOST.TXT').decode().count('PASS: 59')==2
 assert 'PASS: ASCII/CRLF source format' in z.read('TANDI07/EVIDENCE/SOUNDHOST.TXT').decode()
 final=json.loads(z.read('TANDI07/EVIDENCE/FINAL07.JSON'))
 for mode in ['320x200x16','640x200x2','640x200x4']:
  r=json.loads(z.read('TANDI07/EVIDENCE/'+mode+'/RESULT.JSON'))
  assert r['exe_sha256']==pins['RUN/TANDI.EXE'] and r['database_sha256']==pins['RUN/TANDY.DAT']
  for m in final['new_native_flow_metrics']:assert m+'=1\n' in r['log'],(mode,m)
  for m in ['ERRORS=0','COMPLETE=1','SOUND_FAILURES=0','SOUND_LATE_ABORTS=0']:assert m+'\n' in r['log']
  assert r['partial_repaint_exact'] and r['border_expose_exact'] and r['focus_restore_exact']
  assert r['eyes']['only_eye_rectangles_changed'] and r['eyes']['changed_pixels']>0
  assert z.read('TANDI07/EVIDENCE/'+mode+'/SECOND.TXT').decode().strip()=='KEEP'
  assert z.read('TANDI07/EVIDENCE/'+mode+'/FIRST.TXT')==z.read('TANDI07/RUN/README.TXT')
 bad=json.loads(z.read('TANDI07/EVIDENCE/CORRUPT/RESULT.JSON'))
 assert bad['negative'] and bad['exe_sha256']==pins['RUN/TANDI.EXE']
 assert all(m+'\n' in bad['log'] for m in ['APP_ERROR=1','BAD_DAT_EXIT_ONLY=1','COMPLETE=1'])
 assert bad['returned'].strip()=='RETURNED'
print('PASS: 835 archived files, exact runtime/data/art pins, source recipes, three native modes, corrupt-DAT launch, installer protection and platform exclusions.')
print('Physical hardware and independent factual-accuracy qualification remain pending.')
