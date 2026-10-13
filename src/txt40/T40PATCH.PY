#!/usr/bin/env python3
"""TXT40 edits for the TR5 driver: CGA 40x25 colour text from the 320x200x16
shadow (docs/TXT40.MD).

  python3 src/txt40/T40PATCH.PY --check     text self-test (no emulator)

BUILDT40.PY applies patch_staged() to BUILD88's fully staged EGA/TSOFT.ASM,
EGA/TCURSOR.ASM and EGA/TSOFT.DEF for profile 320x200x16, after every TR5
port step and before the first assembly. Every edit must match an exact
count or nothing is written.

TSOFT.ASM
- Enable: BIOS mode 01h (40x25 colour text), then blink off (port 3D8h =
  08h and BIOS 40:65h = 08h, so attribute bit 7 is a bright background),
  hardware cursor hidden, text cleared, hint table emptied. Disable is the
  unchanged BIOS restore of the previous mode.
- The four flush routines become one: clamp, hide the cursor, run the
  presenter (T40PRES.ASM, verbatim) over the dirty rectangle, show the
  cursor. The CURKEEP retain variants become plain flushes.
- StrBlt/ExtTextOut on the screen record a hint for every 8-pixel-wide
  glyph of an 8-pixel-high raster font (FNT 2.0) when no justification or
  character extra is in effect; codes go through an ANSI->CP437 table
  unless the font is OEM. Only hints are recorded; drawing is unchanged.
- Screen-to-screen SRCCOPY BitBlt moves the hints wholly inside the source
  with the pixels (window moves, scrolling).
- New segment _T40 (T40DATA.ASM) holds hints and presenter state.
TCURSOR.ASM
- The mouse cursor is the hot spot's text cell with its attribute XOR 77h.
TSOFT.DEF
- Description names TXT40; segment _T40 is PRELOAD FIXED.
"""
import argparse
import importlib.machinery
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = importlib.machinery.SourceFileLoader("t40model", str(HERE / "T40MODEL.PY")).load_module()


def crlf(s):
    return s.replace("\r\n", "\n").replace("\n", "\r\n")


def fragment(name):
    t = (HERE / name).read_bytes().decode("ascii")
    if "\n" in t.replace("\r\n", ""):
        raise SystemExit(f"T40PATCH: {name} must use CRLF line ends")
    return t


def replace_n(text, old, new, want, name):
    n = text.count(old)
    if n != want:
        raise SystemExit(f"T40PATCH: '{name}' matched {n} times, expected {want}")
    return text.replace(old, new)


def ansi_table_text():
    vals = [M.ansi_to_cp437(c) for c in range(256)]
    lines = ["; T40PATCH: Windows ANSI -> CP437 for the CGA character ROM.\n", "t40_ansi label byte\n"]
    for row in range(0, 256, 16):
        lines.append("    db " + ",".join("%03Xh" % v for v in vals[row:row + 16]) + "\n")
    return crlf("".join(lines))


ENABLE_OLD = "    mov ax,9\r\n    int 10h\r\n"
ENABLE_NEW = crlf("""    mov ax,1                  ; T40PATCH: BIOS 40x25 colour text
    int 10h
    mov dx,3d8h
    mov al,08h                ; 40 columns, colour, video on, blink off
    out dx,al
    push ds
    mov ax,40h
    mov ds,ax
    mov byte ptr ds:[65h],08h ; BIOS copy of the mode register
    pop ds
    mov ah,1
    mov cx,2000h              ; hide the hardware cursor
    int 10h
    mov ax,0b800h
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,T40_NCELL
    cld
    rep stosw
    mov ax,seg t40_slot       ; forget every hint and shown state
    mov es,ax                 ; (t40_reset inline: TEnable is in
    xor di,di                 ; another code segment)
    xor ax,ax
    mov cx,T40_CLRB/2
    rep stosw
    mov es:t40_snv,0          ; no snapshot held
""")

