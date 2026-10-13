; T40PRES.ASM - TXT40/TEXT80 presenter: TR5 shadow pixels -> text cells.
; Specification: src/txt40/T40MODEL.PY (Presenter). MASM 5.1, 8086 only.
;
; This is a fragment. T40PATCH.PY inserts it into the driver's code
; segment; T40TEST.PY assembles the same bytes into a DOS harness. The
; includer provides:
;   segment _T40 holding the T40DATA.ASM fragment (t40_slot at offset 0)
;   T40_SHSEG, T40_VSEG, T40_LSEG and the geometry: see T40DATA.ASM. The
;   shadow is read through t40_sh0/t40_sh1 (t40_rowes); with two bands the
;   includer stores both segments there before the first call.
; Entry points (near; all preserve CS/SS/SP and BP):
;   t40_present AX=first row, BX=end row, CX=first byte, DX=end byte;
;               clamped and non-empty. Clobbers AX-DI, DS, ES.
; t40_save      AX..DX as t40_present, raw: keep the shadow bytes of that
;               rectangle (clamped) for the next t40_pdiff, if they fit in
;               T40_SNAPB bytes. Preserves all.
;   t40_drop    forget the snapshot. Preserves all but flags.
;   t40_pdiff   AX..DX as t40_present: present only what can differ from
;               the snapshot (T40MODEL.Presenter.present_diff); without a
;               matching snapshot, t40_present. Drops the snapshot.
;               Clobbers AX-DI, DS, ES.
; The includer also provides T40_SNSEG: the segment of a T40_SNAPB-byte
; snapshot buffer at offset 0.
;   t40_add     AX=x, BX=y, ES:SI=8 glyph rows, DL=CP437 code. Preserves all.
;   t40_blit    AX=src x, BX=src y, CX=width, DX=height, SI=dx, DI=dy.
;               Preserves all.
;   t40_reset   forget every hint. Preserves all.
; Geometry equates (T40_COLS, T40_NROWS, T40_NGLYPH, ... and those derived from
; them) come from T40DATA.ASM; with none given, 40x25 as TXT40 has always
; been, assembling to the same bytes.
; Hints are stored packed (T40DATA.ASM: 4-byte slots, glyph rows in a
; dictionary). t40_unpack expands one into t40_xs with the layout every
; check uses: +0 x, +2 y, +4 glyph rows 0-7, +12 code, +13 valid.

t40_pop label byte
    db 0,1,1,2,1,2,2,3,1,2,2,3,2,3,3,4,1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5
    db 1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6
    db 1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6
    db 2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7
    db 1,2,2,3,2,3,3,4,2,3,3,4,3,4,4,5,2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6
    db 2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7
    db 2,3,3,4,3,4,4,5,3,4,4,5,4,5,5,6,3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7
    db 3,4,4,5,4,5,5,6,4,5,5,6,5,6,6,7,4,5,5,6,5,6,6,7,5,6,6,7,6,7,7,8

; Box-drawing junction by left<<3 | right<<2 | up<<1 | down.
t40_box label byte
    db 0C5h,0B3h,0B3h,0B3h,0C4h,0DAh,0C0h,0C3h
    db 0C4h,0BFh,0D9h,0B4h,0C4h,0C2h,0C1h,0C5h

; Half blocks in trial order: code, then 8 rows. The foreground is never
; the majority colour, so no full block or dark shade is ever chosen.
t40_shapes label byte
    db 0DFh,0FFh,0FFh,0FFh,0FFh,000h,000h,000h,000h
    db 0DCh,000h,000h,000h,000h,0FFh,0FFh,0FFh,0FFh
    db 0DDh,0F0h,0F0h,0F0h,0F0h,0F0h,0F0h,0F0h,0F0h
    db 0DEh,00Fh,00Fh,00Fh,00Fh,00Fh,00Fh,00Fh,00Fh

assume ds:_T40

; AX = AX * T40_COLS (cell rows) without MUL, which costs ~120 cycles on an
; 8088. Clobbers DX.
t40_x40 macro
    mov dx,ax
    shl ax,1
    shl ax,1
    add ax,dx
    shl ax,1
    shl ax,1
    shl ax,1
  if T40_COLS eq 80
    shl ax,1
  endif
endm

; AX = pixel row (0 <= AX < T40_H) -> ES = the shadow segment holding it,
; AX = the row's offset there. Two bands: rows 200-399 are in t40_sh1 at
; (row - 200) * T40_ROWB. DS = _T40. Clobbers DX.
t40_rowes macro
local tre_b0,tre_done
  if T40_BANDS eq 1
    mov dx,T40_ROWB
    mul dx
    mov es,t40_sh0
  else
    cmp ax,200
    jb tre_b0
    sub ax,200
    mov dx,T40_ROWB
    mul dx
    mov es,t40_sh1
    jmp short tre_done
tre_b0:
    mov dx,T40_ROWB
    mul dx
    mov es,t40_sh0
tre_done:
  endif
endm

; reg = reg * 8 (cell -> its first packed slot). Clobbers CL. Not CX.
t40_slotof macro reg
    mov cl,3
    shl reg,cl
endm

; AX = AX * 8 * T40_ROWB (shadow bytes per cell row: 1280 or 2560) for
; AX <= 51. Clobbers DX.
t40_x1280 macro
    mov dx,ax
    shl ax,1
    shl ax,1
    add ax,dx
    mov ah,al
    xor al,al
  if T40_COLS eq 80
    shl ax,1
  endif
endm

; ---- t40_uni: AH = nonzero column mask. CF=0: AL = the single IRGB colour
; of those pixels in t40_v (R,G,B,I). CF=1: more than one colour.
tu_bit macro idx
local zero,done
    mov bl,t40_v+idx
    and bl,ah
    jz zero
    cmp bl,ah
    jne tu_fail
    stc
    jmp short done
zero:
    clc
done:
    rcl al,1
endm

t40_uni proc near
    push bx
    xor al,al
    tu_bit 3
    tu_bit 0
    tu_bit 1
    tu_bit 2
    pop bx
    clc
    ret
tu_fail:
    pop bx
    stc
    ret
t40_uni endp

; ---- t40_unpack: DI = packed slot of cell BX -> t40_xs (x, y, glyph rows,
; code, valid); SI = offset t40_xs. DS = _T40. Preserves BX, CX, DX, DI.
t40_unpack proc near
    push cx
    push dx
    push di
    mov si,offset t40_xs
    mov byte ptr [si+13],0
    mov dl,[di]
    test dl,80h
    jz tup_done
    mov byte ptr [si+13],1
    mov al,[di+3]
    mov [si+12],al
    mov ax,bx
    mov cl,T40_COLS
    div cl                      ; AL = cell row, AH = cell column
    mov ch,al
    mov al,ah
    xor ah,ah
    mov cl,3
    shl ax,cl
    sub ax,4
    mov cl,dl
    and cl,7
    add al,cl
    adc ah,0
    mov [si],ax                 ; x = 8cx - 4 + dx
    mov al,ch
    xor ah,ah
    mov cl,3
    shl ax,cl
    sub ax,4
    mov cl,dl
    shr cl,1
    shr cl,1
    shr cl,1
    and cl,7
    add al,cl
    adc ah,0
    mov [si+2],ax               ; y = 8cy - 4 + dy
    mov ax,[di+1]
    and ax,T40_NGLYPH-1
    mov cl,3
    shl ax,cl
    mov di,ax
    mov ax,word ptr t40_gly[di]
    mov [si+4],ax
    mov ax,word ptr t40_gly[di+2]
    mov [si+6],ax
    mov ax,word ptr t40_gly[di+4]
    mov [si+8],ax
    mov ax,word ptr t40_gly[di+6]
    mov [si+10],ax
tup_done:
    pop di
    pop dx
    pop cx
    ret
t40_unpack endp

; ---- t40_gfind: ES:SI = 8 glyph rows -> AX = their dictionary index,
; added if new. A new glyph when T40_GLIMIT are kept first resets every hint
; and the dictionary (t40_reset). DS = _T40. Preserves BX-DI.
t40_gfind proc near
    push bx
    push cx
    push dx
    push di
