; JRHOLDT.ASM - EMULATOR-ONLY negative test for JRGUARD and JRPROBE.
; Never run on a real machine you care about. MASM 5.1, .8086, COM.
; Frees the DOS-owned page block at 1800h (as JRFREET does), then allocates
; exactly that range for ITSELF and stays resident, so 1800h-1FFFh is held
; by an ordinary program block (owner = this PSP), not by DOS. JRGUARD must
; then fail and JRPROBE must refuse to touch video. Exit codes: stays
; resident on success; 1 if the free fails; 2 if DOS placed the allocation
; anywhere other than 1800h (test not set up; nothing was proven).
.8086
code segment para public 'CODE'
assume cs:code,ds:code
org 100h
entry:
 mov ax,1800h
 mov es,ax
 mov ah,49h
 int 21h
 jc free_failed
 mov ax,5801h
 xor bx,bx                ; first fit
 int 21h
 mov ah,48h
 mov bx,0800h
 int 21h
 jc wrong_place
 cmp ax,1800h
 jne wrong_place
 mov ax,3100h
 mov dx,(tail - entry + 100h + 15) / 16
 int 21h
free_failed:
 mov ax,4c01h
 int 21h
wrong_place:
 mov ax,4c02h
 int 21h
tail label byte
code ends
end entry
