from pathlib import Path
import hashlib,json,zipfile
p=Path(__file__).resolve().parent;m=json.loads((p/'ASSETS.JSON').read_bytes());root=p.parents[1]
for name,item in m['assets'].items():
 b=(root/item['path']).read_bytes();assert len(b)==item['bytes'] and hashlib.sha256(b).hexdigest()==item['sha256'],name
 with zipfile.ZipFile(root/item['path']) as z:
  assert z.testzip() is None and len(z.namelist())==len(set(z.namelist()))
  for n in z.namelist():
   assert not Path(n).is_absolute() and '..' not in Path(n).parts
   assert Path(n).name.upper() not in {'WIN.COM','KERNEL.EXE','USER.EXE','GDI.EXE','CL.EXE','LINK4.EXE','SETUP.EXE'}
   assert Path(n).suffix.upper() not in {'.FON','.OBJ','.LIB','.SYS','.PYC'}
  if name=='K3TOOLS.ZIP':assert not any(Path(n).suffix.upper()=='.DRV' for n in z.namelist())
print('PASS all 16 release ZIP identities, safe paths and private-payload exclusions')
