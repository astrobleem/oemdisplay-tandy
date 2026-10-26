"""Experimental XY transformation applied AFTER accepted HPAN R3 patch."""
from pathlib import Path
import importlib.machinery,re
HERE=Path(__file__).resolve().parent
def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
def one(s,a,b):
    assert s.count(a)==1,(a,s.count(a))
    return s.replace(a,b)
def patch(renderer):
    base=importlib.machinery.SourceFileLoader('xyr3',str(HERE.parent/'HPAN/HPATCH.PY')).load_module()
    base.patch(renderer)
    p=renderer/'EGA/TSOFT.ASM';s=p.read_text(encoding='latin1')
    s=one(s,'SCREEN_HEIGHT equ 200','SCREEN_HEIGHT equ 256')
    s=one(s,'sEnd ShadowSeg\n','''sEnd ShadowSeg
createSeg _XYTAIL,XYTailSeg,word,public,DATA
sBegin XYTailSeg
public shadow_tail
shadow_tail db 17920 dup (0)
sEnd XYTailSeg
''')
    for typ in (0,1):
        s=one(s,f'BITMAP <{typ},640,200,80,4,1,0,16000,0,0,0,0,0,0>',f'BITMAP <{typ},640,256,80,4,1,0,20480,0,0,0,0,0,0>')
    s=one(s,'dw 0300h,DT_RASDISPLAY,480,180,640,200,1,4','dw 0300h,DT_RASDISPLAY,480,230,640,256,1,4')
    s=one(s,'hp_stage db 800 dup (0)','''hp_stage db 2816 dup (0)
public hp_top,hp_old,hp_oldtop,hp_dy,hp_stage_count,hp_stage_read
public hp_enabled,hp_start,hp_reason,hp_fault,xy_copy_mode
hp_top dw 0
hp_oldtop dw 0
hp_dy dw 0
hp_stage_count dw 0
hp_stage_read dw 0
xy_copy_mode dw 0
xy_h dw 0
xy_v dw 0
xy_hr dw 4 dup (0)
xy_vr dw 4 dup (0)''')
    a=s.index('public FlushShadow,FlushRows,FlushRetainRows');b=s.index('; Translate a screen argument',a)
    old=(HERE.parent/'HPAN/HPAN.ASM').read_text()
    low=old[:old.index('; Caller already owns cursor exclusion')]
    low=one(low,'    mov hp_left,ax\n','''    mov hp_left,ax
    mov hp_top,ax
    mov hp_stage_count,ax
    mov hp_stage_read,ax
    mov xy_copy_mode,ax
''')
    cfg=old[old.index('public hp_config'):old.index('cProc HpShadow')]
    s=s[:a]+(HERE/'XYCOPY.ASM').read_text()+'\n'+low+'\n'+(HERE/'XYPAN.ASM').read_text()+'\n'+cfg+'\n'+s[b:]
    # The old export is intentionally absent: no silent >64K snapshot ABI.
    a=s.index('ORowsSpanSafe proc near');b=s.index('ORowsSpanSafe endp',a)
    s=s[:a]+'''ORowsSpanSafe proc near
    ; Conservative full Output flush until a dual-band alias gate is proved.
    stc
    ret
'''+s[b:]
    s=one(s,'    mov word ptr shadow_device.bmBits,offset shadow_bits\n','''    mov word ptr shadow_device.bmBits,offset shadow_bits
    mov bx,seg shadow_tail
    sub bx,ax
    mov shadow_device.bmSegmentIndex,bx
    mov shadow_device.bmScanSegment,200
    mov shadow_device.bmFillBytes,1536
''')
    s=one(s,'    rep stosw\n    mov enabled_flag,1\n','''    rep stosw
    mov ax,seg shadow_tail
    mov es,ax
    xor ax,ax
    xor di,di
    mov cx,8960
    rep stosw
    mov enabled_flag,1
''')
    # New 2-word API; query uses x=-1 and returns x,y,viewport and logical size.
    a=s.index('cProc TControl');b=s.index('cProc DeviceBitmap',a);t=s[a:b]
    t=t.replace('05858h','05860h').replace('05859h','05861h')
    t=one(t,'    call hp_set\n','    mov dx,es:[di+2]\n    call hp_set\n')
    t=one(t,'    mov ax,hp_left\n    pop ds\n    mov es:[di],ax\n    mov word ptr es:[di+2],320\n    mov word ptr es:[di+4],640\n','''    mov ax,hp_left
    mov dx,hp_top
    pop ds
    mov es:[di],ax
    mov es:[di+2],dx
    mov word ptr es:[di+4],320
    mov word ptr es:[di+6],200
    mov word ptr es:[di+8],640
    mov word ptr es:[di+10],256
''')
    s=s[:a]+t+s[b:];write(p,s)
    p=renderer/'SDIB88.ASM';s=p.read_text(encoding='latin1')
    s=re.sub(r'(?m)^(\s*(?:cmp|mov)\s+\w+,)200(\s*(?:;[^\n]*)?)$',r'\g<1>256\2',s);write(p,s)
    p=renderer/'EGA/TSOFT.DEF';s=p.read_text()
    s=s.replace('HPAN 640x200 logical / 320x200 viewport PRIVATE','HPXY 640x256 logical / 320x200 viewport PRIVATE')
    s=one(s,' _SHADOW PRELOAD FIXED\n',' _SHADOW PRELOAD FIXED\n _XYTAIL PRELOAD FIXED\n')
    s=one(s,' HpShadow @107\n',' XYRows @108\n');write(p,s)
    p=renderer/'EGA/TCURSOR.ASM';s=p.read_text(encoding='latin1')
    s=one(s,'    externW hp_left\n','    externW hp_left\n    externW hp_top\n')
    s=one(s,'    tc_x            dw 160\n','    tc_bank         dw 0\n    tc_x            dw 160\n')
    s=one(s,'    add di,bx\n    add di,hp_bytes\n','''    mov tc_bank,bx
    add di,hp_bytes
    and di,01fffh
    or di,bx
''')
    s=one(s,'tc_scan endp\n','''tc_scan endp
tc_wrap proc near
    pushf
    and di,01fffh
    or di,tc_bank
    popf
    ret
tc_wrap endp
''')
    s=s.replace('    add di,tc_save_xbyte\n','    add di,tc_save_xbyte\n    call tc_wrap\n')
    s=one(s,'    rep movsb\n','''tce_byte:
    movsb
    call tc_wrap
    loop tce_byte
''')
    s=one(s,'    inc di\n    loop tcd_save_byte\n','    inc di\n    call tc_wrap\n    loop tcd_save_byte\n')
    s=one(s,'    add di,ax\n    mov dl,es:[di]\n','    add di,ax\n    call tc_wrap\n    mov dl,es:[di]\n')
    s=one(s,'    sub ax,tc_hot_y\n    mov tc_origin_y,ax\n','    sub ax,tc_hot_y\n    sub ax,hp_top\n    mov tc_origin_y,ax\n')
    a=s.index('cursor_begin_retain proc far');b=s.index('cursor_begin_retain endp',a)
    s=s[:a]+'''cursor_begin_retain proc far
    ; Conservatively disable footprint-retention in the XY experiment.
    pushf
    mov word ptr ss:[si],0
    popf
    retf
'''+s[b:];write(p,s)
