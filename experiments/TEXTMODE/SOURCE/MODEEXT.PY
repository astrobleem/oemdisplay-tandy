#!/usr/bin/env python3
"""Stage the original Tandy 16KB graphics layouts over the audited engine.

Call port(renderer, repo, profile) after PORT8086 and PORTDIB, before MODECOL.
Only staged TSOFT/TCURSOR/SDIB88 change; frozen V1 and DDK inputs are untouched.
All profiles keep four scan-interleaved logical DDB planes. Modes 04h and 06h
show the low two/one planes, leaving quantization/canonicalization to MODECOL.
Fonts, logical DPI/aspect ratios, resources and the DEF description are owned
by MODEPROF. This module changes dimensions, NUMCOLORS, mode selection, the
shadow allocation/clear, physical flush, cursor overlay and DIB-screen bounds.

Every physical layout here has two 8192-byte banks, 100 rows/bank and 80
visible bytes/row. FlushShadow touches 16000 visible bytes, never the 384
padding bytes. Cursor AND/XOR acts only on the actual packed screen bits.
"""
from pathlib import Path
import hashlib
import re

PROFILES = {
    (160, 200, 16, 8): tuple(range(16)),
    (320, 200, 4, 4): (0, 11, 13, 15),
    (640, 200, 2, 6): (0, 15),
}


def read(path):
    return Path(path).read_bytes().replace(b'\r\n', b'\n').decode('latin1')


def write(path, text):
    Path(path).write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('latin1'))


def replace(text, old, new, count=1):
    actual = text.count(old)
    if actual != count:
        raise RuntimeError('16KB layout patch mismatch: %r: %d, expected %d' % (old, actual, count))
    return text.replace(old, new)


def section(text, first, last):
    if text.count(first) != 1 or text.count(last) != 1:
        raise RuntimeError('16KB layout section mismatch: %r / %r' % (first, last))
    start = text.index(first)
    stop = text.index(last, start)
    return text[start:stop]


def mode_select(profile):
    """BIOS mode and fixed palette setup; preserves the standard CGA contract."""
    result = '    mov ax,%04xh\n    int 10h\n' % profile['bios']
    if profile['colors'] == 4:
        # CGA palette 1, high intensity: black, bright cyan/magenta/white.
        # INT 10h/AH=0Bh is supported by the original Tandy BIOS, including
        # mode 04h; no EGA/VGA-only palette-register API is required.
        result += ('    mov ax,0b00h\n    mov bx,0010h\n    int 10h\n'
                   '    mov ax,0b00h\n    mov bx,0101h\n    int 10h\n')
    elif profile['colors'] == 2:
        # In CGA mode 06h the color-select low nibble is the foreground.
        result += '    mov ax,0b00h\n    mov bx,000fh\n    int 10h\n'
    return result


