#!/usr/bin/env python3
"""Final staged TR5 adapter for IBM CGA 160x100 RGBI. Native-unqualified.

No changes to existing profiles or pins. The shadow stays scan-interleaved
R/G/B/I, 20 bytes/plane/row; VRAM is 100 linear rows of 80 character pairs.
DEh (right half block) puts the left pixel in the attribute high nibble.
Timing combines IBM's documented 80-column horizontal and 200-line graphics
vertical values. This is a derived recipe, not an IBM-published full recipe.
"""
import hashlib
import importlib.machinery
from pathlib import Path
from STAGECGA import read, write, once

HERE = Path(__file__).resolve().parent
CRTC = (0x71, 0x50, 0x5a, 0x0a, 0x7f, 6, 0x64, 0x70, 2, 1, 0x20, 0,
        0, 0, 0, 0)


def fragment(name):
    return read(HERE / name)


def geometry(text):
    for old, new in (
        ('SCREEN_HEIGHT equ 200', 'SCREEN_HEIGHT equ 100'),
        ('shadow_bits db 16000 dup (0)', 'shadow_bits db 8000 dup (0)'),
        ('BITMAP <0,160,200,20,4,1,0,4000', 'BITMAP <0,160,100,20,4,1,0,2000'),
        ('BITMAP <1,160,200,20,4,1,0,4000', 'BITMAP <1,160,100,20,4,1,0,2000'),
        ('240,180,160,200,1,4', '240,180,160,100,1,4'),
        ('2400,1800,160,-200', '2400,1800,160,-100'),
        ('24000,18000,160,-200', '24000,18000,160,-100'),
        ('mov cx,8000', 'mov cx,4000'),
        ('HYPOTENUSE\t=\t23', 'HYPOTENUSE\t=\t31'),
        ('Y_MAJOR_DIST\t=\t12', 'Y_MAJOR_DIST\t=\t24'),
        ('dw 1500,900,254,-254', 'dw 1500,1800,254,-254'),
        ('dw 15000,9000,254,-254', 'dw 15000,18000,254,-254'),
        ('dw 21600,6480,254,-127', 'dw 21600,12960,254,-127'),
        ('dw 96,48,DC_IgnoreDFNP', 'dw 48,40,DC_IgnoreDFNP'),
    ):
        text = once(text, old, new)
    return text


def scanlines(text):
    # Four complete converters: full/row, retained row, column, retained
    # column. Preserve upstream bounds, immediate drawing and ROP behavior.
    for row in ('bp', 'ss:[bp-2]'):
        old = ('    mov ax,' + row + '\n    and ax,1\n    mov cl,13\n'
               '    shl ax,cl\n    mov di,ax\n    mov ax,' + row + '\n'
               '    shr ax,1\n    mov cx,80\n    mul cx\n    add di,ax\n')
        text = once(text, old, '    mov ax,' + row + '\n    mov cx,160\n    mul cx\n    mov di,ax\n', 2)
    old = '    mov ax,ss:[bp-6]\n    shl ax,1\n    shl ax,1\n    add di,ax\n'
    text = once(text, old, old.replace('    add di,ax', '    shl ax,1\n    add di,ax'), 2)
    # Four generated physical pixels pairs for each eight logical pixels.
    text = once(text, '      or al,dl\n      stosb\n',
                '      or al,dl\n      mov es:[di+1],al\n'
                '      mov byte ptr es:[di],0deh\n      add di,2\n', 4)
    # Saved-footprint retention uses physical byte coordinates, now 8 bytes
    # per logical-byte column (four character/attribute pairs).
    text = once(text, '    xor cx,cx\n    mov dx,80\n    call cursor_begin_retain',
                '    xor cx,cx\n    mov dx,160\n    call cursor_begin_retain')
    text = once(text, '    shl cx,1\n    shl dx,1\n    lea si,[bp-12]',
                '    shl cx,1\n    shl dx,1\n    shl cx,1\n    shl dx,1\n    lea si,[bp-12]')
    # Every VRAM access, including nested cursor save/restore, is made with
    # video disabled. Helpers preserve registers and caller interrupt state.
    for start, end in (('flush_start:', 'FlushShadow endp'),
                       ('keep_start:', 'FlushRetainRows endp'),
                       ('kcols_start:', 'FlushRetainColumns endp'),
                       ('cols_start:', 'FlushColumns endp')):
        a = text.index('\n'+start)+1
        b = text.index(end,a)
        part = text[a:b]
        part = once(part, '    push es\n', '    push es\n    call cga_vram_begin\n')
        # End after cursor_show/end_retain, but before final pop AX/return.
        p = part.rindex('    pop ax\n')
        part = part[:p] + '    call cga_vram_end\n' + part[p:]
        text = text[:a] + part + text[b:]
    return text


