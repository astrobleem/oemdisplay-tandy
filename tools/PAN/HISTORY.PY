"""Exact immediately preceding unified sources, solely for historical replay."""
from pathlib import Path
import hashlib,io,zipfile
ROOT=Path(__file__).resolve().parents[2]
NAMES=('.github/workflows/current.yml', 'experiments/XYOVERVIEW/XYCTL.C', 'src/cga/CGACTL.C', 'src/cga/PANCTL.C', 'src/panui/PANDLG.C', 'src/panui/PANOWN.C', 'src/panui/PANSTART.C', 'src/softpan/PANCFG.C', 'src/xtpan/XTPAN.C', 'tools/CURRENT/BUNDLE.PY', 'tools/CURRENT/CHECK.PY', 'tools/UPAN/PUBLISH.PY', 'tools/XR1PACK/PUBLISH.PY')
SHA='5dcee205646ca39052243bb633b930a707beeeaac1607c7059afc76fed32b5af'
def previous_source(name,pin):
 def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 data=(ROOT/name).read_bytes()
 if identity(data)==pin:return data
 if name not in NAMES:raise ValueError('Changed historical source outside snapshot: '+name)
 raw=(Path(__file__).parent/'BASE/SRCUPAN.ZIP').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Changed preceding unified source snapshot')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if len(z.namelist())!=len(NAMES) or set(z.namelist())!=set(NAMES):raise ValueError('Preceding source inventory differs')
  data=z.read(name)
 if identity(data)!=pin:raise ValueError('Preceding unified source pin differs: '+name)
 return data
