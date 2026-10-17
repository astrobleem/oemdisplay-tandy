; JRMODE.ASM - test-only DOS program for the grabber switch tests (MIT).
;   JRMODE m      m = 0 1 2 3 4 5 6 8 9 A (BIOS video mode, hex digit)
;   JRMODE m X    fault self-test: after the snapshot, change one cell
;                 itself; the result must then be 'BAD 0001'.
; Sets BIOS mode m, prints 'JRMODE m' through the BIOS teletype, draws a
; known pattern through the BIOS (graphics: rows 40-55, every pixel x,
; colour ((x>>3)+y) AND (colours-1); text: row 5, columns 0-14, 'A'+i with
; attribute i+1), reads it straight back through the BIOS (INT 10h 0Dh /
; 08h) into a snapshot, waits for a key, reads it again and counts cells
; that differ from the snapshot: anything that changed the screen while
; the program waited. It sets mode 03h and writes C:\JRMODEm.TXT:
; 'MODE m OK' or 'MODE m BAD hhhh' (hex count), followed by ' READ hhhh'
; when the first readback already differed from the drawn pattern (the
; BIOS's own read path; DOSBox-X's PCjr BIOS does this in mode 0Ah).
; Exit 0 = OK, 2 = changed, 3 = bad argument, 4 = file error.
; Uses only INT 10h/16h/21h; writes no video memory directly.
.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry:
 cld
 mov si,81h
skip:
 lodsb
 cmp al,' '
 je skip
 cmp al,9
 je skip
 cmp al,'a'
 jb case_ok
 sub al,20h
case_ok:
 mov mode_char,al
 mov al,[si]
 cmp al,' '
 jne no_fault
 mov al,[si+1]
 and al,0dfh
 cmp al,'X'
 jne no_fault
 mov fault,1
no_fault:
 mov al,mode_char
 mov di,offset modes
find:
 mov ah,[di]
 or ah,ah
 jnz find_more
 jmp bad_arg
find_more:
 cmp ah,al
 je found
 add di,6
 jmp short find
found:
 mov al,[di+1]
 mov vmode,al
 mov al,[di+2]
 mov kind,al
 mov ax,[di+3]
 mov xwidth,ax
 mov al,[di+5]
 mov cmask,al
 mov al,mode_char
 mov fname_m,al
 mov title_m,al
 mov line_m,al

 xor ah,ah
 mov al,vmode
 int 10h
 mov si,offset title_s
tty:
 lodsb
 or al,al
 jz tty_done
 mov ah,0eh
 xor bh,bh
 mov bl,cmask
 or bl,bl
 jnz tty_col
 mov bl,7
tty_col:
 int 10h
 jmp short tty
tty_done:
 mov verify,0
 call pattern
 mov verify,1
 call pattern
 cmp fault,0
 je wait_key
 call make_fault
wait_key:
 xor ah,ah
 int 16h
 mov verify,2
 call pattern
 mov ax,0003h
 int 10h

 mov di,offset line_r
 cmp errs,0
 jne write_bad
 mov si,offset ok_s
 mov cx,3
 rep movsb
 jmp short write_file
write_bad:
 mov si,offset bad_s
 mov cx,5
 rep movsb
 mov ax,errs
 mov cx,4
hex_loop:
 push cx
 mov cl,4
 rol ax,cl
 pop cx
 mov bx,ax
 and bx,0fh
 mov dl,hexd[bx]
 mov [di],dl
 inc di
 loop hex_loop
write_file:
 cmp read_errs,0
 je line_end
 mov si,offset read_s
 mov cx,6
 rep movsb
 mov ax,read_errs
 mov cx,4
hex_loop2:
 push cx
 mov cl,4
 rol ax,cl
 pop cx
 mov bx,ax
 and bx,0fh
 mov dl,hexd[bx]
 mov [di],dl
 inc di
 loop hex_loop2
line_end:
 mov word ptr [di],0a0dh
 add di,2
 mov ah,3ch
 xor cx,cx
 mov dx,offset fname
 int 21h
 jc file_err
 mov bx,ax
 mov cx,di
 sub cx,offset line_s
 mov dx,offset line_s
 mov ah,40h
 int 21h
 jc file_err
 mov ah,3eh
 int 21h
 mov al,0
 cmp errs,0
 je done
 mov al,2
