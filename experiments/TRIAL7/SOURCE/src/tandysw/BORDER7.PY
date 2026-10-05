#!/usr/bin/env python3
"""Exact-TR6-pinned synchronous border/line byte-column refresh.

Only the TOutput wrapper changes. The renderer, original eligibility gate,
far-span validation, DIB bridge, conversion and cursor helpers stay exact.
In color modes, two scan intervals are copied independently from the completed shadow; no
points are read after rendering, and no ROP or drawing order is changed.
Monochrome scans retain TR6 rows; thin-line byte bounds remain enabled.
This transformation and its host checks are not runtime qualification.
"""
from pathlib import Path
import hashlib

EXPECTED = {'320x200x16': {'EGA/TSOFT.ASM': '00a67516dfd15f6451fee985cb82d526ee742a6c0db092ea68660293c0305df2',
                'EGA/TCURSOR.ASM': 'f3db33bf3b15237bb2baa378edd3b41831b08355a5d85ac09d9470915e64fc1e',
                'SDIB88.ASM': 'c23feb8e35a4e9aa2c54a3042366318de385e098e4447b6f3d360211a87da25a'},
 '640x200x4': {'EGA/TSOFT.ASM': '575683eaebc5833ad78738b90daa9f1afe45a8c4443addc1ddacad5c600eb352',
               'EGA/TCURSOR.ASM': '250d616dd39ca21708701cac6e009ebfcbac977ed179c4ce19ec984865756aaf',
               'SDIB88.ASM': 'a02662bc3ddc703ef69590e3b9503f81569553e6cd1af43c8d045c81aac657f6'},
 '160x200x16': {'EGA/TSOFT.ASM': 'a48c21357a162203294b48c746f1e61417d0d2191991835c768127d89fe35075',
                'EGA/TCURSOR.ASM': '6ca256ce21fa6215d50a6bc23bd316c4b15c2eceaf1f8136165eec6fe4437bae',
                'SDIB88.ASM': 'd4ceb5a93d0a739a9f7a5a45a7be06f61b6682273d3402885debee9fdac1db1f'},
 '320x200x4': {'EGA/TSOFT.ASM': 'df39381218d745050b8d0001506a1eaf5d6ca257a80c4508aedd8a0d044c12a4',
               'EGA/TCURSOR.ASM': '7cd0588f809a4d6c7de3030656bff83b45debdfc948da0710de3c6407d8b30e0',
               'SDIB88.ASM': 'c23feb8e35a4e9aa2c54a3042366318de385e098e4447b6f3d360211a87da25a'},
 '640x200x2': {'EGA/TSOFT.ASM': '994264d4cae761945f4068f9c2fdbc53f33da8cdce93a4f2fb8e84f6ca1b7f82',
               'EGA/TCURSOR.ASM': '4a504c3b2300a28bcb2a939f1eaeb6fbb67ba93a4d6e3303f0e0cc0109054278',
               'SDIB88.ASM': 'cf499088d92c0e64e515362550953025255ce423c7e87136c034f22453aa2baa'}}

RENDERER_PINS = {'OUTPUT.ASM': '936d80af4d305bb16b11c0203a15b4608375c4bf978f6a21077b82d70b7bd456',
 'POLYLINE.ASM': 'ef21f4f899ccbfe3b783afd1e393b107e46b1725421a10fae6c3bb36301f6299',
 'SCANLINE.ASM': 'f1ba086a7ac163e353ac3523dd41bebc9ea380078af787c566f8cfd3470c0d30',
 'DISPLAY.INC': '204c0ca1240782fddf6d4ed47f2060f7d3526ddbb3d5ec152b9c2cd27ed4c16a',
 'CLIP.INC': '36d3fea586d2ea3178d4f12f9ecdb4e8619dadccdda9eb4ccef14aa1541359fe',
 'POLYBITM.INC': '24310589f5be7ca98c5b3756255f49b42129821f3be7908e1c337c70e59573df',
 'POLYSTYL.INC': 'b5f43b951677291c8020deeb1f5dbf186afa6d143326a0e73e208f825406d11c',
 'PATTERN.INC': 'be8ef8f9016881b9efc70db9d378a0747d193ba592c6abdd1de58bd13496d1d9'}

