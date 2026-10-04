#!/usr/bin/env python3
"""Exact-pinned synchronous cursor retention for two isolated experiments.

Apply after the unchanged profile/8088-safe-copy passes, and BYTECOL when
combined. Changes only staged TSOFT and TCURSOR; original flushes stay exact.
"""
from pathlib import Path
import hashlib

EXPECTED = {'cursor': {'320x200x16': {'TSOFT.ASM': '52e0b385cd05899cce7e5d443b9f04d0084a00eb2eea5c77b741a394d29cafdf', 'TCURSOR.ASM': 'c09642e88edd57ac46a66f2d00754a718f6967f17fea65849adbe3b615a69017'}, '640x200x4': {'TSOFT.ASM': '396c8ca5c742697f33e1fc1d97000f56ac95dfd41cc92065a6e7322351a74e97', 'TCURSOR.ASM': '9024deb7a9a67e40e761624efc51e496c5c212e58c4ce6a533b4db02f3927f64'}, '160x200x16': {'TSOFT.ASM': '9936a30c5b31b80745024bd8c990d0f1e1fae05b4ebe16ab05e9d5ccaa4fe230', 'TCURSOR.ASM': '8c25e5605dc14ce3bc364a5c9b937c56130b99e49984ff011e7ca4e8621f0e01'}, '320x200x4': {'TSOFT.ASM': '697c650365020d8959f0e86b26343c8ff4ada9b01e41910a652516a6cbafd350', 'TCURSOR.ASM': '82f1d117891c5e7d7c5a04b44e703e3c0d69a0caecb6f569847662bc8b838bc5'}, '640x200x2': {'TSOFT.ASM': 'a0b9dc8ac38047fcd7ec01a40f4e78fe4e7d0019b3bfc9edd3483acf1ea81d11', 'TCURSOR.ASM': '0d4b37c10093a288ed1b4236290164875594a665fb94ea7bdc249a851afc7b57'}}, 'combined': {'320x200x16': {'TSOFT.ASM': '652cc11936a011c60c2907b88d5df17de7f59f29415062d6fb8ac425157d4c54', 'TCURSOR.ASM': 'c09642e88edd57ac46a66f2d00754a718f6967f17fea65849adbe3b615a69017'}, '640x200x4': {'TSOFT.ASM': '668b3f637cc49172af0ad26628525dbd018206250abe3351353fba173e071dce', 'TCURSOR.ASM': '9024deb7a9a67e40e761624efc51e496c5c212e58c4ce6a533b4db02f3927f64'}, '160x200x16': {'TSOFT.ASM': '11b6e2dc08457808398871031e7524e21146a5279c39ed0551c11be9bacfd19f', 'TCURSOR.ASM': '8c25e5605dc14ce3bc364a5c9b937c56130b99e49984ff011e7ca4e8621f0e01'}, '320x200x4': {'TSOFT.ASM': '7122d7ae17a882a1d903986a46c1290087dd45b0b501149429b991983f0e5338', 'TCURSOR.ASM': '82f1d117891c5e7d7c5a04b44e703e3c0d69a0caecb6f569847662bc8b838bc5'}, '640x200x2': {'TSOFT.ASM': 'f9b27f77d47d7d0ffaefdd2fd4ecbc6c604a263d552597e5e3af0d418bf2529a', 'TCURSOR.ASM': '0d4b37c10093a288ed1b4236290164875594a665fb94ea7bdc249a851afc7b57'}}}
PHYSICAL_BYTES = {'320x200x16':4,'640x200x4':2,'160x200x16':4,'320x200x4':2,'640x200x2':1}

def normalized(path):
    return Path(path).read_bytes().replace(b'\r\n',b'\n').replace(b'\x1a',b'').decode('latin1')
def sha(text):
    return hashlib.sha256(text.encode('latin1')).hexdigest()
def write_dos(path,text):
    Path(path).write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
def once(text,old,new):
    if text.count(old)!=1: raise RuntimeError('CURKEEP anchor count: '+repr(old))
    return text.replace(old,new)