DATA_ANCHOR = "diag_markers dw 0,0,0,0\r\n"
DATA_NEW = crlf("""; T40PATCH: text call parameters for t40_text.
t40_tx dw 0
t40_ty dw 0
t40_tcount dw 0
t40_tw dw 0
t40_tstr dd 0
t40_tfont dd 0
t40_tmode dd 0
t40_tdxs dd 0
t40_tfirst db 0
t40_tlast db 0
t40_toem db 0
t40_tch db 0
t40_tdone db 0                  ; t40_text walked every character: t40_tx = end
""")

SEG_ANCHOR = "sEnd ShadowSeg\r\n"


GEOMETRY = {"T40_COLS": 40, "T40_NROWS": 25, "T40_VISROWS": 25, "T40_NGLYPH": 1024, "T40_GLIMIT": 896,
            "T40_SNAPB": 8192}
SEGMENTS = {"T40_SHSEG": "seg shadow_bits", "T40_VSEG": "0b800h", "T40_LSEG": "0b800h",
            "T40_SNSEG": "seg t40_snapbuf"}


def geometry_text():
    return crlf("; T40PATCH: presenter geometry and segments (T40DATA.ASM).\n" +
                "".join(f"{k} equ {v}\n" for k, v in GEOMETRY.items()) +
                "".join(f"{k} equ <{v}>\n" for k, v in SEGMENTS.items()))


def seg_text():
    return (geometry_text() + crlf("; T40PATCH: hints and presenter state.\n"
                 "createSeg _T40,T40Seg,word,public,DATA\n"
                 "sBegin T40Seg\n") + fragment("T40DATA.ASM") + crlf(
                 "sEnd T40Seg\n"
                 "; T40PATCH: snapshot of a text call's flush rectangle (t40_save).\n"
                 "createSeg _T40N,T40NSeg,word,public,DATA\n"
                 "sBegin T40NSeg\n"
                 "t40_snapbuf db T40_SNAPB dup (0)\n"
                 "sEnd T40NSeg\n"))


