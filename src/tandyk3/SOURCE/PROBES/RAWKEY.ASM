; First-party XT/Tandy keyboard scan probe. MASM 5/6, 8086 only.
; Owns IRQ1: read 60h ONCE, pulse XT port 61h, acknowledge PIC.
; Does not chain BIOS (which would read 60h again). No DOS in IRQ.
.8086
STACKSEG SEGMENT PARA STACK 'STACK'
 DB 512 DUP (?)
STACKSEG ENDS
CODE SEGMENT PARA PUBLIC 'CODE'
 ASSUME CS:CODE,DS:CODE,SS:STACKSEG
old09 DD 0
count DW 0
stop DB 0
reason DB 0
starttick DW 0
handle DW 0
raw DB 4096 DUP (?)
hex DB '0123456789ABCDEF'
line DB '00',13,10
filename DB 'RAWKEY.LOG',0
intro DB 'RAWKEY: XT/Tandy IRQ1 probe. Release every key first.',13,10
 DB 'Press/release keys. Escape RELEASE exits. Timeout: 5 minutes.',13,10
 DB 'BIOS shortcuts disabled while capturing. File: RAWKEY.LOG',13,10,'$'
header DB 'RAWKEY XT/Tandy raw port 60h bytes, in arrival order.',13,10
 DB 'Not a BIOS/Windows scan translation. Includes prefixes and replies.',13,10
headerlen EQU $-header
finish DB 'IRQ1 restored; RAWKEY.LOG written.',13,10,'$'
fail DB 'IRQ1 restored. Cannot create/write RAWKEY.LOG.',13,10,'$'
fullmsg DB '# STOP: buffer full (4096 bytes); no overwrite.',13,10
fullen EQU $-fullmsg
timemsg DB '# STOP: five-minute timeout.',13,10
timelen EQU $-timemsg
escmsg DB '# STOP: Escape break (81h).',13,10
esclen EQU $-escmsg
irq1 PROC FAR
 push ax
 push bx
 in al,60h
 push ax
 in al,61h
 mov ah,al
 or al,80h
 out 61h,al
 mov al,ah
 out 61h,al
 pop ax
 cmp cs:stop,0
 jne short ack
 mov bx,cs:count
 cmp bx,4096
 jae short overflow
 mov cs:raw[bx],al
 inc bx
 mov cs:count,bx
 cmp al,81h
 jne short capacity
 mov cs:stop,1
 jmp short ack
capacity:
 cmp bx,4096
 jb short ack
overflow:
 mov cs:reason,1
 mov cs:stop,1
ack:
 mov al,20h
 out 20h,al
 pop bx
 pop ax
 iret
irq1 ENDP
start:
 push cs
 pop ds
 mov dx,OFFSET intro
 mov ah,9
 int 21h
 ; Create file before taking IRQ ownership. No DOS I/O while hooked.
 mov dx,OFFSET filename
 xor cx,cx
 mov ah,3ch
 int 21h
 jnc short created
 jmp failure
created:
 mov handle,ax
 mov ax,3509h
 int 21h
 mov WORD PTR old09,bx
 mov WORD PTR old09+2,es
 xor ah,ah
 int 1ah
 mov starttick,dx
 mov dx,OFFSET irq1
 mov ax,2509h
 int 21h
waitkey:
 cmp stop,0
 jne short restore
 xor ah,ah
 int 1ah
 sub dx,starttick
 cmp dx,5460
 jb short waitkey
 mov reason,2
restore:
 ; No DOS service until IRQ vector restored. AH=25h is atomic in DOS.
 lds dx,old09
 mov ax,2509h
 int 21h
 push cs
 pop ds
 mov bx,handle
 mov dx,OFFSET header
 mov cx,headerlen
 call writebuf
 jc short closefail
 xor si,si
writebyte:
 cmp si,count
 jae short trailer
 mov cl,4
 mov al,raw[si]
 shr al,cl
 xor ah,ah
 mov di,ax
 mov al,hex[di]
 mov line,al
 mov al,raw[si]
 and ax,000fh
 mov di,ax
 mov al,hex[di]
 mov line+1,al
 mov dx,OFFSET line
 mov cx,4
 call writebuf
 jc short closefail
 inc si
 jmp short writebyte
trailer:
 mov dx,OFFSET escmsg
 mov cx,esclen
 cmp reason,0
 je short writetail
 mov dx,OFFSET fullmsg
 mov cx,fullen
 cmp reason,1
 je short writetail
 mov dx,OFFSET timemsg
 mov cx,timelen
writetail:
 call writebuf
 jc short closefail
 mov ah,3eh
 int 21h
 jc short failure
 mov dx,OFFSET finish
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
closefail:
 mov ah,3eh
 int 21h
failure:
 mov dx,OFFSET fail
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
writebuf PROC NEAR
 mov ah,40h
 int 21h
 jc short wrdone
 cmp ax,cx
 je short wrdone
 stc
wrdone:
 ret
writebuf ENDP
CODE ENDS
END start
