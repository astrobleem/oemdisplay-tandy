#!/usr/bin/env python3
"""Exact-pinned conservative synchronous Output row bounds after CURKEEP.

Only count=2 solid scanlines and thin polylines are eligible. Full fallback
for every unproven case. This transformation is not runtime qualification.
"""
from pathlib import Path
import hashlib

EXPECTED = {'320x200x16': {'TSOFT.ASM': '946ec043c720a4f46ad663fb0d70e37ea1db53bba3619da5790e8af67f73cbb5', 'TCURSOR.ASM': 'f3db33bf3b15237bb2baa378edd3b41831b08355a5d85ac09d9470915e64fc1e'}, '640x200x4': {'TSOFT.ASM': '939c4171d51494eb320aa577e8df4c2a38d3936bba3b7bc3b1853dad83e9c784', 'TCURSOR.ASM': '250d616dd39ca21708701cac6e009ebfcbac977ed179c4ce19ec984865756aaf'}, '160x200x16': {'TSOFT.ASM': '16cf55b1a48f582081adaef745e148411a871003cc1e26fb25e49213e97eefd9', 'TCURSOR.ASM': '6ca256ce21fa6215d50a6bc23bd316c4b15c2eceaf1f8136165eec6fe4437bae'}, '320x200x4': {'TSOFT.ASM': 'a8f888a05555d60cc6d5b9c7797cbda23de4ff875790b661c3fcf002b8eb6c57', 'TCURSOR.ASM': '7cd0588f809a4d6c7de3030656bff83b45debdfc948da0710de3c6407d8b30e0'}, '640x200x2': {'TSOFT.ASM': '3979c67d3a952f04151372a82cc0a8a58578380f4741f523d630e6985cfb47cb', 'TCURSOR.ASM': '4a504c3b2300a28bcb2a939f1eaeb6fbb67ba93a4d6e3303f0e0cc0109054278'}}

RENDERER_PINS = {'OUTPUT.ASM': '936d80af4d305bb16b11c0203a15b4608375c4bf978f6a21077b82d70b7bd456', 'POLYLINE.ASM': 'ef21f4f899ccbfe3b783afd1e393b107e46b1725421a10fae6c3bb36301f6299', 'SCANLINE.ASM': 'f1ba086a7ac163e353ac3523dd41bebc9ea380078af787c566f8cfd3470c0d30', 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a', 'CLIP.INC': '36d3fea586d2ea3178d4f12f9ecdb4e8619dadccdda9eb4ccef14aa1541359fe', 'POLYBITM.INC': '24310589f5be7ca98c5b3756255f49b42129821f3be7908e1c337c70e59573df', 'POLYSTYL.INC': 'b5f43b951677291c8020deeb1f5dbf186afa6d143326a0e73e208f825406d11c', 'PATTERN.INC': 'be8ef8f9016881b9efc70db9d378a0747d193ba592c6abdd1de58bd13496d1d9'}

def normalized(path):
    return Path(path).read_bytes().replace(b'\r\n',b'\n').replace(b'\x1a',b'').decode('latin1')

def sha(text):
    return hashlib.sha256(text.encode('latin1')).hexdigest()

def write_dos(path,text):
    Path(path).write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))

