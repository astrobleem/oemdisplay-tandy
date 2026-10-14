; T2MODES.ASM - which INT 10h video modes does this Tandy BIOS accept?
; MASM 5.1, .8086, COM via EXE2BIN. Read-only survey for Video II work
; (docs/TGA2.MD): for each mode number 00h-7Fh, INT 10h AH=00h sets it with
; the screen-clear bit off (AL bit 7 set: no video RAM is cleared), then
; AH=0Fh reads the mode back; the BIOS data area bytes 40:49 (mode), 40:4A
; (columns), 40:4C (page size) and 40:65 (mode register copy) are recorded,
; with port 3DAh status. Mode 03h is restored after each one. One line per
; mode to T2MODES.TXT:  MM AA CCCC SSSS RR  (asked, read back, columns,
; page size, 40:65). Writes no video memory and no port except through the
; BIOS. Exit 0.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

fname  db 'T2MODES.TXT',0
handle dw 0
mode   db 0
line   db 'MM AA CCCC SSSS RR',13,10
LLEN   equ $ - line
hexd   db '0123456789ABCDEF'

; AL -> two hex digits at DI
hex2 proc near
 push bx
 push ax
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
 pop ax
 pop bx
 ret
hex2 endp

; AX -> four hex digits at DI
hex4 proc near
 push ax
 mov al,ah
 call hex2
 pop ax
 add di,2
 call hex2
 sub di,2
 ret
hex4 endp

start:
 push cs
 pop ds
 push cs
 pop es
 mov ah,3ch
 xor cx,cx
 mov dx,offset fname
 int 21h
 jc done
 mov handle,ax
 mov mode,0
next:
 mov al,mode
 or al,80h                      ; do not clear video memory
 xor ah,ah
 int 10h
 mov ah,0fh
 int 10h
 push ax
 mov di,offset line
 mov al,mode
 call hex2
 pop ax
 push ax
 and al,7fh
 mov di,offset line+3
 call hex2
 push ds
 mov ax,40h
 mov ds,ax
 mov ax,ds:[4ah]
 mov bx,ds:[4ch]
 mov cl,ds:[65h]
 pop ds
 mov di,offset line+6
 call hex4
 mov ax,bx
 mov di,offset line+11
 call hex4
 mov al,cl
 mov di,offset line+16
 call hex2
 pop ax
 mov ax,0083h                   ; back to mode 03h, no clear
 int 10h
 mov ah,40h
 mov bx,handle
 mov cx,LLEN
 mov dx,offset line
 int 21h
 inc mode
 cmp mode,80h
 jb next
 mov ah,3eh
 mov bx,handle
 int 21h
done:
 mov ax,0003h
 int 10h
 mov ax,4c00h
 int 21h

code ends
end entry
