; Original MIT test-only bounded DOS idle/keyboard drain. No runtime dependency.
.8086
code segment para public 'CODE'
assume cs:code,ds:code
org 100h
entry:
 sti
 xor ah,ah
 int 1ah
 mov cs:starttick,dx
idle:
 sti
 hlt
 mov ah,1
 int 16h
 jz empty
 xor ah,ah
 int 16h
empty:
 xor ah,ah
 int 1ah
 sub dx,cs:starttick
 cmp dx,36
 jb idle
 mov ax,4c00h
 int 21h
starttick dw 0
code ends
end entry