def normalized(path):
    return Path(path).read_bytes().replace(b'\r\n', b'\n').replace(b'\x1a', b'').decode('latin1')


def sha(text):
    return hashlib.sha256(text.encode('latin1')).hexdigest()


def once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('BORDER7 scope anchor mismatch: ' + repr(old))
    return text.replace(old, new)


CHANGES = [('    localW lastrow\ncBegin\n',
  '    localW lastrow\n'
  '    localW outcols\n'
  '    localW firstcol\n'
  '    localW lastcol\n'
  '    localW nextcol\n'
  '    localW nextlast\n'
  'cBegin\n'),
 ('    mov outrows,0\n', '    mov outrows,0\n    mov outcols,0\n'),
 ('    cmp style,18\n    je TOutput_polyline\n', '    cmp style,18\n    or_require jne,TOutput_polyline\n'),
 ('    loop TOutput_scan_interval\n    jmp short TOutput_bounded\n',
  '    loop TOutput_scan_interval\n'
  '    ; BORDER7: snapshot at most two proven intervals before the renderer.\n'
  '    ; Longer lists retain the exact TR6 full-width single-row refresh.\n'
  '    cmp count,3\n'
  '    or_require jbe,TOutput_bounded\n'
  '    les di,points\n'
  '    mov cx,es:[di+4]\n'
  '    mov dx,es:[di+6]\n'
  '    add dx,7\n'
  '    shr cx,1\n'
  '    shr cx,1\n'
  '    shr cx,1\n'
  '    shr dx,1\n'
  '    shr dx,1\n'
  '    shr dx,1\n'
  '    mov firstcol,cx\n'
  '    mov lastcol,dx\n'
  '    mov outcols,1\n'
  '    cmp count,3\n'
  '    jne TOutput_scan_bounded\n'
  '    mov cx,es:[di+8]\n'
  '    mov dx,es:[di+10]\n'
  '    add dx,7\n'
  '    shr cx,1\n'
  '    shr cx,1\n'
  '    shr cx,1\n'
  '    shr dx,1\n'
  '    shr dx,1\n'
  '    shr dx,1\n'
  '    mov nextcol,cx\n'
  '    mov nextlast,dx\n'
  '    mov outcols,2\n'
  'TOutput_scan_bounded:\n'
  '    jmp TOutput_bounded\n'),
 ('    mov lastrow,bx\nTOutput_bounded:\n',
  '    mov lastrow,bx\n'
  '    ; Thin lines remain inside the inclusive endpoint bounding box.\n'
  '    ; Include both endpoints, even though the renderer can omit the last.\n'
  '    cmp cx,dx\n'
  '    jbe TOutput_x_ordered\n'
  '    xchg cx,dx\n'
  'TOutput_x_ordered:\n'
  '    inc dx\n'
  '    add dx,7\n'
  '    shr cx,1\n'
  '    shr cx,1\n'
  '    shr cx,1\n'
  '    shr dx,1\n'
  '    shr dx,1\n'
  '    shr dx,1\n'
  '    mov firstcol,cx\n'
  '    mov lastcol,dx\n'
  '    mov outcols,1\n'
  'TOutput_bounded:\n'),
 ('    push ax\n'
  '    push bx\n'
  '    cmp outrows,0\n'
  '    je TOutput_full\n'
  '    mov ax,firstrow\n'
  '    mov bx,lastrow\n'
  '    call FlushRetainRows\n'
  '    jmp short TOutput_flushed\n'
  'TOutput_full:\n'
  '    call FlushShadow\n'
  'TOutput_flushed:\n'
  '    pop bx\n'
  '    pop ax\n',
  '    push ax\n'
  '    push bx\n'
  '    push cx\n'
  '    push dx\n'
  '    cmp outrows,0\n'
  '    je TOutput_full\n'
  '    mov ax,firstrow\n'
  '    mov bx,lastrow\n'
  '    cmp outcols,0\n'
  '    je TOutput_rows\n'
  '    mov cx,firstcol\n'
  '    mov dx,lastcol\n'
  '    ; Keep the faster existing row path for a single full-width interval.\n'
  '    or cx,cx\n'
  '    jne TOutput_columns\n'
  '    cmp dx,SCREEN_W_BYTES\n'
  '    jne TOutput_columns\n'
  '    cmp outcols,1\n'
  '    je TOutput_rows\n'
  'TOutput_columns:\n'
  '    call FlushRetainColumns\n'
  '    cmp outcols,2\n'
  '    jne TOutput_flushed\n'
  '    ; Both calls copy the final shadow. Overlap/order cannot repeat a ROP.\n'
  '    ; The exact retained-cursor helper handles each physical footprint.\n'
  '    mov cx,nextcol\n'
  '    mov dx,nextlast\n'
  '    call FlushRetainColumns\n'
  '    jmp short TOutput_flushed\n'
  'TOutput_rows:\n'
  '    call FlushRetainRows\n'
  '    jmp short TOutput_flushed\n'
  'TOutput_full:\n'
  '    call FlushShadow\n'
  'TOutput_flushed:\n'
  '    pop dx\n'
  '    pop cx\n'
  '    pop bx\n'
  '    pop ax\n')]

