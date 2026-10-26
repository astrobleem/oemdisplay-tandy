; Experimental 640x256 / 320x200 task-time XY presenter.
; LOCAL PROTOTYPE: disjoint exposed strips, 2816-byte stage budget.
; Larger requests retain the guarded full copy. Default is software.
public hp_full
hp_full proc near
    xor ax,ax
    cmp hp_enabled,0
    je xyh_done
    mov ax,hp_top
    shr ax,1
    shr ax,1
    mov cx,160
    mul cx
    mov cx,hp_left
    shr cx,1
    add ax,cx
    and ax,01fffh
xyh_done:
    mov hp_bytes,ax
    shr ax,1
    mov hp_start,ax
    call FlushShadow
    mov hp_last_cols,320
    mov hp_last_bytes,32000
    inc hp_software
    ret
hp_full endp

xy_rectangles proc near
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
xy_rectangles endp
; SI is a descriptor in the driver Data segment.
xy_rect_load proc near
    mov ax,[si]
    mov bx,[si+2]
    mov cx,[si+4]
    mov dx,[si+6]
    ret
xy_rect_load endp

public hp_set
hp_set proc far
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bx,seg hp_left
    mov ds,bx
    or ax,ax
    jns xys_x0
    xor ax,ax
xys_x0:
    cmp ax,320
    jle xys_x1
    mov ax,320
xys_x1:
    and ax,0fff8h
    or dx,dx
    jns xys_y0
    xor dx,dx
xys_y0:
    cmp dx,56
    jle xys_y1
    mov dx,56
xys_y1:
    and dx,0fffch
    cmp ax,hp_left
    jne xys_changed
    cmp dx,hp_top
    xy_need jne,xys_done
xys_changed:
    mov bx,hp_left
    mov hp_old,bx
    mov bx,hp_top
    mov hp_oldtop,bx
    call cursor_hide
    mov bx,ax
    sub bx,hp_left
    mov hp_delta,bx
    mov bx,dx
    sub bx,hp_top
    mov hp_dy,bx
    mov hp_left,ax
    mov hp_top,dx
    cmp enabled_flag,0
    xy_need jne,xys_show
    mov hp_last_cols,0
    mov hp_last_bytes,0
    mov hp_reason,1
    cmp hp_enabled,0
    xy_need jne,xys_full
    mov cx,hp_delta
    or cx,cx
    jns xys_absx
    neg cx
xys_absx:
    mov si,cx
    mov cx,hp_dy
    or cx,cx
    jns xys_absy
    neg cx
xys_absy:
    ; B = 100*abs(dx) + (160-abs(dx)/2)*abs(dy).
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
    ; Absolute head is safe because both coordinates are quantized.
    mov ax,hp_top
    shr ax,1
    shr ax,1
    mov cx,160
    mul cx
    mov cx,hp_left
    shr cx,1
    add ax,cx
    and ax,01fffh
    mov hp_bytes,ax
    shr ax,1
    mov hp_start,ax
    call xy_rectangles
    mov hp_stage_count,0
    mov xy_copy_mode,1
    cmp xy_h,0
    je xys_stage_v
    mov si,offset xy_hr
    call xy_rect_load
    call FlushColumns
xys_stage_v:
    cmp xy_v,0
    je xys_staged
    mov si,offset xy_vr
    call xy_rect_load
    call FlushColumns
xys_staged:
    mov xy_copy_mode,0
    ; Never blank until conversion is complete.
    mov ax,hp_stage_count
    cmp ax,2816
    xy_need jbe,xys_stage_bad
    mov hp_last_bytes,ax
    mov hp_last_cols,8
    ; A pure Y4 step occupies 160 of each bank's 192 offscreen bytes.
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
    cmp xy_h,0
    je xys_commit_v
    mov si,offset xy_hr
    call xy_rect_load
    call xy_commit_rect
xys_commit_v:
    cmp xy_v,0
    je xys_small_done
    mov si,offset xy_vr
    call xy_rect_load
    call xy_commit_rect
xys_small_done:
    mov hp_reason,0
    jmp short xys_present
xys_stage_bad:
    mov hp_enabled,0
    mov hp_reason,5
xys_full:
    call hp_blank
    call hp_full
xys_present:
    mov ax,hp_start
    call hp_present
    jnc xys_presented
    ; The Y4 fast path has not blanked yet. Recovery must own blanking.
    call hp_blank
    mov hp_enabled,0
    mov hp_reason,4
    call hp_full
    xor ax,ax
    call hp_write
xys_presented:
    cmp hp_reason,0
    jne xys_unblank
    inc hp_hardware
xys_unblank:
    call hp_unblank
xys_show:
    call cursor_show
xys_done:
    mov ax,hp_left
    pop es
    pop ds
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    retf
hp_set endp

; Stream at most 12 canonical rows (3840 bytes), no capture allocation.
; PASCAL XYRows(destination FAR*, first WORD, count WORD) -> byte count.
cProc XYRows,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dest
    parmW first
    parmW rows
    localW current
    localW remain
    localW bytes
cBegin
    mov bytes,0
    cmp first,256
    jae xyrows_done
    mov ax,rows
    cmp ax,12
    ja xyrows_done
    or ax,ax
    jz xyrows_done
    add ax,first
    cmp ax,256
    ja xyrows_done
    mov ax,first
    mov current,ax
    mov ax,rows
    mov remain,ax
    les di,dest
    cld
xyrows_next:
    push ds
    mov ax,current
    call xy_row
    mov cx,160
    rep movsw
    pop ds
    add bytes,320
    inc current
    dec remain
    jnz xyrows_next
xyrows_done:
    mov ax,bytes
cEnd
