"""Host structural/artifact QA; --cpu optionally executes the real module."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
from PIL import Image
from capstone import Cs,CS_ARCH_X86,CS_MODE_16

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def decode(art):
    assert len(art)==4062
    assert art[:2]==b'BM' and struct.unpack_from('<I',art,2)[0]==len(art)
    assert struct.unpack_from('<I',art,10)[0]==62
    assert struct.unpack_from('<IiiHHII',art,14)==(40,640,200,1,1,2,4000)
    assert art[54:62]==bytes.fromhex('00000000ffffff00')
    rows=[[0]*640 for _ in range(200)];at=62;x=y=0
    while at<4062:
        n,v=art[at:at+2];at+=2
        if n:
            assert v in (0,17) and y<200 and x+n<=640
            rows[199-y][x:x+n]=[int(v==17)]*n;x+=n
        elif v==0:
            assert x==640 and y<200;x=0;y+=1
        else:
            assert v==1 and y==200 and x==0 and at==4062
            return rows
    raise AssertionError('Missing EOB')
def framebuffer(rows):
    data=bytearray(16384)
    for y,row in enumerate(rows):
        for x,pixel in enumerate(row):
            if pixel:data[(y//2)*80+(y%2)*8192+x//8]|=128>>(x%8)
    return bytes(data)
def cpu_test(lgo,art,expected):
    # Explicit --cpu only. This is host x86 instruction emulation, not a native
    # Windows/DOSBox qualification or a genuine Windows screenshot.
    from unicorn import Uc,UC_ARCH_X86,UC_MODE_16,UC_HOOK_INTR,UC_HOOK_CODE,UC_HOOK_MEM_WRITE
    from unicorn.x86_const import (UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,
        UC_X86_REG_SI,UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_SP,UC_X86_REG_CS,
        UC_X86_REG_DS,UC_X86_REG_ES,UC_X86_REG_SS,UC_X86_REG_EFLAGS,UC_X86_REG_IP)
    regs=(UC_X86_REG_AX,UC_X86_REG_BX,UC_X86_REG_CX,UC_X86_REG_DX,UC_X86_REG_SI,
          UC_X86_REG_DI,UC_X86_REG_BP,UC_X86_REG_DS,UC_X86_REG_ES)
    seg=0x2000;stop=0x18000;relocated=0x30000
    def run(data,mode=3,page=0):
        u=Uc(UC_ARCH_X86,UC_MODE_16);u.mem_map(0,0x100000)
        u.mem_write(seg*16,data);u.mem_write(0xb8000,b'\xa5'*16384)
        state={'mode':mode,'page':page,'changes':[],'writes':[]}
        values=(0x1111,0x2222,0x3333,0x4444,0x5555,0x6666,0x7777,0x8888,0x9999)
        for reg,value in zip(regs,values):u.reg_write(reg,value)
        u.reg_write(UC_X86_REG_SS,0x4000);u.reg_write(UC_X86_REG_SP,0xff00)
        u.reg_write(UC_X86_REG_EFLAGS,0x646)
        def intr(cpu,number,user):
            assert number==0x10
            ax=cpu.reg_read(UC_X86_REG_AX)
            if ax>>8==15:
                cpu.reg_write(UC_X86_REG_AX,80*256+state['mode'])
                cpu.reg_write(UC_X86_REG_BX,state['page']*256)
            else:
                assert ax>>8==0 and ax&255 in (3,6)
                state['mode']=ax&255;state['changes'].append(ax&255)
                cpu.mem_write(0xb8000,b'\0'*16384)
        def code(cpu,address,size,user):
            if address==stop:cpu.emu_stop()
        def writes(cpu,access,address,size,value,user):
            if 0xb8000<=address<0xc0000:
                assert 0xb8000<=address and address+size<=0xbc000
                state['writes'].append(address)
        u.hook_add(UC_HOOK_INTR,intr);u.hook_add(UC_HOOK_CODE,code);u.hook_add(UC_HOOK_MEM_WRITE,writes)
        def call(base,entry):
            sp=0xff00;u.reg_write(UC_X86_REG_SP,sp-4)
            u.mem_write(0x40000+sp-4,struct.pack('<HH',0,stop//16))
            u.reg_write(UC_X86_REG_CS,base//16);u.reg_write(UC_X86_REG_IP,entry)
            u.emu_start(base+entry,0x100000,count=2000000)
            assert u.reg_read(UC_X86_REG_CS)*16+u.reg_read(UC_X86_REG_IP)==stop
            assert u.reg_read(UC_X86_REG_SP)==sp and u.reg_read(UC_X86_REG_EFLAGS)&0xfff==0x646
        call(seg*16,4)
        assert u.reg_read(UC_X86_REG_AX)==48
        assert tuple(u.reg_read(r) for r in regs[1:])==values[1:]
        pixels=bytes(u.mem_read(0xb8000,16384))
        u.mem_write(relocated,bytes(u.mem_read(seg*16,48)))
        u.mem_write(seg*16,b'\xcc'*len(data))
        before=tuple(u.reg_read(r) for r in regs)
        call(relocated,7);call(relocated,7)
        assert tuple(u.reg_read(r) for r in regs)==before
        return state,pixels
    state,pixels=run(lgo+art)
    assert pixels==expected and state['changes']==[6,3]
    for mode,page in ((0,0),(6,0),(7,0),(3,1)):
        s,p=run(lgo+art,mode,page);assert not s['changes'] and not s['writes'] and p==b'\xa5'*16384
    bad=[]
    for i in range(62):
        b=bytearray(art);b[i]^=1;bad.append(bytes(b))
    for i in (62,64,126,500,1000,2000,4060):
        b=bytearray(art);b[i:i+2]=b'\0\2';bad.append(bytes(b))
    for n in (0,1,61,62,500,4060,4061):bad.append(art[:n]+b'\0'*(len(art)-n))
    for b in bad:
        s,p=run(lgo+b);assert not s['changes'] and not s['writes'] and p==b'\xa5'*16384
    return {'valid_exact_frame':True,'relocated_repeated_hide':True,'register_flags_stack':True,
            'unsupported_entries':4,'corruption_refusals':len(bad),'video_write_bounds':True}
def test(out,cpu=False):
    lgo=(out/'XTSTATIC.LGO').read_bytes();art=(out/'WXTSPL01.RLE').read_bytes()
    assert lgo[:7]==b'LOGO\xe9\x29\0' and lgo[-62:]==art[:62]
    assert len(lgo)+len(art)+3456<=65280
    decoder=Cs(CS_ARCH_X86,CS_MODE_16)
    instructions=list(decoder.disasm(lgo[4:46],4))+list(decoder.disasm(lgo[48:-62],48))
    assert lgo[45:48]==b'\xcb\xff\0'
    assert sum(i.size for i in instructions)==len(lgo)-68
    # This module has no instructions requiring 80186+, no DOS hooks or I/O.
    allowed={'jmp','pushf','push','pop','cmp','je','jne','ja','jae','jns','jb','xor','int',
             'retf','mov','cld','or','call','ret','stc','clc','shr','add','mul','test',
             'inc','dec','loop','lodsw','js','nop','and','popf'}
    assert all(i.mnemonic in allowed and not i.bytes.startswith((b'\x66',b'\x67',b'\x0f')) for i in instructions)
    assert all(i.op_str=='0x10' for i in instructions if i.mnemonic=='int')
    rows=decode(art);pixels=framebuffer(rows)
    image=Image.new('1',(640,200));image.putdata([v for row in rows for v in row]);image.save(out/'HOST640.PNG')
    report={'structural_checks':True,'original_art_exact':True,'native_windows_screenshot':False,
            'framebuffer_sha256':hashlib.sha256(pixels).hexdigest(),'lgo_sha256':hashlib.sha256(lgo).hexdigest(),
            'instruction_count':len(instructions),'resident_bytes':48,'native_qualified':False}
    if cpu:report['host_cpu']=cpu_test(lgo,art,pixels)
    (out/'HOSTQA.JSON').write_bytes((json.dumps(report,indent=2)+'\n').replace('\n','\r\n').encode())
    print(json.dumps(report,indent=2))
if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--cpu',action='store_true');args=parser.parse_args();test(args.out.resolve(),args.cpu)
