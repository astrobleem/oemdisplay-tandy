"""Exact preceding PAN sources, solely to reproduce its accepted packets.

The current compact sources need their own native qualification and review.
This archive never accepts a new runtime or weakens its original source pins.
"""
from pathlib import Path
import hashlib,io,zipfile
ROOT=Path(__file__).resolve().parents[2]
NAMES=('src/cga/INSTALLT.PY', 'src/cga/PACKCGA.PY', 'src/cga/SETUP.C', 'tools/PAN/CGASTAGE.PY', 'tools/PAN/GUIDES/CGA.TXT', 'tools/PAN/PREPCGA.PY', 'tools/PAN/PUBLISH.PY', 'tools/PAN/COMPOSE.PY')
SHA='06e4587883d68684552b1b9005be7ae6b23b10a438d768d9b36965a0f5cdf1b9'

def previous_source(name,pin):
 def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
 data=(ROOT/name).read_bytes()
 if identity(data)==pin:return data
 if name not in NAMES:raise ValueError('Changed historical PAN source outside snapshot: '+name)
 raw=(ROOT/'docs/QUAL/CGACMP/SRCPAN.ZIP').read_bytes()
 if hashlib.sha256(raw).hexdigest()!=SHA:raise ValueError('Changed preceding PAN source snapshot')
 with zipfile.ZipFile(io.BytesIO(raw)) as z:
  if len(z.namelist())!=len(NAMES) or set(z.namelist())!=set(NAMES) or z.testzip():raise ValueError('Preceding PAN source inventory differs')
  data=z.read(name)
 if identity(data)!=pin:raise ValueError('Preceding PAN source pin differs: '+name)
 return data
