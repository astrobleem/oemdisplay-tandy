"""Verify local TANDI11 archive without running any installer or emulator."""
from pathlib import Path
import hashlib,json,zipfile
p=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((p/'PACKAGE.JSON').read_text());assert sha((p/'TANDI11.ZIP').read_bytes())==m['zip_sha256']
for name,key in [('SOURCE.DIF','source_diff_sha256'),('PREVIEW.PNG','preview_sha256'),('TESTPUB.PY','verifier_sha256')]:assert sha((p/name).read_bytes())==m[key]
with zipfile.ZipFile(p/'TANDI11.ZIP') as z:
 assert z.testzip() is None
 expected={'TANDI11/SHA256.TXT'}
 for line in z.read('TANDI11/SHA256.TXT').decode().splitlines():
  digest,name=line.split('  ',1);assert '..' not in Path(name).parts and not Path(name).is_absolute()
  key='TANDI11/'+name;expected.add(key);assert sha(z.read(key))==digest,key
 assert set(z.namelist())==expected and len(expected)==m['files']
 for name in expected:
  suffix=Path(name).suffix.upper();assert suffix not in {'.DRV','.FON','.LIB','.OBJ','.COM','.DLL','.SYS','.LRN','.BAK','.TMP','.BKT','.PYC'},name
  if suffix=='.EXE':assert name in {'TANDI11/RUN/TANDI.EXE','TANDI11/SOURCE/src/TANDI.EXE','TANDI11/SOURCE/tests/LAUNCH10.EXE'},name
 exe=z.read('TANDI11/RUN/TANDI.EXE');assert sha(exe)==m['exe_sha256'] and exe==z.read('TANDI11/SOURCE/src/TANDI.EXE')
 assert b'App 0.3.8; roster rev 0.3.2. F5 notes.' in exe
 assert sha(z.read('TANDI11/RUN/TANDY.DAT'))==m['standard_dat_sha256']=='c952b6c4d5f7b12c469ce73bf8fe9a18fa0c560cac03f339df74779b22ae455f'
 host=json.loads(z.read('TANDI11/SOURCE/evidence/HOST11.JSN'))
 assert host['status']=='passed' and host['host_checks']==226 and host['full_roster_games']==30720 and host['dgroup_plus_heap_stack']<65536
 for name,digest in host['source_files'].items():assert sha(z.read('TANDI11/SOURCE/'+name))==digest,name
 base=json.loads(z.read('TANDI11/SOURCE/evidence/BASE11.JSN'))
 assert base['base_packet_sha256']==m['base_packet_sha256']
 for name,digest in base['unchanged_files'].items():assert sha(z.read('TANDI11/SOURCE/'+name))==digest,name
 native=json.loads(z.read('TANDI11/SOURCE/evidence/NATIVE11.JSN'))
 assert native['status']=='passed' and len(native['runs'])==19
 for r in native['runs']:
  assert r['exe_sha256']==m['exe_sha256'] and r['returncode']==0 and r['normal_report_sentinels_unchanged']
  if not r['negative']:assert r['database_sha256']==m['standard_dat_sha256']
 env=json.loads(z.read('TANDI11/SOURCE/evidence/ENV11.JSN'));assert env['status']=='passed' and len(env['runs'])==19
 assert all(r['exe_sha256']==m['exe_sha256'] and r['win_com_sha256']=='8c8901b4c8482a2aefcf8a0a1beaba2ee07f90af94bf23993a8cf49eb6a30ebc' for r in env['runs'])
 art=json.loads(z.read('TANDI11/SOURCE/evidence/ART11.JSN'))
 assert {r['mode'] for r in art}=={'320x200x16','640x200x2','640x200x4'}
 assert all(r['exe_sha256']==m['exe_sha256'] and r['logo_exact'] and r['wake_all_black'] and r['six_positions'] for r in art)
 static=json.loads(z.read('TANDI11/SOURCE/evidence/ARTBASE11.JSN'));assert static['passed']==8 and static['failed']==static['skipped']==0
 audit=json.loads(z.read('TANDI11/SOURCE/evidence/AUDIT.JSON'));assert audit['exe_sha256']==m['exe_sha256'] and not audit['unsupported_or_fpu']
 settings=json.loads(z.read('TANDI11/SOURCE/evidence/SET11.JSN'));assert settings['checks']==9 and settings['source_sha256']==host['source_files']['src/TANDI.C']
 full=json.loads(z.read('TANDI11/SOURCE/evidence/FULL11.JSN'));assert full['games']==30720 and full['repeat_exact'] and full['max_questions']==40
 assert full['models']['EMPTY-CANON-OFF-Q25']['0']['first_misses']==23 and full['models']['EMPTY-CANON-OFF-Q25']['2']['failures']==31
 assert m['learning_default']=='OFF every launch' and not m['canonical_defaults_changed'] and not m['publication_performed'] and not m['private_media_included']
print('PASS: exact first-party TANDI11 packet; final source/EXE bound; 226 host checks; 30720 roster games; 19 native runs; original art; private payload excluded.')