tgf_again:
    xor ax,ax
    xor bx,bx
    mov cx,8
tgf_hash:
    rol ax,1
    rol ax,1
    rol ax,1
    xor al,es:[bx+si]
    inc bx
    loop tgf_hash
    and ax,T40_NGLYPH-1
    mov bx,ax
tgf_probe:
    mov di,bx
    mov cl,3
    shr di,cl                   ; byte of the in-use bitmap
    mov cl,bl
    and cl,7
    mov dl,1
    shl dl,cl                   ; its bit
    test t40_guse[di],dl
    jz tgf_empty
    push si
    push di
    mov di,bx
    mov cl,3
    shl di,cl
    mov cx,8
tgf_cmp:
    mov al,es:[si]
    cmp al,t40_gly[di]
    jne tgf_ne
    inc si
    inc di
    loop tgf_cmp
    pop di
    pop si
    mov ax,bx
    jmp short tgf_done
tgf_ne:
    pop di
    pop si
    inc bx
    and bx,T40_NGLYPH-1
    jmp short tgf_probe
tgf_empty:
    cmp t40_gcnt,T40_GLIMIT
    jb tgf_insert
    call t40_reset
    jmp short tgf_again
tgf_insert:
    or t40_guse[di],dl
    inc t40_gcnt
    push si
    mov di,bx
    mov cl,3
    shl di,cl
    mov cx,8
tgf_copy:
    mov al,es:[si]
    mov t40_gly[di],al
    inc si
    inc di
    loop tgf_copy
    pop si
    mov ax,bx
tgf_done:
    pop di
    pop dx
    pop cx
    pop bx
    ret
t40_gfind endp

; ---- t40_rowbits: AX = pixel row (on screen). t40_v[p] = the 8 pixels of
; plane p starting at x = t40_x (t40_b0 = x sar 3, t40_sh = x and 7);
; off-screen columns read as 0. ES = shadow. Preserves BX-DI.
t40_rowbits proc near
    push bx
    push cx
    push dx
    push di
    t40_rowes
    mov di,ax
    add di,t40_b0
    xor bx,bx
    mov cl,byte ptr t40_sh
trb_plane:
    xor ax,ax
    cmp t40_b0,0
    jl trb_nolo
    mov ah,es:[di]
trb_nolo:
    cmp t40_b0,T40_COLS-1
    jge trb_nohi
    mov al,es:[di+1]
trb_nohi:
    shl ax,cl
    mov t40_v[bx],ah
    add di,T40_COLS
    inc bx
    cmp bx,4
    jb trb_plane
    pop di
    pop dx
    pop cx
    pop bx
    ret
t40_rowbits endp

; ---- t40_verify: SI = slot. CF=0: AL = attribute B<<4|F. CF=1: not shown.
; Strict check of all rows; if that fails and the glyph has ink in rows 1-6,
; rows 1-6 only (a focus rectangle crosses rows 0 and 7). ES = shadow.
; Preserves BX-DI.
t40_verify proc near
    mov t40_rows,0FFh
    call t40_vrows
    jnc tvf_done
    mov al,[si+5]
    or al,[si+6]
    or al,[si+7]
    or al,[si+8]
    or al,[si+9]
    or al,[si+10]
    jz tvf_fail
    mov t40_rows,07Eh
    call t40_vrows
tvf_done:
    ret
tvf_fail:
    stc
    ret
t40_verify endp

; ---- t40_vrows: the check for the rows set in t40_rows (bit r = row r).
t40_vrows proc near
    push bx
    push cx
    push dx
    push di
    mov ax,[si]
    mov t40_x,ax
    mov bx,ax
    mov cl,3
    sar bx,cl
    mov t40_b0,bx
    and ax,7
    mov t40_sh,ax
    mov ax,t40_x
    mov dl,0FFh
    or ax,ax
    jns tv_right
    neg ax
    mov cl,al
    shr dl,cl
    jmp short tv_mask
tv_right:
    sub ax,T40_W-8
    jle tv_mask
    mov cl,al
    shl dl,cl
tv_mask:
    mov t40_cm,dl
    mov t40_fg,0FFh
    mov t40_bg,0FFh
    mov t40_r7,0FFh
    ; DI = shadow offset of the window's first row at byte t40_b0 (modulo
    ; 64K, so rows above the screen are simply skipped)
    mov ax,[si+2]
    mov dx,ax
    shl ax,1
    shl ax,1
    add ax,dx
    mov cl,T40_ROWSH
    shl ax,cl
    add ax,t40_b0
    mov di,ax
    mov cl,byte ptr t40_sh
    mov dh,1
    xor bx,bx
tv_row:
    test t40_rows,dh
    jnz tv_row_on
    jmp tv_next
tv_row_on:
    mov ax,[si+2]
    add ax,bx
    cmp ax,0
    jge tv_top_ok
    jmp tv_next
tv_top_ok:
    cmp ax,T40_H
    jl tv_on
    jmp tv_next
tv_on:
    cmp t40_b0,0
    jl tv_edge
    cmp t40_b0,T40_COLS-1
    jge tv_edge
  if T40_BANDS ne 1
    push dx                     ; this row's band and offset
    mov ax,[si+2]
    add ax,bx
    t40_rowes
    add ax,t40_b0
    mov di,ax
    pop dx
  endif
    mov ax,es:[di]
    xchg al,ah
    shl ax,cl
    mov t40_v,ah
    mov ax,es:[di+T40_COLS]
    xchg al,ah
    shl ax,cl
    mov t40_v+1,ah
    mov ax,es:[di+2*T40_COLS]
    xchg al,ah
    shl ax,cl
    mov t40_v+2,ah
    mov ax,es:[di+3*T40_COLS]
    xchg al,ah
    shl ax,cl
    mov t40_v+3,ah
    jmp short tv_bits
tv_edge:
    call t40_rowbits
tv_bits:
    mov dl,[si+bx+4]
    cmp bx,7
    jne tv_normal
    cmp byte ptr [si+11],0
    jne tv_normal
    mov ah,t40_cm
    call t40_uni
    jnc tv_r7ok
    jmp tv_fail
tv_r7ok:
    mov t40_r7,al
    jmp short tv_next
tv_normal:
    mov ah,dl
    and ah,t40_cm
    jz tv_bgpart
    call t40_uni
    jnc tv_fgok
    jmp tv_fail
tv_fgok:
    cmp t40_fg,0FFh
    je tv_setfg
    cmp al,t40_fg
    je tv_bgpart
    jmp tv_fail
tv_setfg:
    mov t40_fg,al
tv_bgpart:
    mov ah,dl
    not ah
    and ah,t40_cm
    jz tv_next
    call t40_uni
    jc tv_fail
    cmp t40_bg,0FFh
    je tv_setbg
    cmp al,t40_bg
    jne tv_fail
    jmp short tv_next
tv_setbg:
    mov t40_bg,al
tv_next:
    shl dh,1
    add di,T40_ROWB
    inc bx
    cmp bx,8
    jae tv_rows_done
    jmp tv_row
tv_rows_done:
    mov al,t40_r7
    cmp al,0FFh
    je tv_r7_done
    cmp t40_bg,0FFh
    jne tv_r7_done
    mov t40_bg,al
tv_r7_done:
    mov al,[si+4]
    or al,[si+5]
    or al,[si+6]
    or al,[si+7]
    or al,[si+8]
    or al,[si+9]
    or al,[si+10]
    or al,[si+11]
    jnz tv_glyph
    mov al,t40_bg
    cmp al,0FFh
    je tv_fail
    mov ah,al
    jmp short tv_attr
tv_glyph:
    mov al,t40_fg
    cmp al,0FFh
    je tv_fail
    mov ah,t40_bg
    cmp ah,0FFh
    je tv_fail
    cmp al,ah
    je tv_fail
tv_attr:
    mov cl,4
    shl ah,cl
    or al,ah
    pop di
    pop dx
    pop cx
    pop bx
    clc
    ret
tv_fail:
    pop di
    pop dx
    pop cx
    pop bx
    stc
    ret
