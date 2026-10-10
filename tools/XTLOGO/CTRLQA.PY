"""Execute actual test-controller IRQ instructions with synthetic visible prompts.

Host Unicorn QA only, not native Windows or DOSBox qualification.
"""
from pathlib import Path
import json,re,struct,sys
from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_CODE,UC_HOOK_MEM_WRITE,UC_HOOK_MEM_READ
from unicorn.x86_const import *
build=Path(sys.argv[1]).resolve()
symbols={n:int(a,16) for a,n in re.findall(r'0000:([0-9a-fA-F]+)\*?\s+(\w+)',(build/'SKCTRL.MAP').read_text())}
raw=(build/'SKCTRL.COM').read_bytes();seg=0x2000;base=seg*16;stop=0x18000
regs=(UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_DS,UC_X86_REG_ES)
def word(u,where):return struct.unpack('<H',bytes(u.mem_read(where,2)))[0]
def w(u,where,value):u.mem_write(where,struct.pack('<H',value))
def at(n):return base+symbols[n]
def screen(u,text):
    a=bytearray(b' \x17'*2000)
    for i,c in enumerate(text.encode()):a[(160+i)*2]=c
    u.mem_write(0xb8000,bytes(a))
    return bytes(a)
def make(row):
    u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
    u.mem_write(base+0x100,raw);u.mem_write(0x17000,b'\xcf');u.mem_write(stop,b'\x90')
    w(u,base+0x107,0);w(u,base+0x109,0x1700)
    u.mem_write(at('row'),bytes([row]));u.mem_write(at('observe'),bytes([int(row==6)]));u.mem_write(0x449,b'\x03')
    w(u,0x44e,0);w(u,0x41a,0x1e);w(u,0x41c,0x1e)
    u.hook_add(UC_HOOK_CODE,lambda machine,address,size,user:machine.emu_stop() if address==stop else None)
    writes=[]
    u.hook_add(UC_HOOK_MEM_WRITE,lambda machine,access,address,size,value,user:writes.append((address,size)))
    return u,writes
def tick(u):
    values=(0x1111,0x2222,0x3333,0x4444,0x5555,0x6666,0x7777,0x8888,0x9999)
    for register,value in zip(regs,values):u.reg_write(register,value)
    u.reg_write(UC_X86_REG_CS,seg);u.reg_write(UC_X86_REG_SS,0x4000);u.reg_write(UC_X86_REG_SP,0xfefa);u.reg_write(UC_X86_REG_EFLAGS,0x246)
    u.mem_write(0x4fefa,struct.pack('<HHH',0,0x1800,0x246))
    u.emu_start(base+symbols['tick'],stop+1,count=1000000)
    assert [u.reg_read(r) for r in regs]==list(values),'IRQ registers changed'
    assert u.reg_read(UC_X86_REG_SP)==0xff00,'IRQ frame imbalance'
    assert u.reg_read(UC_X86_REG_EFLAGS)&0xffff==0x246,'IRQ flags changed'
def scene(u,text,target):
    screen(u,text);keys=[]
    for i in range(300):
        tick(u)
        head,tail=word(u,0x41a),word(u,0x41c)
        if head!=tail:
            keys.append(word(u,0x400+head));w(u,0x41a,tail)
        if u.mem_read(at('phase'),1)[0]==target and word(u,at('qlen'))==0 and word(u,at('cool'))==0:return keys
    raise AssertionError('No prompt transition '+text)
results=[]
for row in (0,1,2,3,4,5):
    u,writes=make(row)
    assert scene(u,'System Information',1)==[0x4800]*6+[0x1c0d]
    assert scene(u,'Select a Display from the following list:',2)==[0x5000]*40+[0x1c0d]
    expected=[0x4700]+[0x5300]*16+list(b'C:\\WINXT')+[0x1c0d]
    assert scene(u,'Please insert your display driver disk',3)==expected
    assert scene(u,'Tandy EX/HX 320x200 16 colors',4)==[0x4800]*6+[0x5000]*row+[0x1c0d]
    assert scene(u,'System Information',5)==[0x5000]*6+[0x1c0d]
    assert scene(u,'The new display driver you have chosen',6)==[0x5000]*2+[0x1c0d]
    assert scene(u,'Please insert font disk',6)==expected
    assert not any(0xb8000<=address<0xbc000 for address,size in writes),'Video write'
    assert all(0x41c<=address<=0x43c for address,size in writes if 0x400<=address<0x500),'BDA write boundary'
    results.append({'row':row,'visible_prompts':7,'path_ascii':'C:\\WINXT','irq_register_flags_stack_preserved':True,'video_read_only':True})
