from pathlib import Path
import hashlib,json,zipfile
P=Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
m=json.loads((P/'PACKAGE.JSON').read_text())
assert sha((P/'TANDI08.ZIP').read_bytes())==m['zip_sha256']
assert sha((P/'PREVIEW.PNG').read_bytes())==m['preview_sha256']
assert sha((P/'SOURCE.DIF').read_bytes())==m['source_diff_sha256']
with zipfile.ZipFile(P/'TANDI08.ZIP') as z:
 assert z.testzip() is None
 manifest=z.read('TANDI08/SHA256.TXT').decode().splitlines()
 expected={'TANDI08/SHA256.TXT'}
 for row in manifest:
  digest,path=row.split('  ',1);name='TANDI08/'+path;expected.add(name);assert sha(z.read(name))==digest,name
 assert set(z.namelist())==expected and len(expected)==m['files']
 for name in z.namelist():
  ext=Path(name).suffix.upper();assert ext not in {'.DRV','.DLL','.FON','.LIB','.OBJ','.COM'},name
  if ext=='.EXE':assert Path(name).name=='TANDI.EXE',name
 assert sha(z.read('TANDI08/RUN/TANDI.EXE'))==m['exe_sha256']
 assert sha(z.read('TANDI08/RUN/TANDY.DAT'))==m['standard_dat_sha256']=='c952b6c4d5f7b12c469ce73bf8fe9a18fa0c560cac03f339df74779b22ae455f'
 assert sha(z.read('TANDI08/SOURCE/build/AUDIT08.DAT'))==m['audit_dat_sha256']=='8ad48837d8298b5618e253a05d64067cb4858085464d655379e3382d54b34637'
 assert sha(z.read('TANDI08/SOURCE/src/ENGINE.C'))=='970f9ff2c1750f71aa392d36e801067a1aca7709fbc64837dfaee4fa86ed4b99'
 assert sha(z.read('TANDI08/SOURCE/src/DB.C'))=='e3f078fc5d9534b78b30e102390da98324dce345ec2a3261393a1ae0ebf4a788'
 n=json.loads(z.read('TANDI08/SOURCE/evidence/NATIVE08.JSN'))
 for run in n['modes']:
  assert run['exe_sha256']==m['exe_sha256'] and run['database_sha256']==m['standard_dat_sha256']
  assert all(run[k] for k in ['partial_repaint_exact','border_expose_exact','focus_restore_exact'])
 c=json.loads(z.read('TANDI08/SOURCE/evidence/COMPARE.JSN'));assert c['experimental']['added']['first_guess_misses']==19 and c['new_first_guess_misses'][0]['target']=='Lionel Messi'
 assert not m['canonical_defaults_changed'] and not m['publication_performed']
print('PASS: exact local TANDI08 archive, all manifests/pins, native hashes and platform exclusions')
