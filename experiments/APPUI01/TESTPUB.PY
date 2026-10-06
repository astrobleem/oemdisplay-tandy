"""Verify this isolated app trial without running vintage apps or installers."""
from pathlib import Path
import hashlib,json,subprocess,sys,tempfile,zipfile
root=Path(__file__).resolve().parent
pins=json.loads((root/'SHA256.JSN').read_text());path=root/pins['zip']['name']
assert path.stat().st_size==pins['zip']['bytes']
assert hashlib.sha256(path.read_bytes()).hexdigest()==pins['zip']['sha256']
assert hashlib.sha256((root/'PREVIEW.PNG').read_bytes()).hexdigest()==pins['preview_sha256']
with tempfile.TemporaryDirectory(prefix='appui-verify-') as td:
 with zipfile.ZipFile(path) as z:
  names=z.namelist();assert len(names)==len(set(names))
  for name in names:assert name.startswith('APPUI01/') and not name.startswith('/') and '..' not in Path(name).parts
  for info in z.infolist():assert (info.external_attr>>16)&0o170000!=0o120000
  z.extractall(td)
 kit=Path(td)/'APPUI01';subprocess.run([sys.executable,str(kit/'VERIFY.PY')],check=True)
 assert json.loads((kit/'EVIDENCE/RUNTIME.JSN').read_text())==pins['runtime']
 assert (root/'RUNTIME.JSN').read_bytes()==(kit/'EVIDENCE/RUNTIME.JSN').read_bytes()
 assert (root/'SUMMARY.JSN').read_bytes()==(kit/'EVIDENCE/SUMMARY.JSN').read_bytes()
print('PASS APPUI01 archive, all members, source/runtime pins, evidence and payload scope')
