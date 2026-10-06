#!/usr/bin/env python3
"""Audit the emitted Win16 NE module and historical ordinal-linked caller."""
import argparse,hashlib,json,struct,subprocess,re
from pathlib import Path
U16=lambda b,o:struct.unpack_from('<H',b,o)[0]
U32=lambda b,o:struct.unpack_from('<I',b,o)[0]
def nefile(path):
 b=Path(path).read_bytes();ne=U32(b,0x3c)
 assert b[:2]==b'MZ' and b[ne:ne+2]==b'NE'
 entries={};p=ne+U16(b,ne+4);n=1
 while True:
  count,seg=b[p:p+2];p+=2
  if not count:break
  if not seg:n+=count;continue
  for _ in range(count):
   if seg==255:fl,opcode,sg,off=struct.unpack_from('<BHBH',b,p);p+=6
   else:fl,off=struct.unpack_from('<BH',b,p);sg=seg;p+=3
   entries[n]={'flags':fl,'segment':sg,'offset':off};n+=1
 names={}
 for p in [ne+U16(b,ne+0x26),U32(b,ne+0x2c)]:
  while b[p]:
   count=b[p];name=b[p+1:p+1+count].decode('ascii');ordinal=U16(b,p+1+count);p+=3+count
   names[name]=ordinal
 mods=[];im=ne+U16(b,ne+0x2a)
 for i in range(U16(b,ne+0x1e)):
  q=im+U16(b,ne+U16(b,ne+0x28)+i*2);mods.append(b[q+1:q+1+b[q]].decode())
 segments=[];imports=[]
 for i in range(U16(b,ne+0x1c)):
  sec,size,flags,alloc=struct.unpack_from('<HHHH',b,ne+U16(b,ne+0x22)+8*i);off=sec<<U16(b,ne+0x32);size=size or 65536
  segments.append({'offset':off,'bytes':size,'flags':flags,'allocation':alloc})
  if flags&0x100:
   p=off+size;count=U16(b,p);p+=2
   for j in range(count):
    typ,fl,src,m,o=struct.unpack_from('<BBHHH',b,p+j*8)
    if fl&3==1:imports.append((mods[m-1],o))
    elif fl&3==2:imports.append((mods[m-1],b[im+o+1:im+o+1+b[im+o]].decode()))
 return {'path':str(path),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'flags':U16(b,ne+12),'expected_windows':hex(U16(b,ne+0x3e)),'target_os':b[ne+0x36],'initial_csip':U32(b,ne+0x14),'heap':U16(b,ne+0x10),'names':names,'entries':entries,'modules':mods,'imports':sorted(set(imports)),'segments':segments},b
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--windows',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
exports={m:nefile(a.windows/'SYSTEM'/(m+'.EXE'))[0]['entries'] for m in ['KERNEL','GDI','USER']}
result={}
for name in ['DROPTX','DROPRX']:
 d,b=nefile(a.build/(name+'.EXE'));assert d['expected_windows']=='0x300' and not(d['flags']&8)
 assert set(d['modules']) <= set(exports)
 missing=[(m,o) for m,o in d['imports'] if o not in exports[m]];assert not missing,missing
 result[name]=d
result['all_imports_exist_in_Windows30']=True
result['shell_file_present']=any(a.windows.rglob('SHELL.DLL'))
a.out.write_text(json.dumps(result,indent=2));print('PASS native Windows 3.0 imports and real-mode NE flags')
