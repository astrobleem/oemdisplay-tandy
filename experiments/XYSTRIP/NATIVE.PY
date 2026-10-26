"""Prepare a bounded DOSBox-X standalone source harness. Not Windows QA.

Uses exact current/base XYPAN, XYCOPY and low HPAN routines, far cursor stubs,
timer probes, and the existing TESTFB conventional-memory/MCB guard pattern.
No OS media, accepted driver, installed guest or physical media is touched.
"""
from pathlib import Path
import argparse, hashlib, importlib.machinery, json, re, shutil, struct, subprocess

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
TOOLS=Path(r'C:\Users\chad\Documents\Codex\2026-10-25\task-2\legacy-inputs\BIN')
LEASE=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock')
DOSBOX=Path(r'C:\Program Files\DOSBox-X\dosbox-x.exe')
CASES=[(8,0),(16,0),(24,0),(32,0),(0,4),(0,8),(0,12),(0,16),
       (8,4),(16,4),(8,8),(16,8),(8,12),(32,16),
       (48,0),(64,0),(32,8),(48,16),(0,32),(64,32)]

def text(path,s):path.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def base(path):
    return subprocess.check_output(['git','--git-dir='+str(ROOT/'.git'),
        '--work-tree='+str(ROOT),'show','HEAD:'+path]).decode('ascii').replace('\r\n','\n')
