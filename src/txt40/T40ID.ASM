; T40ID.ASM - check that a CGA-compatible colour text adapter is present for
; TXT40.DRV and report the BIOS video state. MASM 5.1, .8086 only. COM.
; See ../../docs/TXT40.MD.
;
; 1. Records the BIOS video mode (40:49h) and columns (40:4Ah) as found, so
;    a run straight after Windows exits shows whether the driver restored a
;    text mode.
; 2. Records the equipment word's initial video bits (40:10h bits 5-4):
;    01 = 40x25 colour, 10 = 80x25 colour, 11 = monochrome.
; 3. Sets mode 01h with blink off (3D8h = 08h, as the driver does), writes a
;    character and attribute at B800:0000 and B800:07CEh (last cell) and
;    reads them back.
; 4. Restores mode 03h, appends one line to T40ID.TXT and prints it.
;
; Exit 0 only when the adapter is colour (01 or 10) and both cells read back
; (TEXT40=01); exit 1 otherwise.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

f_out   db 'T40ID.TXT',0
line    db 'MODE_BEFORE='
h_mode  db '00 COLS='
h_cols  db '0000 EQUIP_VIDEO='
h_eq    db '00 CELLS='
h_cell  db '00 TEXT40='
h_ok    db '00 COMPLETE=1',13,10
line_len equ $-line
        db '$'

hexd    db '0123456789ABCDEF'

; AL -> two hex digits at [DI]
hex8 proc near
    push ax
    push bx
    mov bx,offset hexd
    mov ah,al
    shr al,1
    shr al,1
    shr al,1
    shr al,1
    xlat
    mov [di],al
    mov al,ah
    and al,0fh
    xlat
    mov [di+1],al
    pop bx
    pop ax
    ret
hex8 endp

start:
    push cs
    pop ds
    xor ax,ax
    mov es,ax
    mov al,es:[449h]
    mov di,offset h_mode
    call hex8
    mov ax,es:[44ah]
    push ax
    mov al,ah
    mov di,offset h_cols
    call hex8
    pop ax
    mov di,offset h_cols+2
    call hex8
    mov al,es:[410h]
    mov cl,4
    shr al,cl
    and al,3
    mov bp,ax
    mov di,offset h_eq
    call hex8

    mov ax,1
    int 10h
    mov dx,3d8h
    mov al,08h
    out dx,al
    mov ax,0b800h
    mov es,ax
    mov word ptr es:[0000h],0F454h
    mov word ptr es:[07ceh],01F34h
    xor si,si
    cmp word ptr es:[0000h],0F454h
    jne cells_done
    cmp word ptr es:[07ceh],01F34h
    jne cells_done
    inc si
cells_done:
    mov ax,si
    mov di,offset h_cell
    call hex8
    mov ax,3
    int 10h

    xor ax,ax
    or si,si
    jz verdict
    mov bx,bp
    cmp bl,1
    je colour
    cmp bl,2
    jne verdict
colour:
    inc ax
verdict:
    mov di,offset h_ok
    call hex8
    push ax

    mov dx,offset f_out
    mov ax,3d01h
    int 21h
    jnc opened
    mov dx,offset f_out
    mov ah,3ch
    xor cx,cx
    int 21h
    jc show
opened:
    mov bx,ax
    mov ax,4202h
    xor cx,cx
    xor dx,dx
    int 21h
    mov dx,offset line
    mov cx,line_len
    mov ah,40h
    int 21h
    mov ah,3eh
    int 21h
show:
    mov dx,offset line
    mov ah,9
    int 21h
    pop ax
    mov ah,4ch
    xor al,1
    int 21h

code ends
end entry
