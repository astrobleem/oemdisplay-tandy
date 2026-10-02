.intel_syntax noprefix
.code16
.global _start
_start:
 push cs
 pop ds
 mov dx, offset title
 mov ah, 9
 int 0x21
 pushf
 pop ax
 and ax, 0xf000
 call printhex
 mov dx, offset pushmsg
 mov ah, 9
 int 0x21
 mov bx, sp
 push sp
 pop ax
 sub ax, bx
 call printhex
 mov dx, offset shiftmsg
 mov ah, 9
 int 0x21
 mov ax, 1
 mov cl, 32
 shl ax, cl
 call printhex
 mov dx, offset newline
 mov ah, 9
 int 0x21
 mov ax, 0x4c00
 int 0x21
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
title: .asciz "FLAGS high=$"
pushmsg: .asciz " PUSH SP delta=$"
shiftmsg: .asciz " 1<<32=$"
newline: .ascii "\r\n$"
