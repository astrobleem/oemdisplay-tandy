from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((P/'PACKAGE.JSON').read_text())
assert sha((P/'TANDI09.ZIP').read_bytes())==m['zip_sha256']
assert sha((P/'PREVIEW.PNG').read_bytes())==m['preview_sha256']
assert sha((P/'SOURCE.DIF').read_bytes())==m['source_diff_sha256']
with zipfile.ZipFile(P/'TANDI09.ZIP') as z:
 assert z.testzip() is None
 expected={'TANDI09/SHA256.TXT'}
 for row in z.read('TANDI09/SHA256.TXT').decode().splitlines():
  digest,path=row.split('  ',1);name='TANDI09/'+path
  assert '..' not in Path(path).parts and not Path(path).is_absolute()
  expected.add(name);assert sha(z.read(name))==digest,name
 assert set(z.namelist())==expected and len(expected)==m['files']
 for name in z.namelist():
  assert Path(name).suffix.upper() not in {'.DRV','.DLL','.FON','.LIB','.OBJ','.COM'}
  if Path(name).suffix.upper()=='.EXE':assert Path(name).name=='TANDI.EXE'
 assert sha(z.read('TANDI09/RUN/TANDI.EXE'))==m['exe_sha256']
 assert sha(z.read('TANDI09/RUN/TANDY.DAT'))==m['standard_dat_sha256']=='c952b6c4d5f7b12c469ce73bf8fe9a18fa0c560cac03f339df74779b22ae455f'
 assert sha(z.read('TANDI09/SOURCE/build/AUDIT08.DAT'))==m['audit_dat_sha256']=='8ad48837d8298b5618e253a05d64067cb4858085464d655379e3382d54b34637'
 base=json.loads(z.read('TANDI09/SOURCE/evidence/BASELINE.JSN'))
 assert base['packet_sha256']=='dd34d2948f7f9270072d4d418aacd9c120b5b788846741ec432cf4744377c2d2'
 for name in ['src/ENGINE.C','src/DB.C','src/TDSOUND.C','src/ART.H','data/STARTER.JSON','data/AUDIT08.JSON']:
  assert sha(z.read('TANDI09/SOURCE/'+name))==base['files'][name]
 assert sha(z.read('TANDI09/SOURCE/tests/BEFORE09.C'))==base['files']['src/TANDI.C']
 n=json.loads(z.read('TANDI09/SOURCE/evidence/NATIVE09.JSN'))
 for run in n['modes']:
  assert run['exe_sha256']==m['exe_sha256'] and run['database_sha256']==m['standard_dat_sha256']
  assert all(run[k] for k in ['partial_repaint_exact','border_expose_exact','focus_restore_exact','leading_count_repaint_exact'])
  assert run['eyes']['only_eye_rectangles_changed']
 assert n['bad_dat']['exe_sha256']==m['exe_sha256']
 noise=json.loads(z.read('TANDI09/SOURCE/evidence/NOISE09.JSN'))
 assert noise['standard']['final_failures']==31 and noise['audit08']['final_failures']==36
 assert noise['standard']['solved']==225 and noise['audit08']['solved']==220
 assert noise['audit08']['dat_sha256']==m['audit_dat_sha256']
 c=json.loads(z.read('TANDI09/SOURCE/evidence/CHECK09.JSN'))
 assert c['passed'] and c['claude_36_vs_31_verified']
 for tag in ['STANDARD','AUDIT08']:
  examples=json.loads(z.read('TANDI09/SOURCE/evidence/EXAMPLES-'+tag+'.JSN'))
  assert len(examples)==512 and len({r['target'] for r in examples})==256
 assert not m['canonical_defaults_changed'] and not m['publication_performed']
 assert m['claude_36_vs_31_verified'] and not m['physical_hardware_tested']
print('PASS: exact local TANDI09, baseline/data pins, native hashes, all-character examples, manifest and exclusions; confirmed independent noisy-game regression explicitly recorded')
