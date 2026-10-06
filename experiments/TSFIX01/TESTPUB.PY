"""Read-only verification of the isolated TSHELL review packet."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,zipfile
root=Path(__file__).resolve().parent
pins=json.loads((root/'SHA256.JSN').read_text());path=root/pins['zip']['name']
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert path.stat().st_size==pins['zip']['bytes'] and sha(path)==pins['zip']['sha256']
assert sha(root/'FIXES.PATCH')==pins['patch_sha256']
assert sha(root/'BROWSE.PNG')==pins['preview_sha256']
assert sha(root/'SUMMARY.JSN')==pins['summary_sha256']
with tempfile.TemporaryDirectory(prefix='tsfix-verify-') as td:
 with zipfile.ZipFile(path) as z:
  names=z.namelist();assert len(names)==len(set(names)) and z.testzip() is None
  for name in names:assert name.startswith('TSFIX01/') and not name.startswith('/') and '..' not in Path(name).parts
  for info in z.infolist():assert (info.external_attr>>16)&0o170000!=0o120000
  z.extractall(td)
 kit=Path(td)/'TSFIX01';subprocess.run([sys.executable,str(kit/'VERIFY.PY')],check=True)
 assert (root/'FIXES.PATCH').read_bytes()==(kit/'FIXES.PATCH').read_bytes()
 assert (root/'SUMMARY.JSN').read_bytes()==(kit/'EVIDENCE/SUMMARY.JSN').read_bytes()
 assert (root/'BROWSE.PNG').read_bytes()==(kit/'EVIDENCE/IMAGES/320.PNG').read_bytes()
 for name,pin in pins['runtime'].items():assert (kit/'RUN'/name).stat().st_size==pin['bytes'] and sha(kit/'RUN'/name)==pin['sha256']
 for pin in pins['patch_targets']:
  relative=pin['path'].removeprefix('examples/TSHELL/')
  assert sha(kit/'SOURCE'/relative)==pin['after_sha256']
 summary=json.loads((kit/'EVIDENCE/SUMMARY.JSN').read_text())
 assert summary['native_checks']==155 and len(summary['accepted_native_runs'])==10
print('PASS TSFIX01 exact packet, archive members, patch/source/runtime identities and final qualification')