def transform(original, mode=None):
    start = original.index('cProc TOutput,')
    end = original.index('cProc TPixel,', start)
    before = original[start:end]
    after = before
    # Monochrome full-row copy is already cheap. Keep the original scan
    # path; split column dispatch costs more than its saved copy work.
    changes = [pair for pair in CHANGES
               if mode != '640x200x2' or 'loop TOutput_scan_interval' not in pair[0]]
    for old, new in changes:
        after = once(after, old, new)
    inverse = after
    for old, new in reversed(changes):
        inverse = once(inverse, new, old)
    if inverse != before:
        raise RuntimeError('BORDER7 inverse wrapper scope failure')
    return original[:start] + after + original[end:]


def port(renderer, mode):
    renderer = Path(renderer)
    if mode not in EXPECTED:
        raise RuntimeError('BORDER7 unsupported mode: ' + repr(mode))
    source = {name: normalized(renderer/name) for name in EXPECTED[mode]}
    actual = {name: sha(text) for name, text in source.items()}
    if actual != EXPECTED[mode]:
        raise RuntimeError('BORDER7 requires exact TR6 staged inputs: ' + repr(actual))
    for name, expected in RENDERER_PINS.items():
        if sha(normalized(renderer/name)) != expected:
            raise RuntimeError('BORDER7 exact renderer mismatch: ' + name)
    old = source['EGA/TSOFT.ASM']
    new = transform(old, mode)
    output = new.replace('\n', '\r\n').encode('latin1')
    (renderer/'EGA/TSOFT.ASM').write_bytes(output)
    return {
        'feature': 'synchronous narrow borders and thin-line byte rectangles',
        'mode': mode,
        'changed_staged_files': ['EGA/TSOFT.ASM'],
        'input_normalized_sha256': actual,
        'renderer_normalized_sha256': RENDERER_PINS,
        'output_normalized_sha256': sha(new),
        'output_sha256': hashlib.sha256(output).hexdigest(),
        'inverse_scope': 'EXACT_TR6_TOUTPUT_ONLY',
        'monochrome_scan_policy': 'retain TR6 rows to avoid measured split-refresh overhead' if mode == '640x200x2' else 'narrow one/two intervals',
        'geometry': ('unchanged TR6 eligibility; all monochrome scans retain rows; thin count2 uses inclusive endpoint rectangle' if mode == '640x200x2' else 'unchanged TR6 eligibility; scan count2/3 uses one/two independent byte intervals; scan count4..64 retains rows; thin count2 uses inclusive endpoint rectangle'),
        'rounding': 'first=floor(left/8); last=ceil(exclusive_right/8); thin exclusive_right=max(endpoint_x)+1',
        'fallback': 'all unproven inputs retain exact TR6 full synchronous FlushShadow; single full-width span retains FlushRetainRows',
        'cursor': 'unchanged retained-column helper checks the scaled physical footprint independently for each interval',
        'preserved': 'renderer result and post-render GPRs; exact renderer, far-span gate, text, DIB bridge, conversion and cursor code',
        'new_memory': 'five private two-byte SS/BP locals; no shared state or new interrupt masking',
        'precondition': 'caller objects are valid live stable allocations; far-span validation is not proof of allocation ownership',
        'runtime': 'NOT_TESTED',
        'physical_hardware': 'NOT_TESTED',
    }
