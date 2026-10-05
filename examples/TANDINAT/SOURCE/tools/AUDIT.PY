#!/usr/bin/env python3
"""Conservative linear NE code-segment opcode audit, backed by emulator tests.
Requires GNU objdump on the modern host, never on the Tandy.
"""
from pathlib import Path
import struct,subprocess,re,json,hashlib
P=Path(__file__).resolve().parents[1]
raw=(P/'src/TANDI.EXE').read_bytes();ne=struct.unpack_from('<I',raw,0x3c)[0]
assert raw[ne:ne+2]==b'NE'
num=struct.unpack_from('<H',raw,ne+0x1c)[0];table=struct.unpack_from('<H',raw,ne+0x22)[0]
shift=struct.unpack_from('<H',raw,ne+0x32)[0];segments=[];bad=[];count=0
entry=struct.unpack_from('<H',raw,ne+0x14)[0]
maptext=(P/'src/TANDI.MAP').read_text()
m=re.search(r'^\s*0001:([0-9A-Fa-f]+)\s+__wflags\s*$',maptext,re.M)
assert m, 'Link /MAP is required to identify CRT embedded __wflags data'
flags_at=int(m[1],16);assert flags_at+2==entry
excluded=[{'segment':1,'start':flags_at,'bytes':2,'symbol':'__wflags','reason':'Embedded CRT data, not instructions; identified by LINK /MAP and immediately before NE entry'}]
banned=set(range(0x60,0x70))|{0x0f,0xc0,0xc1,0xc8,0xc9,0xf1}
prefixes={0x26,0x2e,0x36,0x3e,0xf0,0xf2,0xf3}
for i in range(num):
    offset,size,flags,allocation=struct.unpack_from('<4H',raw,ne+table+i*8)
    segments.append({'segment':i+1,'file_bytes':size,'minimum_allocation':allocation,'data':bool(flags&1)})
    if flags&1:continue
    data=raw[offset<<shift:(offset<<shift)+size]
    # LINK public entry points are instruction boundaries. Zero alignment bytes
    # before CRT procedures must not consume the first opcode of the next one.
    points={0,size}
    for match in re.finditer(r'^\s*%04X:([0-9A-Fa-f]+)\s+\S+\s*$'%(i+1),maptext,re.M):
        points.add(int(match[1],16))
    if i==0:points.update([flags_at,flags_at+2])
    points=sorted(p for p in points if 0<=p<=size)
    spans=[(begin,end) for begin,end in zip(points,points[1:])
           if begin<end and not(i==0 and begin==flags_at)]
    dis=''
    for begin,end in spans:
        code=P/'build'/('CODE%d-%d.BIN'%(i,begin));code.write_bytes(data[begin:end])
        dis+=subprocess.check_output(['objdump','-D','-b','binary','-m','i8086','-Mintel','--adjust-vma='+str(begin),str(code)],text=True)
    (P/'evidence/DISASM.TXT').write_text(dis)
    for line in dis.splitlines():
        m=re.match(r'^\s*([0-9a-f]+):\s*((?:[0-9a-f]{2} )+)\s*([^\s].*)$',line)
        if not m:continue
        data=bytes.fromhex(m[2]);p=0
        while p<len(data) and data[p] in prefixes:p+=1
        if p==len(data):continue
        count+=1
        if data[p] in banned or 0xd8<=data[p]<=0xdf or '(bad)' in m[3]:bad.append(line.strip())
report={'exe_sha256':hashlib.sha256(raw).hexdigest(),'segments':segments,'linear_instructions':count,'unsupported_or_fpu':bad,'excluded_embedded_data':excluded,'scope':'All emitted NE code bytes disassembled, restarting at LINK public instruction boundaries to retain alignment; not a proof of every possible control-flow path. Combined with /G0, integer-only source and actual 8086_prefetch real-mode runs.'}
(P/'evidence/AUDIT.JSON').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert count>1000 and not bad