FLUSH = crlf("""; T40PATCH: every flush presents the dirty rectangle as text cells.
public FlushShadow,FlushRows
FlushShadow proc near
    push ax
    push bx
    xor ax,ax
    mov bx,SCREEN_HEIGHT
    call FlushRows
    pop bx
    pop ax
    ret

; AX first row, BX exclusive last row.
FlushRows label near
    push cx
    push dx
    xor cx,cx
    mov dx,SCREEN_W_BYTES
    call FlushColumns
    pop dx
    pop cx
    ret
FlushShadow endp

; T40PATCH: no cursor retention in text mode; plain hide/show flushes.
public FlushRetainRows
FlushRetainRows proc near
    jmp FlushRows
FlushRetainRows endp

public FlushRetainColumns
FlushRetainColumns proc near
    jmp FlushColumns
FlushRetainColumns endp

; AX first row, BX exclusive last row, CX first byte, DX exclusive last
; byte; signed, clamped here. Preserves every register; CLD.
public FlushColumns
FlushColumns proc near
    cmp enabled_flag,0
    jne t40f_start
    call t40_drop
    ret
t40f_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    cmp ax,0
    jge t40f_top
    xor ax,ax
t40f_top:
    cmp bx,SCREEN_HEIGHT
    jle t40f_bottom
    mov bx,SCREEN_HEIGHT
t40f_bottom:
    cmp cx,0
    jge t40f_left
    xor cx,cx
t40f_left:
    cmp dx,SCREEN_W_BYTES
    jle t40f_right
    mov dx,SCREEN_W_BYTES
t40f_right:
    call cursor_hide
    cld
    cmp ax,bx
    jge t40f_empty
    cmp cx,dx
    jge t40f_empty
    call t40_pdiff              ; drops the snapshot
    jmp short t40f_done
t40f_empty:
    call t40_drop
t40f_done:
    pop es
    pop ds
    call cursor_show
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
FlushColumns endp

; T40PATCH: record hints for one StrBlt/ExtTextOut on the screen.
; DS = Data; parameters in t40_t*. Clobbers AX-DI, ES.
t40_text proc near
    mov t40_tdone,0
    cmp t40_tcount,0
    jg tt_mode
    jmp tt_ret
tt_mode:
    les di,t40_tmode
    mov ax,es
    or ax,di
    jnz tt_mode_ok
    jmp tt_ret
tt_mode_ok:
    cmp es:[di].TBreakExtra,0
    je tt_break_ok
    jmp tt_ret
tt_break_ok:
    cmp es:[di].CharExtra,0
    je tt_font
    jmp tt_ret
tt_font:
    les di,t40_tfont
    mov ax,es
    or ax,ax
    jnz tt_font_seg
    jmp tt_ret
tt_font_seg:
    cmp di,offset fsType
    je tt_font_at
    jmp tt_ret
tt_font_at:
    cmp word ptr es:fsVersion,0200h
    je tt_font_v2
    jmp tt_ret
tt_font_v2:
    cmp word ptr es:fsPixHeight,8
    je tt_font_8
    jmp tt_ret
tt_font_8:
    mov al,es:fsFirstChar
    mov t40_tfirst,al
    mov al,es:fsLastChar
    mov t40_tlast,al
    mov al,es:fsCharSet
    mov t40_toem,al
    xor cx,cx
tt_char:
    cmp cx,t40_tcount
    jl tt_more
    mov t40_tdone,1             ; every advance known: t40_tx is the end
    jmp tt_ret
tt_more:
    les si,t40_tstr
    mov bx,cx
    mov al,es:[bx+si]
    mov t40_tch,al
    cmp al,t40_tfirst
    jae tt_low_ok
    jmp tt_ret
tt_low_ok:
    cmp al,t40_tlast
    jbe tt_in
    jmp tt_ret
tt_in:
    sub al,t40_tfirst
    xor ah,ah
    shl ax,1
    shl ax,1
    mov bx,ax
    les di,t40_tfont
    mov ax,word ptr es:fsCharOffset[bx]
    mov t40_tw,ax
    mov si,word ptr es:fsCharOffset[bx+2]
    cmp ax,8
    jne tt_advance
    mov bl,t40_tch
    xor bh,bh
    cmp t40_toem,255
    je tt_code
    mov bl,cs:t40_ansi[bx]
tt_code:
    mov dl,bl
    mov ax,t40_tx
    mov bx,t40_ty
    call t40_add
tt_advance:
    les di,t40_tdxs
    mov ax,es
    or ax,di
    jz tt_width
    mov bx,cx
    shl bx,1
    mov ax,es:[bx+di]
    jmp short tt_step
tt_width:
    mov ax,t40_tw
tt_step:
    add t40_tx,ax
    inc cx
    jmp tt_char
tt_ret:
    ret
t40_text endp

""")

PRES_TAIL = crlf("""assumes ds,Data
assumes es,nothing
""")


def pres_text():
    return (crlf("; T40PATCH: presenter, verbatim from src/txt40/T40PRES.ASM.\n"
                 ".errnz (offset shadow_bits)\n"
                 )
            + fragment("T40PRES.ASM") + PRES_TAIL + ansi_table_text())


