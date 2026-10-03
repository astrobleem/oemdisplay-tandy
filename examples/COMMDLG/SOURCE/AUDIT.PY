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
p=argparse.ArgumentParser();p.add_argument('--dll',required=True,type=Path);p.add_argument('--caller',required=True,type=Path);p.add_argument('--windows',required=True,type=Path);p.add_argument('--historic-lib',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=False)
d,b=nefile(a.dll);c,_=nefile(a.caller)
expected={'GETOPENFILENAME':1,'GETSAVEFILENAME':2,'COMMDLGEXTENDEDERROR':26,'GETFILETITLE':27}
historical={};lib=a.historic_lib.read_bytes()
for p0 in range(len(lib)-3):
 if lib[p0]!=0x88:continue
 size=U16(lib,p0+1)
 if size<7 or p0+3+size>len(lib):continue
 q=lib[p0+3:p0+2+size]
 if q[:4]!=bytes([0,0xa0,1,1]):continue
 pos=4;count=q[pos];pos+=1;name=q[pos:pos+count].decode('ascii');pos+=count
 count=q[pos];pos+=1;mod=q[pos:pos+count].decode('ascii');pos+=count
 if mod=='COMMDLG' and pos+2==len(q):historical[name]=U16(q,pos)
assert all(historical.get(k)==v for k,v in expected.items()),historical

assert all(d['names'].get(k)==v for k,v in expected.items())
assert d['expected_windows']==c['expected_windows']=='0x300' and d['flags']&0x8000 and not((d['flags']|c['flags'])&8)
assert d['initial_csip'] and set(d['modules'])<={'KERNEL','GDI','USER'}
assert b[d['segments'][1]['offset']:d['segments'][1]['offset']+16]==bytes(4)+bytes([5,0])+bytes(10), 'missing Win16 reserved DS header'
assert sorted(o for m,o in c['imports'] if m=='COMMDLG')==[1,2,26,27]
exports={'COMMDLG':d['entries']}
for mod in ['KERNEL','GDI','USER']:exports[mod]=nefile(a.windows/'SYSTEM'/f'{mod}.EXE')[0]['entries']
missing=[(which,m,o) for which,x in [('dll',d),('caller',c)] for m,o in x['imports'] if o not in exports[m]]
assert not missing,missing
bad=[]
for i,seg in enumerate(d['segments']):
 if seg['flags']&1:continue
 raw=a.out/f'CODE{i+1}.BIN';raw.write_bytes(b[seg['offset']:seg['offset']+seg['bytes']])
 asm=subprocess.check_output(['objdump','-D','-b','binary','-m','i8086',str(raw)],text=True);(a.out/f'CODE{i+1}.ASM').write_text(asm)
 for line in asm.splitlines():
  parts=line.split('\t')
  if len(parts)>2 and re.match(r'^(pusha|popa|enter|leave|pushw?\s+\$|imul\s+\$|ins[bwl]?\b|outs[bwl]?\b|[a-z]*32\b)',parts[2].strip()):bad.append(line)
result={'dll':d,'caller':c,'historical_import_library_sha256':hashlib.sha256(a.historic_lib.read_bytes()).hexdigest(),'reserved_Win16_data_header_bytes':16,'reserved_data_header_verified':True,'historical_ordinals_verified':True,'historical_library_exports':historical,'all_imports_present_in_owned_Windows_3_0':True,'protected_only_flag_clear':True,'linear_instruction_review_candidates':bad,'instruction_review_note':'Compiler /G0 plus original .8086 assembler; linear disassembly is supplementary, native enforced-8086 tests are required.'}
(a.out/'ABI.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'dll_sha256':d['sha256'],'caller_sha256':c['sha256'],'candidate_instructions':bad}))
