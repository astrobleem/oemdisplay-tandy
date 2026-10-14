; MSTEST.ASM - poll a Microsoft serial mouse on COM1 and total its motion.
; MASM 5.1 syntax, .8086 only. Build as a COM (org 100h). Test harness
; check for docs/PCP.MD: proves what the emulator's mouse actually delivers
; to the guest, with no Windows, no mouse driver and no interrupts.
;
; Programs COM1 for 1200 baud 7N1, raises DTR/RTS (a Microsoft mouse
; answers 'M'), then polls the UART. Each 3-byte packet (sync bit 6 in the
;  first byte) adds its signed X/Y to running totals. It prints nothing
; while counting: on a 4.77 MHz XT a DOS screen write takes long enough for
; a polled 8250 to overrun. Any key stops it, then it prints and appends
;  B=bytes P=packets X=sumx Y=sumy BAD=resyncs  (hex, 16-bit) to MSTEST.TXT.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

COM     equ 3f8h
f_out   db 'MSTEST.TXT',0
line    db 'B='
h_b     db '0000 P='
h_p     db '0000 X='
h_x     db '0000 Y='
h_y     db '0000 BAD='
h_bad   db '0000',13,10
line_len equ $-line
        db '$'
hexd    db '0123456789ABCDEF'
cnt_b   dw 0
cnt_p   dw 0
sum_x   dw 0
sum_y   dw 0
cnt_bad dw 0
pk0     db 0
pk1     db 0
pk_n    db 0

; AX -> four hex digits at [DI]
hex16 proc near
    push ax
    push bx
    push cx
    mov bx,offset hexd
    mov cx,4
h16_loop:
    push cx
    mov cl,4
    rol ax,cl
    pop cx
    push ax
    and al,0fh
    xlat
    mov [di],al
    inc di
    pop ax
    loop h16_loop
    pop cx
    pop bx
    pop ax
    ret
hex16 endp

fill proc near
    mov ax,cnt_b
    mov di,offset h_b
    call hex16
    mov ax,cnt_p
    mov di,offset h_p
    call hex16
    mov ax,sum_x
    mov di,offset h_x
    call hex16
    mov ax,sum_y
    mov di,offset h_y
    call hex16
    mov ax,cnt_bad
    mov di,offset h_bad
    call hex16
    ret
fill endp

; AL = received byte
take proc near
    inc cnt_b
    test al,40h
    jz tk_data
    cmp pk_n,0
    je tk_first
    inc cnt_bad
tk_first:
    mov pk0,al
    mov pk_n,1
    ret
tk_data:
    cmp pk_n,1
    je tk_second
    cmp pk_n,2
    je tk_third
    ret                       ; stray byte (e.g. the 'M' ident) ignored
tk_second:
    mov pk1,al
    mov pk_n,2
    ret
tk_third:
    mov pk_n,0
    inc cnt_p
    ; dy = ((pk0 & 0Ch) << 4) | b2
    mov ah,pk0
    and ah,0ch
    mov cl,4
    shl ah,cl
    and al,3fh
    or al,ah
    cbw
    add sum_y,ax
    ; dx = ((pk0 & 03h) << 6) | pk1
    mov ah,pk0
    and ah,03h
    mov cl,6
    shl ah,cl
    mov al,pk1
    and al,3fh
    or al,ah
    cbw
    add sum_x,ax
    ret
take endp

start:
    push cs
    pop ds
    mov dx,COM+3
    mov al,80h
    out dx,al
    mov dx,COM
    mov al,96                 ; 115200/1200
    out dx,al
    inc dx
    xor al,al
    out dx,al
    mov dx,COM+3
    mov al,02h                ; 7 data bits, 1 stop, no parity
    out dx,al
    mov dx,COM+1
    xor al,al                 ; no UART interrupts: pure polling
    out dx,al
    mov dx,COM+4
    xor al,al
    out dx,al                 ; drop DTR/RTS ...
    mov cx,0
dly: loop dly
    mov al,03h
    out dx,al                 ; ... and raise them: mouse resets, sends 'M'
    mov dx,COM
    in al,dx

poll:
    mov dx,COM+5
    in al,dx
    test al,01h
    jz no_byte
    mov dx,COM
    in al,dx
    call take
no_byte:
    mov ah,1
    int 16h
    jz poll
    xor ah,ah
    int 16h

    call fill
    mov dx,offset line
    mov ah,9
    int 21h
    mov dx,offset f_out
    mov ax,3d01h
    int 21h
    jnc opened
    mov dx,offset f_out
    mov ah,3ch
    xor cx,cx
    int 21h
    jc done
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
done:
    mov ax,4c00h
    int 21h

code ends
end entry