def cursor_helpers(stride):
    return '''
; CURKEEP: private synchronous saved-footprint lease. Token belongs to caller SS.
; AX/BX = half-open rows, CX/DX = half-open physical byte columns.
; SI = SS offset of a token word (0 legacy, 1 retained, 2 consumed).
; Preserve all GPRs, DS/ES, SP and FLAGS. No DS=SS assumption.
; The supported foreground flush never yields into Enable/Disable.
; The only new interrupt-masked work is bounded metadata validation/ownership.
ck_require macro condition,failed
local accepted
    condition accepted
    jmp failed
accepted:
endm

public cursor_begin_retain
cursor_begin_retain proc far
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bp,sp
    mov ax,seg tc_x
    mov ds,ax
    mov word ptr ss:[si],0
    cli
    cmp enabled_flag,0
    ck_require jne,ckb_legacy
    cmp tc_busy,0
    ck_require je,ckb_legacy
    cmp tc_depth,0
    ck_require je,ckb_legacy
    cmp tc_drawn,1
    ck_require je,ckb_legacy
    cmp tc_have,1
    ck_require je,ckb_legacy
    ; Validate the actual requested physical footprint, not logical pixels.
    mov ax,ss:[bp+16]
    cmp ax,bx
    ck_require jb,ckb_legacy
    cmp bx,200
    ck_require jbe,ckb_legacy
    cmp cx,dx
    ck_require jb,ckb_legacy
    cmp dx,STRIDE
    ck_require jbe,ckb_legacy
    ; Saved origin/counts must describe a nonempty in-screen byte rectangle.
    mov ax,tc_save_y
    cmp ax,200
    ck_require jb,ckb_legacy
    mov bx,tc_save_rows
    or bx,bx
    ck_require jnz,ckb_legacy
    add bx,ax
    ck_require jnc,ckb_legacy
    cmp bx,200
    ck_require jbe,ckb_legacy
    mov cx,tc_save_xbyte
    cmp cx,STRIDE
    ck_require jb,ckb_legacy
    mov dx,tc_save_bytes
    or dx,dx
    ck_require jnz,ckb_legacy
    add dx,cx
    ck_require jnc,ckb_legacy
    cmp dx,STRIDE
    ck_require jbe,ckb_legacy
    ; Keep saved extents in DI/BX while validating total saved buffer length.
    mov di,dx
    mov ax,tc_save_rows
    mul tc_save_bytes
    or dx,dx
    ck_require jz,ckb_legacy
    cmp ax,544
    ck_require jbe,ckb_legacy
    ; Half-open separation on either physical axis is sufficient.
    mov ax,ss:[bp+14]
    cmp ax,tc_save_y
    jbe ckb_retain
    mov ax,ss:[bp+16]
    cmp ax,bx
    jae ckb_retain
    mov ax,ss:[bp+10]
    cmp ax,cx
    jbe ckb_retain
    mov ax,ss:[bp+12]
    cmp ax,di
    jae ckb_retain
    jmp short ckb_legacy
ckb_retain:
    inc tc_depth
    mov word ptr ss:[si],1
    jmp short ckb_done
ckb_legacy:
    ; Restore caller interrupt state before entering the historical path.
    push word ptr ss:[bp+18]
    popf
    call cursor_hide
ckb_done:
    pop es
    pop ds
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    retf
cursor_begin_retain endp

; Consume only this call's lease; do not steal busy or clear deferred work.
public cursor_end_retain
cursor_end_retain proc far
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bp,sp
    mov ax,seg tc_x
    mov ds,ax
    cli
    mov ax,ss:[si]
    mov word ptr ss:[si],2
    cmp ax,0
    je cke_legacy
    cmp ax,1
    jne cke_done
    cmp tc_depth,0
    je cke_done
    dec tc_depth
    cmp tc_depth,0
    jne cke_done
    cmp enabled_flag,0
    je cke_done
    cmp tc_busy,0
    jne cke_done
    cmp tc_pending,0
    jne cke_refresh
    cmp tc_drawn,0
    jne cke_done
    cmp tc_have,0
    je cke_done
cke_refresh:
    mov tc_busy,1
    push word ptr ss:[bp+18]
    popf
    call tc_refresh
    jmp short cke_done
cke_legacy:
    push word ptr ss:[bp+18]
    popf
    call cursor_show
cke_done:
    pop es
    pop ds
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    retf
cursor_end_retain endp

; Real mode-transition paths call only while enabled_flag is zero.
; Discard old-mode background metadata, never restore pixels into a new mode.
; Preserve shape/latest coordinates/hide nesting/current busy ownership.
public cursor_invalidate
cursor_invalidate proc far
    pushf
    cli
    push ax
    push ds
    mov ax,seg tc_x
    mov ds,ax
    cmp enabled_flag,0
    jne cki_done
    mov tc_drawn,0
    mov tc_save_rows,0
    mov tc_save_bytes,0
    mov tc_pending,1
cki_done:
    pop ds
    pop ax
    popf
    retf
cursor_invalidate endp
'''.replace('STRIDE',str(stride))

def rows_helper(original,stride):
    old = original.split('FlushRows label near\n',1)[1].split('FlushShadow endp\n',1)[0]
    text = old.replace('flush_', 'keep_')
    text = once(text,'    push es\n','    push es\n    sub sp,2\n')
    text = once(text,'    call cursor_hide\n', '    mov si,sp\n    xor cx,cx\n    mov dx,'+str(stride)+'\n    call cursor_begin_retain\n')
    text = once(text,'keep_finished:\n    pop es\n', 'keep_finished:\n    mov si,sp\n    call cursor_end_retain\n    add sp,2\n    pop es\n')
    text = once(text,'    call cursor_show\n','')
    return '\n; CURKEEP: opt-in full physical rows. Two-byte token on caller SS.\npublic FlushRetainRows\nFlushRetainRows proc near\n' + text + 'FlushRetainRows endp\n'

