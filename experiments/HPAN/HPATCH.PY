"""Private staged HPAN over the pinned compact R2 raster. BIOS09 unchanged."""
from pathlib import Path
import re
HERE=Path(__file__).resolve().parent
def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
def one(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
def patch(renderer):
    p=renderer/'EGA/TSOFT.ASM';s=p.read_text(encoding='latin1')
    for a,b in [
      ('SCREEN_WIDTH equ 320','SCREEN_WIDTH equ 640'),
      ('SCREEN_W_BYTES equ 40','SCREEN_W_BYTES equ 80'),
      ('shadow_bits db 32000 dup (0)','shadow_bits db 64000 dup (0)'),
      ('BITMAP <0,320,200,40,4,1,0,8000','BITMAP <0,640,200,80,4,1,0,16000'),
      ('BITMAP <1,320,200,40,4,1,0,8000','BITMAP <1,640,200,80,4,1,0,16000'),
      ('dw 0300h,DT_RASDISPLAY,240,180,320,200,1,4','dw 0300h,DT_RASDISPLAY,480,180,640,200,1,4'),
      ('    mov cx,16000\n    cld\n    rep stosw','    mov cx,32000\n    cld\n    rep stosw')]:s=one(s,a,b)
    data='''public hp_left,hp_bytes
hp_enabled dw 0
hp_bytes dw 0
hp_start dw 0
hp_reason dw 0
hp_hardware dw 0
hp_software dw 0
hp_last_cols dw 0
hp_last_bytes dw 0
hp_left dw 0
hp_fault dw 0
hp_mode dw 0
hp_old dw 0
hp_delta dw 0
public hp_stage,hp_stage_offset
hp_stage_offset dw 0
hp_stage db 800 dup (0)
'''
    s=one(s,'diag_markers dw 0,0,0,0\n','diag_markers dw 0,0,0,0\n'+data)
    a=s.index('public FlushShadow,FlushRows\n');b=s.index('FlushColumns endp\n',a)+len('FlushColumns endp\n')
    s=s[:a]+(HERE/'HFLUSH.ASM').read_text()+'\n'+(HERE/'HPAN.ASM').read_text()+'\n'+s[b:]
    s=one(s,'    mov ax,9\n    int 10h\n','    mov ax,9\n    int 10h\n    call hp_reset\n')
    s=one(s,'    mov al,old_mode\n','    call hp_reset\n    mov al,old_mode\n')
    s=one(s,'    cmp bx,GETCOLORTABLE\n    je control_ok\n','''    cmp bx,GETCOLORTABLE
    je control_ok
    cmp bx,05858h
    je control_ok
    cmp bx,05859h
    je control_ok
''')
    s=one(s,'control_color:\n','''control_color:
    cmp bx,05859h
    jne control_hp_pan
    mov ax,es:[di]
    call hp_config
    jmp control_ok
control_hp_pan:
    cmp bx,05858h
    jne control_hp_other
    mov ax,es:[di]
    cmp ax,0ffffh
    je control_hp_out
    call hp_set
control_hp_out:
    les di,output
    mov ax,es
    or ax,di
    jz control_ok
    push ds
    mov ax,seg hp_left
    mov ds,ax
    mov ax,hp_left
    pop ds
    mov es:[di],ax
    mov word ptr es:[di+2],320
    mov word ptr es:[di+4],640
    jmp control_ok
control_hp_other:
''')
    a=s.index('cProc TControl');b=s.index('cProc DeviceBitmap',a)
    t=s[a:b];n=[0]
    def branch(m):
        n[0]+=1;l='hp_ctrl_skip'+str(n[0]);return '    jne '+l+'\n    jmp control_ok\n'+l+':\n'
    t=re.sub(r'    je control_ok\n',branch,t)
    t=t.replace('    jz control_ok\n','    jnz control_hp_ptr\n    jmp control_ok\ncontrol_hp_ptr:\n')
    s=s[:a]+t+s[b:];write(p,s)
    p=renderer/'SDIB88.ASM';s=p.read_text(encoding='latin1')
    s=re.sub(r'(?m)^(\s*(?:cmp|mov)\s+\w+,)320(\s*(?:;[^\n]*)?)$',r'\g<1>640\2',s);write(p,s)
    p=renderer/'EGA/TCURSOR.ASM';s=p.read_text(encoding='latin1')
    s=one(s,'    externB enabled_flag\n','    externB enabled_flag\n    externW hp_left\n    externW hp_bytes\n')
    s=one(s,'    add di,bx\n','    add di,bx\n    add di,hp_bytes\n')
    s=one(s,'    sub ax,tc_hot_x\n    mov tc_origin_x,ax\n','    sub ax,tc_hot_x\n    sub ax,hp_left\n    mov tc_origin_x,ax\n');write(p,s)
    p=renderer/'EGA/TSOFT.DEF';s=p.read_text()
    s=one(s,'Tandy 320x200 16-color software raster','HPAN 640x200 logical / 320x200 viewport PRIVATE')
    s=one(s,' CheckCursor @104\n',' CheckCursor @104\n HpStats @106\n HpShadow @107\n');write(p,s)
