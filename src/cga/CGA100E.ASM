    ; BH is the active page returned by the preceding BIOS mode query.
    mov cga_old_page,bh
    mov ah,3
    int 10h
    mov cga_old_shape,cx
    mov cga_old_pos,dx
    mov ax,3
    int 10h
    mov dx,3d8h
    mov al,01h                 ; alpha 80-column clock, video off, no blink
    out dx,al
    ; IBM horizontal 80-column table, vertical 200-line graphics table.
    ; 128 character rows * 2 scanlines + 6 adjust = 262 scanlines/frame.
    ; VSYNC starts at 112 * 2 = 224. No zero-width or undocumented timing.
    mov dx,3d4h
    mov ax,07100h
    out dx,ax
    mov ax,05001h
    out dx,ax
    mov ax,05a02h
    out dx,ax
    mov ax,00a03h
    out dx,ax
    mov ax,07f04h
    out dx,ax
    mov ax,00605h
    out dx,ax
    mov ax,06406h
    out dx,ax
    mov ax,07007h
    out dx,ax
    mov ax,00208h
    out dx,ax
    mov ax,00109h
    out dx,ax
    mov ax,0200ah             ; no hardware text cursor
    out dx,ax
    mov ax,0000bh
    out dx,ax
    mov ax,0000ch
    out dx,ax
    mov ax,0000dh
    out dx,ax
    mov ax,0000eh
    out dx,ax
    mov ax,0000fh
    out dx,ax
    mov dx,3d9h
    xor al,al                 ; black border
    out dx,al
    push ds
    mov ax,40h
    mov ds,ax
    mov byte ptr ds:[65h],09h ; intended enabled mode, bright backgrounds
    pop ds
    mov cga_vram_depth,0
    mov ax,0b800h
    mov es,ax
    xor di,di
    mov ax,00deh
    mov cx,8000                ; initialize every character and attribute
    cld
    rep stosw
    ; Shadow clear and enabled_flag follow; video is enabled only afterward.
