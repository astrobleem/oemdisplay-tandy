#!/usr/bin/env python3
"""Derive optional compact UI from exact native driver resources.

Developer-only producer. The accepted normal renderer and color table stay
byte-identical; code/data segments and fixups are checked after rebasing.
Consumer installation uses the resulting ordinary Win16 driver and fonts.
"""
import struct,hashlib
def pin(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def resources(b):
 if len(b)<64 or b[:2]!=b'MZ':raise ValueError('Expected a native MZ/NE driver')
 ne=struct.unpack_from('<I',b,60)[0]
 if ne+64>len(b) or b[ne:ne+2]!=b'NE':raise ValueError('Invalid NE driver header')
 p=ne+struct.unpack_from('<H',b,ne+36)[0];end=ne+struct.unpack_from('<H',b,ne+38)[0]
 if not ne+64<=p<end<=len(b) or p+2>end:raise ValueError('Invalid NE resource table bounds')
 shift=struct.unpack_from('<H',b,p)[0]
 if shift!=4:raise ValueError('Expected the accepted 16-byte resource alignment')
 p+=2;rows=[];seen=set()
 while True:
  if p+4>end:raise ValueError('Unterminated resource table')
  typ,n=struct.unpack_from('<HH',b,p)
  if not typ:break
  if p+8+12*n>end:raise ValueError('Truncated resource entries')
  p+=8
  for i in range(n):
   off,size,flags,ident,handle,usage=struct.unpack_from('<6H',b,p);p+=12
   if not typ&0x8000 or not ident&0x8000 or (typ,ident) in seen:raise ValueError('Unexpected resource identity')
   seen.add((typ,ident))
   if not size or (off<<shift)<end or ((off+size)<<shift)>len(b):raise ValueError('Invalid resource data bounds')
   rows.append(dict(type=typ,id=ident,flags=flags,data=b[off<<shift:(off+size)<<shift]))
 return ne,shift,rows
def compact(original,donor):
 ne,shift,rows=resources(original);_,_,small=resources(donor);wanted={}
 if not all(any(r['type']==0xf006 and r['id']==i for r in small) for i in (0x8001,0x8003)):
  raise ValueError('Compact OEM config/font descriptors missing')
 for r in small:
  if r['type']==0x8002 or (r['type']==0xf006 and r['id'] in (0x8001,0x8003)):wanted[r['type'],r['id']]=r
 changed=[]
 for i,r in enumerate(rows):
  key=r['type'],r['id']
  if key in wanted:rows[i]=wanted.pop(key);changed.append(dict(type=key[0],id=key[1],before=pin(r['data']),after=pin(rows[i]['data'])))
 rows.extend(wanted.values());unit=1<<shift;groups={}
 for r in rows:groups.setdefault(r['type'],[]).append(r)
 tableoff=ne+struct.unpack_from('<H',original,ne+36)[0]
 oldend=ne+struct.unpack_from('<H',original,ne+38)[0]
 oldsize=oldend-tableoff
 tablesize=2+sum(8+12*len(v) for v in groups.values())+3
 while (tablesize-oldsize)%unit:tablesize+=1
 delta=tablesize-oldsize;assert delta>=0
 out=bytearray(original[:tableoff]+bytes(tablesize)+original[oldend:])
 # Expand the table in its conventional header location. Rebase NE file
 # offsets, preserving the complete original segment bytes and fixups.
 for field in (4,34,38,40,42):
  val=struct.unpack_from('<H',original,ne+field)[0]
  if val+ne>=oldend:struct.pack_into('<H',out,ne+field,val+delta)
 nonres=struct.unpack_from('<I',original,ne+44)[0]
 if nonres>=oldend:struct.pack_into('<I',out,ne+44,nonres+delta)
 segtable=ne+struct.unpack_from('<H',original,ne+34)[0];segs=struct.unpack_from('<H',original,ne+28)[0];segshift=struct.unpack_from('<H',original,ne+50)[0]
 assert delta%(1<<segshift)==0
 for i in range(segs):
  pos=segtable+8*i;off=struct.unpack_from('<H',original,pos)[0]
  if off and (off<<segshift)>=oldend:struct.pack_into('<H',out,pos,off+(delta>>segshift))
 table=bytearray(struct.pack('<H',shift))
 for typ,rr in groups.items():
  table+=struct.pack('<HHI',typ,len(rr),0)
  for r in rr:
   while len(out)%unit:out.append(0)
   offset=len(out)//unit;out.extend(r['data'])
   while len(out)%unit:out.append(0)
   length=len(r['data'])//unit;assert len(r['data'])%unit==0
   table+=struct.pack('<6H',offset,length,r['flags'],r['id'],0,0)
 table+=bytes(tablesize-len(table));assert len(table)==tablesize
 out[tableoff:tableoff+len(table)]=table
 segments=[]
 for i in range(segs):
  pos=segtable+8*i;off,size,flags,alloc=struct.unpack_from('<4H',original,pos);new=struct.unpack_from('<H',out,pos)[0]
  if not off:continue
  length=size or 65536;tail=0
  if flags&0x100:tail=2+8*struct.unpack_from('<H',original,(off<<segshift)+length)[0]
  before=original[off<<segshift:(off<<segshift)+length+tail];after=out[new<<segshift:(new<<segshift)+length+tail]
  assert before==after;segments.append(dict(segment=i+1,complete_data_and_fixups=pin(before)))
 actual={(r['type'],r['id']):r['data'] for r in resources(out)[2]}
 for r in small:
  if r['type']==0x8002 or (r['type']==0xf006 and r['id'] in (0x8001,0x8003)):assert actual[r['type'],r['id']]==r['data']
 return bytes(out),dict(method='Exact CGA100 OEM bitmap/config/font-descriptor resource transplant; conventional resource table expanded and NE file offsets rebased; all10file-backed original segments including fixups remain byte-identical; unbacked data segment size/flags unchanged',header_growth=delta,segments=segments,changed=changed,additional_ids=[r['id'] for r in wanted.values()],input=pin(original),donor=pin(donor),output=pin(out))