BOUNDS_MACROS = crlf("""; T40PATCH: a full-screen flush costs seconds on an 8088 in text mode, so
; bound every text flush by rows and columns. dirty=2 (rows proven by
; text_bounds): columns of the validated clip rectangle, widened by a
; validated opaque rectangle. dirty=1 (text_bounds could not prove rows:
; no characters, or a clip rectangle reaching past the screen, which is
; normal for windows wider than 320 pixels): the renderer draws only inside
; the clip rectangle and the opaque rectangle, so flush their union clamped
; to the screen. An unreadable or unordered rectangle keeps the full flush.
t40_rect_cols macro rp
local t40c_left_kept,t40c_right_kept
    les di,rp
    mov ax,es:[di].left
    mov cl,3
    shr ax,cl
    cmp ax,colfirst
    jge t40c_left_kept
    mov colfirst,ax
t40c_left_kept:
    mov ax,es:[di].right
    add ax,7
    shr ax,cl
    cmp ax,collast
    jle t40c_right_kept
    mov collast,ax
t40c_right_kept:
endm

; Union the RECT at rp, clamped to the screen, into rowfirst..rowlast and
; colfirst..collast. Unreadable or unordered: jump to failed.
t40_rect_union macro rp,failed
local empty,l0,r0,t0,b0,k1,k2,k3,k4,t40u_b,t40u_rows,t40u_rf,t40u_rl,t40u_cf,t40u_cl
    les di,rp
    mov ax,es
    or ax,ax
    jnz l0
    jmp failed
l0:
    cmp di,0ffffh-((size RECT)-1)
    jbe r0
    jmp failed
r0:
    mov ax,es:[di].left
    cmp ax,es:[di].right
    jle t0
    jmp failed
t0:
    mov ax,es:[di].top
    cmp ax,es:[di].bottom
    jle b0
    jmp failed
b0:
    mov ax,es:[di].left
    or ax,ax
    jns k1
    xor ax,ax
k1:
    mov cx,es:[di].right
    cmp cx,SCREEN_WIDTH
    jle k2
    mov cx,SCREEN_WIDTH
k2:
    cmp ax,cx
    jl k3
    jmp empty
k3:
    mov bx,es:[di].top
    or bx,bx
    jns k4
    xor bx,bx
k4:
    mov dx,es:[di].bottom
    cmp dx,SCREEN_HEIGHT
    jle t40u_b
    mov dx,SCREEN_HEIGHT
t40u_b:
    cmp bx,dx
    jl t40u_rows
    jmp empty
t40u_rows:
    cmp bx,rowfirst
    jge t40u_rf
    mov rowfirst,bx
t40u_rf:
    cmp dx,rowlast
    jle t40u_rl
    mov rowlast,dx
t40u_rl:
    push cx
    mov cl,3
    shr ax,cl
    pop cx
    cmp ax,colfirst
    jge t40u_cf
    mov colfirst,ax
t40u_cf:
    add cx,7
    push ax
    mov ax,cx
    mov cl,3
    shr ax,cl
    cmp ax,collast
    jle t40u_cl
    mov collast,ax
t40u_cl:
    pop ax
empty:
endm

; Intersect rowfirst..rowlast, colfirst..collast with the RECT at rp
; (screen-clamped copy). Unreadable or unordered: unchanged (a superset).
t40_rect_isect macro rp
local keep,k1,k2,k3,k4
    les di,rp
    mov ax,es
    or ax,ax
    jz keep
    cmp di,0ffffh-((size RECT)-1)
    ja keep
    mov ax,es:[di].left
    cmp ax,es:[di].right
    jg keep
    mov ax,es:[di].top
    cmp ax,es:[di].bottom
    jg keep
    mov ax,es:[di].top
    cmp ax,rowfirst
    jle k1
    mov rowfirst,ax
k1:
    mov ax,es:[di].bottom
    cmp ax,rowlast
    jge k2
    mov rowlast,ax
k2:
    mov ax,es:[di].left
    mov cl,3
    sar ax,cl
    cmp ax,colfirst
    jle k3
    mov colfirst,ax
k3:
    mov ax,es:[di].right
    add ax,7
    sar ax,cl
    cmp ax,collast
    jge k4
    mov collast,ax
k4:
keep:
endm

; The renderer draws only inside the clip rectangle: every flush bound is
; intersected with it. dirty=2 (rows proven by text_bounds: the text and,
; with ETO_OPAQUE fill, the opaque rows): those rows, the clip columns.
; dirty=1 (rows not proven): with characters, the clip rectangle; with no
; characters (an opaque-only ExtTextOut, e.g. an edit control erasing the
; rest of a line), the opaque rectangle if ETO_OPAQUE fills, else nothing
; is drawn. Proven rows with every character walked by t40_text (8-pixel
; fonts, no justification): the columns of the text itself, from x to its
; end plus one pixel (simulated bold), widened by a filled opaque
; rectangle, then intersected with the clip. Otherwise the clip columns.
; (An edit control's one-character ExtTextOut otherwise flushed and
; compared the whole width of the edit control on every keystroke.)
; TEXT80: TXT40 flushed the union of the clip and opaque
; rectangles here, which for Notepad was the whole client area on every
; keystroke (2.6 s of a 3.1 s keystroke on an XT, docs/TEXT80.MD).
t40_bounds macro extended
local proven,unproven,full,done,t40b_chars,t40b_none,t40b_np,t40b_up,t40b_nochars,t40b_fill
local t40b_ord,t40b_clipcols,t40b_colsdone,t40b_textcols
    push ax
    push bx
    push cx
    push dx
    push di
    push es
    mov colfirst,SCREEN_W_BYTES
    mov collast,0
    cmp dirty,2
    jne t40b_np
    jmp proven
t40b_np:
    cmp dirty,1
    je t40b_up
    jmp done
t40b_up:
    jmp unproven
proven:
    cmp t40_tdone,0
    jne t40b_textcols
    jmp t40b_clipcols
t40b_textcols:
    mov ax,x
    mov bx,t40_tx
    cmp ax,bx
    jle t40b_ord
    xchg ax,bx
t40b_ord:
    inc bx
    add bx,7
    mov cl,3
    sar ax,cl
    sar bx,cl
    mov colfirst,ax
    mov collast,bx
    if extended
    test options,ETO_OPAQUE_FILL
    jz t40b_colsdone
    mov ax,word ptr opaquerect+2
    or ax,ax
    jz t40b_clipcols            ; filled but no rectangle: be safe
    t40_rect_cols opaquerect
    endif
    jmp short t40b_colsdone
t40b_clipcols:
    mov colfirst,SCREEN_W_BYTES
    mov collast,0
    t40_rect_cols clip
t40b_colsdone:
    t40_rect_isect clip
    jmp done
unproven:
    mov rowfirst,SCREEN_HEIGHT
    mov rowlast,0
    cmp count,0
    jle t40b_nochars
    jmp t40b_chars
t40b_nochars:
    if extended
    test options,ETO_OPAQUE_FILL
    jnz t40b_fill
    jmp t40b_none
t40b_fill:
    t40_rect_union opaquerect,full
    t40_rect_isect clip
    mov dirty,2
    jmp done
    endif
t40b_none:
    mov rowfirst,0              ; nothing is drawn: an empty flush
    mov rowlast,0
    mov dirty,2
    jmp done
t40b_chars:
    t40_rect_union clip,full
    mov dirty,2
    jmp done
full:
    mov dirty,1
done:
    pop es
    pop di
    pop dx
    pop cx
    pop bx
    pop ax
endm

; T40PATCH: windows wider than 320 pixels have clip (and opaque) rectangles
; reaching past the screen, which text_bounds rejects, costing a flush of
; the whole clip area. Give text_bounds and t40_bounds screen-clamped copies
; on the private stack frame; the renderer still gets the caller's pointers.
t40_clamp1 macro rp,copy,saved
local skip
    push bx
    lea bx,saved
    mov ax,word ptr rp
    mov ss:[bx],ax
    mov ax,word ptr rp+2
    mov ss:[bx+2],ax
    les di,rp
    mov ax,es
    or ax,ax
    jz skip
    cmp di,0ffffh-((size RECT)-1)
    ja skip
    lea bx,copy
    mov ax,es:[di].left
    t40_clampax SCREEN_WIDTH
    mov ss:[bx].left,ax
    mov ax,es:[di].right
    t40_clampax SCREEN_WIDTH
    mov ss:[bx].right,ax
    mov ax,es:[di].top
    t40_clampax SCREEN_HEIGHT
    mov ss:[bx].top,ax
    mov ax,es:[di].bottom
    t40_clampax SCREEN_HEIGHT
    mov ss:[bx].bottom,ax
    mov word ptr rp,bx
    mov word ptr rp+2,ss
skip:
    pop bx
endm

t40_clampax macro limit
local low_ok,high_ok
    or ax,ax
    jns low_ok
    xor ax,ax
low_ok:
    cmp ax,limit
    jle high_ok
    mov ax,limit
high_ok:
endm

t40_clamp macro extended
    push ax
    push di
    push es
    t40_clamp1 clip,t40cr,t40sclip
    if extended
    t40_clamp1 opaquerect,t40or,t40sopq
    endif
    pop es
    pop di
    pop ax
endm

t40_unclamp macro extended
    push ax
    push bx
    lea bx,t40sclip
    mov ax,ss:[bx]
    mov word ptr clip,ax
    mov ax,ss:[bx+2]
    mov word ptr clip+2,ax
    if extended
    lea bx,t40sopq
    mov ax,ss:[bx]
    mov word ptr opaquerect,ax
    mov ax,ss:[bx+2]
    mov word ptr opaquerect+2,ax
    endif
    pop bx
    pop ax
endm

; T40PATCH: before the renderer draws, keep the pixels of the proven flush
; rectangle (t40_save); the flush then presents only cells that changed or
; whose hints did (t40_pdiff). Not proven: no snapshot (ordinary flush).
t40_takesnap macro
local skip
    cmp dirty,2
    jne skip
    push ax
    push bx
    push cx
    push dx
    mov ax,rowfirst
    mov bx,rowlast
    mov cx,colfirst
    mov dx,collast
    call t40_save
    pop dx
    pop cx
    pop bx
    pop ax
skip:
endm

t40_flush macro
local full,done
    push ax
    push bx
    push cx
    push dx
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    mov cx,colfirst
    mov dx,collast
    call FlushColumns
    jmp short done
full:
    call FlushShadow
done:
    pop dx
    pop cx
    pop bx
    pop ax
endm

""")

