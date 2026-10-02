.intel_syntax noprefix
.code16
.global _start
_start:
 push cs
 pop ds
 mov ax, 0x3506
 int 0x21
 mov word ptr [oldoff],bx
 mov word ptr [oldseg],es
 mov dx, offset handler
 mov ax, 0x2506
 int 0x21
 mov dx, offset title
 mov ah,9
 int 0x21
 mov bx,sp
 xor ax,ax
 .byte 0x60,0x90,0x90
 mov ax,sp
 mov sp,bx
 sub ax,bx
 call printhex
 mov dx,offset immmsg
 mov ah,9
 int 0x21
 mov bx,sp
 xor ax,ax
 .byte 0x68,0x90,0x90
 mov ax,sp
 mov sp,bx
 sub ax,bx
 call printhex
 mov dx,offset shiftmsg
 mov ah,9
 int 0x21
 mov word ptr [savedsp],sp
 mov ax,1
 call shiftproc
 mov sp,word ptr [savedsp]
 call printhex
 mov dx,offset prefixmsg
 mov ah,9
 int 0x21
 xor ax,ax
 inc ax
 .byte 0x66,0xb8,0x90,0x90,0x90,0x90
 call printhex
 mov dx,offset trapmsg
 mov ah,9
 int 0x21
 mov ax,word ptr [traps]
 call printhex
 mov dx,offset newline
 mov ah,9
 int 0x21
 mov dx,word ptr [oldoff]
 mov ax,word ptr [oldseg]
 mov ds,ax
 mov ax,0x2506
 int 0x21
 mov ax,0x4c00
 int 0x21
shiftproc:
 .byte 0xc0,0xe0,0x03
 ret
handler:
 push bp
 mov bp,sp
 add word ptr ss:[bp+2],3
 inc word ptr cs:[traps]
 pop bp
 iret
printhex:
 push ax
 push bx
 push cx
 push dx
 mov bx, ax
 mov cx, 4
hexloop:
 push cx
 mov cl, 4
 rol bx, cl
 pop cx
 mov dl, bl
 and dl, 15
 add dl, 48
 cmp dl, 57
 jbe decimal
 add dl, 7
decimal:
 mov ah, 2
 int 0x21
 loop hexloop
 pop dx
 pop cx
 pop bx
 pop ax
 ret
oldoff: .word 0
oldseg: .word 0
savedsp: .word 0
traps: .word 0
title: .ascii "PUSHA SPdelta=$"
immmsg: .ascii " PUSHimm SPdelta=$"
shiftmsg: .ascii " C0 shift=$"
prefixmsg: .ascii " 66prefix AX=$"
trapmsg: .ascii " INT6=$"
newline: .ascii "\r\n$"
