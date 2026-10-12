; T40PRES.ASM - TXT40 presenter: TR5 shadow pixels -> CGA 40x25 text cells.
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
; Slot (16 bytes): +0 x, +2 y, +4 glyph rows 0-7, +12 code, +13 valid.
; Cell k owns slots at k*32 (newest) and k*32+16.

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
    mov cx,160
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
    cmp t40_b0,39
    jge trb_nohi
    mov al,es:[di+1]
trb_nohi:
    shl ax,cl
    mov t40_v[bx],ah
    add di,40
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
; ES = shadow. Preserves BX-DI.
t40_verify proc near
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
    sub ax,312
    jle tv_mask
    mov cl,al
    shl dl,cl
tv_mask:
    mov t40_cm,dl
    mov t40_fg,0FFh
    mov t40_bg,0FFh
    mov t40_r7,0FFh
    xor bx,bx
tv_row:
    mov ax,[si+2]
    add ax,bx
    cmp ax,0
    jge tv_top_ok
    jmp tv_next
tv_top_ok:
    cmp ax,200
    jl tv_on
    jmp tv_next
tv_on:
    call t40_rowbits
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
t40_verify endp

; ---- t40_shown: BX = cell. Sets t40_vst[BX] (0 none, 1/2 slot) and
; t40_vat[BX]. ES = shadow. Preserves BX.
t40_shown proc near
    mov t40_vst[bx],0
    mov si,bx
    mov cl,5
    shl si,cl
    cmp byte ptr [si+13],0
    je ts_second
    call t40_verify
    jc ts_second
    mov t40_vat[bx],al
    mov t40_vst[bx],1
    ret
ts_second:
    add si,16
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
    mov cl,5
    shl di,cl
    cmp t40_vst[bx],1
    je tcf_slot
    add di,16
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

; ---- t40_cell: text word for cell t40_cy/t40_cx in AX. ES = shadow.
t40_cell proc near
    mov ax,t40_cy
    mov cx,40
    mul cx
    add ax,t40_cx
    mov bx,ax
    mov al,t40_vst[bx]
    or al,al
    jz tc_approx
    mov di,bx
    mov cl,5
    shl di,cl
    cmp al,1
    je tc_own
    add di,16
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
    mov ax,t40_cy
    dec ax
    mov t40_ny,ax
tc_ny:
    mov ax,t40_ny
    cmp ax,0
    jl tc_ny_next
    cmp ax,24
    jg tc_ny_next
    mov ax,t40_cx
    dec ax
    mov t40_nx,ax
tc_nx:
    mov ax,t40_nx
    cmp ax,0
    jl tc_nx_next
    cmp ax,39
    jg tc_nx_next
    mov ax,t40_ny
    mov cx,40
    mul cx
    add ax,t40_nx
    mov bx,ax
    cmp t40_vst[bx],0
    je tc_nx_next
    call t40_claim_from
tc_nx_next:
    inc t40_nx
    mov ax,t40_cx
    inc ax
    cmp t40_nx,ax
    jle tc_nx
tc_ny_next:
    inc t40_ny
    mov ax,t40_cy
    inc ax
    cmp t40_ny,ax
    jle tc_ny
    ; live = not claimed; load the cell's plane bytes
    xor si,si
    xor di,di
    mov ax,t40_cy
    mov cx,1280
    mul cx
    add ax,t40_cx
    mov bx,ax
tc_load:
    not t40_live[si]
    mov al,es:[bx]
    mov t40_pl[di],al
    mov al,es:[bx+40]
    mov t40_pl[di+1],al
    mov al,es:[bx+80]
    mov t40_pl[di+2],al
    mov al,es:[bx+120]
    mov t40_pl[di+3],al
    add bx,160
    add di,4
    inc si
    cmp si,8
    jb tc_load
    ; colour counts of live pixels
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

; ---- t40_present ---------------------------------------------------------
; A glyph window spans at most two cell rows and two cell columns, so pixels
; of the dirty cells can change only the dirty cells and one cell around
; them (output range). Shown state is recomputed one cell further (verify
; range) so every output cell sees its whole 3x3 neighbourhood fresh.
t40_present proc near
    mov si,seg t40_slot
    mov ds,si
    mov si,T40_SHSEG
    mov es,si
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
    cmp bx,24
    jle tpr_r1
    mov bx,24
tpr_r1:
    mov t40_r1,bx
    sub si,1
    jge tpr_c0
    xor si,si
tpr_c0:
    mov t40_c0,si
    cmp dx,39
    jle tpr_c1
    mov dx,39
tpr_c1:
    mov t40_c1,dx
    ; verification range: one more cell each way
    mov ax,t40_r0
    dec ax
    jge tpr_vr0
    xor ax,ax
tpr_vr0:
    mov t40_cy,ax
tpr_vrow:
    mov ax,t40_c0
    dec ax
    jge tpr_vc0
    xor ax,ax
tpr_vc0:
    mov t40_cx,ax
tpr_vcol:
    mov ax,t40_cy
    mov cx,40
    mul cx
    add ax,t40_cx
    mov bx,ax
    call t40_shown
    inc t40_cx
    mov ax,t40_c1
    inc ax
    cmp ax,39
    jle tpr_vc1
    mov ax,39
tpr_vc1:
    cmp t40_cx,ax
    jle tpr_vcol
    inc t40_cy
    mov ax,t40_r1
    inc ax
    cmp ax,24
    jle tpr_vr1
    mov ax,24
tpr_vr1:
    cmp t40_cy,ax
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
    mov cx,40
    mul cx
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
    cmp ax,316
    jge ta_out
    cmp bx,-4
    jl ta_out
    cmp bx,196
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
    mov cx,40
    mul cx
    mov di,t40_ax
    add di,4
    mov cl,3
    shr di,cl
    add ax,di
    mov cl,5
    shl ax,cl
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
    mov cx,8
    xor bx,bx
ta_copy:
    mov ax,[bx+di]
    mov [bx+di+16],ax
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
    mov ax,24
    mov bx,-1
tb_rdir:
    mov t40_cy,ax
    mov t40_ny,bx
tb_row:
    xor ax,ax
    mov bx,1
    cmp t40_ddx,0
    jle tb_cdir
    mov ax,39
    mov bx,-1
tb_cdir:
    mov t40_cx,ax
    mov t40_nx,bx
tb_col:
    mov ax,t40_cy
    mov cx,40
    mul cx
    add ax,t40_cx
    mov cl,5
    shl ax,cl
    mov si,ax
    xor bx,bx
tb_snap:
    mov ax,[bx+si]
    mov word ptr t40_snap[bx],ax
    add bx,2
    cmp bx,32
    jb tb_snap
    mov di,16
    call t40_blit_one
    xor di,di
    call t40_blit_one
    mov ax,t40_nx
    add t40_cx,ax
    mov ax,t40_cx
    cmp ax,0
    jl tb_row_done
    cmp ax,39
    jle tb_col
tb_row_done:
    mov ax,t40_ny
    add t40_cy,ax
    mov ax,t40_cy
    cmp ax,0
    jl tb_done
    cmp ax,24
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

; DI = 0 or 16: snapshot slot to re-add if wholly inside the source.
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
    mov cx,16000
    cld
    rep stosw
    pop es
    pop di
    pop cx
    pop ax
    ret
t40_reset endp
