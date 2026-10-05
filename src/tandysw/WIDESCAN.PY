#!/usr/bin/env python3
"""Bounded synchronous multi-interval scanline refresh, after exact Trial4.

Renderer operations and geometry are unchanged. GDI decomposes wide rectangles
into OS_SCANLINES with two edge intervals. Only validated solid scan rows with
2..64 points qualify; all uncertain cases retain the original full refresh.
"""
from pathlib import Path
import hashlib

EXPECTED = {'320x200x16': '2eec973b3603bc9591abc855948459181054220f925e5cb2c6e9d74f9b13a513', '640x200x4': 'fe08b58f1b925365a9e49efd98851d262edf3e0fec10f998855c9fca391c15cd', '160x200x16': 'd513690cf6f820fa5ffb498bdebefc08b3957320029ebac9cbb735f98e64256f', '320x200x4': '94e59cd37ca8642da8f2abf2e487ac4ef5dbf8ad3e42e668d8b5e712b830dc81', '640x200x2': '447788c01cfbb0dd3ffa7c7e46ad4b6c29984cabc1e593e6470351e03ec8b40e'}

def once(s,old,new):
    if s.count(old)!=1:raise RuntimeError('WIDESCAN scope anchor mismatch: '+repr(old))
    return s.replace(old,new)

CHANGES = [
('    cmp count,2\n    or_require je,TOutput_render\n    cmp style,18\n    je TOutput_style_ok\n    cmp style,4\n    or_require je,TOutput_render\nTOutput_style_ok:\n    les di,points\n    mov cx,8\n','    ; WIDESCAN: bounded scan lists only. Thin-line gate stays count=2.\n    cmp style,4\n    jne TOutput_thin_count\n    cmp count,2\n    or_require jae,TOutput_render\n    cmp count,64\n    or_require jbe,TOutput_render\n    jmp short TOutput_style_ok\nTOutput_thin_count:\n    cmp style,18\n    or_require je,TOutput_render\n    cmp count,2\n    or_require je,TOutput_render\nTOutput_style_ok:\n    les di,points\n    mov cx,count\n    shl cx,1\n    shl cx,1\n'),
('    ; One scanline: ignored x, y, left, exclusive right.\n    mov ax,es:[di+2]\n    cmp ax,SCREEN_HEIGHT\n    or_require jb,TOutput_render\n    mov bx,es:[di+4]\n    mov dx,es:[di+6]\n    cmp bx,dx\n    or_require jb,TOutput_render\n    cmp dx,SCREEN_WIDTH\n    or_require jbe,TOutput_render\n    mov firstrow,ax\n    inc ax\n    mov lastrow,ax\n    jmp short TOutput_bounded\n','    ; One Y shared by count-1 intervals. Rendering order/overlap unchanged.\n    ; Validate the complete far span above, then every exclusive-X pair.\n    mov ax,es:[di+2]\n    cmp ax,SCREEN_HEIGHT\n    or_require jb,TOutput_render\n    mov firstrow,ax\n    inc ax\n    mov lastrow,ax\n    mov cx,count\n    dec cx\nTOutput_scan_interval:\n    add di,4\n    mov bx,es:[di]\n    mov dx,es:[di+2]\n    cmp bx,dx\n    or_require jb,TOutput_render\n    cmp dx,SCREEN_WIDTH\n    or_require jbe,TOutput_render\n    loop TOutput_scan_interval\n    jmp short TOutput_bounded\n')]

def port(renderer,mode):
    p=Path(renderer)/'EGA/TSOFT.ASM';before=p.read_bytes()
    if hashlib.sha256(before).hexdigest()!=EXPECTED[mode]:
        raise RuntimeError('WIDESCAN exact Trial4 input mismatch')
    old=before.decode('latin1').replace('\r\n','\n');new=old
    for a,b in CHANGES:new=once(new,a,b)
    inverse=new
    for a,b in reversed(CHANGES):inverse=once(inverse,b,a)
    if inverse!=old:raise RuntimeError('WIDESCAN inverse scope failure')
    p.write_bytes(new.replace('\n','\r\n').encode('latin1'))
    return {'feature':'bounded synchronous multi-interval scanline row refresh',
      'input_sha256':EXPECTED[mode],'output_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),
      'changed_staged_files':['EGA/TSOFT.ASM'],'inverse_scope':'EXACT_TRIAL4',
      'limit':'style4 count2..64, complete 4*count far span, all exclusive-X intervals nonempty and in screen, Y in screen',
      'unchanged':'renderer, drawing order, ROP2, brushes, polyline count2 contract, clipping semantics, cursor retain/hide, all copy and conversion helpers',
      'fallback':'original full synchronous refresh for all unproven inputs',
      'runtime':'NOT_TESTED'}
