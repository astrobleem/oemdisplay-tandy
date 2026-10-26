#!/usr/bin/env python3
"""Software-panning layer for the IBM CGA 160x100 TR5 stage. Native-unqualified.

Applied by STAGECGA after CGA100.stage() and leaves CGA100.PY untouched. Windows
sees a 320x200 16-color desktop (32,000-byte shadow, 40 bytes/plane/row); the
screen is a 160x100 viewport onto it in the same 1:1 pixels and the same DEh
character/attribute encoding. Normal modes and CGA100 are not changed.

Viewport state (Data segment, written only by pan_set and the lifecycle reset):
  pan_x      first logical column shown, pixels, multiple of 8 (0..160)
  pan_xb     pan_x / 8, the first visible shadow byte column
  pan_xr     pan_xb + VIEW_BYTES, exclusive last visible byte column
  pan_top    first logical row shown (0..100)
  pan_bottom pan_top + VIEW_ROWS, exclusive last visible row

Logical versus physical, constant by constant (once() proves each count, it
cannot prove the meaning, so this table is the review checklist):

  SCREEN_WIDTH   160 -> 320   logical pixels   (public; renderer clips use it)
  SCREEN_HEIGHT  100 -> 200   logical rows
  SCREEN_W_BYTES  20 ->  40   logical bytes per plane row (shadow stride)
  VIEW_COLS/ROWS  new 160/100 physical pixels / rows
  VIEW_BYTES      new 20      visible shadow bytes per plane row
  shadow_bits  8000 -> 32000  logical
  BITMAP <0|1,...>            logical (GDI's screen and shadow descriptors)
  GDIINFO 160,100 -> 320,200  logical HORZRES/VERTRES; 240,180 -> 480,360 mm
                              (a pixel stays 1.5 mm). The mapping-extent rows
                              hold units-per-pixel ratios and do not change.
  mov cx,4000 (Enable)        -> 16000 words: the logical shadow clear
  mov cx,8000 (Enable)        physical 16 KB VRAM fill: unchanged
  mov cx,160 / mov dx,160     physical CGA row bytes: unchanged
  mov cx,20 (inner loop)      VIEW_BYTES, physical: unchanged
  [si+20],[si+40],[si+60]     plane offsets: now multiples of SCREEN_W_BYTES
  add si,60 (row skip)        4*SCREEN_W_BYTES - VIEW_BYTES
  SDIB88 cmp bx,160 / 100     logical screen clip: 320 / 200
  TCURSOR 160 / 100 clips     physical: unchanged
  TCURSOR origin              logical position minus the viewport origin

Each flush intersects its logical rectangle with the viewport first, then keeps
a physical row counter; the shadow address alone is computed from logical
coordinates. Cursor-retain calls take physical rows and bytes (origin removed).
"""
import hashlib
from pathlib import Path
from STAGECGA import read, write, once

HERE = Path(__file__).resolve().parent
LOGICAL_W, LOGICAL_H = 320, 200
VIEW_W, VIEW_H = 160, 100
W_BYTES, VIEW_BYTES = LOGICAL_W // 8, VIEW_W // 8
ESC_XY, ESC_MODE = 0x5860, 0x5861

assert (W_BYTES, VIEW_BYTES) == (40, 20)
assert W_BYTES * 4 * LOGICAL_H == 32000

DATA = """; CGAPAN: viewport state (see CGAPAN.PY)
public pan_x,pan_xb,pan_xr,pan_top,pan_bottom
pan_x dw 0
pan_xb dw 0
pan_xr dw VIEW_BYTES
pan_top dw 0
pan_bottom dw VIEW_ROWS
"""

RESET = """    mov pan_x,0
    mov pan_xb,0
    mov pan_xr,VIEW_BYTES
    mov pan_top,0
    mov pan_bottom,VIEW_ROWS
"""

# Clip logical rows AX (first) / BX (exclusive last) to the viewport; both
# leave inside [pan_top,pan_bottom] and ordered, so the physical values passed
# to cursor_begin_retain are never negative or reversed. DS = Data.
ROW_CLIP = """    ; CGAPAN: only rows inside the viewport reach video memory
    cmp ax,pan_top
    jge @@@_a
    mov ax,pan_top
@@@_a:
    cmp ax,pan_bottom
    jle @@@_b
    mov ax,pan_bottom
@@@_b:
    cmp bx,pan_bottom
    jle @@@_c
    mov bx,pan_bottom
@@@_c:
    cmp bx,ax
    jge @@@_d
    mov bx,ax
@@@_d:
"""