u,writes=make(1);blocked=screen(u,'Unrecognized Setup prompt')
w(u,at('age'),727);tick(u)
assert u.mem_read(at('phase'),1)[0]==99 and u.mem_read(at('armed'),1)[0]==0
assert bytes(u.mem_read(at('screen'),4000))==blocked,'Failure screen not preserved'
assert word(u,0x41a)==word(u,0x41c),'Unknown prompt must not inject input'
u,writes=make(6);screen(u,'System Information');tick(u);assert u.mem_read(at('armed'),1)[0]==0 and word(u,at('actions'))==0;assert word(u,0x41a)==word(u,0x41c)
for offset in (4096,12288):
    u,writes=make(6);w(u,0x44e,offset);frame=screen(u,'System Information');u.mem_write(0xb8000+offset,frame);u.mem_write(0xb8000,b' '*4000);tick(u);assert u.mem_read(at('armed'),1)[0]==0 and bytes(u.mem_read(at('screen'),4000))==frame;assert word(u,at('view')+2)==offset;assert not any(0xb8000<=a<0xbc000 for a,z in writes)
# Newly observed copy-source transition, executed as actual 8086 IRQ code.
copy_cases=[]
expected=[0x4700]+[0x5300]*16+list(b'C:\\WINXT')+[0x1c0d]
def copyframe(u,filename='TR56402.DRV',offset=0,footer=1800,media=True,copy=True):
    a=bytearray(b' \x17'*2000)
    text='Please insert the: '+('Windows XT All-in-One' if media else 'Other media')
    for i,c in enumerate(text.encode()):a[(160+i)*2]=c
    if copy:
        for i,c in enumerate(('Copying : '+filename).encode()[:2000-footer]):a[(footer+i)*2]=c
    w(u,0x44e,offset);u.mem_write(0xb8000+offset,bytes(a))
    if offset:u.mem_write(0xb8000,b' '*4000)
    return bytes(a)
def pump(u):
    keys=[]
    for _ in range(300):
        tick(u)
        head,tail=word(u,0x41a),word(u,0x41c)
        if head!=tail:
            keys.append(word(u,0x400+head));w(u,0x41a,tail)
        if word(u,at('qlen'))==0 and word(u,at('cool'))==0:return keys
    raise AssertionError('Copy prompt did not drain')
for phase in (4,5,6):
    for offset in (0,4096,12288):
        u,writes=make(4);u.mem_write(at('phase'),bytes([phase]));frame=copyframe(u,offset=offset)
        reads=[]
        u.hook_add(UC_HOOK_MEM_READ,lambda machine,access,address,size,value,user:reads.append((address,size)) if 0xb8000<=address<0xbc000 else None)
        assert pump(u)==expected
        assert u.mem_read(at('phase'),1)[0]==phase,'Copy source changed phase'
        actions=word(u,at('actions'))
        for _ in range(20):tick(u)
        assert word(u,at('actions'))==actions and word(u,0x41a)==word(u,0x41c),'Repeated unchanged copy prompt'
        copyframe(u,'TXTMODE.DRV',offset=offset)
        assert pump(u)==expected,'New copy filename was not accepted'
        assert word(u,at('actions'))==actions+1
        assert bytes(u.mem_read(at('screen'),4000))==bytes(u.mem_read(0xb8000+offset,4000))
        assert all(0xb8000+offset<=a and a+n<=0xb8000+offset+4000 for a,n in reads),'VRAM read outside active page'
        assert not any(0xb8000<=a<0xbc000 for a,n in writes),'Copy prompt wrote VRAM'
        copy_cases.append({'phase':phase,'active_page_offset':offset,'same_file_latched':True,'changed_file_accepted':True})
for media,footer_present in ((False,True),(True,False)):
    u,writes=make(4);u.mem_write(at('phase'),b'\x04');copyframe(u,media=media,copy=footer_present)
    assert pump(u)==[] and word(u,at('actions'))==0,'Unknown copy source received input'
u,writes=make(4);u.mem_write(at('phase'),b'\x04');copyframe(u,footer=1990,offset=12288)
assert pump(u)==expected,'Bounded footer at page end failed'
assert bytes(u.mem_read(at('copy_token')+10,22))==bytes(22),'Footer token was not padded at page end'
u,writes=make(6);copyframe(u);tick(u)
assert word(u,at('actions'))==0 and word(u,0x41a)==word(u,0x41c),'Passive observer gained copy input'

for phase in (4,5):
    u,writes=make(4);u.mem_write(at('phase'),bytes([phase]));copyframe(u)
    assert pump(u)==expected
    if phase==4:assert scene(u,'System Information',5)==[0x5000]*6+[0x1c0d]
    else:assert scene(u,'The new display driver you have chosen',6)==[0x5000]*2+[0x1c0d]
    assert u.mem_read(at('copy_latch'),1)[0]==0,'Copy latch failed to clear'

report={'copy_prompt_normal_transition_resumed':True,'copy_source_cases':copy_cases,'unknown_copy_prompt_ignored':True,'footer_page_end_bounded':True,'kind':'Host execution of real IRQ instructions; not native qualification','cases':results,'bounded_unknown_prompt_disarm_without_input':True,'resident_bytes':(symbols['resident_end']+15)//16*16}
(build/'CTRLQA.JSON').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