def cursor(text, width, colors):
    text = replace(text, 'Tandy 320x200 monochrome',
                   'Tandy %dx200 %d-color' % (width, colors))
    text = replace(text, 'tc_x            dw 160', 'tc_x            dw %d' % (width // 2))
    text = replace(text, 'cmp tc_right,320', 'cmp tc_right,%d' % width)
    text = replace(text, 'mov tc_right,320', 'mov tc_right,%d' % width)
    text = replace(text, '    and bx,3\n', '    and bx,1\n')
    text = replace(text, '    shr ax,1\n    shr ax,1\n    mov dx,160\n',
                   '    shr ax,1\n    mov dx,80\n')
    if colors == 16:
        return text
    shift = 2 if colors == 4 else 3
    first = '    mov ax,tc_left\n    shr ax,1\n    mov tc_save_xbyte,ax'
    last = '\n    ; Save full touched bytes'
    old = section(text, first, last)
    text = replace(text, old,
                   '    mov ax,tc_left\n' + '    shr ax,1\n' * shift +
                   '    mov tc_save_xbyte,ax\n    mov bx,tc_right\n    dec bx\n' +
                   '    shr bx,1\n' * shift +
                   '    sub bx,ax\n    inc bx\n    mov tc_save_bytes,bx\n')
    text = replace(text, 'including the unaffected edge nibble.',
                   'including unaffected edge pixels.')
    first = '    mov ax,tc_work_x\n    shr ax,1\n    mov di,tc_row_offset'
    last = '    inc tc_work_x\n'
    old = section(text, first, last)
    # BL remains the cursor-mask bit; BH is all physical bits of this pixel.
    new = ('    ; Preserve other packed pixels in this byte at either edge.\n'
           '    mov ax,tc_work_x\n    mov cx,ax\n'
           '    and cx,%d\n    xor cx,%d\n' % ((1 << shift)-1, (1 << shift)-1))
    if colors == 4:
        new += '    shl cx,1\n'
    new += ('    mov bh,%d\n    shl bh,cl\n' % (colors-1) +
            '    shr ax,1\n' * shift +
            '    mov di,tc_row_offset\n    add di,ax\n    mov dl,es:[di]\n'
            '    test tc_and[si],bl\n    jnz tcd_and_done\n'
            '    mov al,bh\n    not al\n    and dl,al\n'
            'tcd_and_done:\n    test tc_xor[si],bl\n    jz tcd_xor_done\n'
            '    xor dl,bh\ntcd_xor_done:\n    mov es:[di],dl\n')
    return replace(text, old, new)


def port(renderer, repo, profile):
    """Stage 08h/04h/06h; reject unsupported profiles before writing files."""
    renderer, repo = Path(renderer), Path(repo)
    key = tuple(profile[name] for name in ('width', 'height', 'colors', 'bios'))
    if key not in PROFILES or tuple(profile['palette']) != PROFILES[key]:
        raise ValueError('Unsupported original-Tandy 16KB mode/palette: %r' % (profile,))
    width, height, colors, bios = key
    stride, shadow_bytes = width // 8, width // 8 * 4 * height
    text = read(renderer / 'EGA/TSOFT.ASM')
    if 'DIMapSeg_color_table label\tdword' not in text:
        raise RuntimeError('PORTDIB must run before MODEEXT')
    if '.8086' not in read(renderer / 'INC/CMACROS.INC'):
        raise RuntimeError('PORT8086 must run before MODEEXT')
    if not re.search(r'^COLOR_FORMAT equ 0104h$', text, re.M):
        raise RuntimeError('MODEEXT requires the retained four-plane DDB format')
    baseline = read(repo / 'src/tandysw/V1.ASM')
    # Require the full known flush and cursor input, not a partially edited
    # mode. All validation/preparation finishes before any staged file changes.
    first, last = 'get_nibble macro\n', 'FlushShadow endp'
    old = section(baseline, first, last)
    if old not in text:
        raise RuntimeError('MODEEXT requires the unmodified V1 flush')
    old_cursor = read(renderer / 'EGA/TCURSOR.ASM')
    if old_cursor != read(repo / 'src/tandysw/TCURSOR.ASM'):
        raise RuntimeError('MODEEXT requires the unmodified cursor input')
    for old, new in (
        ('320x200x16, real mode', '%dx200x%d, real mode' % (width, colors)),
        ('SCREEN_WIDTH equ 320', 'SCREEN_WIDTH equ %d' % width),
        ('SCREEN_W_BYTES equ 40', 'SCREEN_W_BYTES equ %d' % stride),
        ('shadow_bits db 32000 dup (0)', 'shadow_bits db %d dup (0)' % shadow_bytes),
        ('BITMAP <0,320,200,40,4,1,0,8000', 'BITMAP <0,%d,200,%d,4,1,0,%d' % (width, stride, stride*height)),
        ('BITMAP <1,320,200,40,4,1,0,8000', 'BITMAP <1,%d,200,%d,4,1,0,%d' % (width, stride, stride*height)),
        ('dw 0300h,DT_RASDISPLAY,240,180,320,200,1,4',
         'dw 0300h,DT_RASDISPLAY,240,180,%d,200,1,4' % width),
        ('dw -1,80,0,0,16,size BITMAP', 'dw -1,%d,0,0,%d,size BITMAP' % (colors*5, colors)),
        ('2400,1800,320,-200', '2400,1800,%d,-200' % width),
        ('24000,18000,320,-200', '24000,18000,%d,-200' % width),
        ('mov cx,16000', 'mov cx,%d' % (shadow_bytes // 2)),
        ('    mov ax,9\n    int 10h\n', mode_select(profile)),
        ('    and ax,3\n', '    and ax,1\n'),
        ('    shr ax,1\n    shr ax,1\n    mov cx,160\n',
         '    shr ax,1\n    mov cx,80\n'),
    ):
        text = replace(text, old, new)
    first, last = '    mov cx,40\nflush_byte:', '    inc bp\n'
    old = section(text, first, last)
    if colors == 16:
        new = old
        for a, b in (('mov cx,40', 'mov cx,20'), ('[si+40]', '[si+20]'),
                     ('[si+80]', '[si+40]'), ('[si+120]', '[si+60]'),
                     ('add si,120', 'add si,60')):
            new = replace(new, a, b)
    elif colors == 4:
        new = '''    ; Low logical C0/C1 become packed CGA pixel bits 0/1.
    mov cx,40
flush_byte:
    mov bl,[si]
    mov bh,[si+40]
    rept 2
      xor al,al
      rept 4
        shl bh,1
        rcl al,1
        shl bl,1
        rcl al,1
      endm
      stosb
    endm
    inc si
    loop flush_byte
flush_next_row:
    add si,120
'''
    else:
        new = '''    ; Only the low logical plane is visible in 640x200 mono.
    mov cx,80
flush_byte:
    rep movsb
flush_next_row:
    add si,240
'''
    text = replace(text, old, new)
    dib = read(renderer / 'SDIB88.ASM')
    dib = replace(dib, 'physical 320x200 shadow', 'physical %dx200 shadow' % width)
    dib = replace(dib, '    cmp bx,320\n', '    cmp bx,%d\n' % width)
    dib = replace(dib, '    mov bx,320\n', '    mov bx,%d\n' % width)
    changed = {'EGA/TSOFT.ASM': text, 'EGA/TCURSOR.ASM': cursor(old_cursor, width, colors),
               'SDIB88.ASM': dib}
    for name, value in changed.items():
        write(renderer / name, value)
    return dict(feature='original-Tandy 16KB packed graphics layout', bios_mode=bios,
                width=width, height=height, colors=colors, logical_planes=4,
                shadow_bytes=shadow_bytes, vram_bytes=16384, visible_vram_bytes=16000,
                padding_bytes=384, banks=2, bank_bytes=8192, physical_row_bytes=80,
                palette_method='CGA INT 10h/AH=0Bh' if colors < 16 else 'BIOS 08h RGBI defaults',
                patched_files=sorted(changed),
                staged_sha256={name: hashlib.sha256((renderer/name).read_bytes()).hexdigest()
                               for name in sorted(changed)})
