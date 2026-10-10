#!/usr/bin/env python3
"""Original deterministic SZDD packing for pinned original public runtime payloads."""
from collections import defaultdict, deque
PACKED_NAMES = {'TR51616.DRV': 'TR51616.DR_', 'XTMODE.EXE': 'XTMODE.EX_', 'TR53216.DRV': 'TR53216.DR_', 'TR56404.DRV': 'TR56404.DR_', 'TXTMODE.DRV': 'TXTMODE.DR_', 'XTCSYS.FON': 'XTCSYS.FO_', 'XTCFIX.FON': 'XTCFIX.FO_', 'XTCOEM.FON': 'XTCOEM.FO_', 'XTESYS.FON': 'XTESYS.FO_', 'XTEFIX.FON': 'XTEFIX.FO_', 'XTEOEM.FON': 'XTEOEM.FO_', 'XTTSYS.FON': 'XTTSYS.FO_', 'TSHELL.EXE': 'TSHELL.EX_'}
def pack(data):
 out=bytearray(b'SZDD\x88\xf0\x27\x33A\x00'+len(data).to_bytes(4,'little'));d=defaultdict(deque);pos=0
 while pos<len(data):
  fl=len(out);out.append(0)
  for bit in range(8):
   if pos==len(data):break
   best=0;candidate=0;key=data[pos:pos+3];q=d[key]
   while q and q[0]<pos-4096:q.popleft()
   for at in reversed(q):
    n=0
    while n<18 and pos+n<len(data) and data[at+n]==data[pos+n]:n+=1
    if n>best:best=n;candidate=at
    if n==18:break
   n=best if best>=3 else 1
   if n==1:out[fl]|=1<<bit;out.append(data[pos])
   else:
    off=(4080+candidate)&4095;out.extend([off&255,((off>>4)&240)|(n-3)])
   for i in range(n):d[data[pos+i:pos+i+3]].append(pos+i)
   pos+=n
 return bytes(out)
