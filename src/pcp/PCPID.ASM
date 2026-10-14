; PCPID.ASM - identify a Plantronics ColorPlus-class card and report the
; BIOS video state. MASM 5.1 syntax, .8086 only. Build as a COM (org 100h).
; See ../../docs/PCP.MD.
;
; 1. Records the BIOS video mode (40:49h) and column count (40:4Ah) as found,
;    so a run straight after Windows exits shows whether the driver restored
;    a text mode.
; 2. Sets INT 10h mode 04h and port 3DDh = 10h (ColorPlus 320x200x16), then
;    writes different bytes at B800:0000/0001 and B800:4000/4001 and reads
;    them back. A ColorPlus has 32KB with two separate 16KB planes; a plain
;    16KB CGA mirrors 0000h at 4000h, so the first bytes are overwritten.
; 3. With 3DDh = 0 the card must behave as a plain CGA again: a byte written
;    at B800:4000 must appear at B800:0000.
; 4. Restores 3DDh = 0 and mode 03h, appends one line to PCPID.TXT in the
;    current directory and prints it.
;
; Exit 0 only when both 2 and 3 hold (COLORPLUS=01); exit 1 otherwise.
; Port 3DDh is write-only, so the card is judged only by its memory.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

f_out   db 'PCPID.TXT',0
line    db 'MODE_BEFORE='
h_mode  db '00 COLS='
h_cols  db '0000 SPLIT='
h_r0    db '00'
        db ','
h_r1    db '00'
        db ','
h_r2    db '00'
        db ','
h_r3    db '00 OFF_ALIAS='
h_off   db '00 COLORPLUS='
h_cp    db '00 COMPLETE=1',13,10
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

    mov ax,4
    int 10h
    mov dx,3ddh
    mov al,10h
    out dx,al
    mov ax,0b800h
    mov es,ax
    mov byte ptr es:[0000h],5ah
    mov byte ptr es:[0001h],33h
    mov byte ptr es:[4000h],0a5h
    mov byte ptr es:[4001h],0cch
    mov al,es:[0000h]
    mov bl,al
    mov di,offset h_r0
    call hex8
    mov al,es:[0001h]
    mov bh,al
    mov di,offset h_r1
    call hex8
    mov al,es:[4000h]
    mov cl,al
    mov di,offset h_r2
    call hex8
    mov al,es:[4001h]
    mov ch,al
    mov di,offset h_r3
    call hex8
    xor si,si
    cmp bx,335ah
    jne split_done
    cmp cx,0cca5h
    jne split_done
    inc si
split_done:

    mov dx,3ddh
    xor al,al
    out dx,al
    mov byte ptr es:[0000h],11h
    mov byte ptr es:[4000h],22h
    mov al,es:[0000h]
    xor bp,bp
    cmp al,22h
    jne off_done
    inc bp
off_done:
    mov ax,bp
    mov di,offset h_off
    call hex8

    mov ax,3
    int 10h

    xor ax,ax
    or si,si
    jz verdict
    or bp,bp
    jz verdict
    inc ax
verdict:
    mov di,offset h_cp
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
