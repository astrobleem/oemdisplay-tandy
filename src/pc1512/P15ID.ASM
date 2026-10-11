; P15ID.ASM - identify Amstrad PC1512 plane hardware and report BIOS video
; state. MASM 5.1 syntax, .8086 only. Build as a COM (org 100h).
; See ../../docs/PC1512.MD.
;
; 1. Records the BIOS mode (40:49h) and columns (40:4Ah) as found, so a run
;    straight after Windows exits shows whether a text mode was restored.
; 2. Sets ROS mode 6 and 3D9h = 0Fh, then writes 11h/22h/44h/88h at B800:0000
;    with the plane write mask (3DDh) set to blue/green/red/intensity only,
;    and reads each plane back through 3DEh = 0..3. A PC1512 returns
;    11,22,44,88; a plain CGA, which ignores both ports, returns 88 four times.
; 3. With 3DDh = 0Fh one write of 5Ah must appear in all four planes.
; 4. Restores 3DDh = 0Fh, 3DEh = 0, 3D9h = 7 and mode 03h, appends one line to
;    P15ID.TXT in the current directory and prints it.
; Exit 0 only when 2 and 3 both hold (PC1512=01); exit 1 otherwise.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

f_out   db 'P15ID.TXT',0
line    db 'MODE_BEFORE='
h_mode  db '00 COLS='
h_cols  db '0000 PLANES='
h_p0    db '00'
        db ','
h_p1    db '00'
        db ','
h_p2    db '00'
        db ','
h_p3    db '00 ALL='
h_a0    db '00'
        db ','
h_a1    db '00'
        db ','
h_a2    db '00'
        db ','
h_a3    db '00 PC1512='
h_ok    db '00 COMPLETE=1',13,10
line_len equ $-line
        db '$'
hexd    db '0123456789ABCDEF'
want    db 11h,22h,44h,88h
got     db 4 dup (0)
all     db 4 dup (0)
p_out   dw offset h_p0,offset h_p1,offset h_p2,offset h_p3
a_out   dw offset h_a0,offset h_a1,offset h_a2,offset h_a3

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

; BL = plane 0..3 -> AL = byte at B800:SI read through 3DEh
rd_plane proc near
    mov dx,3deh
    mov al,bl
    out dx,al
    mov al,es:[si]
    ret
rd_plane endp

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

    mov ax,6
    int 10h
    mov dx,3d9h
    mov al,0fh
    out dx,al
    mov ax,0b800h
    mov es,ax

    ; One byte per plane through single-plane write masks.
    xor bx,bx
    xor si,si
wr_loop:
    mov dx,3ddh
    mov al,1
    mov cl,bl
    shl al,cl
    out dx,al
    mov al,want[bx]
    mov es:[si],al
    inc bx
    cmp bx,4
    jb wr_loop
    xor si,si
    xor bx,bx
rd_loop:
    call rd_plane
    mov got[bx],al
    inc bx
    cmp bx,4
    jb rd_loop

    ; One write with all planes enabled.
    mov dx,3ddh
    mov al,0fh
    out dx,al
    mov si,1
    mov byte ptr es:[si],5ah
    xor bx,bx
all_loop:
    call rd_plane
    mov all[bx],al
    inc bx
    cmp bx,4
    jb all_loop

    ; Defaults back, text mode.
    mov dx,3ddh
    mov al,0fh
    out dx,al
    mov dx,3deh
    xor al,al
    out dx,al
    mov dx,3d9h
    mov al,7
    out dx,al
    mov ax,3
    int 10h

    ; Report and judge.
    xor bp,bp                 ; BP = number of mismatches
    xor bx,bx
rep_loop:
    mov al,got[bx]
    push bx
    shl bx,1
    mov di,p_out[bx]
    pop bx
    call hex8
    cmp al,want[bx]
    je rep_a
    inc bp
rep_a:
    mov al,all[bx]
    push bx
    shl bx,1
    mov di,a_out[bx]
    pop bx
    call hex8
    cmp al,5ah
    je rep_next
    inc bp
rep_next:
    inc bx
    cmp bx,4
    jb rep_loop
    xor ax,ax
    or bp,bp
    jnz verdict
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
