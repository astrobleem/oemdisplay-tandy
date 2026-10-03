#!/usr/bin/env python3
"""Isolated Tandy BIOS modes and raw-VRAM tests; no Windows-driver claim.

Uses only copied MASM/LINK tools and a disposable output directory. Tests the
first-generation Tandy modes 04/06/08/09/0A on the accepted 8086_prefetch core
and normal 640KB memory. Compares every pixel through independent BIOS and
host decoding paths, all storage bytes, padding and MCB safety. No GUI is used.
"""
from pathlib import Path
import argparse, hashlib, importlib.machinery, json, os, re, shutil, struct, sys

HERE = Path(__file__).resolve().parent
BASE = importlib.machinery.SourceFileLoader('testfb', str(HERE/'TESTFB.PY')).load_module()
MODES = {4:(320,4,16384),6:(640,2,16384),8:(160,16,16384),9:(320,16,32768),10:(640,4,32768)}

ASM = r""".8086
code segment para public 'CODE'
assume cs:code,ds:code,ss:stackseg
JFAIL macro condition
 local okay
 condition okay
 jmp failed
okay:
endm
CHECK macro a,b
 cmp a,b
 JFAIL je
endm
start:
 mov ax,es
 mov bx,code
 mov ds,bx
 mov psp,ax
 mov code_seg,bx
 mov ax,stackseg
 mov bx,offset stack_end
 add bx,15
 mov cl,4
 shr bx,cl
 add ax,bx
 mov live_end,ax
 cmp ax,9800h
 JFAIL jbe
 mov ax,psp
 dec ax
 mov es,ax
 CHECK <byte ptr es:[0]>,90
 mov ax,psp
 CHECK es:[1],ax
 add ax,es:[3]
 mov block_end,ax
 CHECK ax,9c00h
 xor si,si
 mov di,offset mcb_before
 mov cx,16
savemcb:
 mov al,es:[si]
 mov [di],al
 inc si
 inc di
 loop savemcb
 mov ax,40h
 mov es,ax
 mov ax,es:[13h]
 mov kb_before,ax
 CHECK ax,624
 mov dx,offset config_name
 mov ax,3d00h
 int 21h
 JFAIL jnc
 mov bx,ax
 mov dx,offset wanted_mode
 mov cx,8
 mov ah,3fh
 int 21h
 JFAIL jnc
 CHECK ax,8
 mov ah,3eh
 int 21h
 JFAIL jnc
 mov ax,wanted_mode
 int 10h
 mov mode_set,1
 mov ax,40h
 mov es,ax
 xor ax,ax
 mov al,es:[49h]
 mov got_mode,ax
 CHECK ax,wanted_mode
 mov ax,es:[4ah]
 mov got_columns,ax
 mov ax,es:[13h]
 mov kb_after,ax
 CHECK ax,624
 ; Direct host-generated pixels go to VRAM; BIOS independently reads them.
 mov dx,offset input_name
 mov ax,3d00h
 int 21h
 JFAIL jnc
 mov bx,ax
 push ds
 mov cx,byte_count
 mov ax,0b800h
 mov ds,ax
 xor dx,dx
 mov ah,3fh
 int 21h
 pop ds
 JFAIL jnc
 CHECK ax,byte_count
 mov ah,3eh
 int 21h
 JFAIL jnc
 mov dx,offset reads_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jnc
 mov read_handle,ax
 mov py,0
readrow:
 mov px,0
readpixel:
 mov cx,px
 mov dx,py
 xor bx,bx
 mov ah,0dh
 int 10h
 mov si,px
 mov pixelrow[si],al
 inc px
 mov ax,px
 cmp ax,screen_w
 jb readpixel
 mov bx,read_handle
 mov dx,offset pixelrow
 mov cx,screen_w
 mov ah,40h
 int 21h
 JFAIL jnc
 CHECK ax,screen_w
 inc py
 cmp py,200
 jb readrow
 mov bx,read_handle
 mov ah,3eh
 int 21h
 JFAIL jnc
 ; Fill only the visible pixels through BIOS, preserving sentinel padding.
 mov py,0
writerow:
 mov px,0
writepixel:
 mov ax,px
 mov cl,3
 shr ax,cl
 mov bx,py
 shr bx,1
 xor ax,bx
 xor ax,px
 and ax,colormask
 mov cx,px
 mov dx,py
 xor bx,bx
 mov ah,0ch
 int 10h
 inc px
 mov ax,px
 cmp ax,screen_w
 jb writepixel
 inc py
 cmp py,200
 jb writerow
 ; Verify physical Tandy shared-RAM alias for the selected bank mode.
 push ds
 mov cx,byte_count
 mov ax,9c00h
 cmp cx,8000h
 jne aliasstart
 mov ax,9800h
aliasstart:
 mov es,ax
 mov ax,0b800h
 mov ds,ax
 xor si,si
 xor di,di
 cld
 repe cmpsb
 pop ds
 JFAIL je
 mov alias_ok,1
 mov dx,offset output_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jnc
 mov bx,ax
 push ds
 mov cx,byte_count
 mov ax,0b800h
 mov ds,ax
 xor dx,dx
 mov ah,40h
 int 21h
 pop ds
 JFAIL jnc
 CHECK ax,byte_count
 mov ah,3eh
 int 21h
 JFAIL jnc
 mov ax,psp
 dec ax
 mov es,ax
 mov si,offset mcb_before
 xor di,di
 mov cx,16
 repe cmpsb
 JFAIL je
 mov mcb_ok,1
 ; Return to text before reporting success, checking the BIOS readback.
 mov ax,3
 int 10h
 mov ah,0fh
 int 10h
 CHECK al,3
 mov text_ok,1
 mov dx,offset meta_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jnc
 mov bx,ax
 mov dx,offset metadata
 mov cx,metadata_end-metadata
 mov ah,40h
 int 21h
 JFAIL jnc
 CHECK ax,<metadata_end-metadata>
 mov ah,3eh
 int 21h
 JFAIL jnc
 mov dx,offset passed
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
failed:
 mov ax,3
 int 10h
 mov dx,offset failure
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
metadata label byte
wanted_mode dw 0
screen_w dw 0
colormask dw 0
byte_count dw 0
psp dw 0
code_seg dw 0
live_end dw 0
block_end dw 0
kb_before dw 0
kb_after dw 0
got_mode dw 0
got_columns dw 0
alias_ok dw 0
mcb_ok dw 0
text_ok dw 0
metadata_end label byte
mode_set db 0
read_handle dw 0
px dw 0
py dw 0
mcb_before db 16 dup(0)
pixelrow db 640 dup(0)
config_name db 'MODE.BIN',0
input_name db 'INPUT.BIN',0
reads_name db 'READS.BIN',0
output_name db 'WRITE.BIN',0
meta_name db 'META.BIN',0
passed db 'PASS: mode, BIOS pixel read/write, memory, text return',13,10,'$'
failure db 'FAIL: memory, BIOS mode, I/O or text return',13,10,'$'
code ends
stackseg segment para stack 'STACK'
 dw 512 dup(0)
stack_end label byte
stackseg ends
end start
"""