def cursor(text):
    text = once(text, 'tc_y            dw 100', 'tc_y            dw 50')
    text = once(text, 'tc_saved        db 544 dup (0)', 'tc_saved        db 1088 dup (0)')
    text = once(text, 'cmp ax,544', 'cmp ax,1088')
    text = once(text, 'cmp tc_bottom,200', 'cmp tc_bottom,100')
    text = once(text, 'mov tc_bottom,200', 'mov tc_bottom,100')
    text = once(text, 'cmp bx,200', 'cmp bx,100', 2)
    text = once(text, 'cmp ax,200', 'cmp ax,100')
    for reg in ('dx', 'cx'):
        text = once(text, 'cmp ' + reg + ',80', 'cmp ' + reg + ',160', 2 if reg == 'dx' else 1)
    a, b = text.index('tc_scan proc near'), text.index('tc_scan endp')
    text = text[:a] + '''tc_scan proc near
    push dx
    mov dx,160
    mul dx
    mov di,ax
    pop dx
    ret
''' + text[b:]
    text = once(text, '    shr ax,1\n    mov tc_save_xbyte,ax',
                '    shr ax,1\n    shl ax,1\n    mov tc_save_xbyte,ax')
    text = once(text, '    shr bx,1\n    sub bx,ax\n    inc bx\n    mov tc_save_bytes,bx',
                '    shr bx,1\n    shl bx,1\n    sub bx,ax\n    add bx,2\n    mov tc_save_bytes,bx')
    text = once(text, '    mov ax,tc_work_x\n    shr ax,1\n    mov di,tc_row_offset\n    add di,ax',
                '    mov ax,tc_work_x\n    shr ax,1\n    shl ax,1\n    inc ax\n'
                '    mov di,tc_row_offset\n    add di,ax')
    text = once(text, 'include windefs.inc\n',
                'include windefs.inc\nexternFP cga_vram_begin\nexternFP cga_vram_end\n')
    text = once(text, '    mov si,offset tc_saved\n',
                '    call cga_vram_begin\n    mov si,offset tc_saved\n', 2)
    text = once(text, 'tce_done:\n', '    call cga_vram_end\ntce_done:\n')
    # Only the nonempty drawn path reaches the final ret.
    a, b = text.index('tc_draw proc near'), text.index('tc_draw endp')
    part = text[a:b]
    p = part.rindex('    ret\n')
    part = part[:p] + '    call cga_vram_end\n' + part[p:]
    return text[:a] + part + text[b:]


def stage(renderer, resources):
    paths = {name: renderer / name for name in ('EGA/TSOFT.ASM', 'EGA/TCURSOR.ASM', 'SDIB88.ASM', 'EGA/TSOFT.DEF')}
    originals = {name: read(path) for name, path in paths.items()}
    text = geometry(originals['EGA/TSOFT.ASM'])
    text = scanlines(text)
    text = once(text, 'old_mode db 3\n', 'old_mode db 3\n' + fragment('CGA100D.ASM'))
    text = once(text, 'get_nibble macro\n', fragment('CGAVRAM.ASM') + 'get_nibble macro\n')
    text = once(text, '    mov ax,0008h\n    int 10h\n', fragment('CGA100E.ASM'))
    # Added initialization is too long for TEnable's former short branch.
    text = once(text, '    cmp enabled_flag,0\n    jne enable_ok\n',
                '    cmp enabled_flag,0\n    je cga_enable_first\n    jmp enable_ok\ncga_enable_first:\n')
    text = once(text, '    mov enabled_flag,1\n',
                '    mov enabled_flag,1\n    mov dx,3d8h\n    mov al,09h\n    out dx,al\n')
    text = once(text, '    mov al,old_mode\n    xor ah,ah\n    int 10h\n',
                '    mov cga_vram_depth,0\n    mov al,old_mode\n    xor ah,ah\n    int 10h\n'
                '    cmp old_mode,3\n    ja cga_restore_done\n'
                '    mov al,cga_old_page\n    mov ah,5\n    int 10h\n    mov cx,cga_old_shape\n'
                '    mov ah,1\n    int 10h\n    mov bh,cga_old_page\n'
                '    mov dx,cga_old_pos\n    mov ah,2\n    int 10h\ncga_restore_done:\n')
    dib = originals['SDIB88.ASM'].replace('physical 160x200 shadow', 'physical 160x100 shadow')
    dib = once(dib, '    cmp bx,200\n', '    cmp bx,100\n')
    dib = once(dib, '    mov bx,200\n', '    mov bx,100\n')
    changed = {'EGA/TSOFT.ASM': text, 'EGA/TCURSOR.ASM': cursor(originals['EGA/TCURSOR.ASM']),
               'SDIB88.ASM': dib,
               'EGA/TSOFT.DEF': once(originals['EGA/TSOFT.DEF'],
                    '200,96,48 : Tandy 160x200 16-color software raster',
                    '100,48,40 : IBM CGA 160x100 16-color (experimental)')}
    # Validate all source edits before writing the stage.
    for name, value in changed.items():
        write(paths[name], value)
    ui = importlib.machinery.SourceFileLoader('cga100ui', str(HERE / 'CGAUI.PY')).load_module()
    ui.stage(resources)
    return dict(shadow_bytes=8000, vram_bytes=16384, visible_vram_bytes=16000,
                physical_row_bytes=160, character=0xde, crtc=list(CRTC),
                timing='DERIVED_IBM_TABLE_COMBINATION; MC6845 only; native verification pending',
                pixel_aspect_width_over_height='5/6 at a 4:3 active picture',
                snow_policy='video disabled around every converter/cursor VRAM access; may visibly blank',
                input_sha256={k: hashlib.sha256(v.encode('latin1')).hexdigest() for k,v in originals.items()},
                runtime='NOT_TESTED')