t40_vrows endp

; ---- t40_shown: BX = cell. Sets t40_vst[BX] (0 none, 1/2 slot) and
; t40_vat[BX]. ES = shadow. Preserves BX.
t40_shown proc near
    mov t40_vst[bx],0
    mov di,bx
    t40_slotof di
    call t40_unpack
    cmp byte ptr [si+13],0
    je ts_second
    call t40_verify
    jc ts_second
    mov t40_vat[bx],al
    mov t40_vst[bx],1
    ret
ts_second:
    add di,4
    call t40_unpack
    cmp byte ptr [si+13],0
    je ts_none
    call t40_verify
    jc ts_none
    mov t40_vat[bx],al
    mov t40_vst[bx],2
ts_none:
    ret
t40_shown endp

; ---- t40_claim_from: BX = neighbour cell with a shown hint. ORs its window
; into t40_live (claim rows) for cell t40_cy/t40_cx; first hit sets t40_cbg.
t40_claim_from proc near
    mov di,bx
    t40_slotof di
    mov al,t40_vst[bx]
    and al,3
    cmp al,1
    je tcf_slot
    add di,4
tcf_slot:
    call t40_unpack
    mov ax,word ptr t40_xs
    mov dx,t40_cx
    mov cl,3
    shl dx,cl
    sub ax,dx
    cmp ax,8
    jl tcf_left_ok
    ret
tcf_left_ok:
    cmp ax,-8
    jg tcf_in
    ret
tcf_in:
    mov dl,0FFh
    or ax,ax
    jns tcf_pos
    neg ax
    mov cl,al
    shl dl,cl
    jmp short tcf_bits
tcf_pos:
    mov cl,al
    shr dl,cl
tcf_bits:
    mov ax,t40_cy
    mov cl,3
    shl ax,cl
    sub ax,word ptr t40_xs+2
    xor si,si
    xor dh,dh
tcf_row:
    cmp ax,8
    jae tcf_skip
    or t40_live[si],dl
    mov dh,1
tcf_skip:
    inc ax
    inc si
    cmp si,8
    jb tcf_row
    or dh,dh
    jz tcf_done
    cmp t40_cbg,0FFh
    jne tcf_done
    mov al,t40_vat[bx]
    mov cl,4
    shr al,cl
    mov t40_cbg,al
tcf_done:
    ret
t40_claim_from endp

; ---- t40_pick: character for t40_mask within t40_live. Returns AL.
t40_pick proc near
    xor dx,dx
    xor bx,bx
    xor si,si
    mov t40_n,0
tp_count:
    mov bl,t40_live[si]
    mov al,cs:t40_pop[bx]
    xor ah,ah
    add t40_n,ax
    mov bl,t40_mask[si]
    mov al,cs:t40_pop[bx]
    add dx,ax
    inc si
    cmp si,8
    jb tp_count
    or dx,dx
    jnz tp_mixed
    mov al,20h
    ret
tp_mixed:
    mov t40_on,dx
    ; full foreground rows and columns
    xor cx,cx
    mov t40_rf,0FFh
    mov ah,0FFh
    xor si,si
tp_rows:
    mov al,t40_mask[si]
    cmp al,0FFh
    jne tp_notfull
    inc cx
    cmp t40_rf,0FFh
    jne tp_last
    mov bx,si
    mov t40_rf,bl
tp_last:
    mov bx,si
    mov t40_rl,bl
tp_notfull:
    mov bl,t40_live[si]
    not bl
    or bl,al
    and ah,bl
    inc si
    cmp si,8
    jb tp_rows
    mov t40_colm,ah
    mov bl,ah
    xor bh,bh
    mov bl,cs:t40_pop[bx]
    ; CX = full rows, BX = full columns
    mov ax,cx
    or ax,bx
    jnz tp_lines
    jmp tp_shapes
tp_lines:
    cmp cx,2
    jbe tp_r2
    jmp tp_shapes
tp_r2:
    cmp bx,2
    jbe tp_c2
    jmp tp_shapes
tp_c2:
    mov ax,cx
    mul bl
    add ax,t40_on
    mov dx,cx
    add dx,bx
    push cx
    mov cl,3
    shl dx,cl
    pop cx
    sub ax,dx
    cmp ax,2
    jle tp_thin
    jmp tp_shapes
tp_thin:
    or cx,cx
    jz tp_vertical
    or bx,bx
    jnz tp_junction
    mov al,0C4h
    ret
tp_vertical:
    mov al,0B3h
    ret
tp_junction:
    xor bx,bx
    mov ah,t40_colm
    test ah,80h
    jnz tp_jl
    or bl,8
tp_jl:
    test ah,1
    jnz tp_jr
    or bl,4
tp_jr:
    cmp t40_rf,0
    je tp_ju
    test t40_mask,ah
    jz tp_ju
    or bl,2
tp_ju:
    cmp t40_rl,7
    je tp_jd
    test t40_mask+7,ah
    jz tp_jd
    or bl,1
tp_jd:
    mov al,cs:t40_box[bx]
    ret
tp_shapes:
    mov t40_bestd,65
    mov t40_best,0
    xor di,di
tp_shape:
    xor dx,dx
    xor si,si
    xor bh,bh
tp_srow:
    mov bl,t40_mask[si]
    xor bl,cs:t40_shapes[di+1]
    and bl,t40_live[si]
    mov al,cs:t40_pop[bx]
    xor ah,ah
    add dx,ax
    inc di
    inc si
    cmp si,8
    jb tp_srow
    sub di,8
    cmp dx,t40_bestd
    jae tp_snext
    mov t40_bestd,dx
    mov al,cs:t40_shapes[di]
    mov t40_best,al
tp_snext:
    add di,9
    cmp di,36
    jb tp_shape
    mov ax,t40_bestd
    mov cl,3
    shl ax,cl
    cmp ax,t40_n
    ja tp_density
    mov al,t40_best
    ret
tp_density:
    mov ax,t40_on
    shl ax,cl
    mov bx,t40_n
    xor dx,dx
    div bx
    or ax,ax
    jnz tp_q1
    mov al,20h
    ret
tp_q1:
    cmp ax,2
    ja tp_q3
    mov al,0B0h
    ret
tp_q3:
    mov al,0B1h
    ret
t40_pick endp

; ---- t40_setfm: AL = IRGB colour -> t40_fm = 00h/FFh per plane (R,G,B,I).
; Preserves all but flags.
t40_setfm proc near
    push ax
    push bx
    mov bl,al
    xor ax,ax
    test bl,4
    jz tsf_r
    dec al
tsf_r:
    test bl,2
    jz tsf_g
    dec ah
tsf_g:
    mov word ptr t40_fm,ax
    xor ax,ax
    test bl,1
    jz tsf_b
    dec al
tsf_b:
    test bl,8
    jz tsf_i
    dec ah
tsf_i:
    mov word ptr t40_fm+2,ax
    pop bx
    pop ax
    ret
t40_setfm endp

; AH = pixels of row DI/4 equal to the t40_setfm colour. Clobbers AL.
t40_eq macro
    mov ah,t40_pl[di]
    xor ah,t40_fm
    mov al,t40_pl[di+1]
    xor al,t40_fm+1
    or ah,al
    mov al,t40_pl[di+2]
    xor al,t40_fm+2
    or ah,al
    mov al,t40_pl[di+3]
    xor al,t40_fm+3
    or ah,al
    not ah
endm

; ---- t40_first: SI -> 8 row masks. CF=1: all zero. Else AL = IRGB colour
; of the first set pixel (row-major, leftmost first) in t40_pl.
t40_first proc near
    push bx
    push dx
    push di
    xor bx,bx
tf_row:
    mov dl,[bx+si]
    or dl,dl
    jnz tf_found
    inc bx
    cmp bx,8
    jb tf_row
    pop di
    pop dx
    pop bx
    stc
    ret
tf_found:
    mov dh,80h
tf_bit:
    test dl,dh
    jnz tf_bit_ok
    shr dh,1
    jmp short tf_bit
tf_bit_ok:
    mov di,bx
    shl di,1
    shl di,1
    xor al,al
    test t40_pl[di+3],dh
    jz tf_i
    or al,8
