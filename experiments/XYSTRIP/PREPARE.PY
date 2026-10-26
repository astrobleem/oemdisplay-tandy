"""Apply the local 2816-byte staged-strip prototype; no native execution."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

def one(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new)

def write(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))

p = ROOT / 'experiments/XYPAN/XYPAN.ASM'
s = p.read_text()
s = one(s, '; Only |dx|=8 and/or |dy|=4 use the 1440-byte preconverted stage.\n'
        '; Every other change uses guarded full copy. Default is software.',
        '; LOCAL PROTOTYPE: disjoint exposed strips, 2816-byte stage budget.\n'
        '; Larger requests retain the guarded full copy. Default is software.')
a = s.index('xy_rectangles proc near')
b = s.index('xy_rectangles endp', a)
s = s[:a] + '''xy_rectangles proc near
    ; The vertical strip owns the diagonal corner. Horizontal Y is shared.
    mov xy_h,0
    mov xy_v,0
    cmp hp_delta,0
    je xyr_vertical
    mov xy_h,1
    mov ax,hp_top
    mov bx,ax
    add bx,200
    cmp hp_dy,0
    jge xyr_hbottom
    sub ax,hp_dy
xyr_hbottom:
    cmp hp_dy,0
    jle xyr_hy
    sub bx,hp_dy
xyr_hy:
    mov xy_hr,ax
    mov xy_hr+2,bx
    mov cx,hp_left
    mov dx,hp_delta
    cmp dx,0
    jl xyr_hleft
    add cx,320
    sub cx,dx
    jmp short xyr_hwidth
xyr_hleft:
    neg dx
xyr_hwidth:
    add dx,cx
    shr cx,1
    shr cx,1
    shr cx,1
    shr dx,1
    shr dx,1
    shr dx,1
    mov xy_hr+4,cx
    mov xy_hr+6,dx
xyr_vertical:
    cmp hp_dy,0
    je xyr_rect_done
    mov xy_v,1
    mov ax,hp_top
    mov bx,hp_dy
    cmp bx,0
    jl xyr_vup
    add ax,200
    sub ax,bx
    jmp short xyr_vheight
xyr_vup:
    neg bx
xyr_vheight:
    mov xy_vr,ax
    add ax,bx
    mov xy_vr+2,ax
    mov ax,hp_left
    shr ax,1
    shr ax,1
    shr ax,1
    mov xy_vr+4,ax
    add ax,40
    mov xy_vr+6,ax
xyr_rect_done:
    ret
''' + s[b:]
s = one(s, '    cmp cx,8\n    xy_need jbe,xys_full\n',
        '    mov si,cx\n')
s = one(s, '    cmp cx,4\n    xy_need jbe,xys_full\n', '''    ; B = 100*abs(dx) + (160-abs(dx)/2)*abs(dy).
    ; Clamped geometry bounds B to 32000, so the 16-bit sum cannot wrap.
    mov ax,si
    mov bx,100
    mul bx
    mov di,ax
    shr si,1
    mov ax,160
    sub ax,si
    mul cx
    add ax,di
    cmp ax,2816
    xy_need jbe,xys_full
''')
s = one(s, '    cmp ax,1440\n', '    cmp ax,2816\n')
s = one(s, '    call hp_blank\n    mov hp_stage_read,0\n', '''    ; A pure Y4 step occupies 160 of each bank's 192 offscreen bytes.
    ; Every staged destination is outside the OLD visible view, both ways.
    cmp hp_delta,0
    jne xys_blank_strip
    cmp hp_dy,4
    je xys_commit_start
    cmp hp_dy,-4
    je xys_commit_start
xys_blank_strip:
    call hp_blank
xys_commit_start:
    mov hp_stage_read,0
''')
s = one(s, '    jnc xys_presented\n    mov hp_enabled,0\n', '''    jnc xys_presented
    ; The Y4 fast path has not blanked yet. Recovery must own blanking.
    call hp_blank
    mov hp_enabled,0
''')
write(p, s)
p = ROOT / 'experiments/XYPAN/XYPATCH.PY'
s = p.read_text()
s = one(s, 'hp_stage db 1440 dup (0)', 'hp_stage db 2816 dup (0)')
write(p, s)
# Comments describing the scratch allocation follow the prototype too.
p = ROOT / 'experiments/XYPAN/XYCOPY.ASM'
s = p.read_text().replace('private 1440-byte stage', 'private 2816-byte stage')
write(p, s)
print('Prepared LOCAL, UNQUALIFIED 2816-byte stage-budget prototype')
