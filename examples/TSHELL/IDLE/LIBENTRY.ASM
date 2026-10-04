; No CRT and no local heap. Windows enters with DS=DGROUP, DI=instance,
; CX=heap size, ES:SI=command line. All instructions are 8086 compatible.
.8086
.MODEL SMALL
EXTRN LIBMAIN:FAR
.CODE
LibEntry PROC FAR
    push di
    push ds
    push cx
    push es
    push si
    call LIBMAIN
    retf
LibEntry ENDP
; Milliseconds since midnight, as DX:AX. INT21/AH2C is the documented DOS
; current-time read service. Preserve SI and use only 8086 arithmetic.
PUBLIC READDOSCLOCK
READDOSCLOCK PROC FAR
    push si
    mov ah,2ch
    int 21h
    mov si,dx
    xor ax,ax
    mov al,ch
    mov bx,60
    mul bx
    xor ch,ch
    add ax,cx
    mov bx,60000
    mul bx
    push dx
    push ax
    mov ax,si
    mov al,ah
    xor ah,ah
    mov bx,1000
    mul bx
    mov bx,ax
    mov ax,si
    xor ah,ah
    mov cx,10
    mul cx
    add bx,ax
    pop ax
    pop dx
    add ax,bx
    adc dx,0
    pop si
    retf
READDOSCLOCK ENDP
END LibEntry