# Same for logical byte columns CX (first) / DX (exclusive last).
COL_CLIP = """    ; CGAPAN: only byte columns inside the viewport reach video memory
    cmp cx,pan_xb
    jge @@@_a
    mov cx,pan_xb
@@@_a:
    cmp cx,pan_xr
    jle @@@_b
    mov cx,pan_xr
@@@_b:
    cmp dx,pan_xr
    jle @@@_c
    mov dx,pan_xr
@@@_c:
    cmp dx,cx
    jge @@@_d
    mov dx,cx
@@@_d:
"""

COLUMN_SETUP_OLD = ("    mov ss:[bp-2],ax\n    mov ss:[bp-4],bx\n"
                    "    mov ss:[bp-6],cx\n    sub dx,cx\n")
# DI is saved on entry and unused until the conversion loop.
COLUMN_SETUP_NEW = """    mov di,ax                  ; CGAPAN: physical first row
    sub di,pan_top
    mov ss:[bp-2],di
    mov di,bx                  ; physical exclusive last row
    sub di,pan_top
    mov ss:[bp-4],di
    mov di,cx                  ; physical first byte (view relative)
    sub di,pan_xb
    mov ss:[bp-6],di
    sub dx,cx
"""

RETAIN_ROWS = ("    mov dx,160\n    sub ax,pan_top             ; CGAPAN: physical rows\n"
               "    sub bx,pan_top\n    call cursor_begin_retain\n"
               "    add ax,pan_top\n    add bx,pan_top\n")
RETAIN_COLS = ("    lea si,[bp-12]\n    sub ax,pan_top             ; CGAPAN: physical rows\n"
               "    sub bx,pan_top\n    call cursor_begin_retain\n"
               "    add ax,pan_top\n    add bx,pan_top\n")

PAN_SET = """
; CGAPAN: record a viewport origin. AX = left pixel, DX = top row, both already
; clamped and the left a multiple of 8. Uses BX; DS = Data.
pan_store proc near
    mov pan_x,ax
    mov pan_top,dx
    mov bx,ax
    shr bx,1
    shr bx,1
    shr bx,1
    mov pan_xb,bx
    add bx,VIEW_BYTES
    mov pan_xr,bx
    mov bx,dx
    add bx,VIEW_ROWS
    mov pan_bottom,bx
    ret
pan_store endp

; CGAPAN: move the viewport. AX = requested left pixel, DX = requested top row;
; clamped to 0..SCREEN-VIEW, left rounded down to a multiple of 8. Preserves
; every register. Task time only (Control): repaints all 100 visible rows.
public pan_set
pan_set proc far
    push ax
    push bx
    push dx
    push ds
    mov bx,seg pan_x
    mov ds,bx
    or ax,ax
    jns pan_set_xlo
    xor ax,ax
pan_set_xlo:
    cmp ax,SCREEN_WIDTH-VIEW_COLS
    jle pan_set_xhi
    mov ax,SCREEN_WIDTH-VIEW_COLS
pan_set_xhi:
    and ax,0fff8h
    or dx,dx
    jns pan_set_ylo
    xor dx,dx
pan_set_ylo:
    cmp dx,SCREEN_HEIGHT-VIEW_ROWS
    jle pan_set_yhi
    mov dx,SCREEN_HEIGHT-VIEW_ROWS
pan_set_yhi:
    cmp ax,pan_x
    jne pan_set_move
    cmp dx,pan_top
    je pan_set_done
pan_set_move:
    cmp enabled_flag,0
    jne pan_set_flush
    call pan_store
    jmp short pan_set_done
pan_set_flush:
    call cursor_hide
    call pan_store
    call FlushShadow
    call cursor_show
pan_set_done:
    pop ds
    pop dx
    pop bx
    pop ax
    ret
pan_set endp

; CGAPAN: Control escapes, called by TControl with the PASCAL frame
;   [bp+14] function  [bp+12:10] input  [bp+8:6] output
; Returns AX = 0FFFFh (not ours), 1 (handled) or 0 (refused).
;   CGAPAN_ESC  in: left (0FFFFh only queries), top. out: 6 words = left, top,
;               viewport width, viewport height, logical width, logical height.
;   CGAPAN_MODE in: 0 (software panning, the only mode here) -> 1, else 0.
public pan_escape
pan_escape proc far
    push bp
    mov bp,sp
    push ds
    push si
    push di
    mov bx,[bp+14]
    cmp bx,CGAPAN_ESC
    je pan_esc_xy
    cmp bx,CGAPAN_MODE
    je pan_esc_mode
    mov ax,0ffffh
    jmp short pan_esc_done
pan_esc_mode:
    les di,[bp+10]
    xor ax,ax
    cmp word ptr es:[di],0
    jne pan_esc_done
    inc ax
    jmp short pan_esc_done
pan_esc_xy:
    les di,[bp+10]
    mov ax,es:[di]
    mov dx,es:[di+2]
    cmp ax,0ffffh
    je pan_esc_out
    call pan_set
pan_esc_out:
    les di,[bp+6]
    mov ax,es
    or ax,di
    jz pan_esc_ok
    mov ax,seg pan_x
    mov ds,ax
    mov ax,pan_x
    mov es:[di],ax
    mov ax,pan_top
    mov es:[di+2],ax
    mov word ptr es:[di+4],VIEW_COLS
    mov word ptr es:[di+6],VIEW_ROWS
    mov word ptr es:[di+8],SCREEN_WIDTH
    mov word ptr es:[di+10],SCREEN_HEIGHT
pan_esc_ok:
    mov ax,1
pan_esc_done:
    pop di
    pop si
    pop ds
    pop bp
    ret 10
pan_escape endp
"""