RECORD_MACRO = crlf("""; T40PATCH: after map_device, dirty=1 means the destination is the screen.
t40_record macro extended
local skip,go
    cmp dirty,0
    jne go
    jmp skip
go:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    mov ax,x
    mov t40_tx,ax
    mov ax,y
    mov t40_ty,ax
    mov ax,count
    mov t40_tcount,ax
    mov ax,word ptr string
    mov word ptr t40_tstr,ax
    mov ax,word ptr string+2
    mov word ptr t40_tstr+2,ax
    mov ax,word ptr font
    mov word ptr t40_tfont,ax
    mov ax,word ptr font+2
    mov word ptr t40_tfont+2,ax
    mov ax,word ptr mode
    mov word ptr t40_tmode,ax
    mov ax,word ptr mode+2
    mov word ptr t40_tmode+2,ax
    if extended
    mov ax,word ptr dxs
    mov word ptr t40_tdxs,ax
    mov ax,word ptr dxs+2
    mov word ptr t40_tdxs+2,ax
    else
    xor ax,ax
    mov word ptr t40_tdxs,ax
    mov word ptr t40_tdxs+2,ax
    endif
    call t40_text
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
skip:
endm

""")

BLIT_OLD = "TBitBlt_mapped:\r\n    map_device dst,1\r\n"
BLIT_NEW = crlf("""TBitBlt_mapped:
    ; T40PATCH: a screen-to-screen SRCCOPY moves the hints with the pixels.
    cmp word ptr rop,0020h
    jne t40b_done
    cmp word ptr rop+2,00cch
    jne t40b_done
    les di,dst
    mov ax,es
    or ax,di
    jz t40b_done
    cmp word ptr es:[di],0
    je t40b_done
    les di,src
    mov ax,es
    or ax,di
    jz t40b_done
    cmp word ptr es:[di],0
    je t40b_done
    mov ax,sx
    or ax,ax
    js t40b_done
    mov bx,sy
    or bx,bx
    js t40b_done
    mov cx,xextent
    or cx,cx
    jle t40b_done
    cmp cx,SCREEN_WIDTH
    jg t40b_done
    mov dx,yextent
    or dx,dx
    jle t40b_done
    cmp dx,SCREEN_HEIGHT
    jg t40b_done
    mov si,ax
    add si,cx
    cmp si,SCREEN_WIDTH
    jg t40b_done
    mov si,bx
    add si,dx
    cmp si,SCREEN_HEIGHT
    jg t40b_done
    mov si,dstx
    sub si,ax
    mov di,dsty
    sub di,bx
    call t40_blit
t40b_done:
    map_device dst,1
""")