FIELDS = 'wanted_mode width colormask byte_count psp code_seg live_end block_end kb_before kb_after got_mode got_columns alias_ok mcb_ok text_ok'.split()

def color(x,y,mask):
    return ((x>>3)^(y>>1)^x)&mask

def offset(mode,x,y):
    if mode==10:
        return (y%4)*8192+(y//4)*160+(x//8)*2
    if mode==9:
        return (y%4)*8192+(y//4)*160+x//2
    return (y%2)*8192+(y//2)*80+x//(8 if mode==6 else 4 if mode==4 else 2)

def encode(mode):
    width,colors,size=MODES[mode]
    raw=bytearray([0xa5]*size)
    for y in range(200):
        for x in range(width):
            a=offset(mode,x,y); c=color(x,y,colors-1)
            if mode==10:
                mask=0x80>>(x%8)
                for bit in range(2):
                    raw[a+bit]=(raw[a+bit]&~mask)|(mask if c&(1<<bit) else 0)
            else:
                bits=1 if mode==6 else 2 if mode==4 else 4
                shift=(8//bits-1-x%(8//bits))*bits; mask=(colors-1)<<shift
                raw[a]=(raw[a]&~mask)|(c<<shift)
    return bytes(raw)

def decode(mode,raw):
    width,colors,size=MODES[mode]; result=[]
    for y in range(200):
        for x in range(width):
            a=offset(mode,x,y)
            if mode==10:
                shift=7-x%8
                c=((raw[a]>>shift)&1)|(((raw[a+1]>>shift)&1)<<1)
            else:
                bits=1 if mode==6 else 2 if mode==4 else 4
                c=(raw[a]>>((8//bits-1-x%(8//bits))*bits))&(colors-1)
            result.append(c)
    return bytes(result)

def run(dosbox,directory):
    # Explicit normal 640KB configuration, no inherited user configuration.
    old=BASE.dos_text
    def configured(path,value):
        old(path,value.replace('memsize=1','memsize=0\nmemsizekb=640').replace('core=normal','fpu=false\ncore=normal'))
    BASE.dos_text=configured
    try:
        BASE.run_dos(dosbox,directory,120)
    finally:
        BASE.dos_text=old

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dosbox',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); out=a.out.resolve(); repo=HERE.parents[1]
    if out.exists(): p.error('--out must be fresh')
    out.mkdir(parents=True); build=out/'build'; build.mkdir()
    for name in ('MASM.EXE','LINK4.EXE'): shutil.copyfile(repo/'BIN'/name,build/name)
    BASE.dos_text(build/'MODETEST.ASM',ASM)
    BASE.dos_text(build/'RUN.BAT','@ECHO OFF\nMASM MODETEST.ASM,MODETEST.OBJ,MODETEST.LST; > BUILD.LOG\nLINK4 MODETEST.OBJ,MODETEST.EXE,MODETEST.MAP; >> BUILD.LOG\nEXIT\n')
    run(a.dosbox.resolve(),build)
    log=(build/'BUILD.LOG').read_text(errors='replace')
    if re.findall(r'(\d+)\s+Severe\s+Errors',log)!=['0'] or re.search(r'error [AL]\d+|fatal error',log,re.I):
        raise RuntimeError(log)
    results={}
    for mode,(width,colors,size) in MODES.items():
        directory=out/f'mode{mode:02x}'; directory.mkdir()
        shutil.copyfile(build/'MODETEST.EXE',directory/'MODETEST.EXE')
        raw=encode(mode)
        expected=bytes(color(x,y,colors-1) for y in range(200) for x in range(width))
        assert decode(mode,raw)==expected
        (directory/'MODE.BIN').write_bytes(struct.pack('<4H',mode,width,colors-1,size))
        (directory/'INPUT.BIN').write_bytes(raw)
        BASE.dos_text(directory/'RUN.BAT','@ECHO OFF\nCONFIG -GET CPU CPUTYPE > CPU.TXT\nMODETEST > TEST.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO PASS>RESULT.TXT\nGOTO DONE\n:FAIL\nECHO FAIL>RESULT.TXT\n:DONE\nEXIT\n')
        run(a.dosbox.resolve(),directory)
        assert (directory/'RESULT.TXT').read_text().strip()=='PASS',(mode,(directory/'TEST.LOG').read_text())
        actual=(directory/'WRITE.BIN').read_bytes(); reads=(directory/'READS.BIN').read_bytes()
        assert actual==raw,f'BIOS writes differ from independent raw-VRAM reference: {mode}'
        assert len(reads)==len(expected)
        read_errors=sum(a!=b for a,b in zip(reads,expected))
        legacy_match=False
        if mode==10:
            legacy=bytes((raw[(y//2)*80+(x//4)+(8192 if y&1 else 0)]>>((3-(x&3))*2))&3 for y in range(200) for x in range(width))
            legacy_match=reads==legacy
        elif read_errors:
            raise AssertionError(f'BIOS reads differ from expected pixels: {mode}')
        meta=dict(zip(FIELDS,struct.unpack('<15H',(directory/'META.BIN').read_bytes())))
        assert meta['got_mode']==mode and meta['got_columns']==width//8
        assert meta['kb_before']==meta['kb_after']==624
        assert meta['live_end']<=0x9800 and meta['block_end']==0x9c00
        assert meta['alias_ok']==meta['mcb_ok']==meta['text_ok']==1
        palette=BASE.PALETTE if colors==16 else [BASE.PALETTE[i] for i in ([0,15] if colors==2 else [0,3,5,15])]
        from PIL import Image
        im=Image.new('RGB',(width,200)); im.putdata([palette[c] for c in expected]); im.save(directory/'DECODED.PNG')
        # Image is a decode using stated preview colors, not a captured screen or palette-readback proof.
        results[f'{mode:02X}']=dict(status='BIOS_READ_FAIL' if read_errors else 'PASS',width=width,height=200,colors=colors,pixels_compared=width*200,raw_bytes_compared=size,read_mismatches=read_errors,write_mismatches=0,incorrect_16kb_cga_read_formula_matches=legacy_match,metadata=meta,sha256=hashlib.sha256(actual).hexdigest(),image='DECODED.PNG',image_kind='raw-VRAM decode, illustrative preview colors')
    report=dict(status='PARTIAL: mode0A BIOS readback bug' if any(r['read_mismatches'] for r in results.values()) else 'PASS',cpu='8086_prefetch',memory='640KB physical; 624KB BIOS; no XMS/EMS/UMB or expanded conventional memory',source_sha256=hashlib.sha256(ASM.encode()).hexdigest(),exe_sha256=hashlib.sha256((build/'MODETEST.EXE').read_bytes()).hexdigest(),modes=results,limits='DOS BIOS/framebuffer only; no Windows/GDI/font/cursor/save-readback validation, no physical hardware test')
    (out/'RESULT.JSON').write_text(json.dumps(report,indent=2)+'\n'); print(json.dumps(report,indent=2))
    return 2 if any(r['read_mismatches'] for r in results.values()) else 0
if __name__=='__main__': sys.exit(main())