def source(candidate,budget=2816):
    pan=(ROOT/'experiments/XYPAN/XYPAN.ASM').read_text() if candidate else base('experiments/XYPAN/XYPAN.ASM')
    pan=pan[:pan.index('; Stream at most')]
    if candidate:pan=pan.replace('2816',str(budget))
    copy=(ROOT/'experiments/XYPAN/XYCOPY.ASM').read_text()
    low=(ROOT/'experiments/HPAN/HPAN.ASM').read_text().split('; Caller already owns')[0]
    for name,event in [('hp_blank',1),('hp_present',2),('hp_unblank',4)]:
        low=low.replace(name+' proc near\n',name+' proc near\n    call stamp'+str(event)+'\n')
    low=low.replace('hp_ready:\n','hp_ready:\n    call stamp3\n')
    macro=re.search(r'get_nibble macro\n.*?\nendm', (ROOT/'src/tandysw/V1.ASM').read_text(),re.S).group()
    names=('hp_enabled hp_bytes hp_start hp_reason hp_hardware hp_software '
           'hp_last_cols hp_last_bytes hp_left hp_fault hp_mode hp_old hp_delta '
           'hp_top hp_oldtop hp_dy hp_stage_count hp_stage_read xy_copy_mode xy_h xy_v').split()
    data='\n'.join(n+' dw 0' for n in names)+'\nxy_hr dw 4 dup(0)\nxy_vr dw 4 dup(0)\n'
    data+='hp_stage db %d dup(0)\nenabled_flag db 1\n'%(budget if candidate else 1440)
    body='''.8086
code segment para public 'CODE'
assume cs:code,ds:code,ss:stackseg
start:
 mov ax,code
 mov ds,ax
 mov ax,es
 mov psp,ax
 dec ax
 mov es,ax
 cmp byte ptr es:[0],90
 jne failed
 mov ax,psp
 cmp es:[1],ax
 jne failed
 add ax,es:[3]
 cmp ax,9c00h
 jne failed
 mov dx,offset input_name
 mov ax,3d00h
 int 21h
 jc failed
 mov bx,ax
 push ds
 mov ax,shadowseg
 mov ds,ax
 xor dx,dx
 mov cx,64000
 mov ah,3fh
 int 21h
 pop ds
 jc failed
 cmp ax,64000
 jne failed
 push ds
 mov ax,tailseg
 mov ds,ax
 xor dx,dx
 mov cx,17920
 mov ah,3fh
 int 21h
 pop ds
 jc failed
 cmp ax,17920
 jne failed
 mov ah,3eh
 int 21h
 mov ax,code
 mov bx,offset live_end
 add bx,15
 mov cl,4
 shr bx,cl
 add ax,bx
 cmp ax,9800h
 ja failed
 mov ax,9
 int 10h
 call hp_reset
 mov hp_enabled,1
 ; Harness timer only: BIOS tick frequency is unchanged. Rate generator
 ; mode avoids mode-3's twice-per-tick counter phase ambiguity.
 mov al,34h
 out 43h,al
 xor al,al
 out 40h,al
 out 40h,al
'''
    for i,(dx,dy) in enumerate(CASES):
        # Odd request count finishes at the nonzero endpoint; directions alternate.
        # Alternate origin quadrant to exercise high logical rows and wrap.
        ax,ay=(320-dx,56-dy) if i&1 else (0,0)
        bx,by=ax+dx,ay+dy
        body+=f''' mov hp_left,{ax}
 mov hp_top,{ay}
 call hp_blank
 call hp_full
 mov ax,hp_start
 call hp_write
 call hp_unblank
 mov trace_count,0
'''
        for k in range(17):
            x,y=(bx,by) if not k&1 else (ax,ay)
            body+=f''' call stamp0
 mov ax,{x}
 mov dx,{y}
 call hp_set
 call stamp5
'''
        body+=f''' mov dx,offset trace_name{i}
 mov si,offset traces
 mov cx,trace_count
 shl cx,1
 shl cx,1
 shl cx,1
 call file_write
 mov dx,offset frame_name{i}
 xor si,si
 mov cx,32768
 call frame_write
'''
    body+=''' mov hp_fault,1
 mov ax,hp_left
 mov dx,hp_top
 cmp dx,4
 jb fault_down
 sub dx,4
 jmp short fault_set
fault_down:
 add dx,4
fault_set:
 call far ptr hp_set
 cmp hp_enabled,0
 jne failed
 cmp hp_reason,4
 jne failed
 cmp hp_last_bytes,32000
 jne failed
 mov al,36h
 out 43h,al
 xor al,al
 out 40h,al
 out 40h,al
 mov ax,3
 int 10h
 mov ax,psp
 dec ax
 mov es,ax
 cmp byte ptr es:[0],90
 jne failed
 mov ax,psp
 cmp es:[1],ax
 jne failed
 add ax,es:[3]
 cmp ax,9c00h
 jne failed
 mov ax,4c00h
 int 21h
failed:
 mov ax,3
 int 10h
 mov ax,4c01h
 int 21h
frame_write proc near
 mov ax,3c00h
 push cx
 xor cx,cx
 int 21h
 pop cx
 jc failed
 mov bx,ax
 push ds
 mov ax,0b800h
 mov ds,ax
 mov dx,si
 mov ah,40h
 int 21h
 pop ds
 jc failed
 mov ah,3eh
 int 21h
 ret
frame_write endp
file_write proc near
 mov ax,3c00h
 push cx
 xor cx,cx
 int 21h
 pop cx
 jc failed
 mov bx,ax
 mov dx,si
 mov ah,40h
 int 21h
 jc failed
 mov ah,3eh
 int 21h
 ret
file_write endp
cursor_hide proc far
 retf
cursor_hide endp
cursor_show proc far
 retf
cursor_show endp
'''
    for i in range(6):
        body+=f'''stamp{i} proc near
 push ax
 mov ax,{i}
 call stamp
 pop ax
 ret
stamp{i} endp
'''
    body+='''stamp proc near
 pushf
 cli
 push ax
 push bx
 push cx
 push dx
 push di
 push es
 mov di,trace_count
 cmp di,510
 jae stamp_done
 shl di,1
 shl di,1
 shl di,1
 add di,offset traces
 mov [di],ax
 mov ax,40h
 mov es,ax
 mov cx,es:[6ch]
 xor al,al
 out 43h,al
 in al,40h
 mov bl,al
 in al,40h
 mov bh,al
 mov al,0ah
 out 20h,al
 in al,20h
 test al,1
 jz stamp_tick
 inc cx
stamp_tick:
 neg bx
 mov [di+2],bx
 mov [di+4],cx
 mov ax,hp_last_bytes
 mov [di+6],ax
 inc trace_count
stamp_done:
 pop es
 pop di
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
stamp endp
'''
    body+=macro+'\n'+copy+'\n'+low+'\n'+pan+'\n'+data
    body+='psp dw 0\ntrace_count dw 0\ntraces db 4096 dup(0)\ninput_name db "SHADOW.BIN",0\n'
    for i in range(len(CASES)):
        body+=f'trace_name{i} db "T{i:02d}.BIN",0\nframe_name{i} db "F{i:02d}.BIN",0\n'
    body+='''code ends
shadowseg segment para public 'DATA'
shadow_bits db 64000 dup(0)
shadowseg ends
tailseg segment para public 'DATA'
shadow_tail db 17920 dup(0)
tailseg ends
stackseg segment para stack 'STACK'
 db 1024 dup(0)
stackseg ends
end start
'''
    # Harness-only forward FAR declarations and 8086 conditional long jumps.
    body=body.replace(' call hp_set\n',' call far ptr hp_set\n').replace(' call hp_reset\n',' call far ptr hp_reset\n')
    inverses={'jne':'je','jc':'jnc','ja':'jbe'}
    index=[0]
    def far_failure(match):
        index[0]+=1
        label='harness_ok_'+str(index[0])
        return ' '+inverses[match[1]]+' '+label+'\n jmp failed\n'+label+':'
    body=re.sub(r'^ (jne|jc|ja) failed$',far_failure,body,flags=re.M)
    # Match the driver's data-before-code declaration order. MASM 5.10 can
    # otherwise reserve a different first-pass size for forward SEG operands.
    a=body.index(data)
    b=body.index('code ends',a)
    declarations=body[a:b]
    segments=body[b+len('code ends\n'):body.index('end start')]
    body=body[:a]+'live_end label byte\ncode ends\nend start\n'
    body=body.replace('.8086\n','.8086\n'+segments,1)
    body=body.replace('start:\n',declarations+'start:\n',1)
    return body

