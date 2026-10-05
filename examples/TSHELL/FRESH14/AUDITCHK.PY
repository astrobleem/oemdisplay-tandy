#!/usr/bin/env python3
"""Read-only scoped 8088 disassembly audit of an NE executable, using objdump."""
import argparse,collections,hashlib,json,pathlib,re,struct,subprocess
ap=argparse.ArgumentParser();ap.add_argument('exe',type=pathlib.Path);a=ap.parse_args()
p=a.exe;b=p.read_bytes();assert b[:2]==b'MZ'
base=struct.unpack_from('<H',b,8)[0]*16
entry=struct.unpack_from('<H',b,20)[0]+16*struct.unpack_from('<H',b,22)[0]
size=int(re.search(r'([0-9A-F]+)H _TEXT\s+CODE',p.with_suffix('.MAP').read_text())[1],16)
end=base+size
queue=collections.deque([base+entry]);decoded={};suspects=[];indirect=[]
post8088=r'\b(pusha\w*|popa\w*|enter\w*|leave\w*|bound|ins[bw]|outs[bw]|arpl|movzx|movsx|bsf|bsr|lss|lfs|lgs|set\w+|shld|shrd|ud2|cpuid|rdtsc|clts|lldt|ltr|smsw|lmsw|lgdt|lidt|sgdt|sidt|lar|lsl|verr|verw)\b|\b(eax|ebx|ecx|edx|esp|ebp|esi|edi|fs|gs)\b|^push\s+\$|^(shl|shr|sar|rol|ror|rcl|rcr)\s+\$(?!1,)|^imul\s+\$'
while queue:
    start=queue.popleft()
    if start in decoded or not base<=start<end:continue
    out=subprocess.check_output(['objdump','-D','-b','binary','-m','i8086',f'--start-address={start}',f'--stop-address={end}',str(p)],text=True)
    for row in out.splitlines():
        m=re.match(r'\s*([0-9a-f]+):\s+((?:[0-9a-f]{2} )+)\s*([^\t]+)',row)
        if not m:continue
        address=int(m[1],16);instruction=m[3].strip()
        if address in decoded:break
        decoded[address]=instruction
        if re.search(post8088,instruction) or '(bad)' in instruction:
            suspects.append({'offset':hex(address-base),'instruction':instruction})
        if re.match(r'^(j\w+|loop\w*|call)\s+0x',instruction):
            queue.append(int(re.search(r'0x([0-9a-f]+)',instruction)[1],16))
        if instruction.startswith(('ret','lret','iret','hlt','jmp ')):
            if '*' in instruction:indirect.append({'offset':hex(address-base),'instruction':instruction})
            break
io=[{'offset':hex(address-base),'instruction':s} for address,s in decoded.items() if re.match(r'^(out|in|cli|sti|popf|pushf|int)\b',s)]
result={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest(),'code_bytes':size,'entry_offset':hex(entry),'reachable_instructions_checked':len(decoded),'post8088_suspects':suspects,'indirect_branch_sites':indirect,'scope':'MZ entry, following direct branches/calls within linked _TEXT. Indirect and untraced far calls excluded; native DOS tests supplement this scoped audit.'}
print(json.dumps(result,indent=2))
raise SystemExit(bool(suspects))