def columns_helper(original,factor):
    old = original.split('FlushColumns proc near\n',1)[1].split('FlushColumns endp\n',1)[0]
    text = old.replace('cols_', 'kcols_')
    text = once(text,'    sub sp,10\n','    sub sp,12\n')
    entry='    push cx\n    push dx\n'
    entry+= ('    shl cx,1\n    shl dx,1\n')*(factor.bit_length()-1)
    entry+='    lea si,[bp-12]\n    call cursor_begin_retain\n    pop dx\n    pop cx\n'
    text=once(text,'    call cursor_hide\n',entry)
    text=once(text,'kcols_finished:\n    mov sp,bp\n','kcols_finished:\n    lea si,[bp-12]\n    call cursor_end_retain\n    mov sp,bp\n')
    text=once(text,'    call cursor_show\n','')
    return '\n; CURKEEP: opt-in logical-byte columns; begin compares scaled physical bytes.\n; SS:BP-12 token, other private locals identical to FlushColumns.\npublic FlushRetainColumns\nFlushRetainColumns proc near\n'+text+'FlushRetainColumns endp\n'

def port(renderer,mode,combined=False):
    variant='combined' if combined else 'cursor'
    base=Path(renderer)/'EGA'
    source={name:normalized(base/name) for name in ('TSOFT.ASM','TCURSOR.ASM')}
    for name,text in source.items():
        actual=sha(text)
        if actual!=EXPECTED[variant][mode][name]:
            raise RuntimeError('Unaudited CURKEEP '+variant+' '+mode+' '+name+': '+actual)
    text=source['TSOFT.ASM']
    stride=int(mode.split('x')[0])//8*PHYSICAL_BYTES[mode]
    rows=rows_helper(text,stride)
    columns=columns_helper(text,PHYSICAL_BYTES[mode]) if combined else ''
    text=once(text,'externFP cursor_show\n','externFP cursor_show\nexternFP cursor_begin_retain\nexternFP cursor_end_retain\nexternFP cursor_invalidate\n')
    text=once(text,'FlushShadow endp\n','FlushShadow endp\n'+rows+columns)
    begin,end=text.index('cProc TBitBlt,'),text.index('cProc TOutput,')
    blt=text[begin:end]
    blt=once(blt,'    call FlushRows\n','    call FlushRetainRows\n')
    if combined: blt=once(blt,'    call FlushColumns\n','    call FlushRetainColumns\n')
    text=text[:begin]+blt+text[end:]
    begin,end=text.index('cProc TPixel,'),text.index('cProc TScanLR,')
    pixel=text[begin:end]
    legacy='FlushColumns' if combined else 'FlushRows'
    retained='FlushRetainColumns' if combined else 'FlushRetainRows'
    pixel=once(pixel,'TPixel_flush:\n    call '+legacy+'\n', '    call '+retained+'\n    jmp short TPixel_flushed\nTPixel_flush:\n    call '+legacy+'\nTPixel_flushed:\n')
    text=text[:begin]+pixel+text[end:]
    text=once(text,'    cmp enabled_flag,0\n    jne enable_ok\n','    cmp enabled_flag,0\n    jne enable_ok\n    call cursor_invalidate\n')
    text=once(text,'    mov enabled_flag,0\n    mov al,old_mode\n', '    pushf\n    cli\n    mov enabled_flag,0\n    call cursor_invalidate\n    popf\n    mov al,old_mode\n')
    cur=once(source['TCURSOR.ASM'],'cursor_show endp\n','cursor_show endp\n'+cursor_helpers(stride))
    # Original helpers and public cursor APIs must remain source-identical.
    def section(t,start,end): return t.split(start,1)[1].split(end,1)[0]
    for start,end in [('public FlushShadow,FlushRows\n','FlushShadow endp\n')]+([('public FlushColumns\n','FlushColumns endp\n')] if combined else []):
        if section(text,start,end)!=section(source['TSOFT.ASM'],start,end): raise RuntimeError('Original flush changed')
    if cur.split('cProc Inquire,',1)[1]!=source['TCURSOR.ASM'].split('cProc Inquire,',1)[1]: raise RuntimeError('Public cursor APIs changed')
    write_dos(base/'TSOFT.ASM',text)
    write_dos(base/'TCURSOR.ASM',cur)
    return {'feature':'synchronous cursor saved-footprint retention', 'variant':variant, 'mode':mode,
      'changed_staged_files':['EGA/TSOFT.ASM','EGA/TCURSOR.ASM'],
      'input_normalized_sha256':EXPECTED[variant][mode],
      'output_normalized_sha256':{'TSOFT.ASM':sha(text),'TCURSOR.ASM':sha(cur)},
      'physical_row_bytes':stride,'original_flush_helpers':'SOURCE_IDENTICAL',
      'public_cursor_apis':'SOURCE_IDENTICAL','runtime':'NOT_TESTED',
      'contract':'AX/BX physical rows; CX/DX physical bytes; SI SS token word, 0 legacy / 1 retained / 2 consumed; private far helpers preserve GPR/DS/ES/FLAGS; owned depth only; no new masked pixel work',
      'lifecycle':'serialized non-yielding foreground; disabled-only metadata invalidation before BIOS; no depth/busy/shape/position reset'}