tf_i:
    test t40_pl[di],dh
    jz tf_r
    or al,4
tf_r:
    test t40_pl[di+1],dh
    jz tf_g
    or al,2
tf_g:
    test t40_pl[di+2],dh
    jz tf_b
    or al,1
tf_b:
    pop di
    pop dx
    pop bx
    clc
    ret
t40_first endp

; ---- t40_two: colours of the live pixels when there are at most two.
; CF=1: three or more (use the counting path). CF=0: AL = background
; (0FFh: no live pixel), AH = foreground (0FFh: one colour only); with two
; colours t40_mask = live pixels of the foreground. Same choice as the
; counting path: more pixels wins, the lower index on a tie.
t40_two proc near
    mov si,offset t40_live
    call t40_first
    jnc tw_a
    mov ax,0FFFFh
    clc
    ret
tw_a:
    mov t40_ca,al
    call t40_setfm
    xor si,si
    xor di,di
    xor dx,dx
    xor bx,bx
tw_arow:
    t40_eq
    mov cl,t40_live[si]
    mov ch,cl
    and ch,ah
    mov t40_eqa[si],ch
    mov bl,ch
    add dl,cs:t40_pop[bx]
    not ah
    and cl,ah
    mov t40_rem[si],cl
    or dh,cl
    add di,4
    inc si
    cmp si,8
    jb tw_arow
    mov t40_na,dl
    or dh,dh
    jnz tw_b
    mov al,t40_ca
    mov ah,0FFh
    clc
    ret
tw_b:
    mov si,offset t40_rem
    call t40_first
    mov t40_cb,al
    call t40_setfm
    xor si,si
    xor di,di
    xor dx,dx
tw_brow:
    t40_eq
    mov cl,t40_rem[si]
    mov ch,cl
    and ch,ah
    mov t40_eqb[si],ch
    mov bl,ch
    add dl,cs:t40_pop[bx]
    not ah
    and cl,ah
    or dh,cl
    add di,4
    inc si
    cmp si,8
    jb tw_brow
    or dh,dh
    jz tw_two
    stc
    ret
tw_two:
    ; DL = pixels of b, t40_na = pixels of a
    mov al,t40_ca
    mov ah,t40_cb
    cmp t40_na,dl
    ja tw_a_bg
    jb tw_b_bg
    cmp al,ah
    jb tw_a_bg
tw_b_bg:
    xchg al,ah
    mov si,offset t40_eqa
    jmp short tw_mask
tw_a_bg:
    mov si,offset t40_eqb
tw_mask:
    mov bx,[si]
    mov word ptr t40_mask,bx
    mov bx,[si+2]
    mov word ptr t40_mask+2,bx
    mov bx,[si+4]
    mov word ptr t40_mask+4,bx
    mov bx,[si+6]
    mov word ptr t40_mask+6,bx
    clc
    ret
t40_two endp

; One neighbour: BX = this cell. Claims from cell BX+off when the t40_nbf
; bits in need are all set and that cell shows a hint.
t40_nb macro off,need
local skip
    if need
    mov al,t40_nbf
    and al,need
    cmp al,need
    jne skip
    endif
    test t40_vst[bx+off],3
    jz skip
    push bx
    add bx,off
    call t40_claim_from
    pop bx
skip:
endm

; ---- t40_cell: text word for cell t40_cy/t40_cx in AX. ES = shadow.
t40_cell proc near
    mov ax,t40_cy
    t40_x40
    add ax,t40_cx
    mov bx,ax
    mov al,t40_vst[bx]
    and al,3                    ; the kept slot (not the stale/changed marks)
    jz tc_approx
    mov di,bx
    t40_slotof di
    cmp al,1
    je tc_own
    add di,4
tc_own:
    mov al,[di+3]
    mov ah,t40_vat[bx]
    ret
tc_approx:
    xor ax,ax
    mov word ptr t40_live,ax
    mov word ptr t40_live+2,ax
    mov word ptr t40_live+4,ax
    mov word ptr t40_live+6,ax
    mov t40_cbg,0FFh
    ; neighbours in row-major order; t40_nbf bit 0 = row above exists,
    ; 1 = row below, 2 = column left, 3 = column right
    xor al,al
    cmp t40_cy,0
    je tc_nb_top
    or al,1
tc_nb_top:
    cmp t40_cy,T40_NROWS-1
    je tc_nb_bottom
    or al,2
tc_nb_bottom:
    cmp t40_cx,0
    je tc_nb_left
    or al,4
tc_nb_left:
    cmp t40_cx,T40_COLS-1
    je tc_nb_right
    or al,8
tc_nb_right:
    mov t40_nbf,al
    t40_nb -(T40_COLS+1),5
    t40_nb -T40_COLS,1
    t40_nb -(T40_COLS-1),9
    t40_nb -1,4
    t40_nb 0,0
    t40_nb 1,8
    t40_nb T40_COLS-1,6
    t40_nb T40_COLS,2
    t40_nb T40_COLS+1,10
    ; live = not claimed; load the cell's plane bytes
    xor si,si
    xor di,di
  if T40_BANDS eq 1
    mov ax,t40_cy
    t40_x1280
  else
    mov ax,t40_cy               ; a cell row never spans two bands
    mov cl,3
    shl ax,cl
    t40_rowes
  endif
    add ax,t40_cx
    mov bx,ax
tc_load:
    not t40_live[si]
    mov al,es:[bx]
    mov t40_pl[di],al
    mov al,es:[bx+T40_COLS]
    mov t40_pl[di+1],al
    mov al,es:[bx+2*T40_COLS]
    mov t40_pl[di+2],al
    mov al,es:[bx+3*T40_COLS]
    mov t40_pl[di+3],al
    add bx,T40_ROWB
    add di,4
    inc si
    cmp si,8
    jb tc_load
    ; no claims and every row the same single colour: a blank cell
    mov ax,0FFFFh
    cmp word ptr t40_live,ax
    jne tc_mixed
    cmp word ptr t40_live+2,ax
    jne tc_mixed
    cmp word ptr t40_live+4,ax
    jne tc_mixed
    cmp word ptr t40_live+6,ax
    jne tc_mixed
    mov ax,word ptr t40_pl
    mov dx,word ptr t40_pl+2
    mov si,4
tc_solid_row:
    cmp ax,word ptr t40_pl[si]
    jne tc_mixed
    cmp dx,word ptr t40_pl[si+2]
    jne tc_mixed
    add si,4
    cmp si,32
    jb tc_solid_row
    xor bl,bl
    cmp al,0
    je tc_s_r
    cmp al,0FFh
    jne tc_mixed
    or bl,4
tc_s_r:
    cmp ah,0
    je tc_s_g
    cmp ah,0FFh
    jne tc_mixed
    or bl,2
tc_s_g:
    cmp dl,0
    je tc_s_b
    cmp dl,0FFh
    jne tc_mixed
    or bl,1
tc_s_b:
    cmp dh,0
    je tc_s_i
    cmp dh,0FFh
    jne tc_mixed
    or bl,8
tc_s_i:
    mov ah,bl
    mov cl,4
    shl ah,cl
    or ah,bl
    mov al,20h
    ret
tc_mixed:
    call t40_two
    jnc tc_fast
    jmp tc_counts
tc_fast:
    cmp al,0FFh
    jne tc_fast_live
    jmp tc_nolive
tc_fast_live:
    cmp ah,0FFh
    jne tc_fast_two
    mov ah,al
    mov cl,4
    shl ah,cl
    or ah,al
    mov al,20h
    ret
tc_fast_two:
    mov t40_bgc,al
    mov t40_fgc,ah
    call t40_pick
    mov ah,t40_bgc
    mov cl,4
    shl ah,cl
    or ah,t40_fgc
    ret
tc_counts:
    ; three or more colours: colour counts of live pixels
    xor ax,ax
    xor si,si
tc_zero:
    mov t40_cnt[si],ax
    add si,2
    cmp si,32
    jb tc_zero
    xor si,si
    xor di,di
