#!/usr/bin/env python3
"""Execute the actual JOYCAP machine bytes in a tiny explicit instruction model.
Only the exact documented instruction sequence is accepted. I/O is simulated.
This is not a general CPU emulator or hardware timing test.
"""
import argparse,hashlib,json,re,struct
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('exe',type=Path);a=p.parse_args()
b=a.exe.read_bytes();ne=struct.unpack_from('<I',b,60)[0];tab=ne+struct.unpack_from('<H',b,ne+34)[0];base=struct.unpack_from('<H',b,tab)[0]<<struct.unpack_from('<H',b,ne+50)[0]
off=int(re.search(r'0001:([0-9A-Fa-f]+)\s+_joy_capture',a.exe.with_suffix('.MAP').read_text())[1],16)
expected=bytes.fromhex('558bec5652518b7604ba0102b9000233c0eeec880446e2fa595a5e5dc3')
code=b[base+off:base+off+len(expected)];assert code==expected,code.hex()
checks=0;maxsteps=0
for state in (0,0x200):
 for thresholds in ((0,1,511,512),(512,512,512,512),(0,0,0,0),(40,100,5,230)):
  for buttons in range(16):
   r={'ax':0x1122,'bp':0x3456,'si':0x4567,'dx':0x5678,'cx':0x6789,'sp':0x9000};old=r.copy();mem=bytearray([0xa5])*65536
   def word(addr,val=None):
    if val is None:return mem[addr]|mem[addr+1]<<8
    mem[addr]=val&255;mem[addr+1]=val>>8
   def push(reg):r['sp']-=2;word(r['sp'],r[reg])
   def pop(reg):r[reg]=word(r['sp']);r['sp']+=2
   word(0x9000,0xffff);word(0x9002,0x2000);ip=0;n=0;steps=0;outs=[];seq=[];flag_if=state
   while True:
    steps+=1;assert steps<2100
    op=code[ip];ip+=1
    if op in (0x55,0x56,0x52,0x51):push({0x55:'bp',0x56:'si',0x52:'dx',0x51:'cx'}[op])
    elif op in (0x5d,0x5e,0x5a,0x59):pop({0x5d:'bp',0x5e:'si',0x5a:'dx',0x59:'cx'}[op])
    elif op==0x8b:
     mod=code[ip];ip+=1
     if mod==0xec:r['bp']=r['sp']
     else:assert mod==0x76 and code[ip]==4;r['si']=word(r['bp']+4);ip+=1
    elif op in (0xba,0xb9):r['dx' if op==0xba else 'cx']=code[ip]|code[ip+1]<<8;ip+=2
    elif op==0x33:assert code[ip]==0xc0;ip+=1;r['ax']=0
    elif op==0xee:outs.append((r['dx'],r['ax']&255))
    elif op==0xec:
     assert r['dx']==0x201 and n<512
     v=((~buttons)&15)<<4
     for axis,t in enumerate(thresholds):
      if n<t:v|=1<<axis
     seq.append(v);r['ax']=(r['ax']&0xff00)|v;n+=1
    elif op==0x88:assert code[ip]==4;ip+=1;mem[r['si']]=r['ax']&255
    elif op==0x46:r['si']=(r['si']+1)&65535
    elif op==0xe2:
     disp=struct.unpack('b',code[ip:ip+1])[0];ip+=1;r['cx']=(r['cx']-1)&65535
     if r['cx']:ip+=disp
    elif op==0xc3:assert word(r['sp'])==0xffff;r['sp']+=2;break
    else:raise AssertionError(hex(op))
   assert outs==[(0x201,0)] and n==512
   assert mem[0x2000:0x2200]==bytes(seq) and mem[0x1fff]==mem[0x2200]==0xa5
   assert all(r[k]==old[k] for k in ('bp','si','dx','cx')) and r['sp']==0x9002
   assert flag_if==state;checks+=1;maxsteps=max(maxsteps,steps)
print(json.dumps({'passed':True,'cases':checks,'max_instructions_per_capture':maxsteps,'reads_per_capture':512,'writes_per_capture':1,'only_port':'0201h','routine_hex':code.hex(),'exe_sha256':hashlib.sha256(b).hexdigest(),'scope':'Exact assembled JOYCAP bytes, simulated IN/OUT and stack/register/buffer checks. No physical or emulator joystick/timing validation.'},indent=2))
