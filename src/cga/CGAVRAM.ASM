; No polling loops or interrupt-masked conversion work. The outermost
; access blanks video; nested cursor calls keep it blank until the end.
; Preserve all registers, segments and FLAGS, including caller IF and DF.
public cga_vram_begin,cga_vram_end
cga_vram_begin proc far
    pushf
    cli
    push ax
    push dx
    push ds
    mov ax,seg cga_vram_depth
    mov ds,ax
    cmp cga_vram_depth,0
    jne cga_vram_nested
    mov dx,3d8h
    mov al,01h
    out dx,al
cga_vram_nested:
    inc cga_vram_depth
    pop ds
    pop dx
    pop ax
    popf
    retf
cga_vram_begin endp
cga_vram_end proc far
    pushf
    cli
    push ax
    push dx
    push ds
    mov ax,seg cga_vram_depth
    mov ds,ax
    cmp cga_vram_depth,0
    je cga_vram_done
    dec cga_vram_depth
    jne cga_vram_done
    mov dx,3d8h
    mov al,09h
    out dx,al
cga_vram_done:
    pop ds
    pop dx
    pop ax
    popf
    retf
cga_vram_end endp