tc_crow:
    mov ah,t40_pl[di]
    mov bl,t40_pl[di+1]
    mov bh,t40_pl[di+2]
    mov dh,t40_pl[di+3]
    mov dl,t40_live[si]
    mov cx,8
tc_cpix:
    xor al,al
    shl dh,1
    rcl al,1
    shl ah,1
    rcl al,1
    shl bl,1
    rcl al,1
    shl bh,1
    rcl al,1
    shl dl,1
    jnc tc_cskip
    push bx
    mov bl,al
    xor bh,bh
    shl bx,1
    inc t40_cnt[bx]
    pop bx
tc_cskip:
    loop tc_cpix
    add di,4
    inc si
    cmp si,8
    jb tc_crow
    ; background: most frequent, lowest index on ties; then foreground
    mov dl,0FFh
    xor bx,bx
tc_bg:
    mov ax,t40_cnt[bx]
    or ax,ax
    jz tc_bg_next
    cmp dl,0FFh
    je tc_bg_set
    mov si,dx
    and si,0Fh
    shl si,1
    cmp ax,t40_cnt[si]
    jbe tc_bg_next
tc_bg_set:
    mov dl,bl
    shr dl,1
tc_bg_next:
    add bx,2
    cmp bx,32
    jb tc_bg
    cmp dl,0FFh
    jne tc_have_bg
tc_nolive:
    mov al,t40_cbg
    cmp al,0FFh
    jne tc_cbg
    xor al,al
tc_cbg:
    mov ah,al
    mov cl,4
    shl ah,cl
    or ah,al
    mov al,20h
    ret
tc_have_bg:
    mov t40_bgc,dl
    mov dh,0FFh
    xor bx,bx
tc_fg:
    mov ax,bx
    shr ax,1
    cmp al,dl
    je tc_fg_next
    mov ax,t40_cnt[bx]
    or ax,ax
    jz tc_fg_next
    cmp dh,0FFh
    je tc_fg_set
    mov cl,dh
    xor ch,ch
    mov si,cx
    shl si,1
    cmp ax,t40_cnt[si]
    jbe tc_fg_next
tc_fg_set:
    mov dh,bl
    shr dh,1
tc_fg_next:
    add bx,2
    cmp bx,32
    jb tc_fg
    cmp dh,0FFh
    jne tc_have_fg
    mov al,dl
    mov ah,dl
    mov cl,4
    shl ah,cl
    or ah,al
    mov al,20h
    ret
tc_have_fg:
    mov t40_fgc,dh
    ; foreground mask: live pixels equal to the foreground colour
    xor si,si
    xor di,di
tc_mrow:
    mov dl,t40_fgc
    xor al,al
    test dl,4
    jz tc_m1
    not al
tc_m1:
    xor al,t40_pl[di]
    mov ah,al
    xor al,al
    test dl,2
    jz tc_m2
    not al
tc_m2:
    xor al,t40_pl[di+1]
    or ah,al
    xor al,al
    test dl,1
    jz tc_m3
    not al
tc_m3:
    xor al,t40_pl[di+2]
    or ah,al
    xor al,al
    test dl,8
    jz tc_m4
    not al
tc_m4:
    xor al,t40_pl[di+3]
    or ah,al
    not ah
    and ah,t40_live[si]
    mov t40_mask[si],ah
    add di,4
    inc si
    cmp si,8
    jb tc_mrow
    call t40_pick
    mov ah,t40_bgc
    mov cl,4
    shl ah,cl
    or ah,t40_fgc
    ret
t40_cell endp

; ---- t40_touch: SI = slot. CF=1 if it is valid and its 8x8 window touches
; the dirty pixels t40_px0..t40_px1-1 x t40_py0..t40_py1-1. Clobbers AX.
t40_touch proc near
    cmp byte ptr [si+13],0
    je tch_no
    mov ax,[si]
    cmp ax,t40_px1
    jge tch_no
    add ax,8
    cmp ax,t40_px0
    jle tch_no
    mov ax,[si+2]
    cmp ax,t40_py1
    jge tch_no
    add ax,8
    cmp ax,t40_py0
    jle tch_no
    stc
    ret
tch_no:
    clc
    ret
t40_touch endp

; ---- t40_present ---------------------------------------------------------
; A glyph window spans at most two cell rows and two cell columns, so pixels
; of the dirty cells can change only the dirty cells and one cell around
; them (output range). Their shown hints are re-verified; neighbours keep
; the state from the flush that last covered them.
t40_present proc near
    mov si,seg t40_slot
    mov ds,si
    cmp t40_cpv,0
    je tpr_go
    jmp t40_ring
tpr_go:
    mov es,t40_sh0
    mov t40_py0,ax
    mov t40_py1,bx
    mov si,cx
    shl si,1
    shl si,1
    shl si,1
    mov t40_px0,si
    mov si,dx
    shl si,1
    shl si,1
    shl si,1
    mov t40_px1,si
    mov si,cx
    mov cl,3
    shr ax,cl
    sub ax,1
    jge tpr_r0
    xor ax,ax
tpr_r0:
    mov t40_r0,ax
    dec bx
    shr bx,cl
    add bx,1
    cmp bx,T40_NROWS-1
    jle tpr_r1
    mov bx,T40_NROWS-1
tpr_r1:
    mov t40_r1,bx
    sub si,1
    jge tpr_c0
    xor si,si
tpr_c0:
    mov t40_c0,si
    cmp dx,T40_COLS-1
    jle tpr_c1
    mov dx,T40_COLS-1
tpr_c1:
    mov t40_c1,dx
    ; re-verify output cells that are stale or have a hint window touching
    ; the dirty pixels; every other kept state is still exact
    mov ax,t40_r0
    mov t40_cy,ax
tpr_vrow:
    mov ax,t40_c0
    mov t40_cx,ax
tpr_vcol:
    mov ax,t40_cy
    t40_x40
    add ax,t40_cx
    mov bx,ax
    test t40_vst[bx],80h
    jnz tpr_verify
    mov di,bx
    t40_slotof di
    call t40_unpack
    call t40_touch
    jc tpr_verify
    add di,4
    call t40_unpack
    call t40_touch
    jnc tpr_kept
tpr_verify:
    mov al,t40_vst[bx]          ; TEXT80: was it stale, or does its kept
    mov ah,t40_vat[bx]          ; state change? Then mark it changed (40h):
    push ax                     ; it and its neighbours are output
    call t40_shown
    pop ax
    test al,80h
    jnz tpr_chg
    and al,3
    cmp al,t40_vst[bx]
    jne tpr_chg
    or al,al
    jz tpr_kept
    cmp ah,t40_vat[bx]
    je tpr_kept
tpr_chg:
    or t40_vst[bx],40h
tpr_kept:
    inc t40_cx
    mov ax,t40_cx
    cmp ax,t40_c1
    jg tpr_vcdone
    jmp tpr_vcol
tpr_vcdone:
    inc t40_cy
    mov ax,t40_cy
    cmp ax,t40_r1
    jg tpr_vdone
    jmp tpr_vrow
tpr_vdone:
    ; output (TEXT80 tight range): the dirty cells, the changed cells and
    ; their neighbours, scanned over the verify range and one around it
    mov ax,t40_py0
    mov cl,3
    shr ax,cl
    mov t40_qr0,ax
    mov ax,t40_py1
    dec ax
    shr ax,cl
    mov t40_qr1,ax
    mov ax,t40_px0
    shr ax,cl
    mov t40_qc0,ax
    mov ax,t40_px1
    shr ax,cl
    dec ax
    mov t40_qc1,ax
    mov ax,t40_r0
    dec ax
    jns tpr_or0
    xor ax,ax
tpr_or0:
    mov t40_or0,ax
    mov ax,t40_r1
    inc ax
    cmp ax,T40_NROWS-1
    jle tpr_or1
    mov ax,T40_NROWS-1
tpr_or1:
    mov t40_or1,ax
    mov ax,t40_c0
    dec ax
    jns tpr_oc0
    xor ax,ax
tpr_oc0:
    mov t40_oc0,ax
    mov ax,t40_c1
    inc ax
    cmp ax,T40_COLS-1
    jle tpr_oc1
    mov ax,T40_COLS-1
