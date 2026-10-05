#!/usr/bin/env python3
"""Read-only exact kit validation; no emulator or licensed inputs required."""
from pathlib import Path
import hashlib,json
K=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={}
for line in (K/'MANIFEST.SHA').read_text().splitlines():
 h,n=line.split('  ',1);assert n not in expected;expected[n]=h
actual={str(p.relative_to(K)):sha(p) for p in K.rglob('*') if p.is_file() and p.name!='MANIFEST.SHA' and '__pycache__' not in p.parts}
assert actual==expected,'Manifest mismatch'
assert {str(p.relative_to(K)) for p in K.rglob('*.EXE')}=={'BIN/WHEEL.EXE','BIN/WXTSPL.EXE'}
for p in K.rglob('*'):
 if p.is_file():
  assert p.name.upper() not in {'WIN.COM','KERNEL.EXE','USER.EXE','GDI.EXE','CL.EXE','LINK4.EXE','SETUP.EXE'}
  assert p.suffix.upper() not in {'.FON','.DRV','.LIB','.OBJ','.AVI'}
  if p.suffix.upper() in {'.TXT','.MD','.C','.H','.PY','.BAT','.JSN','.LOG','.SHA','.CNF'}:assert b'\n' not in p.read_bytes().replace(b'\r\n',b''),str(p)
r=json.loads((K/'EVIDENCE/NATIVE/RUNTIME.JSN').read_text())
for name,item in r.items():assert sha(K/'BIN'/name)==item['sha256']==item['executed_guest_sha256']
assert json.loads((K/'EVIDENCE/NATIVE/RESULT.JSN').read_text())['pass']
assert json.loads((K/'EVIDENCE/HOST/SPLSAN.JSN').read_text())['pass']
assert (K/'EVIDENCE/HOST/WHEEL.LOG').read_text().count('MOCK PASS ')==10
print('PASS exact manifest, qualified runtimes, host/native evidence, CRLF and payload allowlist')