def patch_tsoft(t):
    start = t.index("public FlushShadow,FlushRows\r\n")
    end_marker = "FlushColumns endp\r\n"
    if t.count("public FlushShadow,FlushRows\r\n") != 1 or t.count(end_marker) != 1:
        raise SystemExit("T40PATCH: flush block anchors not unique")
    end = t.index(end_marker) + len(end_marker)
    if end <= start:
        raise SystemExit("T40PATCH: flush block anchors out of order")
    t = t[:start] + FLUSH + pres_text() + t[end:]
    t = replace_n(t, SEG_ANCHOR, SEG_ANCHOR + seg_text(), 1, "segment _T40")
    t = replace_n(t, DATA_ANCHOR, DATA_ANCHOR + DATA_NEW, 1, "text parameters")
    t = replace_n(t, ENABLE_OLD, ENABLE_NEW, 1, "enable mode")
    t = replace_n(t, "cProc TStrBlt,", BOUNDS_MACROS + RECORD_MACRO + "cProc TStrBlt,", 1, "record macro")
    t = replace_n(t, "    localW rowfirst\r\n    localW rowlast\r\ncBegin\r\n",
                  "    localW rowfirst\r\n    localW rowlast\r\n    localW colfirst\r\n    localW collast\r\n"
                  "    localV t40cr,%d\r\n    localV t40or,%d\r\n    localD t40sclip\r\n    localD t40sopq\r\n"
                  "cBegin\r\n" % (8, 8), 2, "column locals")
    t = replace_n(t, "    text_bounds 0,0,0\r\n    cCall RStrBlt",
                  "    t40_clamp 0\r\n    text_bounds 0,0,0\r\n    t40_bounds 0\r\n    t40_unclamp 0\r\n"
                  "    t40_takesnap\r\n    cCall RStrBlt", 1, "StrBlt columns")
    t = replace_n(t, "    text_bounds 1,opaquerect,options\r\n    cCall RExtTextOut",
                  "    t40_clamp 1\r\n    text_bounds 1,opaquerect,options\r\n    t40_bounds 1\r\n"
                  "    t40_unclamp 1\r\n    t40_takesnap\r\n    cCall RExtTextOut", 1, "ExtTextOut columns")
    t = replace_n(t, "    text_flush\r\nTStrBlt_done:", "    t40_flush\r\nTStrBlt_done:", 1, "StrBlt flush")
    t = replace_n(t, "    text_flush\r\nTExtTextOut_done:", "    t40_flush\r\nTExtTextOut_done:", 1,
                  "ExtTextOut flush")
    t = replace_n(t, "TStrBlt_render:\r\n", "TStrBlt_render:\r\n    t40_record 0\r\n", 1, "StrBlt hints")
    t = replace_n(t, "TExtTextOut_render:\r\n", "TExtTextOut_render:\r\n    t40_record 1\r\n", 1,
                  "ExtTextOut hints")
    t = replace_n(t, BLIT_OLD, BLIT_NEW, 1, "BitBlt hint moves")
    for gone in ("get_nibble\r\n    or al,dl", "and ax,3\r\n    mov cl,13\r\n", "call cursor_begin_retain"):
        if gone in t:
            raise SystemExit(f"T40PATCH: graphics flush text left in TSOFT: {gone!r}")
    return t


