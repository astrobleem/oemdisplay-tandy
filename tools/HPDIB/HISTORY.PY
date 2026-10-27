"""Exact preceding PAN sources solely for historical acceptance replay."""
from pathlib import Path
import hashlib,io,zipfile
ROOT=Path(__file__).resolve().parents[2]
NAMES=('.github/workflows/current.yml', 'tools/CURRENT/BUNDLE.PY', 'tools/CURRENT/CHECK.PY', 'tools/XR1PACK/PUBLISH.PY', 'tools/PAN/PUBLISH.PY')
SHA='ee4e192db3347c4e55aa056e30dc01ed5f847d11fb2972a09e4db13cd7e23e2c'

def previous_source(name,pin):
 def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 data=(ROOT/name).read_bytes()
 if identity(data)==pin:return data
 if name not in NAMES:raise ValueError('Changed historical PAN source outside snapshot: '+name)
 raw=(Path(__file__).parent/'BASE/SRCPAN.ZIP').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Changed preceding PAN source snapshot')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if len(z.namelist())!=len(NAMES) or set(z.namelist())!=set(NAMES):raise ValueError('Preceding PAN source inventory differs')
  data=z.read(name)
 if identity(data)!=pin:raise ValueError('Preceding PAN source pin differs: '+name)
 return data