done:
 mov ah,4ch
 int 21h
file_err:
 mov ax,4c04h
 int 21h
bad_arg:
 mov dx,offset usage
 mov ah,9
 int 21h
 mov ax,4c03h
 int 21h

; Fault self-test: change the first pattern cell (graphics: pixel 0,40
; to colour 1 or 0; text: row 5 column 0 to '#').
make_fault proc near
 cmp kind,2
 je mf_graphics
 mov ah,2
 xor bh,bh
 mov dx,0500h
 int 10h
 mov ax,0923h
 mov bx,0007h
 mov cx,1
 int 10h
 ret
mf_graphics:
 mov al,buf
 xor al,1
 and al,cmask
 mov ah,0ch
 xor bh,bh
 xor cx,cx
 mov dx,40
 int 10h
 ret
make_fault endp

; verify = 0: draw. 1: read back into buf, count cells unlike the drawn
; pattern in read_errs. 2: read back, count cells unlike buf in errs.
pattern proc near
 mov di,offset buf
 cmp kind,2
 je graphics
 xor si,si
text_cell:
 mov ah,2
 xor bh,bh
 mov dx,si
 mov dh,5
 int 10h
 cmp verify,0
 jne text_read
 mov ax,si
 add al,'A'
 mov ah,9
 mov bx,si
 inc bx
 mov cx,1
 int 10h
 jmp short text_next
text_read:
 mov ah,8
 xor bh,bh
 int 10h
 cmp verify,1
 jne text_cmp
 mov [di],ax
 mov dx,si
 add dl,'A'
 cmp al,dl
 jne text_rbad
 mov dx,si
 inc dl
 cmp ah,dl
 je text_adv
text_rbad:
 inc read_errs
 jmp short text_adv
text_cmp:
 cmp ax,[di]
 je text_adv
 inc errs
text_adv:
 add di,2
text_next:
 inc si
 cmp si,15
 jb text_cell
 ret
graphics:
 mov dx,40
g_row:
 xor cx,cx
g_pix:
 mov ax,cx
 shr ax,1
 shr ax,1
 shr ax,1
 add ax,dx
 and al,cmask
 mov bl,al
 cmp verify,0
 jne g_read
 mov al,bl
 mov ah,0ch
 xor bh,bh
 push cx
 push dx
 int 10h
 pop dx
 pop cx
 jmp short g_next
g_read:
 push bx
 push cx
 push dx
 mov ah,0dh
 xor bh,bh
 int 10h
 pop dx
 pop cx
 pop bx
 cmp verify,1
 jne g_cmp
 mov [di],al
 cmp al,bl
 je g_adv
 inc read_errs
 jmp short g_adv
g_cmp:
 cmp al,[di]
 je g_adv
 inc errs
g_adv:
 inc di
g_next:
 inc cx
 cmp cx,xwidth
 jb g_pix
 inc dx
 cmp dx,56
 jb g_row
 ret
pattern endp

; char, BIOS mode, kind (0 text, 2 graphics), width (word), colours-1
modes db '0',00h,0
      dw 40
      db 0
      db '1',01h,0
      dw 40
      db 0
      db '2',02h,0
      dw 80
      db 0
      db '3',03h,0
      dw 80
      db 0
      db '4',04h,2
      dw 320
      db 3
      db '5',05h,2
      dw 320
      db 3
      db '6',06h,2
      dw 640
      db 1
      db '8',08h,2
      dw 160
      db 15
      db '9',09h,2
      dw 320
      db 15
      db 'A',0ah,2
      dw 640
      db 3
      db 0
mode_char db 0
vmode db 0
kind db 0
xwidth dw 0
cmask db 0
verify db 0
fault db 0
errs dw 0
read_errs dw 0
hexd db '0123456789ABCDEF'
ok_s db ' OK'
bad_s db ' BAD '
read_s db ' READ '
title_s db 'JRMODE '
title_m db '?'
 db 0
fname db 'C:\JRMODE'
fname_m db '?'
 db '.TXT',0
usage db 'JRMODE m: m = 0 1 2 3 4 5 6 8 9 A',13,10,'$'
line_s db 'MODE '
line_m db '?'
line_r db 32 dup (0)
buf label byte                    ; up to 10,240 bytes (640 x 16)
code ends
end entry
