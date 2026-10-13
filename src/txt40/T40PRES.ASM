; T40PRES.ASM - TXT40/TEXT80 presenter: TR5 shadow pixels -> text cells.
; Specification: src/txt40/T40MODEL.PY (Presenter). MASM 5.1, 8086 only.
;
; This is a fragment. T40PATCH.PY inserts it into the driver's code
; segment; T40TEST.PY assembles the same bytes into a DOS harness. The
; includer provides:
;   segment _T40 holding the T40DATA.ASM fragment (t40_slot at offset 0)
;   T40_SHSEG  text equate: segment value of the shadow (shadow at offset 0)
;   T40_VSEG   text equate: segment value of the text buffer (B800h)
; Entry points (near; all preserve CS/SS/SP and BP):
;   t40_present AX=first row, BX=end row, CX=first byte, DX=end byte;
;               clamped and non-empty. Clobbers AX-DI, DS, ES.
;   t40_add     AX=x, BX=y, ES:SI=8 glyph rows, DL=CP437 code. Preserves all.
;   t40_blit    AX=src x, BX=src y, CX=width, DX=height, SI=dx, DI=dy.
;               Preserves all.
;   t40_reset   forget every hint. Preserves all.
; Geometry equates (T40_COLS, T40_ROWS, T40_SLOTB and those derived from
; them) come from T40DATA.ASM; with none given, 40x25 as TXT40 has always
; been, assembling to the same bytes.
; Slot (T40_SLOTB = 16 or 14 bytes): +0 x, +2 y, +4 glyph rows 0-7, +12
; code, +13 valid. Cell k owns slots at k*T40_CELLB (newest) and
; k*T40_CELLB+T40_SLOTB.

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

; reg = reg * T40_CELLB (cell -> its first slot). Clobbers CL; with 14-byte
; slots also t40_tmp. reg must not be CX.
t40_slotof macro reg
  if T40_SLOTB eq 16
    mov cl,5
    shl reg,cl
  else
    mov cl,2
    shl reg,cl
    mov t40_tmp,reg
    mov cl,3
    shl reg,cl
    sub reg,t40_tmp
  endif
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

; ---- t40_rowbits: AX = pixel row (on screen). t40_v[p] = the 8 pixels of
; plane p starting at x = t40_x (t40_b0 = x sar 3, t40_sh = x and 7);
; off-screen columns read as 0. ES = shadow. Preserves BX-DI.
t40_rowbits proc near
    push bx
    push cx
    push dx
    push di
    mov cx,T40_ROWB
    mul cx
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
    mov si,bx
    t40_slotof si
    cmp byte ptr [si+13],0
    je ts_second
    call t40_verify
    jc ts_second
    mov t40_vat[bx],al
    mov t40_vst[bx],1
    ret
ts_second:
    add si,T40_SLOTB
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
    add di,T40_SLOTB
tcf_slot:
    mov ax,[di]
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
    sub ax,[di+2]
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
    or al,al
    jz tc_approx
    mov di,bx
    t40_slotof di
    cmp al,1
    je tc_own
    add di,T40_SLOTB
tc_own:
    mov al,[di+12]
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
    cmp t40_cy,T40_ROWS-1
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
    mov ax,t40_cy
    t40_x1280
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
    mov si,T40_SHSEG
    mov es,si
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
    cmp bx,T40_ROWS-1
    jle tpr_r1
    mov bx,T40_ROWS-1
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
    mov si,bx
    t40_slotof si
    call t40_touch
    jc tpr_verify
    add si,T40_SLOTB
    call t40_touch
    jnc tpr_kept
tpr_verify:
    call t40_shown
tpr_kept:
    inc t40_cx
    mov ax,t40_cx
    cmp ax,t40_c1
    jle tpr_vcol
    inc t40_cy
    mov ax,t40_cy
    cmp ax,t40_r1
    jle tpr_vrow
    ; output range
    mov ax,t40_r0
    mov t40_cy,ax
tpr_orow:
    mov ax,t40_c0
    mov t40_cx,ax
tpr_ocol:
    call t40_cell
    push ax
    mov ax,t40_cy
    t40_x40
    add ax,t40_cx
    shl ax,1
    mov di,ax
    pop ax
    mov si,T40_VSEG
    mov es,si
    mov es:[di],ax
    mov si,T40_SHSEG
    mov es,si
    inc t40_cx
    mov ax,t40_cx
    cmp ax,t40_c1
    jle tpr_ocol
    inc t40_cy
    mov ax,t40_cy
    cmp ax,t40_r1
    jle tpr_orow
    ret
t40_present endp

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
    push dx
    mov ax,bx
    add ax,4
    mov cl,3
    shr ax,cl
    t40_x40
    mov di,t40_ax
    add di,4
    mov cl,3
    shr di,cl
    add ax,di
  if T40_SLOTB ne 16
    mov t40_acell,ax
  endif
    t40_slotof ax
    mov di,ax
    pop dx
    cmp byte ptr [di+13],0
    je ta_write
    mov ax,[di]
    cmp ax,t40_ax
    jne ta_push
    mov ax,[di+2]
    cmp ax,t40_ay
    je ta_write
ta_push:
    mov cx,T40_SLOTB/2
    xor bx,bx
ta_copy:
    mov ax,[bx+di]
    mov [bx+di+T40_SLOTB],ax
    add bx,2
    loop ta_copy
ta_write:
    mov ax,t40_ax
    mov [di],ax
    mov ax,t40_ay
    mov [di+2],ax
    mov cx,8
    xor bx,bx
ta_glyph:
    mov al,es:[bx+si]
    mov [bx+di+4],al
    inc bx
    loop ta_glyph
    mov [di+12],dl
    mov byte ptr [di+13],1
  if T40_SLOTB eq 16
    mov bx,di                   ; mark the cell stale: re-verify it at the
    mov cl,5                    ; next flush whose output range holds it
    shr bx,cl
  else
    mov bx,t40_acell
  endif
    or t40_vst[bx],80h
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
    mov ax,si
    or ax,di
    jnz tb_moves
    jmp tb_done                 ; identity copy: nothing moves
tb_moves:
    ; rows bottom-up when moving down, columns right-to-left when moving right
    xor ax,ax
    mov bx,1
    cmp di,0
    jle tb_rdir
    mov ax,T40_ROWS-1
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
    t40_slotof ax
    mov si,ax
    xor bx,bx
tb_snap:
    mov ax,[bx+si]
    mov word ptr t40_snap[bx],ax
    add bx,2
    cmp bx,T40_CELLB
    jb tb_snap
    mov di,T40_SLOTB
    call t40_blit_one
    xor di,di
    call t40_blit_one
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
    cmp ax,T40_ROWS-1
    jle tb_row
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

; DI = 0 or T40_SLOTB: snapshot slot to re-add if wholly inside the source.
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
    mov cx,T40_NCELL*(T40_CELLB+2)/2 ; slots, t40_vst and t40_vat
    cld
    rep stosw
    pop es
    pop di
    pop cx
    pop ax
    ret
t40_reset endp
