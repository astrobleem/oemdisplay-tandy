"""Execute the candidate's staged FlushRows in DOSBox, targeting guarded RAM.

This tests actual assembled viewport conversion code, not Windows or a
ColorPlus adapter. Only the physical video-segment load is redirected.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.machinery
import json
import os
import random
import shutil

HERE=Path(__file__).resolve().parent
CASES=[(t,0,400) for t in (0,1,99,100,199,200)]+[(100,95,108),(100,0,20),(100,299,305),
       (200,393,410),(1,-10,2),(200,400,401),(0,200,200)]


def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--build',type=Path,required=True)
    ap.add_argument('--repo',type=Path,required=True)
    ap.add_argument('--dosbox',type=Path,required=True)
    ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    source=(a.build/'renderer/EGA/TSOFT.ASM').read_text(encoding='latin1')
    routine=source[source.index('FlushShadow proc near'):source.index('FlushShadow endp')+len('FlushShadow endp')]
    anchor='    mov ax,0b800h\n    mov es,ax\n'
    assert routine.count(anchor)==1
    routine=routine.replace(anchor,'    mov ax,vbuf\n    mov es,ax\n')
    start=source.index('; PCPPATCH: one shadow byte column')
    macros=source[start:source.index('public FlushShadow,FlushRows',start)]
    rng=random.Random(1984);shadow=bytes(rng.randrange(256) for _ in range(64000))
    (out/'SHADOW.BIN').write_bytes(shadow)
    code=""".8086
stk segment stack 'STACK'
 db 512 dup(?)
stk ends
shad segment para public 'SHAD'
shadow_bits db 64000 dup(?)
shad ends
vbuf segment para public 'VBUF'
 db 32768 dup(?)
 db 16 dup(?)
vbuf ends
code segment para public 'CODE'
assume cs:code,ds:code
SCREEN_HEIGHT equ 400
SCREEN_W_BYTES equ 40
VIEW_ROWS equ 200
enabled_flag db 1
pan_top dw 0
input db 'SHADOW.BIN',0
output db 'VR00.BIN',0
handle dw 0
"""+macros+routine+"""
cursor_hide proc far
 retf
cursor_hide endp
cursor_show proc far
 retf
cursor_show endp
start:
 push cs
 pop ds
 mov dx,offset input
 mov ax,3d00h
 int 21h
 jc fail
 mov bx,ax
 mov ax,shad
 mov ds,ax
 xor dx,dx
 mov cx,64000
 mov ah,3fh
 int 21h
 jc fail
 cmp ax,64000
 jne fail
 mov ah,3eh
 int 21h
 push cs
 pop ds
"""
    for i,(top,first,last) in enumerate(CASES):
        code+=''' mov ax,vbuf
 mov es,ax
 xor di,di
 mov ax,0a5a5h
 mov cx,16392
 cld
 rep stosw
 mov pan_top,%d
 mov ax,%d
 mov bx,%d
 call FlushRows
 mov byte ptr output+2,'%s'
 mov byte ptr output+3,'%s'
 call save
'''%(top,first,last,str(i//10),str(i%10))
    code+=''' mov ax,4c00h
 int 21h
fail:
 mov ax,4c01h
 int 21h
save proc near
 mov dx,offset output
 xor cx,cx
 mov ah,3ch
 int 21h
 jc fail
 mov bx,ax
 push ds
 mov ax,vbuf
 mov ds,ax
 xor dx,dx
 mov cx,32784
 mov ah,40h
 int 21h
 pop ds
 jc fail
 cmp ax,32784
 jne fail
 mov ah,3eh
 int 21h
 ret
save endp
code ends
end start
'''
    code=code.replace('jc fail','req jnc').replace('jne fail','req je')
    code=code.replace('\nstart:\n','\nreq macro condition\n local ok\n condition ok\n jmp fail\nok:\n endm\nstart:\n')
    code=code.replace('call cursor_hide','call far ptr cursor_hide').replace('call cursor_show','call far ptr cursor_show')
    write(out/'RAMTEST.ASM',code)
    write(out/'BUILD.BAT','@ECHO OFF\nC:\\BIN\\MASM RAMTEST.ASM,RAMTEST.OBJ,RAMTEST.LST; > BUILD.LOG\nIF ERRORLEVEL 1 GOTO END\nC:\\BIN\\LINK RAMTEST.OBJ,RAMTEST.EXE,RAMTEST.MAP; >> BUILD.LOG\nIF ERRORLEVEL 1 GOTO END\nRAMTEST.EXE\nIF ERRORLEVEL 1 GOTO END\nECHO PASS > DONE.TXT\n:END\nEXIT\n')
    cfg='[sdl]\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=1\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[autoexec]\nmount C "'+str(a.repo.resolve())+'"\nmount D "'+str(out)+'"\nD:\nBUILD.BAT\n'
    write(out/'RUN.CNF',cfg)
    m=importlib.machinery.SourceFileLoader('sp_ramrun',str(HERE/'WINRUN.PY')).load_module()
    runner=m.Runner(out/'LEASE.JSON');env=dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
    with runner.lease():runner.run([a.dosbox.resolve(),'-nopromptfolder','-conf',out/'RUN.CNF'],env,out/'HOST.LOG')
    assert (out/'DONE.TXT').exists(),(out/'BUILD.LOG').read_text()
    results=[]
    for i,(top,first,last) in enumerate(CASES):
        want=bytearray([0xa5]*32784)
        for y in range(max(0,top,first),min(400,top+200,last)):
            vy=y-top
            for x in range(320):
                bits=[(shadow[y*160+p*40+x//8]>>(7-x%8))&1 for p in range(4)]
                at=(vy%2)*8192+(vy//2)*80+x//4;shift=6-2*(x%4);mask=3<<shift
                for plane,value in enumerate((2*bits[0]+bits[1],2*bits[2]+bits[3])):
                    pos=at+16384*plane
                    want[pos]=(want[pos]&~mask)|(value<<shift)
        got=(out/('VR%02d.BIN'%i)).read_bytes()
        bad=[j for j,(a,b) in enumerate(zip(got,want)) if a!=b]
        results.append({'top':top,'first':first,'last':last,'bytes':len(got),'mismatches':len(bad),
                        'first_mismatches':bad[:8],'pass':got==want})
    r={'pass':all(x['pass'] for x in results),'cases':len(results),'bytes_compared':len(results)*32784,
       'staged_tsoft_sha256':hashlib.sha256((a.build/'renderer/EGA/TSOFT.ASM').read_bytes()).hexdigest(),
       'scope':'actual staged FlushRows and ColorPlus macros, video segment redirected to guarded RAM; not Windows/adapter qualification',
       'results':results}
    write(out/'RESULT.JSON',json.dumps(r,indent=2));print(json.dumps(r,indent=2))
    return int(not r['pass'])


if __name__=='__main__':raise SystemExit(main())