tpr_oc1:
    mov t40_oc1,ax
    mov ax,t40_or0
    mov t40_cy,ax
tpr_orow:
    mov ax,t40_oc0
    mov t40_cx,ax
tpr_ocol:
    call t40_need
    jc tpr_doit
    jmp tpr_onext
tpr_doit:
    call t40_cell
    push ax
    mov ax,t40_cy
    t40_x40
    add ax,t40_cx
    shl ax,1
    mov di,ax
    pop ax
  if T40_PANNED
    mov si,T40_LSEG             ; the logical text of every row
    mov es,si
    mov es:[di],ax
    mov si,t40_cy               ; and the screen, if the row is shown
    sub si,t40_vtop
    jb tpr_hidden
    cmp si,T40_VISROWS
    jae tpr_hidden
    sub di,t40_voff
    mov si,T40_VSEG
    mov es,si
    mov es:[di],ax
tpr_hidden:
  else
    mov si,T40_VSEG
    mov es,si
    mov es:[di],ax
  endif
    mov es,t40_sh0
tpr_onext:
    inc t40_cx
    mov ax,t40_cx
    cmp ax,t40_oc1
    jle tpr_ocol
    inc t40_cy
    mov ax,t40_cy
    cmp ax,t40_or1
    jle tpr_orow
    call t40_unmark
    ret
t40_present endp

; ---- t40_need: CF=1 when cell t40_cy/t40_cx is dirty (t40_qr0..qr1,
; t40_qc0..qc1) or it or a neighbour was marked changed (vst 40h).
; DS = _T40. Clobbers AX, DX.
t40_need proc near
    mov ax,t40_cy
    cmp ax,t40_qr0
    jl tn_nb
    cmp ax,t40_qr1
    jg tn_nb
    mov ax,t40_cx
    cmp ax,t40_qc0
    jl tn_nb
    cmp ax,t40_qc1
    jg tn_nb
    stc
    ret
tn_nb:
    push bx
    push cx
    mov cx,t40_cy
    dec cx                      ; neighbour row
tn_row:
    cmp cx,0
    jl tn_nextrow
    cmp cx,T40_NROWS-1
    jg tn_nextrow
    mov ax,cx
    t40_x40
    add ax,t40_cx
    mov bx,ax                   ; the row's cell in this column
    test t40_vst[bx],40h
    jnz tn_yes
    cmp t40_cx,0
    je tn_noleft
    test t40_vst[bx-1],40h
    jnz tn_yes
tn_noleft:
    cmp t40_cx,T40_COLS-1
    je tn_nextrow
    test t40_vst[bx+1],40h
    jnz tn_yes
tn_nextrow:
    inc cx
    mov ax,t40_cy
    inc ax
    cmp cx,ax
    jle tn_row
    pop cx
    pop bx
    clc
    ret
tn_yes:
    pop cx
    pop bx
    stc
    ret
t40_need endp

; ---- t40_unmark: clear the changed marks (vst 40h) of the verify range.
; DS = _T40. Clobbers AX, BX, DX.
t40_unmark proc near
    mov ax,t40_r0
    mov t40_cy,ax
tu_row:
    mov ax,t40_cy
    t40_x40
    add ax,t40_c0
    mov bx,ax
    mov dx,t40_c1
    sub dx,t40_c0
tu_col:
    and t40_vst[bx],0BFh
    inc bx
    dec dx
    jns tu_col
    inc t40_cy
    mov ax,t40_cy
    cmp ax,t40_r1
    jle tu_row
    ret
t40_unmark endp

; ---- t40_pan: AX = first logical text row to show (clamped to
; 0..T40_NROWS-T40_VISROWS): the screen becomes a copy of those logical rows;
; no cell is converted. Preserves all but flags. (Panned builds only.)
  if T40_PANNED
t40_pan proc near
    push ax
    push cx
    push dx
    push si
    push di
    push ds
    push es
    mov si,seg t40_slot
    mov ds,si
    or ax,ax
    jns tpn_lo
    xor ax,ax
tpn_lo:
    cmp ax,T40_NROWS-T40_VISROWS
    jle tpn_hi
    mov ax,T40_NROWS-T40_VISROWS
tpn_hi:
    mov t40_vtop,ax
    t40_x40
    shl ax,1
    mov t40_voff,ax
    mov si,ax
    xor di,di
    mov ax,T40_VSEG
    mov es,ax
    mov ax,T40_LSEG
    mov ds,ax
    mov cx,T40_VISROWS*T40_COLS
    cld
    rep movsw
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop ax
    ret
t40_pan endp
  endif

; ---- t40_drop: forget the snapshot. Preserves all but flags.
t40_drop proc near
    push ds
    push ax
    mov ax,seg t40_slot
    mov ds,ax
    mov t40_snv,0
    mov t40_cpv,0
    pop ax
    pop ds
    ret
t40_drop endp

; ---- TEXT80 aligned copies (specification: T40MODEL.Presenter.blit) ------
; t40_aligned: in t40_blit (DS = _T40, t40_sx..t40_ddy set). When the source
; rectangle and the offset are whole cells and source and destination lie on
; the screen, and the destination has interior cells (it less its outer
; ring), sets t40_cpv = 1 and the destination in cells (t40_cpr0..cpr1,
; t40_cpc0..cpc1, exclusive ends) and the offset (t40_cdr, t40_cdc).
; Clobbers AX, CX.
t40_aligned proc near
    mov ax,t40_sx
    or ax,t40_sy
    or ax,t40_ex
    or ax,t40_ey
    or ax,t40_ddx
    or ax,t40_ddy
    test ax,7
    jz tal_cells
    ret
tal_cells:
    cmp t40_sx,0
    jge tlj1
    jmp tal_no
tlj1:
    cmp t40_sy,0
    jge tlj2
    jmp tal_no
tlj2:
    cmp t40_ex,T40_W
    jle tlj3
    jmp tal_no
tlj3:
    cmp t40_ey,T40_H
    jle tlj4
    jmp tal_no
tlj4:
    mov cl,3
    mov ax,t40_ddy
    sar ax,cl
    mov t40_cdr,ax
    mov ax,t40_ddx
    sar ax,cl
    mov t40_cdc,ax
    mov ax,t40_sy
    add ax,t40_ddy
    jge tlj5
    jmp tal_no
tlj5:
    sar ax,cl
    mov t40_cpr0,ax
    mov ax,t40_ey
    add ax,t40_ddy
    cmp ax,T40_H
    jle tlj6
    jmp tal_no
tlj6:
    sar ax,cl
    mov t40_cpr1,ax
    mov ax,t40_sx
    add ax,t40_ddx
    jge tlj7
    jmp tal_no
tlj7:
    sar ax,cl
    mov t40_cpc0,ax
    mov ax,t40_ex
    add ax,t40_ddx
    cmp ax,T40_W
    jle tlj8
    jmp tal_no
tlj8:
    sar ax,cl
    mov t40_cpc1,ax
    mov ax,t40_cpr0             ; interior rows cpr0+1 .. cpr1-2
    add ax,2
    cmp ax,t40_cpr1
    jl tlj9
    jmp tal_no
tlj9:
    mov ax,t40_cpc0
    add ax,2
    cmp ax,t40_cpc1
    jl tlj10
    jmp tal_no
tlj10:
    mov t40_cpv,1
tal_no:
    ret
t40_aligned endp

; t40_cpcell: BX = source cell (t40_cy, t40_cx). If its destination is an
; interior cell, the destination takes its two slots, kept state and text
; (logical and, if shown, video) and CF=1; else CF=0. DS = ES = _T40.
; Preserves BX. Clobbers AX, CX, DX, SI, DI.
t40_cpcell proc near
    mov ax,t40_cy
    add ax,t40_cdr
    mov dx,t40_cpr0
    inc dx
    cmp ax,dx
    jge tlj11
    jmp tcp_no
tlj11:
    mov dx,t40_cpr1
    dec dx
    cmp ax,dx
    jl tlj12
    jmp tcp_no
