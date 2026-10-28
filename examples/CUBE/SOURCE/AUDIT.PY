"""Read-only scoped direct-control-flow 8088 audit of the native Cube EXE."""
from pathlib import Path
import argparse,collections,hashlib,json,os,re,struct,subprocess
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('exe',type=Path);p.add_argument('--objdump',type=Path,required=True);p.add_argument('--out',type=Path,required=True)
a=p.parse_args();b=a.exe.read_bytes();ne=struct.unpack_from('<I',b,0x3c)[0];assert b[ne:ne+2]==b'NE'
tab=ne+struct.unpack_from('<H',b,ne+0x22)[0];shift=struct.unpack_from('<H',b,ne+0x32)[0]
sec,size,flags,minimum=struct.unpack_from('<4H',b,tab);base=sec<<shift;end=base+size
assert struct.unpack_from('<H',b,ne+0x16)[0]==1
entry=struct.unpack_from('<H',b,ne+0x14)[0];roots=[entry]
maptext=a.exe.with_suffix('.MAP').read_text()
for name in ('CubeProc','CubeCfgProc','CubeQAProc'):
    roots.append(int(re.search(r'0001:([A-Fa-f0-9]+) '+name,maptext)[1],16))
env=os.environ.copy();env['PATH']=str(a.objdump.resolve().parent)+os.pathsep+env.get('PATH','')
listing=subprocess.check_output([str(a.objdump),'-D','-b','binary','-m','i8086',f'--start-address={base}',f'--stop-address={end}',str(a.exe)],env=env,text=True)
instructions={}
for row in listing.splitlines():
    m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*([^\t]+)',row)
    if m:instructions[int(m[1],16)]=(len(m[2].split()),m[3].strip())
queue=collections.deque(base+n for n in roots);decoded={};indirect=[];suspects=[]
bad=r'\b(pusha\w*|popa\w*|enter\w*|leave\w*|bound|ins[bw]|outs[bw]|arpl|movzx|movsx|bsf|bsr|lss|lfs|lgs|set\w+|shld|shrd|ud2|cpuid|rdtsc|clts|lldt|ltr|smsw|lmsw|lgdt|lidt|sgdt|sidt|lar|lsl|verr|verw)\b|\b(eax|ebx|ecx|edx|esp|ebp|esi|edi|fs|gs)\b|^push\s+\$|^(shl|shr|sar|rol|ror|rcl|rcr)\s+\$(?!1,)|^imul\s+\$'
while queue:
    at=queue.popleft()
    while at in instructions and at not in decoded:
        length,s=instructions[at];decoded[at]=s
        if re.search(bad,s)or'(bad)'in s:suspects.append(dict(offset=hex(at-base),instruction=s))
        if re.match(r'^(j\w+|loop\w*|call)\s+0x',s):queue.append(int(re.search(r'0x([0-9a-f]+)',s)[1],16))
        if s.startswith(('ret','lret','iret','hlt','jmp ')):
            if '*'in s:indirect.append(dict(offset=hex(at-base),instruction=s))
            break
        at+=length
r=dict(executable=dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest()),target_version=hex(struct.unpack_from('<H',b,ne+0x3e)[0]),
       code_bytes=size,roots=roots,direct_instructions=len(decoded),post8088_suspects=suspects,indirect_branches=indirect,
       scope='NE entry and three exported callbacks; direct near calls/branches only. Indirect CRT continuations, callback tables and imported Windows code excluded. Not exhaustive ISA or hardware qualification.')
a.out.write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r));raise SystemExit(bool(suspects))
