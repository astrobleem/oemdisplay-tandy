#!/usr/bin/env python3
"""Verify the actual NE segment/export/import contract, not host ABI guesses."""
import hashlib, json, struct, sys
from pathlib import Path
p=Path(sys.argv[1]); b=p.read_bytes()
u16=lambda at: struct.unpack_from('<H',b,at)[0]
u32=lambda at: struct.unpack_from('<I',b,at)[0]
assert b[:2]==b'MZ'
n=u32(0x3c); assert b[n:n+2]==b'NE'
assert u16(n+12)&0x8000, 'Not a library'
assert u16(n+12)&1, 'Not single shared data'
assert u16(n+16)==0, 'Unexpected local heap'
segments=[]
for i in range(u16(n+28)):
    off,size,flags,minalloc=struct.unpack_from('<4H',b,n+u16(n+34)+8*i)
    assert flags&0x40, 'Segment not preloaded'
    assert not flags&0x10, 'Moveable segment'
    assert not flags&0x1000, 'Discardable segment'
    segments.append({'number':i+1,'bytes':size or 65536,'minimum_allocation':minalloc,'flags':hex(flags)})
def names(at):
    result={}
    while b[at]:
        length=b[at]; name=b[at+1:at+1+length].decode('ascii'); ordinal=u16(at+1+length)
        result[name]=ordinal;at+=length+3
    return result
resident=names(n+u16(n+38)); nonresident=names(u32(n+44)); exports=resident|nonresident
for name,ordinal in [('IdleInstall',1),('IdleRemove',2),('IdleGeneration',3),('IdleReady',4),('IdleRecord',5),('WEP',6)]:
    assert exports.get(name.upper())==ordinal,(name,exports)
assert resident.get('WEP')==6, 'WEP not resident-named'
mods=[]; table=n+u16(n+40); strings=n+u16(n+42)
for i in range(u16(n+30)):
    at=strings+u16(table+2*i);mods.append(b[at+1:at+1+b[at]].decode('ascii'))
assert set(mods)<={'USER','KERNEL'},mods
print(json.dumps({'file':str(p),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),
                  'segments':segments,'resident_names':resident,'imports':mods,
                  'status':'PASS: fixed/preloaded code and single data, no heap, expected exports, only Win3 USER/KERNEL imports'},indent=2))
