; HPAN task-time presentation. No allocation, GDI call or logging here.
; Software is default. An 8px hardware strip is converted into a private
; 800-byte buffer before blanking, then committed while display is disabled.
; Other sizes keep the full guarded path. New row tails alias old prefixes.
hp_write proc near
    pushf
    cli
    push ax
    push bx
    push dx
    mov bx,ax
    mov dx,3d4h
    mov al,12
    out dx,al
    inc dx
    mov al,bh
    out dx,al
    dec dx
    mov al,13
    out dx,al
    inc dx
    mov al,bl
    out dx,al
    pop dx
    pop bx
    pop ax
    popf
    ret
hp_write endp
hp_present proc near
    cmp hp_fault,0
    je hp_wait
    mov hp_fault,0
    stc
    ret
hp_wait:
    push ax
    push cx
    push dx
    mov dx,3dah
    mov cx,0ffffh
hp_off:
    in al,dx
    test al,8
    jz hp_on_start
    loop hp_off
    jmp short hp_bad
hp_on_start:
    mov cx,0ffffh
hp_on:
    in al,dx
    test al,8
    jnz hp_ready
    loop hp_on
hp_bad:
    pop dx
    pop cx
    pop ax
    stc
    ret
hp_ready:
    pop dx
    pop cx
    pop ax
    call hp_write
    clc
    ret
hp_present endp
hp_blank proc near
    push ax
    push dx
    mov dx,3d8h
    mov al,byte ptr hp_mode
    and al,0f7h
    out dx,al
    pop dx
    pop ax
    ret
hp_blank endp
hp_unblank proc near
    push ax
    push dx
    mov dx,3d8h
    mov al,byte ptr hp_mode
    out dx,al
    pop dx
    pop ax
    ret
hp_unblank endp
public hp_reset
hp_reset proc far
    push ax
    push ds
    push es
    mov ax,seg hp_left
    mov ds,ax
    xor ax,ax
    mov hp_enabled,ax
    mov hp_bytes,ax
    mov hp_start,ax
    mov hp_left,ax
    mov hp_fault,ax
    mov hp_reason,ax
    mov hp_hardware,ax
    mov hp_software,ax
    mov hp_last_cols,ax
    mov hp_last_bytes,ax
    call hp_write
    mov ax,40h
    mov es,ax
    mov al,es:[65h]
    xor ah,ah
    mov hp_mode,ax
    pop es
    pop ds
    pop ax
    retf
hp_reset endp
; Caller already owns cursor exclusion and the display is blanked.
hp_full proc near
    xor ax,ax
    mov hp_bytes,ax
    mov hp_start,ax
    cmp hp_enabled,0
    je hp_full_copy
    mov ax,hp_left
    shr ax,1
    mov hp_bytes,ax
    shr ax,1
    mov hp_start,ax
hp_full_copy:
    call FlushShadow
    mov hp_last_cols,320
    mov hp_last_bytes,32000
    inc hp_software
    ret
hp_full endp
; Called only with the outer cursor exclusion held. CX is the logical
; eight-pixel column. This conversion changes no video memory or CRTC state.
public hp_stage_strip,hp_commit_strip
hp_stage_strip proc near
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    mov ax,seg hp_stage
    mov es,ax
    mov di,offset hp_stage
    mov ax,seg shadow_bits
    mov ds,ax
    mov si,cx
    mov cx,200
    cld
hss_row:
    mov ah,[si]
    mov bl,[si+80]
    mov bh,[si+160]
    mov dh,[si+240]
    rept 4
      get_nibble
      shl al,1
      shl al,1
      shl al,1
      shl al,1
      mov dl,al
      get_nibble
      or al,dl
      stosb
    endm
    add si,320
    dec cx
    jz hss_done
    jmp hss_row
hss_done:
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
hp_stage_strip endp
; Exactly four staged bytes per row. No shadow conversion while blanked.
; Hardware layout makes each destination bankRowBase + logicalX/2.
hp_commit_strip proc near
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    mov ax,seg hp_stage
    mov ds,ax
    mov si,offset hp_stage
    mov ax,0b800h
    mov es,ax
    xor bx,bx
    cld
hcs_row:
    mov ax,bx
    and ax,3
    mov cl,13
    shl ax,cl
    mov di,ax
    mov ax,bx
    shr ax,1
    shr ax,1
    mov dx,160
    mul dx
    add di,ax
    add di,hp_stage_offset
    movsw
    movsw
    inc bx
    cmp bx,200
    jb hcs_row
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
hp_commit_strip endp

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
    jns hp_low
    xor ax,ax