HELPER = r'''
; OUTROWS: conservative far-span gate. ES:DI, CX=size (6/8/32/54).
; CF clear means nonnull, no offset/20-bit wrap, no canonical-shadow alias.
; Preserve every GPR and segment. SS:BP private locals; DS need not equal SS.
; No dereference, interrupt masking, callbacks, or persistent state.
or_require macro condition,failed
local accepted
    condition accepted
    jmp failed
accepted:
endm

public ORowsSpanSafe
ORowsSpanSafe proc near
    push bp
    mov bp,sp
    sub sp,12
    push ax
    push bx
    push cx
    push dx
    mov ax,es
    or ax,di
    or_require jnz,ors_bad
    mov ax,cx
    dec ax
    add ax,di
    or_require jnc,ors_bad
    mov ax,es
    mov bx,16
    mul bx
    add ax,di
    adc dx,0
    mov ss:[bp-2],ax
    mov ss:[bp-4],dx
    add ax,cx
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_input_ok
    or ax,ax
    or_require jz,ors_bad
ors_input_ok:
    mov ss:[bp-6],ax
    mov ss:[bp-8],dx
    mov ax,seg shadow_bits
    mul bx
    add ax,offset shadow_bits
    adc dx,0
    mov ss:[bp-10],ax
    mov ss:[bp-12],dx
    add ax,SCREEN_W_BYTES*4*SCREEN_HEIGHT
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_shadow_ok
    or ax,ax
    or_require jz,ors_bad
ors_shadow_ok:
    ; Object start >= shadow end, or object end <= shadow start.
    cmp ss:[bp-4],dx
    ja ors_good
    jb ors_before_end
    cmp ss:[bp-2],ax
    jae ors_good
ors_before_end:
    mov dx,ss:[bp-12]
    cmp ss:[bp-8],dx
    jb ors_good
    ja ors_bad
    mov ax,ss:[bp-10]
    cmp ss:[bp-6],ax
    jbe ors_good
ors_bad:
    stc
    jmp short ors_done
ors_good:
    clc
ors_done:
    pop dx
    pop cx
    pop bx
    pop ax
    mov sp,bp
    pop bp
    ret
ORowsSpanSafe endp

'''
WRAPPER = r'''cProc TOutput,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW style
    parmW count
    parmD points
    parmD pen
    parmD brush
    parmD mode
    parmD clip
    localW dirty
    localW outrows
    localW firstrow
    localW lastrow
cBegin
    mov dirty,0
    mov outrows,0
    map_device dst,1
    ; Capture bounds before rendering. FULL is the fail-closed default.
    ; Restore all validation scratch state before the exact renderer call.
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    cmp dirty,0
    or_require jne,TOutput_render
    cmp count,2
    or_require je,TOutput_render
    cmp style,18
    je TOutput_style_ok
    cmp style,4
    or_require je,TOutput_render
TOutput_style_ok:
    les di,points
    mov cx,8
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    les di,mode
    mov cx,32
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    dec ax
    cmp ax,15
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    dec ax
    cmp ax,1
    or_require jbe,TOutput_render
    ; SCANLINE never reads clip. Do not newly dereference an ignored input.
    cmp style,4
    je TOutput_clip_ok
    les di,clip
    mov ax,es
    or ax,di
    jz TOutput_clip_ok
    mov cx,8
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    mov bx,es:[di+4]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    mov bx,es:[di+6]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_HEIGHT
    or_require jbe,TOutput_render
TOutput_clip_ok:
    cmp style,18
    je TOutput_check_pen
    les di,brush
    mov ax,es
    or ax,di
    jz TOutput_check_pen
    mov cx,54
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+40],0
    or_require je,TOutput_render
    jmp short TOutput_objects_ok
TOutput_check_pen:
    les di,pen
    mov cx,6
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+4],4
    or_require jbe,TOutput_render
TOutput_objects_ok:
    les di,points
    cmp style,18
    je TOutput_polyline
    ; One scanline: ignored x, y, left, exclusive right.
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov bx,es:[di+4]
    mov dx,es:[di+6]
    cmp bx,dx
    or_require jb,TOutput_render
    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    mov firstrow,ax
    inc ax
    mov lastrow,ax
    jmp short TOutput_bounded
TOutput_polyline:
    mov cx,es:[di]
    cmp cx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov dx,es:[di+4]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov bx,es:[di+6]
    cmp bx,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp ax,bx
    jne TOutput_line_nonempty
    cmp cx,dx
    or_require jne,TOutput_render
TOutput_line_nonempty:
    cmp ax,bx
    jbe TOutput_line_ordered
    xchg ax,bx
TOutput_line_ordered:
    mov firstrow,ax
    inc bx
    mov lastrow,bx
TOutput_bounded:
    mov outrows,1
TOutput_render:
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp dirty,0
    je TOutput_done
    ; Preserve the actual renderer result and all post-render GPRs.
    push ax
    push bx
    cmp outrows,0
    je TOutput_full
    mov ax,firstrow
    mov bx,lastrow
    call FlushRetainRows
    jmp short TOutput_flushed
TOutput_full:
    call FlushShadow
TOutput_flushed:
    pop bx
    pop ax
TOutput_done:
cEnd

'''
ORIGINAL = r'''cProc TOutput,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW style
    parmW count
    parmD points
    parmD pen
    parmD brush
    parmD mode
    parmD clip
    localW dirty
cBegin
    mov dirty,0
    map_device dst,1
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp dirty,0
    je TOutput_done
    call FlushShadow
TOutput_done:
cEnd

'''

def port(renderer,mode):
    renderer=Path(renderer)
    for name,expected in RENDERER_PINS.items():
        if sha(normalized(renderer/name))!=expected:
            raise RuntimeError('OUTROWS renderer input mismatch: '+name)
    base=renderer/'EGA'
    source={name:normalized(base/name) for name in EXPECTED[mode]}
    actual={name:sha(text) for name,text in source.items()}
    if actual!=EXPECTED[mode]:
        raise RuntimeError('OUTROWS exact staged input mismatch: '+repr(actual))
    old=source['TSOFT.ASM']
    if old.count(ORIGINAL)!=1:
        raise RuntimeError('OUTROWS exact wrapper anchor mismatch')
    new=old.replace(ORIGINAL,HELPER+WRAPPER)
    if new.replace(HELPER+WRAPPER,ORIGINAL)!=old:
        raise RuntimeError('OUTROWS inverse-scope proof failed')
    write_dos(base/'TSOFT.ASM',new)
    return {'feature':'synchronous conservative Output full-width row bounds',
      'mode':mode,'changed_staged_files':['EGA/TSOFT.ASM'],
      'input_normalized_sha256':EXPECTED[mode],
      'renderer_normalized_sha256':RENDERER_PINS,
      'output_normalized_sha256':{'TSOFT.ASM':sha(new),'TCURSOR.ASM':actual['TCURSOR.ASM']},
      'scope_inverse':'EXACT_SOURCE_IDENTITY', 'runtime':'NOT_TESTED',
      'geometry':'count=2 only; style18 in-screen nondegenerate thin line or style4 single nonempty in-screen scan interval',
      'objects':'points8; mode32 ROP2 1..16 bkMode1/2; pen6 style0..4 or scanline brush54 BS_SOLID0; polyline-only optional ordered in-screen clip8; scanline clip ignored',
      'pointers':'checked full far spans; reject 64K/20-bit wrap and physical canonical-shadow overlap before dereference',
      'flush':'exact existing FlushRetainRows, synchronous full-width footprint; full FlushShadow fallback',
      'unchanged':'real renderer, cursor source, other wrappers, conversion helpers, marker80/81, identity SRCCOPY resync, safe-copy fix',
      'state':'private SS/BP locals only; no IRQ masking or callback state',
      'precondition':'caller objects are valid live stable allocations; far-span checks do not establish allocation ownership'}
