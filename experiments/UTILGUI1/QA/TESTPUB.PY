#!/usr/bin/env python3
"""Exact GUI trial validation; no emulator or licensed guest required."""
from pathlib import Path
import hashlib,json
K=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected={}
for line in (K/'MANIFEST.SHA').read_text().splitlines():h,n=line.split('  ',1);assert n not in expected;expected[n]=h
actual={str(p.relative_to(K)):sha(p) for p in K.rglob('*') if p.is_file() and p.name!='MANIFEST.SHA' and '__pycache__' not in p.parts};assert actual==expected
assert {str(p.relative_to(K)) for p in K.rglob('*.EXE')}=={'BIN/EXJOY.EXE','BIN/DROPRX.EXE','BIN/DROPTX.EXE','BIN/CDTEST.EXE','BIN/CDSTART.EXE'}
assert {str(p.relative_to(K)) for p in K.rglob('*.DLL')}=={'BIN/COMMDLG.DLL'}
assert {str(p.relative_to(K)) for p in K.rglob('*.LIB')}=={'BIN/TDROP.LIB'}
for p in K.rglob('*'):
 if p.is_file():
  assert p.suffix.upper() not in {'.FON','.DRV','.OBJ','.AVI'}
  assert p.name.upper() not in {'WIN.COM','KERNEL.EXE','USER.EXE','GDI.EXE','CL.EXE','LINK4.EXE','SETUP.EXE'}
  if p.suffix.upper() in {'.C','.H','.ASM','.PY','.BAT','.RSP','.DEF','.TXT','.MD','.LOG','.JSN','.SHA'}:assert b'\n' not in p.read_bytes().replace(b'\r\n',b'')
for name,pin in json.loads((K/'BIN/SOURCES.JSN').read_text()).items():assert sha(K/name)==pin
report=json.loads((K/'EVIDENCE/NATIVE/SUMMARY.JSN').read_text());assert report['pass'] and report['qualified_cases']==26
assert len(report['screens'])==30
assert report['supplementary_queued_paint_cases']==1
assert json.loads((K/report['queued_paint_record']).read_text())['pass']
assert json.loads((K/'EVIDENCE/PROBE3204/PORTABLE.JSN').read_text())['pass']
for label,item in report['cases'].items():
 r=json.loads((K/item['result']).read_text())
 if label.endswith('/NORMAL'):
  assert r['pass'] and r['normal_diagnostic_logs_absent'] and r['original_fixture_unchanged'] and r['cpu_sentinels_pass']
  for name,pin in r['runtime'].items():assert sha(K/'BIN'/name)==pin
 elif label.endswith('/EXJOY') or label=='PORTTEST':assert r['passed'] and r['app_sha256']==sha(K/'BIN/EXJOY.EXE')
 elif label.endswith('/FILEDROP'):assert r['dos_return'] and r['returncode']==0 and 'DISPLAY PAIR PASS' in r['logs']['DROPRX.LOG']
 else:assert r['final_pass'] and r['dos_return'] and not r['fail_lines']
print('PASS exact manifest, first-party allowlist, 26 qualified cases, 30 native screenshots, CRLF')
