"""Read an owned Win3.0 Control Panel without copying it into a deliverable.

Capstone is used only by this private host inspection; the shell has no new
runtime dependency. The exact file hash scopes the startup-code findings.
"""
from pathlib import Path
import argparse,hashlib,json,struct
from capstone import Cs,CS_ARCH_X86,CS_MODE_16
p=argparse.ArgumentParser()
p.add_argument('--control',type=Path,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args();b=a.control.read_bytes()
sha=hashlib.sha256(b).hexdigest()
assert sha=='ba33951fcfe28c0bd73178027b4b2226ea054f121ed50c1a594bf569ff424ddd','Uninspected CONTROL.EXE version'
u=lambda o:struct.unpack_from('<H',b,o)[0]
n=struct.unpack_from('<I',b,60)[0];assert b[n:n+2]==b'NE'
shift=u(n+50);segments=[struct.unpack_from('<4H',b,n+u(n+34)+i*8) for i in range(u(n+28))]
o=n+u(n+36);rshift=u(o);o+=2;resources={}
while u(o):
 typ,count,_=struct.unpack_from('<HHI',b,o);o+=8
 for _ in range(count):
  off,size,flags,ident,handle,usage=struct.unpack_from('<6H',b,o);o+=12
  resources[typ&0x7fff,ident&0x7fff]=b[off<<rshift:(off+size)<<rshift]
strings={}
for (typ,block),data in resources.items():
 if typ!=6:continue
 q=0
 for j in range(16):
  length=data[q];q+=1;strings[(block-1)*16+j]=data[q:q+length].decode('cp1252');q+=length
assert strings[16]=='CtlPanelClass'
menu=resources[4,1];q=4;settings=[]
while q<len(menu):
 flags=struct.unpack_from('<H',menu,q)[0];q+=2
 if flags&16:ident=None
 else:ident=struct.unpack_from('<H',menu,q)[0];q+=2
 z=menu.index(0,q);caption=menu[q:z].decode('cp1252');q=z+1
 settings.append({'command':ident,'caption':caption,'flags':flags})
 if ident==51:break
expected={0:'&Color...',8:'&Desktop...',7:'Date/&Time...',2:'&Fonts...',
 3:'&International...',5:'&Keyboard...',6:'&Mouse...',4:'P&orts...',
 1:'&Printers...',9:'&Sound...'}
actual={x['command']:x['caption'] for x in settings if x['caption']}
assert all(actual[k]==v for k,v in expected.items())
# Resolve the movable entry called by the C startup code: entry 116 is
# WinMain in this owned executable. Decode its complete straight byte range
# through RETF 10, including both startup and message-loop paths.
o=n+u(n+4);end=o+u(n+6);idx=1;entries={}
while o<end:
 count,seg=b[o:o+2];o+=2
 if not count:break
 for _ in range(count):
  if not seg:item=None
  elif seg==255:
   flags,int3,s,offset=struct.unpack_from('<BHBH',b,o);o+=6;item=(s,offset)
  else:item=(seg,u(o+1));o+=3
  entries[idx]=item;idx+=1
assert entries[116]==(1,0x599)
base=segments[0][0]<<shift
ins=list(Cs(CS_ARCH_X86,CS_MODE_16).disasm(b[base+0x599:base+0xbc2],0x599))
assert ins[-1].address==0xbbf and ins[-1].mnemonic=='retf' and ins[-1].op_str=='0xa'
assert sum(i.size for i in ins)==0xbc2-0x599
assert not any('[bp + 8]' in i.op_str or '[bp + 0xa]' in i.op_str for i in ins)
result={'control_sha256':sha,'bytes':len(b),'class':strings[16],
 'applets':expected,'excluded':['Network: optional driver','386 Enhanced: unavailable in real mode'],
 'interface':'Native Settings menu commands; no CPL files or command-line dispatch',
 'startup_inspection':{'entry':116,'segment':1,'start':'0599','end':'0BC2',
 'instruction_count':len(ins),'lpCmdLine_stack_words_read':False},
 'scope':'Static owned-file evidence only. Native launch/dialog/focus/layout not yet tested.'}
if a.out.exists():p.error('--out must be new')
a.out.write_bytes((json.dumps(result,indent=2)+'\n').replace('\n','\r\n').encode('ascii'))
print(json.dumps(result,indent=2))