TC_NEW = crlf("""; T40PATCH: text-mode cursor. The hot spot's cell shows its attribute
; XOR 77h; tc_save_xbyte keeps that attribute byte's offset in B800h.
tc_erase proc near
    cmp tc_drawn,0
    je tce_done
    mov tc_drawn,0
    cmp enabled_flag,0
    je tce_done
    mov ax,0B800h
    mov es,ax
    mov di,tc_save_xbyte
    xor byte ptr es:[di],77h
tce_done:
    ret
tc_erase endp

tc_draw proc near
    cmp enabled_flag,0
    jne tcd_enabled
    ret
tcd_enabled:
    cmp tc_have,0
    jne tcd_have
    ret
tcd_have:
    mov ax,tc_origin_x
    add ax,tc_hot_x
    cmp ax,0
    jge tcd_x0
    ret
tcd_x0:
    cmp ax,320
    jl tcd_x1
    ret
tcd_x1:
    mov bx,tc_origin_y
    add bx,tc_hot_y
    cmp bx,0
    jge tcd_y0
    ret
tcd_y0:
    cmp bx,200
    jl tcd_y1
    ret
tcd_y1:
    mov cl,3
    shr ax,cl
    shr bx,cl
    xchg ax,bx
    mov dx,40
    mul dx
    add ax,bx
    shl ax,1
    inc ax
    mov di,ax
    mov tc_save_xbyte,di
    mov ax,0B800h
    mov es,ax
    xor byte ptr es:[di],77h
    mov tc_drawn,1
    ret
tc_draw endp
""")


