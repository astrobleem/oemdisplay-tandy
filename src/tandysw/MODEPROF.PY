#!/usr/bin/env python3
"""Deterministic original-Tandy profiles over the audited software engine.

Only staged sources change. The default accepted 320x200x16 build is a no-op.
Four-plane compatible bitmaps are intentionally retained in reduced-color
profiles: PLANES describes the DDB representation, NUMCOLORS the real palette.
The 640-pixel profile uses 64000 shadow bytes, below the 65536-byte segment limit.
"""
from pathlib import Path
import hashlib, importlib.machinery, re

PROFILES = {
    '320x200x16': dict(width=320,height=200,colors=16,bios=9,driver='TANDY88.DRV',palette=list(range(16))),
    '640x200x4': dict(width=640,height=200,colors=4,bios=10,driver='TNDY6404.DRV',palette=[0,12,10,15]),
    '160x200x16': dict(width=160,height=200,colors=16,bios=8,driver='TNDY160.DRV',palette=list(range(16))),
    '320x200x4': dict(width=320,height=200,colors=4,bios=4,driver='TNDY3204.DRV',palette=[0,11,13,15]),
    '640x200x2': dict(width=640,height=200,colors=2,bios=6,driver='TNDY6402.DRV',palette=[0,15]),
}


def read(p):
    return p.read_bytes().replace(b'\r\n',b'\n').decode('latin1')


def write(p,s):
    p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))


def replace(s,a,b,n=1):
    if s.count(a)!=n:
        raise ValueError('Profile patch mismatch: '+repr(a)+' count='+str(s.count(a)))
    return s.replace(a,b)


def port(renderer,resources,repo,key):
    profile=PROFILES[key].copy()
    profile['key']=key
    profile['logical_planes']=4
    profile['shadow_bytes']=profile['width']//8*4*profile['height']
    if key=='320x200x16':
        return dict(profile=profile,stage='unchanged accepted baseline')
    if key!='640x200x4':
        return extended(renderer,resources,repo,profile)
    path=renderer/'EGA/TSOFT.ASM'
    s=read(path)
    for a,b,n in [
        ('SCREEN_WIDTH equ 320','SCREEN_WIDTH equ 640',1),
        ('SCREEN_W_BYTES equ 40','SCREEN_W_BYTES equ 80',1),
        ('shadow_bits db 32000 dup (0)','shadow_bits db 64000 dup (0)',1),
        ('BITMAP <0,320,200,40,4,1,0,8000','BITMAP <0,640,200,80,4,1,0,16000',1),
        ('BITMAP <1,320,200,40,4,1,0,8000','BITMAP <1,640,200,80,4,1,0,16000',1),
        ('dw 0300h,DT_RASDISPLAY,240,180,320,200,1,4','dw 0300h,DT_RASDISPLAY,240,180,640,200,1,4',1),
        ('dw -1,80,0,0,16,size BITMAP','dw -1,20,0,0,4,size BITMAP',1),
        ('2400,1800,320,-200','2400,1800,640,-200',1),
        ('24000,18000,320,-200','24000,18000,640,-200',1),
        ('mov cx,16000','mov cx,32000',1),
        ('HYPOTENUSE\t=\t61','HYPOTENUSE\t=\t13',1),
        ('Y_MAJOR_DIST\t=\t48','Y_MAJOR_DIST\t=\t12',1),
        ('X_MAJOR_DIST\t=\t38','X_MAJOR_DIST\t=\t5',1),
        ('dw 1200,900,406,-254','dw 375,900,254,-254',1),
        ('dw 12000,9000,406,-254','dw 3750,9000,254,-254',1),
        ('dw 17280,12960,406,-254','dw 5400,6480,254,-127',1),
        ('dw 96,72,DC_IgnoreDFNP','dw 96,48,DC_IgnoreDFNP',1),
    ]: s=replace(s,a,b,n)
    start=s.index('    mov cx,40\nflush_byte:')
    end=s.index('    inc bp\n',start)
    s=s[:start]+r'''    ; The low two logical planes are the actual four-color pixel index.
    ; Plane 2/3 are redundant for normal colors, preserving all DDK ROPs.
    mov cx,80
flush_byte:
    mov al,[si]
    mov ah,[si+80]
    stosw
    inc si
    loop flush_byte
flush_next_row:
    add si,240
'''+s[end:]
    palette='    mov ax,000ah\n    int 10h\n'
    for register,color in enumerate(profile['palette']):
        palette+='    mov ax,1000h\n    mov bx,%04xh\n    int 10h\n'%((color<<8)|register)
    palette+='    mov ax,1001h\n    xor bx,bx\n    int 10h\n'
    s=replace(s,'    mov ax,9\n    int 10h\n',palette)
    write(path,s)
    path=renderer/'SDIB88.ASM'
    s=read(path)
    # Screen bounds only; DIB width/stride arithmetic stays four-plane.
    s=re.sub(r'(?m)^(\s*(?:cmp|mov)\s+\w+,)320(\s*(?:;[^\n]*)?)$',r'\g<1>640\2',s)
    write(path,s)
    path=renderer/'EGA/TSOFT.DEF'
    write(path,replace(read(path),'133,96,72 : Tandy 320x200 16-color software raster','200,96,48 : Tandy 640x200 4-color software raster'))
    # CGA 80-column fonts have eight scan lines and 96x48 logical DPI.
    low=repo/'DDK/286/DISPLAY/1PLANE/RC_LOW'
    write(resources/'FONTS.ASM',read(low/'FONTS.ASM').replace(chr(26),''))
    config=read(resources/'CONFIG.ASM')
    write(resources/'CONFIG.ASM',replace(config,'\tdw\t1\t\t\t;cxBorder','\tdw\t2\t\t\t;cxBorder'))
    cursor(renderer/'EGA/TCURSOR.ASM')
    module=importlib.machinery.SourceFileLoader('modecol',str(repo/'src/tandysw/MODECOL.PY')).load_module()
    color=module.port(renderer,repo,profile)
    return dict(profile=profile,color=color,stage='experimental mode profile; runtime validation required',
                staged_sha256={str(p.relative_to(renderer)):hashlib.sha256(p.read_bytes()).hexdigest()
                               for p in [renderer/'EGA/TSOFT.ASM',renderer/'EGA/TCURSOR.ASM',renderer/'SDIB88.ASM']})


