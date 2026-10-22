; HPAN: all drawing stays in the canonical 640x200 four-plane shadow.
; Presentation is 320x200, with one nonwrapping 8K window per video bank.
; Every entry preserves registers. Cursor exclusion covers each dirty copy.
public FlushShadow,FlushRows,FlushRetainRows,FlushColumns,FlushRetainColumns
FlushShadow proc near
    push ax
    push bx
    xor ax,ax
    mov bx,SCREEN_HEIGHT
    call FlushRows
    pop bx
    pop ax
    ret
FlushShadow endp
FlushRetainRows label near
FlushRows proc near
    push cx
    push dx
    xor cx,cx
    mov dx,SCREEN_W_BYTES
    call FlushColumns
    pop dx
    pop cx
    ret
FlushRows endp
FlushRetainColumns label near
FlushColumns proc near
    cmp enabled_flag,0
    jne hf_live
    ret
hf_live:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bp,sp
    sub sp,16
    cmp ax,0
    jge hf_y0
    xor ax,ax
hf_y0:
    cmp bx,200
    jle hf_y1
    mov bx,200
hf_y1:
    mov ss:[bp-2],ax
    mov ss:[bp-4],bx
    mov ax,hp_left
    shr ax,1
    shr ax,1
    shr ax,1
    mov ss:[bp-10],ax
    cmp cx,ax
    jge hf_x0
    mov cx,ax
hf_x0:
    add ax,40
    cmp dx,ax
    jle hf_x1
    mov dx,ax
hf_x1:
    mov ss:[bp-6],cx
    mov ss:[bp-8],dx
    mov ax,hp_bytes
    mov ss:[bp-12],ax
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jl hf_check_x
    jmp hf_empty
hf_check_x:
    cmp cx,dx
    jl hf_nonempty
    jmp hf_empty
hf_nonempty:
    call cursor_hide
    cld
    mov ax,seg shadow_bits
    mov ds,ax
    mov ax,0b800h
    mov es,ax
hf_row:
    mov ax,ss:[bp-2]
    mov cx,SCREEN_W_BYTES*4
    mul cx
    mov si,ax
    add si,ss:[bp-6]
    mov ax,ss:[bp-2]
    and ax,3
    mov cl,13
    shl ax,cl
    mov di,ax
    mov ax,ss:[bp-2]
    shr ax,1
    shr ax,1
    mov cx,160
    mul cx
    add di,ax
    add di,ss:[bp-12]
    mov ax,ss:[bp-6]
    sub ax,ss:[bp-10]
    shl ax,1
    shl ax,1
    add di,ax
    mov cx,ss:[bp-8]
    sub cx,ss:[bp-6]
hf_group:
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
    inc si
    dec cx
    jz hf_row_done
    jmp hf_group
hf_row_done:
    inc word ptr ss:[bp-2]
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jge hf_finished
    jmp hf_row
hf_finished:
    mov ax,seg hp_left
    mov ds,ax
    call cursor_show
hf_empty:
    mov sp,bp
    pop es
    pop ds
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
FlushColumns endp