def prepare(out,candidate,budget):
    out.mkdir()
    for name in ('MASM.EXE','LINK4.EXE'):shutil.copyfile(TOOLS/name,out/name)
    text(out/'PAN.ASM',source(candidate,budget))
    # Packed source is random but repeatable; DDK R,G,B,I plane order.
    shadow=bytearray(81920)
    for y in range(256):
        for x in range(640):
            v=((x*73+y*173)^((x*13+y*31)>>3))&15
            for p,w in enumerate((4,2,1,8)):
                if v&w:shadow[y*320+p*80+x//8]|=128>>(x&7)
    (out/'SHADOW.BIN').write_bytes(shadow)
    text(out/'RUN.BAT','@ECHO OFF\nMASM PAN.ASM,PAN.OBJ,PAN.LST; > BUILD.LOG\n'
         'IF ERRORLEVEL 1 GOTO FAIL\nLINK4 PAN.OBJ,PAN.EXE,PAN.MAP; >> BUILD.LOG\n'
         'IF ERRORLEVEL 1 GOTO FAIL\nPAN.EXE\nIF ERRORLEVEL 1 GOTO FAIL\n'
         'ECHO PASS>RESULT.TXT\nGOTO DONE\n:FAIL\nECHO FAIL>RESULT.TXT\n:DONE\nEXIT\n')
    text(out/'RUN.CONF',f'''[sdl]
fullscreen=false
output=surface
[dosbox]
machine=tandy
allow more than 640kb base memory=false
memsize=1
[cpu]
core=normal
cputype=8086_prefetch
cycles=fixed 20000
[mixer]
nosound=true
[midi]
mididevice=none
[dos]
xms=false
ems=false
umb=false
[autoexec]
mount c "{out}"
c:
CALL RUN.BAT
''')
    return out

def verify(out):
    assert (out/'RESULT.TXT').read_text().strip()=='PASS',(out/'BUILD.LOG').read_text()
    reports=[]
    for i,(dx,dy) in enumerate(CASES):
        ax,ay=(320-dx,56-dy) if i&1 else (0,0)
        x0,y0=ax+dx,ay+dy
        frame=(out/f'F{i:02d}.BIN').read_bytes();assert len(frame)==32768
        for y in range(y0,y0+200):
            for x in range(x0,x0+320,2):
                def pixel(x):return ((x*73+y*173)^((x*13+y*31)>>3))&15
                address=(y&3)*8192+(y//4*160+x//2)%8192
                assert frame[address]==(pixel(x)<<4|pixel(x+1)),(i,x,y,address)
        raw=(out/f'T{i:02d}.BIN').read_bytes();events=[struct.unpack_from('<HHHH',raw,j) for j in range(0,len(raw),8)]
        groups=[];cur=[]
        for event,lo,hi,n in events:
            if event==0:cur=[]
            cur.append((event,(hi<<16)|lo,n))
            if event==5:groups.append(cur)
        assert len(groups)==17,len(groups)
        phases=[]
        for g in groups:
            ids=[e[0] for e in g]
            assert ids in [list(range(6)),[0,2,3,4,5]],g
            t={e[0]:e[1] for e in g}
            diff=lambda a,b:((t[b]-t[a])&0xffffffff)*1000/(14318180/12)
            assert diff(0,5)<1000,('invalid timer sample',i,g)
            for a,b in zip(ids,ids[1:]):assert diff(a,b)<1000,('timer reversal',i,g)
            phases.append(dict(total_ms=diff(0,5),before_blank_ms=diff(0,1),
                               commit_or_full_ms=diff(1,2),wait_ms=diff(2,3),blank_ms=diff(1,4))
                          if 1 in t else dict(total_ms=diff(0,5),before_blank_ms=diff(0,2),
                               commit_or_full_ms=None,wait_ms=diff(2,3),blank_ms=0.0))
        mean={k:sum(p[k] for p in phases)/len(phases) if phases[0][k] is not None else None for k in phases[0]}
        reports.append(dict(dx=dx,dy=dy,bytes=groups[-1][-1][2],mean=mean,
                            min_blank_ms=min(p['blank_ms'] for p in phases),
                            max_blank_ms=max(p['blank_ms'] for p in phases)))
    result=dict(status='PASS',case_count=len(CASES),pans=17*len(CASES),
                compared_frame_bytes=32000*len(CASES),cases=reports,fault_recovery='PASS',
                scope='Standalone DOSBox-X 8086_prefetch fixed 20000; not 7.16MHz 8088, Windows, real cursor or hardware timing',
                caveat='PIT probes add overhead; blank interval measured from entry probes immediately around mode-control routines')
    (out/'NATIVE.JSN').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run','verify'])
    p.add_argument('--out',type=Path,required=True);p.add_argument('--candidate',action='store_true')
    p.add_argument('--budget',type=int,default=2816);a=p.parse_args()
    if a.action=='prepare':prepare(a.out.resolve(),a.candidate,a.budget)
    elif a.action=='verify':verify(a.out.resolve())
    else:
        runner=importlib.machinery.SourceFileLoader('pan_rundos',str(ROOT/'tools/SOUNDOWN/RUNDOS.PY')).load_module()
        runner.run(DOSBOX,a.out/'RUN.CONF',LEASE,120)
