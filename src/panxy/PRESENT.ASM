; Software-only viewport. No CRTC, blanking or hardware-pan registers.
public hp_reset
hp_reset proc far
    push ax
    push ds
    mov ax,seg hp_left
    mov ds,ax
    xor ax,ax
    mov hp_left,ax
    mov hp_top,ax
    mov hp_bytes,ax
    mov hp_enabled,ax
    mov xy_copy_mode,ax
    pop ds
    pop ax
    retf
hp_reset endp
public hp_set
hp_set proc far
    push bx
    push ds
    mov bx,seg hp_left
    mov ds,bx
    or ax,ax
    jns px_xlow
    xor ax,ax
px_xlow:
    cmp ax,320
    jle px_xhigh
    mov ax,320
px_xhigh:
    and ax,0fff8h
    or dx,dx
    jns px_ylow
    xor dx,dx
px_ylow:
    cmp dx,200
    jle px_yhigh
    mov dx,200
px_yhigh:
    and dx,0fffch
    cmp ax,hp_left
    jne px_move
    cmp dx,hp_top
    je px_done
px_move:
    call cursor_hide
    mov hp_left,ax
    mov hp_top,dx
    cmp enabled_flag,0
    je px_show
    call FlushShadow
px_show:
    call cursor_show
px_done:
    mov ax,hp_left
    pop ds
    pop bx
    retf
hp_set endp
public hp_config
hp_config proc far
    ; Software is the only supported mode. There is no fault-injection API.
    xor ax,ax
    retf
hp_config endp