CONTROL_QUERY_OLD = ("    cmp bx,GETCOLORTABLE\n    je control_ok\n"
                     "    jmp control_done\ncontrol_color:\n")
CONTROL_QUERY_NEW = """    cmp bx,GETCOLORTABLE
    je control_ok
    cmp bx,CGAPAN_ESC
    je control_ok
    cmp bx,CGAPAN_MODE
    je control_ok
    jmp control_done
control_color:
    push bx                    ; CGAPAN: pan escapes, see pan_escape
    push es
    push di
    push seg_output
    push off_output
    call pan_escape
    cmp ax,0ffffh
    jne control_pan_done
    les di,input
    mov bx,function
    jmp short control_not_pan
control_pan_done:
    jmp control_done
control_not_pan:
"""


def sub(template, tag):
    return template.replace('@@@', 'pan_' + tag)


def tsoft(text):
    for old, new in (
        ('SCREEN_WIDTH equ 160\nSCREEN_HEIGHT equ 100\nSCREEN_W_BYTES equ 20\n',
         'SCREEN_WIDTH equ %d\nSCREEN_HEIGHT equ %d\nSCREEN_W_BYTES equ %d\n'
         'VIEW_COLS equ %d             ; CGAPAN: physical pixels\n'
         'VIEW_ROWS equ %d             ; CGAPAN: physical rows\n'
         'VIEW_BYTES equ %d              ; CGAPAN: visible bytes per plane row\n'
         'CGAPAN_ESC equ %05Xh          ; CGAPAN: Control escapes\n'
         'CGAPAN_MODE equ %05Xh\n'
         % (LOGICAL_W, LOGICAL_H, W_BYTES, VIEW_W, VIEW_H, VIEW_BYTES,
            ESC_XY, ESC_MODE)),
        ('shadow_bits db 8000 dup (0)', 'shadow_bits db 32000 dup (0)'),
        ('BITMAP <0,160,100,20,4,1,0,2000', 'BITMAP <0,320,200,40,4,1,0,8000'),
        ('BITMAP <1,160,100,20,4,1,0,2000', 'BITMAP <1,320,200,40,4,1,0,8000'),
        ('    dw 0300h,DT_RASDISPLAY,240,180,160,100,1,4\n',
         '    dw 0300h,DT_RASDISPLAY,480,360,320,200,1,4\n'),
    ):
        text = once(text, old, new)
    # Logical shadow clear in Enable (the 8000-word VRAM fill is physical).
    text = once(text, '    mov cx,4000\n    cld\n    rep stosw\n    mov enabled_flag,1\n',
                '    mov cx,16000\n    cld\n    rep stosw\n' + RESET + '    mov enabled_flag,1\n')
    text = once(text, '    cli\n    mov enabled_flag,0\n',
                '    cli\n' + RESET + '    mov enabled_flag,0\n')
    text = once(text, 'diag_markers dw 0,0,0,0\n', 'diag_markers dw 0,0,0,0\n' + DATA)
    # Every flush intersects its rectangle with the viewport after its clamps.
    for label, tag in (('\nflush_last_clamped:\n', 'fr'), ('\nkeep_last_clamped:\n', 'kr'),
                       ('\nkcols_last_row:\n', 'kcr'), ('\ncols_last_row:\n', 'fcr')):
        text = once(text, label, label + sub(ROW_CLIP, tag))
    for label, tag in (('\nkcols_last_byte:\n', 'kcc'), ('\ncols_last_byte:\n', 'fcc')):
        text = once(text, label, label + sub(COL_CLIP, tag))
    # Whole-row conversions: physical row counter and limit; shadow address
    # from the logical row plus the first visible byte.
    text = once(text,
        '    mov bp,ax\n    push bx\n    mov cx,SCREEN_W_BYTES*4\n    mul cx\n    mov si,ax\n',
        '    mov bp,ax\n    sub bp,pan_top             ; CGAPAN: physical row\n'
        '    sub bx,pan_top\n    push bx\n    mov cx,SCREEN_W_BYTES*4\n    mul cx\n'
        '    mov si,ax\n    add si,pan_xb\n', count=2)
    text = once(text, COLUMN_SETUP_OLD, COLUMN_SETUP_NEW, count=2)
    # Plane offsets and the row skip follow the new shadow stride.
    text = once(text, '    mov bl,[si+20]\n    mov bh,[si+40]\n    mov dh,[si+60]\n',
                '    mov bl,[si+SCREEN_W_BYTES]\n    mov bh,[si+SCREEN_W_BYTES*2]\n'
                '    mov dh,[si+SCREEN_W_BYTES*3]\n', count=4)
    text = once(text, '    add si,60\n', '    add si,SCREEN_W_BYTES*4-VIEW_BYTES\n', count=2)
    # Cursor retention is physical rows and physical bytes.
    text = once(text, '    mov dx,160\n    call cursor_begin_retain\n', RETAIN_ROWS)
    text = once(text, '    push cx\n    push dx\n    shl cx,1\n',
                '    push cx\n    push dx\n    sub cx,pan_xb              ; CGAPAN: physical bytes\n'
                '    sub dx,pan_xb\n    shl cx,1\n')
    text = once(text, '    lea si,[bp-12]\n    call cursor_begin_retain\n', RETAIN_COLS)
    text = once(text, 'FlushColumns endp\n', 'FlushColumns endp\n' + PAN_SET)
    text = once(text, CONTROL_QUERY_OLD, CONTROL_QUERY_NEW)
    return text