def patch_tcursor(t):
    start = t.index("tc_erase proc near\r\n")
    end_marker = "tc_draw endp\r\n"
    if t.count("tc_erase proc near\r\n") != 1 or t.count(end_marker) != 1:
        raise SystemExit("T40PATCH: cursor anchors not unique")
    end = t.index(end_marker) + len(end_marker)
    return t[:start] + TC_NEW + t[end:]


def patch_def(t):
    t = replace_n(t, "Tandy 320x200 16-color software raster",
                  "TXT40 CGA 40x25 color text (experimental)", 1, "description")
    t = replace_n(t, " _SHADOW PRELOAD FIXED\r\n", " _SHADOW PRELOAD FIXED\r\n _T40 PRELOAD FIXED\r\n _T40N PRELOAD FIXED\r\n", 1,
                  "segment list")
    return t


def patch_staged(ega_dir):
    ega = Path(ega_dir)
    done = {}
    for name, fn in (("TSOFT.ASM", patch_tsoft), ("TCURSOR.ASM", patch_tcursor), ("TSOFT.DEF", patch_def)):
        p = ega / name
        old = p.read_bytes().decode("latin-1")
        new = fn(old)
        if "\n" in new.replace("\r\n", ""):
            raise SystemExit(f"T40PATCH: bare LF in {name}")
        done[name] = new
    for name, new in done.items():
        (ega / name).write_bytes(new.encode("latin-1"))
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.parse_args()
    t = ansi_table_text()
    assert t.count("db") == 16 and "\n" not in t.replace("\r\n", "")
    for name in ("T40PRES.ASM", "T40DATA.ASM"):
        fragment(name)
    assert M.ansi_to_cp437(0xE9) == 0x82 and M.ansi_to_cp437(ord("A")) == ord("A")
    print("T40PATCH: check PASS (fragments CRLF, ANSI table 256 entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
