; JRMODE9.ASM - test-only DOS program for the grabber switch tests (MIT).
; Sets BIOS mode 09h (PCjr 320x200x16), prints a line through the BIOS
; teletype in colour 14, waits for a key, sets mode 03h and exits 0.
; Uses only INT 10h/16h/21h; writes no video memory directly. On a
; machine whose BIOS lacks mode 09h it still exits after a key.
.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry:
 mov ax,0009h
 int 10h
 mov si,offset msg
next:
 lodsb
 or al,al
 jz waitkey
 mov ah,0eh
 mov bx,000eh
 int 10h
 jmp short next
waitkey:
 xor ah,ah
 int 16h
 mov ax,0003h
 int 10h
 mov ax,4c00h
 int 21h
msg db 'JRMODE9: PCjr mode 9. Press a key.',0
code ends
end entry
