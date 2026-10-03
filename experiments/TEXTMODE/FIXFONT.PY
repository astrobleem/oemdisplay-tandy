"""Lab-only: build fixed-cell system font from owner's existing Windows fonts.
No font bytes are redistributed. Keep original CGASYS module identity so
Windows' system and fixed font modules do not become the same loaded module.
"""
from pathlib import Path
import struct,sys,hashlib,json

def resources(data):
 ne=struct.unpack_from('<I',data,60)[0];p=ne+struct.unpack_from('<H',data,ne+36)[0];shift=struct.unpack_from('<H',data,p)[0];p+=2;out={}
 while True:
  typ,n=struct.unpack_from('<HH',data,p);p+=8
  if typ==0:break
  for i in range(n):
   off,length,flags,rid=struct.unpack_from('<HHHH',data,p);out[(typ,rid)]=(p,off<<shift,length<<shift,shift);p+=12
 return out
src=Path(sys.argv[1]);fixed=Path(sys.argv[2]);dest=Path(sys.argv[3])
a=bytearray(src.read_bytes());b=fixed.read_bytes()
if hashlib.sha256(a).hexdigest()!='baf8fa607806d949dfb6992113ce93494678abdef07783b22222b62e5de28ef4':raise SystemExit('Unsupported CGASYS input; leave the installation unchanged')
if hashlib.sha256(b).hexdigest()!='b0c043a65e2b551bce3c77d25921394dfd2533f50633bc129abd240c7aeb5f89':raise SystemExit('Unsupported CGAFIX input; leave the installation unchanged')
ar,br=resources(a),resources(b)
for key in [(0x8007,0x8001),(0x8008,0x801b)]:
 ent,off,size,shift=ar[key];_,boff,bsize,_=br[key]
 if bsize>size:raise SystemExit('Fixed resource cannot fit original slot')
 a[off:off+size]=b[boff:boff+bsize]+bytes(size-bsize)
 # Preserve the original slot length, offsets, and NE module identity.
# FNT resource's embedded size retains the exact donor length.
dest.write_bytes(a)
print(json.dumps({'output':str(dest),'sha256':hashlib.sha256(a).hexdigest(),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'donor_sha256':hashlib.sha256(b).hexdigest(),'changed_resources':['FONTDIR','FONT27'],'module_identity':'original CGASYS'},indent=2))
