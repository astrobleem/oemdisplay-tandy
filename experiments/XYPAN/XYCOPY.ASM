; Task-time rectangle conversion. AX/BX = logical Y endpoints,
; CX/DX = logical eight-pixel columns. All registers preserved.
; xy_copy_mode=0 presents; =1 appends to the private 2816-byte stage.
xy_need macro condition,failed
local accepted
    condition accepted
    jmp failed
accepted:
endm
public xy_row
; AX logical row -> DS:SI. No offset may cross a band allocation.
xy_row proc near
    push ax
    push dx
    cmp ax,200
    jb xyr_first
    sub ax,200
    mov dx,seg shadow_tail
    jmp short xyr_mul
xyr_first:
    mov dx,seg shadow_bits
xyr_mul:
    mov ds,dx
    mov dx,320
    mul dx
    mov si,ax
    pop dx
    pop ax
    ret
xy_row endp
public FlushShadow,FlushRows,FlushRetainRows,FlushColumns,FlushRetainColumns
FlushShadow proc near
    push ax
    push bx
    xor ax,ax
    mov bx,256
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
    mov dx,80
    call FlushColumns
    pop dx
    pop cx
    ret
FlushRows endp
FlushRetainColumns label near
FlushColumns proc near
    pushf
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
    sub sp,24
    cmp enabled_flag,0
    xy_need jne,xyc_done
    ; Clamp in canonical logical coordinates to the current viewport.
    mov si,hp_top
    cmp ax,si
    jge xyc_y0
    mov ax,si
xyc_y0:
    mov ss:[bp-14],si
    add si,200
    cmp bx,si
    jle xyc_y1
    mov bx,si
xyc_y1:
    mov ss:[bp-2],ax
    mov ss:[bp-4],bx
    mov si,hp_left
    shr si,1
    shr si,1
    shr si,1
    mov ss:[bp-10],si
    cmp cx,si
    jge xyc_x0
    mov cx,si
xyc_x0:
    add si,40
    cmp dx,si
    jle xyc_x1
    mov dx,si
xyc_x1:
    mov ss:[bp-6],cx
    mov ss:[bp-8],dx
    mov si,hp_bytes
    mov ss:[bp-12],si
    mov si,xy_copy_mode
    mov ss:[bp-18],si
    mov si,hp_stage_count
    add si,offset hp_stage
    mov ss:[bp-20],si
    cmp ax,bx
    xy_need jl,xyc_done
    cmp cx,dx
    xy_need jl,xyc_done
    cmp word ptr ss:[bp-18],0
    jne xyc_begin
    call cursor_hide
xyc_begin:
    cld
xyc_row:
    mov ax,ss:[bp-2]
    call xy_row
    add si,ss:[bp-6]
    cmp word ptr ss:[bp-18],0
    je xyc_video
    mov ax,seg hp_stage
    mov es,ax
    mov di,ss:[bp-20]
    jmp short xyc_groups
xyc_video:
    mov ax,0b800h
    mov es,ax
    mov ax,ss:[bp-2]
    sub ax,ss:[bp-14]
    mov di,ax
    and di,3
    mov cl,13
    shl di,cl
    mov ss:[bp-16],di
    shr ax,1
    shr ax,1
    mov cx,160
    mul cx
    add ax,ss:[bp-12]
    mov di,ax
    mov ax,ss:[bp-6]
    sub ax,ss:[bp-10]
    shl ax,1
    shl ax,1
    add di,ax
    and di,01fffh
    or di,ss:[bp-16]
xyc_groups:
    mov cx,ss:[bp-8]
    sub cx,ss:[bp-6]
xyc_group:
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
    cmp word ptr ss:[bp-18],0
    jne xyc_next
    and di,01fffh
    or di,ss:[bp-16]
xyc_next:
    inc si
    dec cx
    jz xyc_row_done
    jmp xyc_group
xyc_row_done:
    mov ss:[bp-20],di
    inc word ptr ss:[bp-2]
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jge xyc_finish
    jmp xyc_row
xyc_finish:
    mov ax,seg hp_left
    mov ds,ax
    cmp word ptr ss:[bp-18],0
    je xyc_show
    mov ax,ss:[bp-20]
    sub ax,offset hp_stage
    mov hp_stage_count,ax
    jmp short xyc_done
xyc_show:
    call cursor_show
xyc_done:
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
    popf
    ret
FlushColumns endp

; Commit the same already-clipped rectangle from staged packed bytes.
; Exactly four bytes/group, masked back into the original 8KiB bank.
xy_commit_rect proc near
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push es
    mov bp,sp
    sub sp,10
    mov ss:[bp-2],ax
    mov ss:[bp-4],bx
    sub dx,cx
    mov ss:[bp-6],dx
    mov ax,hp_left
    shr ax,1
    shr ax,1
    shr ax,1
    sub cx,ax
    shl cx,1
    shl cx,1
    mov ss:[bp-8],cx
    mov si,offset hp_stage
    add si,hp_stage_read
    mov ax,0b800h
    mov es,ax
    cld
xycr_row:
    mov ax,ss:[bp-2]
    sub ax,hp_top
    mov bx,ax
    and bx,3
    mov cl,13
    shl bx,cl
    mov ss:[bp-10],bx
    shr ax,1
    shr ax,1
    mov dx,160
    mul dx
    mov di,ax
    add di,hp_bytes
    add di,ss:[bp-8]
    and di,01fffh
    or di,bx
    mov cx,ss:[bp-6]
xycr_group:
    movsw
    movsw
    and di,01fffh
    or di,ss:[bp-10]
    loop xycr_group
    inc word ptr ss:[bp-2]
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jb xycr_row
    sub si,offset hp_stage
    mov hp_stage_read,si
    mov sp,bp
    pop es
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
xy_commit_rect endp