tlj12:
    mov dx,ax                   ; DX = destination row
    mov ax,t40_cx
    add ax,t40_cdc
    mov cx,t40_cpc0
    inc cx
    cmp ax,cx
    jge tlj13
    jmp tcp_no
tlj13:
    mov cx,t40_cpc1
    dec cx
    cmp ax,cx
    jl tlj14
    jmp tcp_no
tlj14:
    push dx
    mov cx,ax                   ; CX = destination column
    mov ax,dx
    t40_x40
    add ax,cx
    mov di,ax                   ; DI = destination cell
    pop dx
    mov al,t40_vst[bx]
    mov t40_vst[di],al
    mov al,t40_vat[bx]
    mov t40_vat[di],al
    push di
    push bx
    mov si,bx
    t40_slotof si
    t40_slotof di
    mov ax,[si]
    mov [di],ax
    mov ax,[si+2]
    mov [di+2],ax
    mov ax,[si+4]
    mov [di+4],ax
    mov ax,[si+6]
    mov [di+6],ax
    pop bx
    pop di
    push es
    mov si,bx
    shl si,1
    shl di,1
    mov ax,T40_LSEG
    mov es,ax
    mov ax,es:[si]              ; the source cell's text
    mov es:[di],ax
  if T40_PANNED
    sub dx,t40_vtop             ; and the screen, if the row is shown
    jb tcp_hidden
    cmp dx,T40_VISROWS
    jae tcp_hidden
    sub di,t40_voff
    mov si,T40_VSEG
    mov es,si
    mov es:[di],ax
tcp_hidden:
  endif
    pop es
    stc
    ret
tcp_no:
    clc
    ret
t40_cpcell endp

; t40_ring: the flush that follows an aligned copy (t40_cpv = 1, from
; t40_present; DS = _T40). If it is the destination rectangle exactly, only
; its outer ring of cells is presented, as four strips; otherwise an
; ordinary present. Either way the copy is consumed.
t40_ring proc near
    mov t40_cpv,0
    mov si,t40_cpr0             ; SI: free here (t40_present set DS with it)
    shl si,1
    shl si,1
    shl si,1
    cmp ax,si
    jne trg_plain
    mov si,t40_cpr1
    shl si,1
    shl si,1
    shl si,1
    cmp bx,si
    jne trg_plain
    cmp cx,t40_cpc0
    jne trg_plain
    cmp dx,t40_cpc1
    jne trg_plain
    mov ax,t40_cpr0             ; top strip
    shl ax,1
    shl ax,1
    shl ax,1
    mov bx,ax
    add bx,8
    mov cx,t40_cpc0
    mov dx,t40_cpc1
    call t40_present
    mov ax,t40_cpr1             ; bottom strip
    shl ax,1
    shl ax,1
    shl ax,1
    mov bx,ax
    sub ax,8
    mov cx,t40_cpc0
    mov dx,t40_cpc1
    call t40_present
    call trg_rows               ; left strip
    mov cx,t40_cpc0
    mov dx,cx
    inc dx
    call t40_present
    call trg_rows               ; right strip
    mov dx,t40_cpc1
    mov cx,dx
    dec cx
    call t40_present
    ret
trg_plain:
    jmp tpr_go
; AX..BX = the rows between the top and bottom strips
trg_rows:
    mov ax,t40_cpr0
    inc ax
    shl ax,1
    shl ax,1
    shl ax,1
    mov bx,t40_cpr1
    dec bx
    shl bx,1
    shl bx,1
    shl bx,1
    ret
t40_ring endp

; ---- t40_save --------------------------------------------------------------
t40_save proc near
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    push ax
    mov ax,seg t40_slot
    mov ds,ax
    pop ax
    mov t40_snv,0
    cmp ax,0
    jge tsn_top
    xor ax,ax
tsn_top:
    cmp bx,T40_H
    jle tsn_bottom
    mov bx,T40_H
tsn_bottom:
    cmp cx,0
    jge tsn_left
    xor cx,cx
tsn_left:
    cmp dx,T40_COLS
    jle tsn_right
    mov dx,T40_COLS
tsn_right:
    cmp ax,bx
    jl tsn_rows
    jmp tsn_done
tsn_rows:
    cmp cx,dx
    jl tsn_cols
    jmp tsn_done
tsn_cols:
    mov t40_sy0,ax
    mov t40_sy1,bx
    mov t40_sx0,cx
    mov t40_sx1,dx
    sub dx,cx
    mov t40_snc,dx
    mov ax,bx
    sub ax,t40_sy0
    mul t40_snc                 ; rows * bytes <= 200 * 80
    cmp ax,T40_SNAPB/4
    ja tsn_done
    mov t40_snv,1
    mov bx,t40_snc
    mov dx,t40_sy0              ; DX = row
    xor di,di
    cld
tsn_row:
    push dx
    mov ax,dx
    t40_rowes                   ; ES:AX = the row (in its band)
    pop dx
    add ax,t40_sx0
    mov si,ax
    push ds
    push es
    pop ds                      ; DS:SI = shadow row
    mov ax,T40_SNSEG
    mov es,ax                   ; ES:DI = snapshot
    mov cx,bx
    push si
    rep movsb
    pop si
    add si,T40_COLS
    mov cx,bx
    push si
    rep movsb
    pop si
    add si,T40_COLS
    mov cx,bx
    push si
    rep movsb
    pop si
    add si,T40_COLS
    mov cx,bx
    push si
    rep movsb
    pop si
    pop ds
    inc dx
    cmp dx,t40_sy1
    jb tsn_row
tsn_done:
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
t40_save endp

; ---- t40_changed: CF=1 if cell t40_dcy/t40_dcx lies in the snapshot's
; columns and one of its bytes within the snapshot's rows differs from it.
; DS = _T40. Clobbers AX-DI, ES; restores DS.
t40_changed proc near
    mov ax,t40_dcx
    cmp ax,t40_sx0
    jge tch2_in0
    jmp tch2_same
tch2_in0:
    cmp ax,t40_sx1
    jl tch2_in1
    jmp tch2_same
tch2_in1:
    mov ax,t40_dcy              ; rows max(sy0, 8cy) .. min(sy1, 8cy+8)
    mov cl,3
    shl ax,cl
    mov bx,ax
    add bx,8
    cmp ax,t40_sy0
    jge tch2_ya
    mov ax,t40_sy0
tch2_ya:
    cmp bx,t40_sy1
    jle tch2_yb
    mov bx,t40_sy1
tch2_yb:
    sub bx,ax
    jg tch2_rows
    jmp tch2_same
