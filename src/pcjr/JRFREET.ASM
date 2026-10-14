; JRFREET.ASM - EMULATOR-ONLY negative test for JRGUARD. Never run on a
; real machine you care about. MASM 5.1 syntax, .8086, COM (org 100h).
; DOSBox/DOSBox-X PCjr guests hold the mode-09 page in a DOS-owned block at
; segment 1800h. This frees that block (INT 21h AH=49h on ES=1800h) so that
; JRGUARD must then fail closed. Exit 0 if DOS accepted the free, else 1.
.8086
code segment para public 'CODE'
assume cs:code,ds:code
org 100h
entry:
 mov ax,1800h
 mov es,ax
 mov ah,49h
 int 21h
 mov ax,4c00h
 jnc done
 mov al,1
done:
 int 21h
code ends
end entry