hp_low:
    cmp ax,320
    jle hp_high
    mov ax,320
hp_high:
    and ax,0fff8h
    cmp ax,hp_left
    jne hp_changed
    jmp hp_done
hp_changed:
    mov bx,hp_left
    mov hp_old,bx
    mov hp_left,ax
    cmp enabled_flag,0
    jne hp_live
    jmp hp_done
hp_live:
    ; Erase using the OLD cursor coordinate transform before changing head.
    mov hp_left,bx
    call cursor_hide
    mov hp_left,ax
    mov hp_last_bytes,0
    mov hp_last_cols,0
    cmp hp_enabled,0
    jne hp_hw
    call hp_blank
    mov hp_reason,1
    call hp_full
    jmp hp_commit
hp_hw:
    mov dx,ax
    sub dx,bx
    mov hp_delta,dx
    mov cx,dx
    or cx,cx
    jns hp_abs
    neg cx
hp_abs:
    cmp cx,8
    jne hp_unstaged
    jmp hp_staged
hp_unstaged:
    call hp_blank
    cmp cx,320
    jb hp_overlap
    mov hp_reason,3
    call hp_full
    jmp hp_commit
hp_overlap:
    mov hp_last_cols,cx
    push ax
    mov ax,cx
    mov si,100
    mul si
    mov hp_last_bytes,ax
    pop ax
    shr ax,1
    mov hp_bytes,ax
    shr ax,1
    mov hp_start,ax
    cmp hp_delta,0
    jl hp_strip_left
    mov cx,hp_old
    add cx,320
    mov dx,hp_left
    add dx,320
    jmp short hp_strip
hp_strip_left:
    mov cx,hp_left
    mov dx,hp_old
hp_strip:
    shr cx,1
    shr cx,1
    shr cx,1
    shr dx,1
    shr dx,1
    shr dx,1
    xor ax,ax
    mov bx,200
    call FlushColumns
    mov hp_reason,0
    jmp hp_commit
hp_staged:
    mov hp_last_cols,8
    mov hp_last_bytes,800
    mov ax,hp_left
    shr ax,1
    mov hp_bytes,ax
    shr ax,1
    mov hp_start,ax
    mov cx,hp_left
    cmp hp_delta,0
    jl hp_stage_x
    mov cx,hp_old
    add cx,320
hp_stage_x:
    shr cx,1
    shr cx,1
    shr cx,1
    mov ax,cx
    shl ax,1
    shl ax,1
    mov hp_stage_offset,ax
    call hp_stage_strip
    call hp_blank
    call hp_commit_strip
    mov hp_reason,0
hp_commit:
    mov ax,hp_start
    call hp_present
    jc hp_recover
    cmp hp_reason,0
    jne hp_show
    inc hp_hardware
    jmp short hp_show
hp_recover:
    mov hp_enabled,0
    mov hp_reason,4
    call hp_full
    xor ax,ax
    call hp_write
hp_show:
    call hp_unblank
    call cursor_show
hp_done:
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
public hp_config
hp_config proc far
    push bx
    push ds
    mov bx,seg hp_left
    mov ds,bx
    cmp ax,2
    jne hpc_mode
    mov hp_fault,1
    jmp short hpc_done
hpc_mode:
    cmp ax,1
    jbe hpc_set
    jmp short hpc_done
hpc_set:
    cmp enabled_flag,0
    je hpc_done
    cmp ax,hp_enabled
    je hpc_done
    call cursor_hide
    call hp_blank
    mov hp_enabled,ax
    call hp_full
    mov ax,hp_start
    call hp_present
    jnc hpc_show
    mov hp_enabled,0
    mov hp_reason,4
    call hp_full
    xor ax,ax
    call hp_write
hpc_show:
    call hp_unblank
    call cursor_show
hpc_done:
    mov ax,hp_enabled
    pop ds
    pop bx
    retf
hp_config endp
cProc HpStats,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dest
cBegin
    les di,dest
    mov si,offset hp_enabled
    mov cx,8
    cld
    rep movsw
    mov ax,1
cEnd
cProc HpShadow,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dest
cBegin
    les di,dest
    push ds
    mov ax,seg shadow_bits
    mov ds,ax
    mov si,offset shadow_bits
    mov cx,32000
    cld
    rep movsw
    pop ds
    mov ax,1
cEnd