tch2_rows:
    push bx                     ; rows
    push ax                     ; first row
    t40_rowes                   ; ES:DI = first row, this column (the
    add ax,t40_dcx              ; cell's rows are in one band)
    mov di,ax
    pop ax                      ; SI = (first row - sy0) * 4 * nc + column - sx0
    sub ax,t40_sy0
    shl ax,1
    shl ax,1
    mul t40_snc
    add ax,t40_dcx
    sub ax,t40_sx0
    mov si,ax
    pop cx                      ; rows
    mov bx,t40_snc
    push ds
    mov ax,T40_SNSEG
    mov ds,ax
tch2_row:
    mov al,[si]
    cmp al,es:[di]
    jne tch2_diff
    mov al,[bx+si]
    cmp al,es:[di+T40_COLS]
    jne tch2_diff
    add si,bx
    mov al,[bx+si]
    cmp al,es:[di+2*T40_COLS]
    jne tch2_diff
    add si,bx
    mov al,[bx+si]
    cmp al,es:[di+3*T40_COLS]
    jne tch2_diff
    add si,bx
    add si,bx                   ; next snapshot row
    add di,T40_ROWB
    loop tch2_row
    pop ds
tch2_same:
    clc
    ret
tch2_diff:
    pop ds
    stc
    ret
t40_changed endp

; ---- t40_pdiff -------------------------------------------------------------
t40_pdiff proc near
    mov si,seg t40_slot
    mov ds,si
    cmp t40_snv,0
    je tpd_full
    mov t40_snv,0
    cmp ax,t40_sy0
    jne tpd_full
    cmp bx,t40_sy1
    jne tpd_full
    cmp cx,t40_sx0
    jne tpd_full
    cmp dx,t40_sx1
    je tpd_go
tpd_full:
    jmp t40_present
tpd_go:
    mov t40_cpv,0
    ; output range: as t40_present
    mov si,cx
    mov cl,3
    shr ax,cl
    sub ax,1
    jge tpd_r0
    xor ax,ax
tpd_r0:
    mov t40_dr0,ax
    dec bx
    shr bx,cl
    add bx,1
    cmp bx,T40_NROWS-1
    jle tpd_r1
    mov bx,T40_NROWS-1
tpd_r1:
    mov t40_dr1,bx
    sub si,1
    jge tpd_c0
    xor si,si
tpd_c0:
    mov t40_dc0,si
    cmp dx,T40_COLS-1
    jle tpd_c1
    mov dx,T40_COLS-1
tpd_c1:
    mov t40_dc1,dx
    mov ax,t40_dr0
    mov t40_dcy,ax
tpd_row:
    mov t40_drun,-1
    mov ax,t40_dc0
    mov t40_dcx,ax
tpd_col:
    ; need = column <= c1 and (stale or changed)
    mov ax,t40_dcx
    cmp ax,t40_dc1
    jle tpd_inside
    jmp tpd_no
tpd_inside:
    mov ax,t40_dcy
    t40_x40
    add ax,t40_dcx
    mov bx,ax
    test t40_vst[bx],80h
    jz tpd_cmp
    jmp tpd_yes
tpd_cmp:
    call t40_changed
    jnc tpd_no
    jmp tpd_yes
tpd_no:
    cmp t40_drun,0
    jl tpd_next
    ; close the run: present its cells' full pixel rows
    mov ax,t40_dcy
    mov cl,3
    shl ax,cl
    mov bx,ax
    add bx,8
    mov cx,t40_drun
    mov dx,t40_dcx
    call t40_present
    mov si,seg t40_slot
    mov ds,si
    mov t40_drun,-1
    jmp short tpd_next
tpd_yes:
    cmp t40_drun,0
    jge tpd_next
    mov ax,t40_dcx
    mov t40_drun,ax
tpd_next:
    inc t40_dcx
    mov ax,t40_dc1
    inc ax
    cmp t40_dcx,ax
    jg tpd_rowend
    jmp tpd_col
tpd_rowend:
    inc t40_dcy
    mov ax,t40_dcy
    cmp ax,t40_dr1
    jg tpd_done
    jmp tpd_row
tpd_done:
    ret
t40_pdiff endp

; ---- t40_add ---------------------------------------------------------------
t40_add proc near
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    mov di,seg t40_slot
    mov ds,di
    cmp ax,-4
    jl ta_out
    cmp ax,T40_W-4
    jge ta_out
    cmp bx,-4
    jl ta_out
    cmp bx,T40_H-4
    jl ta_in
ta_out:
    jmp ta_done
ta_in:
    mov t40_ax,ax
    mov t40_ay,bx
    push dx                     ; DL = code
    call t40_gfind              ; first: it may reset every hint
    mov t40_gidx,ax
    mov ax,bx                   ; cell = ((y+4)>>3)*T40_COLS + ((x+4)>>3)
    add ax,4
    mov cl,3
    shr ax,cl
    t40_x40
    mov di,t40_ax
    add di,4
    mov cl,3
    shr di,cl
    add ax,di
    mov t40_acell,ax
    mov bx,t40_ay               ; packed position: 80h | dy<<3 | dx
    add bx,4
    and bx,7
    shl bl,1
    shl bl,1
    shl bl,1
    mov cx,t40_ax
    add cx,4
    and cx,7
    or bl,cl
    or bl,80h
    t40_slotof ax
    mov di,ax
    pop dx
    test byte ptr [di],80h
    jz ta_write                 ; no hint here yet
    cmp [di],bl
    je ta_write                 ; same place: the newer replaces
ta_push:
    mov ax,[di]
    mov [di+4],ax
    mov ax,[di+2]
    mov [di+6],ax
ta_write:
    mov [di],bl
    mov ax,t40_gidx
    mov [di+1],ax
    mov [di+3],dl
    mov bx,t40_acell            ; mark the cell stale: re-verify it at the
    or t40_vst[bx],80h          ; next flush whose output range holds it
ta_done:
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
t40_add endp

; ---- t40_blit ----------------------------------------------------------------
t40_blit proc near
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    push ax
    mov ax,seg t40_slot
    mov ds,ax
    mov es,ax
    pop ax
    mov t40_sx,ax
    mov t40_sy,bx
    add ax,cx
    mov t40_ex,ax
    add bx,dx
    mov t40_ey,bx
    mov t40_ddx,si
    mov t40_ddy,di
    mov t40_cpv,0
    mov ax,si
    or ax,di
    jnz tb_moves
    jmp tb_done                 ; identity copy: nothing moves
tb_moves:
    call t40_aligned            ; TEXT80: whole-cell copy? (t40_cpv)
    ; rows bottom-up when moving down, columns right-to-left when moving right
    xor ax,ax
    mov bx,1
    cmp di,0
    jle tb_rdir
    mov ax,T40_NROWS-1
    mov bx,-1
tb_rdir:
    mov t40_cy,ax
    mov t40_ny,bx
tb_row:
    xor ax,ax
    mov bx,1
    cmp t40_ddx,0
    jle tb_cdir
    mov ax,T40_COLS-1
    mov bx,-1
tb_cdir:
    mov t40_cx,ax
    mov t40_nx,bx
tb_col:
    mov ax,t40_cy
    t40_x40
    add ax,t40_cx
    mov bx,ax
    cmp t40_cpv,0
    je tb_hints
    call t40_cpcell             ; CF=1: an interior destination, copied
    jnc tb_hints
    jmp tb_next
tb_hints:
    mov di,bx
    t40_slotof di
    call t40_unpack             ; both slots, unpacked, newest first
    xor si,si
tb_snap0:
    mov al,t40_xs[si]
    mov t40_snap[si],al
    inc si
    cmp si,14
    jb tb_snap0
    add di,4
    call t40_unpack
    xor si,si
tb_snap1:
    mov al,t40_xs[si]
    mov t40_snap[si+14],al
    inc si
    cmp si,14
    jb tb_snap1
    mov di,14
    call t40_blit_one
    xor di,di
    call t40_blit_one
tb_next:
    mov ax,t40_nx
    add t40_cx,ax
    mov ax,t40_cx
    cmp ax,0
    jl tb_row_done
    cmp ax,T40_COLS-1
    jle tb_col
tb_row_done:
    mov ax,t40_ny
    add t40_cy,ax
    mov ax,t40_cy
    cmp ax,0
    jl tb_done
    cmp ax,T40_NROWS-1
    jg tb_done
    jmp tb_row
tb_done:
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
t40_blit endp

; DI = 0 or 14: snapshot slot to re-add if wholly inside the source.
t40_blit_one proc near
    cmp byte ptr t40_snap[di+13],0
    je tbo_done
    mov ax,word ptr t40_snap[di]
    cmp ax,t40_sx
    jl tbo_done
    add ax,8
    cmp ax,t40_ex
    jg tbo_done
    mov bx,word ptr t40_snap[di+2]
    cmp bx,t40_sy
    jl tbo_done
    add bx,8
    cmp bx,t40_ey
    jg tbo_done
    sub ax,8
    sub bx,8
    add ax,t40_ddx
    add bx,t40_ddy
    lea si,t40_snap[di+4]
    mov dl,byte ptr t40_snap[di+12]
    call t40_add
tbo_done:
    ret
t40_blit_one endp

; ---- t40_reset ---------------------------------------------------------------
t40_reset proc near
    push ax
    push cx
    push di
    push es
    mov ax,seg t40_slot
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,T40_CLRB/2           ; slots, t40_vst, t40_vat, dictionary use
    cld
    rep stosw
    mov es:t40_cpv,0            ; no aligned copy pending
    pop es
    pop di
    pop cx
    pop ax
    ret
t40_reset endp