def tcursor(text):
    text = once(text, '    externB enabled_flag\n',
                '    externB enabled_flag\n    externW pan_x\n    externW pan_top\n')
    text = once(text, '    mov ax,tc_x\n    sub ax,tc_hot_x\n    mov tc_origin_x,ax\n',
                '    mov ax,tc_x\n    sub ax,tc_hot_x\n    sub ax,pan_x               ; CGAPAN: viewport\n'
                '    mov tc_origin_x,ax\n')
    return once(text, '    mov ax,tc_y\n    sub ax,tc_hot_y\n    mov tc_origin_y,ax\n',
                '    mov ax,tc_y\n    sub ax,tc_hot_y\n    sub ax,pan_top             ; CGAPAN: viewport\n'
                '    mov tc_origin_y,ax\n')


def sdib(text):
    text = once(text, '    cmp bx,160\n    jle sd_clip_right\n    mov bx,160\n',
                '    cmp bx,%d\n    jle sd_clip_right\n    mov bx,%d\n' % (LOGICAL_W, LOGICAL_W))
    return once(text, '    cmp bx,100\n    jle sd_clip_bottom\n    mov bx,100\n',
                '    cmp bx,%d\n    jle sd_clip_bottom\n    mov bx,%d\n' % (LOGICAL_H, LOGICAL_H))


def stage(renderer, resources):
    """Edit the already CGA100-staged sources. Validates every edit first."""
    paths = {name: renderer / name for name in
             ('EGA/TSOFT.ASM', 'EGA/TCURSOR.ASM', 'SDIB88.ASM', 'EGA/TSOFT.DEF')}
    before = {name: read(path) for name, path in paths.items()}
    after = {'EGA/TSOFT.ASM': tsoft(before['EGA/TSOFT.ASM']),
             'EGA/TCURSOR.ASM': tcursor(before['EGA/TCURSOR.ASM']),
             'SDIB88.ASM': sdib(before['SDIB88.ASM']),
             'EGA/TSOFT.DEF': once(before['EGA/TSOFT.DEF'],
                                   'IBM CGA 160x100 16-color (experimental)',
                                   'IBM CGA 160x100 view of 320x200 16-color (experimental)')}
    for name, value in after.items():
        write(paths[name], value)
    return dict(logical=[LOGICAL_W, LOGICAL_H], viewport=[VIEW_W, VIEW_H],
                shadow_bytes=W_BYTES * 4 * LOGICAL_H, shadow_stride=W_BYTES,
                escapes={'query_set': ESC_XY, 'mode': ESC_MODE},
                x_alignment=8, y_alignment=1,
                input_sha256={k: hashlib.sha256(v.encode('latin1')).hexdigest()
                              for k, v in before.items()},
                runtime='NOT_TESTED')
