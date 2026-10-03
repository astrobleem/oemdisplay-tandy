; No display character is ever read into the canonical bitmap.
; This presenter quantizes each changed 8x8 tile independently.
public TxInit
TxInit proc far
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    ; IBM-compatible CGA ROM glyphs 0..127. Later validation dumps this table.
    push ds
    pop es
    mov di,offset tx_font
    mov ax,0f000h
    mov ds,ax
    mov si,0fa6eh
    mov cx,1024
    cld
    rep movsb
    push es
    pop ds
    mov di,offset tx_heads
    mov al,255
    mov cx,384
    rep stosb
    mov dx,32
 txi_char:
    mov si,dx
    shl si,1
    shl si,1
    shl si,1
    add si,offset tx_font
    xor bl,bl
    mov cx,8
 txi_hash:
    xor bl,[si]
    inc si
    loop txi_hash
    xor bh,bh
    mov al,tx_heads[bx]
    mov si,dx
    mov tx_links[si],al
    mov tx_heads[bx],dl
    inc dx
    cmp dx,127
    jb txi_char
    mov tx_first,1
    mov di,offset tx_overlay
    xor ax,ax
    mov cx,2000
    rep stosw
    mov ax,seg tx_cache
    mov es,ax
    xor di,di
    mov ax,0ffffh
    mov cx,8000
    rep stosw
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    retf
TxInit endp

; DS=data. Return AX=character/attribute. Hash probes only exact ASCII shapes.
TxMatch proc near
    xor bx,bx
    xor si,si
    mov cx,8
 txm_hash:
    xor bl,tx_tile[si]
    inc si
    loop txm_hash
    mov dl,tx_heads[bx]
 txm_chain:
    cmp dl,255
    je txm_fallback
    xor dh,dh
    mov si,dx
    shl si,1
    shl si,1
    shl si,1
    add si,offset tx_font
    mov al,[si]
    xor al,tx_tile
    cmp al,0
    je txm_compare
    cmp al,255
    jne txm_next
 txm_compare:
    mov tx_inverse,al
    xor di,di
    mov cx,8
 txm_compare_row:
    mov al,[si]
    xor al,tx_tile[di]
    cmp al,tx_inverse
    jne txm_next
    inc si
    inc di
    loop txm_compare_row
    mov al,dl
    mov ah,07h
    cmp tx_inverse,0
    je txm_return
    mov ah,70h
 txm_return:
    ret
 txm_next:
    mov si,dx
    mov dl,tx_links[si]
    jmp txm_chain
 txm_fallback:
    ; Nine shapes x eight rows, only for changed non-exact tiles.
    mov tx_best,65
    mov si,offset tx_shapes
    mov bp,9
 txm_shape:
    lodsb
    mov tx_char,al
    xor di,di
    xor dx,dx
    mov cx,8
 txm_distance:
    lodsb
    xor al,tx_tile[di]
    xor ah,ah
    mov bx,ax
    mov al,tx_pop[bx]
    xor ah,ah
    add dx,ax
    inc di
    loop txm_distance
    cmp dx,tx_best
    jae txm_continue
    mov tx_best,dx
    mov al,tx_char
    mov tx_attr,al
 txm_continue:
    dec bp
    jnz txm_shape
    mov al,tx_attr
    mov ah,07h
    ret
TxMatch endp

public FlushShadow
FlushShadow proc near
    cmp enabled_flag,0
    jne txf_start
    ret
 txf_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    call cursor_hide
    mov tx_source,0
    mov tx_cachepos,0
    mov tx_screen,0
    mov tx_row,0
    cld
 txf_row:
    mov tx_col,0
 txf_cell:
    mov ax,seg shadow_bits
    mov es,ax
    mov si,tx_source
    xor di,di
    mov cx,8
 txf_gather:
    mov al,es:[si]
    mov tx_tile[di],al
    add si,320
    inc di
    loop txf_gather
    mov ax,seg tx_cache
    mov es,ax
    mov di,tx_cachepos
    xor si,si
    mov dx,tx_first
    mov cx,8
 txf_dirty:
    mov al,tx_tile[si]
    cmp al,es:[di]
    je txf_equal
    mov dl,1
    mov es:[di],al
 txf_equal:
    inc si
    inc di
    loop txf_dirty
    or dl,dl
    jz txf_next
    mov di,tx_screen
    cmp tx_keeptext,0
    je txf_replace
    mov ax,tx_overlay[di]
    or ax,ax
    jnz txf_write
 txf_replace:
    mov word ptr tx_overlay[di],0
    call TxMatch
 txf_write:
    mov bx,0b800h
    mov es,bx
    mov di,tx_screen
    mov es:[di],ax
 txf_next:
    add tx_cachepos,8
    add tx_screen,2
    inc tx_source
    inc tx_col
    cmp tx_col,80
    jae txf_row_end
    jmp txf_cell
 txf_row_end:
    add tx_source,2480
    inc tx_row
    cmp tx_row,25
    jae txf_finish
    jmp txf_row
 txf_finish:
    mov tx_first,0
    call cursor_show
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
FlushShadow endp