def cursor(path):
    s=read(path).replace('Tandy 320x200 monochrome','Tandy 640x200 four-color')
    s=replace(s,'tc_x            dw 160','tc_x            dw 320')
    s=replace(s,'cmp tc_right,320','cmp tc_right,640')
    s=replace(s,'mov tc_right,320','mov tc_right,640')
    a=s.index('    mov ax,tc_left\n    shr ax,1\n    mov tc_save_xbyte,ax')
    b=s.index('\n    ; Save full touched bytes',a)
    s=s[:a]+r'''    ; Cover complete adjacent plane-byte pairs for the clipped cursor.
    mov ax,tc_left
    shr ax,1
    shr ax,1
    shr ax,1
    shl ax,1
    mov tc_save_xbyte,ax
    mov bx,tc_right
    dec bx
    shr bx,1
    shr bx,1
    shr bx,1
    shl bx,1
    sub bx,ax
    add bx,2
    mov tc_save_bytes,bx
'''+s[b:]
    a=s.index('    mov ax,tc_work_x\n    shr ax,1\n    mov di,tc_row_offset')
    b=s.index('    inc tc_work_x\n',a)
    s=s[:a]+r'''    ; BL is the cursor-mask bit. BH is the physical screen-pixel bit.
    mov ax,tc_work_x
    mov cx,ax
    and cx,7
    mov bh,80h
    shr bh,cl
    shr ax,1
    shr ax,1
    shr ax,1
    shl ax,1
    mov di,tc_row_offset
    add di,ax
    mov ax,es:[di]
    test tc_and[si],bl
    jnz tcd_and_done
    mov dl,bh
    not dl
    and al,dl
    and ah,dl
 tcd_and_done:
    test tc_xor[si],bl
    jz tcd_xor_done
    xor al,bh
    xor ah,bh
 tcd_xor_done:
    mov es:[di],ax
'''+s[b:]
    write(path,s)


def extended(renderer,resources,repo,profile):
    """Integrate independently tested 16KB layouts, low fonts and palette."""
    w,c=profile['width'],profile['colors']
    ext=importlib.machinery.SourceFileLoader('modeext',str(repo/'src/tandysw/MODEEXT.PY')).load_module()
    layout=ext.port(renderer,repo,profile)
    path=renderer/'EGA/TSOFT.ASM';s=read(path)
    x=5*640//w
    hyp={160:23,320:16,640:13}[w]
    for a,b in [
        ('HYPOTENUSE\t=\t61','HYPOTENUSE\t=\t%d'%hyp),
        ('Y_MAJOR_DIST\t=\t48','Y_MAJOR_DIST\t=\t12'),
        ('X_MAJOR_DIST\t=\t38','X_MAJOR_DIST\t=\t%d'%x),
        ('dw 1200,900,406,-254','dw %d,900,254,-254'%(375*640//w)),
        ('dw 12000,9000,406,-254','dw %d,9000,254,-254'%(3750*640//w)),
        ('dw 17280,12960,406,-254','dw %d,6480,254,-127'%(5400*640//w)),
        ('dw 96,72,DC_IgnoreDFNP','dw 96,48,DC_IgnoreDFNP'),
    ]:s=replace(s,a,b)
    write(path,s)
    path=renderer/'EGA/TSOFT.DEF'
    write(path,replace(read(path),'133,96,72 : Tandy 320x200 16-color software raster',
                       '200,96,48 : Tandy %dx200 %d-color software raster'%(w,c)))
    low=repo/'DDK/286/DISPLAY/1PLANE/RC_LOW'
    write(resources/'FONTS.ASM',read(low/'FONTS.ASM').replace(chr(26),''))
    if w==640:
        path=resources/'CONFIG.ASM'
        write(path,replace(read(path),'\tdw\t1\t\t\t;cxBorder','\tdw\t2\t\t\t;cxBorder'))
    color={'feature':'unchanged sixteen-color mapper'}
    if c<16:
        name='MODECOL' if c==4 else 'MONOCOL'
        module=importlib.machinery.SourceFileLoader(name.lower(),str(repo/('src/tandysw/'+name+'.PY'))).load_module()
        color=module.port(renderer,repo,profile)
    return dict(profile=profile,layout=layout,color=color,
                stage='experimental original-Tandy profile; Windows acceptance required',
                font_contract='CGA system/fixed/OEM fonts, eight-pixel height, 200,96,48')
