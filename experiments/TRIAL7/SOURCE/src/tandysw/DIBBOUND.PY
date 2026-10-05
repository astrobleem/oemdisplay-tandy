#!/usr/bin/env python3
"""Exact-pinned synchronous DIB-band refresh over the unchanged Trial5 core."""
from pathlib import Path
import hashlib

EXPECTED = {
    '160x200x16': ('08960b02040635e47b1c34fc0a36f3b9a5b8bf31f3826f49d0db07674b546abb', 'a48c21357a162203294b48c746f1e61417d0d2191991835c768127d89fe35075'),
    '320x200x16': ('e76afa30f17dfd1102e567af246b8289e2aa2814515d2d59525b957039358620', '00a67516dfd15f6451fee985cb82d526ee742a6c0db092ea68660293c0305df2'),
    '320x200x4': ('e76afa30f17dfd1102e567af246b8289e2aa2814515d2d59525b957039358620', 'df39381218d745050b8d0001506a1eaf5d6ca257a80c4508aedd8a0d044c12a4'),
    '640x200x4': ('010982ee88307074dd02fb02fa6f126207758c0177bc3312a798cb2a5f20681f', '575683eaebc5833ad78738b90daa9f1afe45a8c4443addc1ddacad5c600eb352'),
    '640x200x2': ('6ed87054e65d90d6d497a6dc68e6f9e66130e0adfd1fbc6d2733e1c3054e7d63', '994264d4cae761945f4068f9c2fdbc53f33da8cdce93a4f2fb8e84f6ca1b7f82'),
}

def normalized(path):
    return Path(path).read_bytes().replace(b'\r\n',b'\n').replace(b'\x1a',b'').decode('latin1')

def sha(text):
    return hashlib.sha256(text.encode('latin1')).hexdigest()

def once(text,old,new):
    if text.count(old)!=1: raise RuntimeError('DIBBOUND anchor: '+repr(old))
    return text.replace(old,new)

def transform(original,width):
    text=once(original,'; FlushShadow runs once, after conversion of the visible band.',
              '; Bounded refresh runs once, after conversion of the successful rows.')
    text=once(text,'externNP FlushShadow\n','externNP FlushRetainRows\nexternNP FlushRetainColumns\n')
    text=once(text,'    localW resultScans\n','    localW resultScans\n    localW dirtyBottom\n')
    text=once(text,'    mov rowCount,cx\n    dec bx\n',
              '    mov rowCount,cx\n    ; Immutable exclusive bottom: yDst differs on completion and failure.\n    mov dirtyBottom,bx\n    dec bx\n')
    text=once(text,'    call FlushShadow\nsd_cleanup:', '''    ; Successful copies are contiguous bottom-up rows. Count them instead
    ; of trusting the mutable current yDst after an early converter failure.
    ; Initial clipping proved 0 <= xDst < xDst+xCount <= screen width and
    ; 0 <= dirtyBottom-resultScans < dirtyBottom <= 200. Rounded logical
    ; bytes can refresh neighboring pixels only from the unchanged shadow.
    mov bx,dirtyBottom
    mov ax,bx
    sub ax,resultScans
    mov cx,xDst
    mov dx,cx
    add dx,xCount
    add dx,7
    shr cx,1
    shr cx,1
    shr cx,1
    shr dx,1
    shr dx,1
    shr dx,1
    or cx,cx
    jne sd_flush_columns
    cmp dx,WIDTH_BYTES
    jne sd_flush_columns
    call FlushRetainRows
    jmp short sd_cleanup
sd_flush_columns:
    call FlushRetainColumns
sd_cleanup:'''.replace('WIDTH_BYTES',str(width//8)))
    return text

def port(renderer,mode):
    renderer=Path(renderer);path=renderer/'SDIB88.ASM'
    original=normalized(path);core=normalized(renderer/'EGA/TSOFT.ASM')
    if (sha(original),sha(core))!=EXPECTED[mode]:
        raise RuntimeError('DIBBOUND requires exact Trial5 DIB bridge and retained flush core')
    text=transform(original,int(mode.split('x')[0]))
    path.write_bytes(text.replace('\n','\r\n').encode('latin1'))
    return {'feature':'synchronous bounded DIB-band byte rectangle',
            'mode':mode,'changed_staged_files':['SDIB88.ASM'],
            'input_normalized_sha256':sha(original),'output_normalized_sha256':sha(text),
            'bounds':'bottom=immutable clipped exclusive bottom; top=bottom-successful rows; columns=floor(left/8)..ceil(right/8)',
            'helpers':'exact unchanged Trial5 FlushRetainRows/FlushRetainColumns',
            'preserved':'conversion, clipping, bottom-up band mapping, successful-scan return, memory cleanup, cursor helpers, shadow allocation and all other rendering',
            'new_memory':'one private two-byte stack local',
            'runtime':'NOT_TESTED','physical_hardware':'NOT_TESTED'}
