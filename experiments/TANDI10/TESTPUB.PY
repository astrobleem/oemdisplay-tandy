"""Verify first-party packet contents; never execute an installer or emulator."""
from pathlib import Path
import hashlib,json,zipfile
p=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((p/'PACKAGE.JSON').read_text())
assert sha((p/'TANDI10.ZIP').read_bytes())==m['zip_sha256']
for name,key in [('PREVIEW.PNG','preview_sha256'),('SOURCE.DIF','source_diff_sha256'),('TSHELL.DIF','shell_diff_sha256')]:assert sha((p/name).read_bytes())==m[key]
with zipfile.ZipFile(p/'TANDI10.ZIP') as z:
 assert z.testzip() is None
 expected={'TANDI10/SHA256.TXT'}
 for line in z.read('TANDI10/SHA256.TXT').decode().splitlines():
  digest,path=line.split('  ',1);assert '..' not in Path(path).parts and not Path(path).is_absolute()
  name='TANDI10/'+path;expected.add(name);assert sha(z.read(name))==digest,name
 assert len(expected)==m['files'] and set(z.namelist())==expected
 allowed_exe={'TANDI10/RUN/TANDI.EXE','TANDI10/SOURCE/src/TANDI.EXE','TANDI10/SOURCE/tests/LAUNCH10.EXE','TANDI10/TSHELL/TSHELL.EXE','TANDI10/TSHELL/TS10QA.EXE'}
 for name in expected:
  suffix=Path(name).suffix.upper()
  assert suffix not in {'.DRV','.FON','.LIB','.OBJ','.COM'},name
  if suffix=='.EXE':assert name in allowed_exe,name
  if suffix=='.DLL':assert name=='TANDI10/TSHELL/TSINPUT.DLL',name
 exe=z.read('TANDI10/RUN/TANDI.EXE');assert sha(exe)==m['exe_sha256']
 assert b'App 0.3.7; roster revision 0.3.2.' in exe
 assert z.read('TANDI10/SOURCE/src/TANDI.EXE')==exe
 assert sha(z.read('TANDI10/RUN/TANDY.DAT'))==m['standard_dat_sha256']=='c952b6c4d5f7b12c469ce73bf8fe9a18fa0c560cac03f339df74779b22ae455f'
 assert sha(z.read('TANDI10/SOURCE/build/AUDIT08.DAT'))==m['audit_dat_sha256']=='8ad48837d8298b5618e253a05d64067cb4858085464d655379e3382d54b34637'
 base=json.loads(z.read('TANDI10/SOURCE/evidence/BASE10.JSN'))
 assert base['packet_sha256']=='da14fd8c55ca68782239ded222b60f05735b5a9aaadd18a2b3c324fdcea1b9af'
 for name in ['src/ENGINE.C','src/DB.C','src/OBSERVE.C','src/TDSOUND.C','src/ART.H','data/STARTER.JSON','data/AUDIT08.JSON']:
  assert sha(z.read('TANDI10/SOURCE/'+name))==base['source_files'][name]
 native=json.loads(z.read('TANDI10/SOURCE/evidence/NATIVE10.JSN'))
 assert native['status']=='passed' and len(native['runs'])==19
 for r in native['runs']:
  assert r['exe_sha256']==m['exe_sha256'] and r['returncode']==0
  if not r.get('negative',False):assert r['database_sha256']==m['standard_dat_sha256']
 art=json.loads(z.read('TANDI10/SOURCE/evidence/ART10.JSN'))
 assert {r['mode'] for r in art['modes']}==set(m['qualified_runtime_modes'])
 assert all(r['cabinet_exact_outside_animated_face'] and r['logo_exact'] and r['wake_all_black'] and r['six_positions'] for r in art['modes'])
 audit=json.loads(z.read('TANDI10/SOURCE/evidence/AUDIT.JSON'))
 assert audit['exe_sha256']==m['exe_sha256'] and not audit['unsupported_or_fpu']
 shellbase=json.loads(z.read('TANDI10/TSHELL/BASELINE.JSN'))
 assert len(shellbase['verified_main_git_blobs'])==38
 assert sha(z.read('TANDI10/TSHELL/TSINPUT.DLL'))==shellbase['files']['TSINPUT.DLL']
 assert sha(z.read('TANDI10/TSHELL/TSHELL.EXE'))==m['optional_shell_sha256']
 shell=json.loads(z.read('TANDI10/SOURCE/evidence/SHELL10.JSN'))
 assert len(shell['modes'])==3 and all(r['optional_shell_sha256']==m['optional_shell_sha256'] and 'COMPLETE PASS' in r['log'] and ' FAIL' not in r['log'] for r in shell['modes'])
 assert not m['canonical_defaults_changed'] and not m['settings_written_by_demo'] and not m['learning_enabled']
 assert m['two_wrong_final_failures']=={'standard':31,'audit08':36}
 readme=z.read('TANDI10/RUN/README.TXT')
 assert b'31 standard versus 36 AUDIT08' in readme and b'awaits the exact harness' not in readme
 assert b'do not\r\nguarantee protection from CRT burn-in' in readme
print('PASS: TANDI10 exact packet, 19 native runs, translated art/eyes/black frames, unchanged engine/data, optional fourth saver, noise disclosure and exclusions')
