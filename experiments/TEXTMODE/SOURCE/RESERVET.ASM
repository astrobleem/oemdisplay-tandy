; RESERVET.ASM - isolated DOS regression probe, never needed by Windows.
.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start
JFAIL macro condition, target
 local taken, done
 condition taken
 jmp short done
taken: jmp target
done:
endm
start:
 cli
 mov sp,offset stack_end
 sti
 push cs
 pop ds
 cld
 push cs
 pop es
 mov bx,KEEP_PARAS
 mov ah,4ah
 int 21h
 JFAIL jc,bad
 mov al,ds:[82h]
 cmp al,'A'
 JFAIL je,short_arena
 cmp al,'T'
 JFAIL je,occupy_exact
 cmp al,'M'
 JFAIL je,wrong_mode
 cmp al,'O'
 JFAIL je,occupy
 cmp al,'B'
 JFAIL je,wrong_bda
 cmp al,'1'
 JFAIL je,set_first
 cmp al,'2'
 JFAIL je,set_best
 cmp al,'3'
 JFAIL je,set_last
 cmp al,'P'
 JFAIL je,probe
 jmp snapshot

set_first: mov bx,0
 jmp short set_strategy
set_best: mov bx,1
 jmp short set_strategy
set_last: mov bx,2
set_strategy:
 mov ax,5801h
 int 21h
 JFAIL jc,bad
 jmp good

occupy_exact:
 mov hog_size,400h
 mov hog_expect,9800h
occupy:
 mov bx,2
 mov ax,5801h
 int 21h
 JFAIL jc,bad
 mov bx,hog_size
 mov ah,48h
 int 21h
 JFAIL jc,bad
 cmp ax,hog_expect
 JFAIL jne,bad
 mov dx,KEEP_PARAS
 mov ax,3100h
 int 21h
; Test-only synthetic layout: shorten a valid free terminal arena by1K.
; This runs only in a disposable emulator boot, never on the user's DOS.
short_arena:
 mov ah,52h
 int 21h
 mov ax,es:[bx-2]
short_next:
 mov es,ax
 cmp byte ptr es:[0],'Z'
 je short_last
 cmp byte ptr es:[0],'M'
 JFAIL jne,bad
 add ax,es:[3]
 inc ax
 jmp short short_next
short_last:
 cmp word ptr es:[1],0
 JFAIL jne,bad
 cmp word ptr es:[3],40h
 JFAIL jbe,bad
 sub word ptr es:[3],40h
 jmp good
wrong_mode:
 mov ax,9
 int 10h
 jmp good
wrong_bda:
 mov ax,40h
 mov es,ax
 mov word ptr es:[13h],623
 jmp good

snapshot:
 mov ax,40h
 mov es,ax
 mov ax,es:[13h]
 mov bda_kb,ax
 mov ax,5800h
 int 21h
 mov strategy,ax
 mov ah,52h
 int 21h
 mov ax,es:[bx-2]
 mov first_mcb,ax
 mov cx,0
walk:
 inc cx
 cmp cx,1000h
 JFAIL ja,bad
 mov es,ax
 mov bx,es:[3]
 mov si,es:[1]
 mov di,es:[0]
 mov last_mcb,ax
 mov last_size,bx
 mov last_owner,si
 mov last_type,di
 add ax,bx
 JFAIL jc,bad
 inc ax
 JFAIL jz,bad
 cmp byte ptr es:[0],'Z'
 je walked
 cmp byte ptr es:[0],'M'
 JFAIL jne,bad
 jmp short walk
walked:
 mov arena_end,ax
 mov block_count,cx
 mov ax,cs
 mov probe_psp,ax
 cmp last_mcb,97ffh
 jne no_jft
 cmp last_size,400h
 jne no_jft
 mov ax,last_owner
 or ax,ax
 jz no_jft
 mov es,ax
 mov di,18h
 mov cx,20
 xor bx,bx
jft_next:
 cmp byte ptr es:[di],0ffh
 je jft_closed
 inc bx
jft_closed:
 inc di
 loop jft_next
 mov owner_open_handles,bx
no_jft:
 mov dx,offset filename
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jc,bad
 mov bx,ax
 mov dx,offset report
 mov cx,report_end-report
 mov ah,40h
 int 21h
 JFAIL jc,bad
 mov ah,3eh
 int 21h
 JFAIL jc,bad
 jmp good

probe:
 ; Real maximum DOS allocation must end BEFORE the protected MCB.
 mov bx,0ffffh
 mov ah,48h
 int 21h
 JFAIL jnc,bad
 or bx,bx
 JFAIL jz,bad
 mov alloc_size,bx
 mov ah,48h
 int 21h
 JFAIL jc,bad
 mov alloc_segment,ax
 add ax,alloc_size
 cmp ax,97ffh
 JFAIL ja,bad
 mov alloc_end,ax
 dec ax
 mov guard_segment,ax
 mov es,ax
 xor di,di
 mov ax,6d3ah
 mov cx,8
 rep stosw
 ; Record DOS metadata that must survive both BIOS mode switches AND
 ; a full 32KB video write. Save 97FFh's MCB including its owner.
 mov ax,97ffh
 mov es,ax
 mov si,0
 mov di,offset before_mcb
 mov cx,8
save_mcb:
 mov ax,es:[si]
 mov [di],ax
 add si,2
 add di,2
 loop save_mcb
 cmp byte ptr before_mcb,'Z'
 JFAIL jne,bad
 cmp word ptr before_mcb+3,400h
 JFAIL jne,bad

 mov ax,9
 int 10h
 mov ax,0b800h
 mov es,ax
 xor di,di
 mov ax,0a55ah
 mov cx,4000h
 rep stosw
 ; Prove mode09 B8000h aliases physical conventional overlap, so this
 ; test would actually catch an unprotected allocation at the top.
 mov ax,9800h
 mov es,ax
 xor di,di
 mov ax,0a55ah
 mov cx,2000h
 repe scasw
 JFAIL jne,bad_video
 mov alias_verified,1
 mov ax,3
 int 10h
 mov ax,guard_segment
 mov es,ax
 xor di,di
 mov ax,6d3ah
 mov cx,8
 repe scasw
 JFAIL jne,bad
 mov ax,97ffh
 mov es,ax
 xor di,di
 mov si,offset before_mcb
 mov cx,16
 repe cmpsb
 JFAIL jne,bad
 mov mcb_verified,1
 mov ax,alloc_segment
 mov es,ax
 mov ah,49h
 int 21h
 JFAIL jc,bad
 mov alloc_segment,0
 jmp snapshot
bad_video:
 mov ax,3
 int 10h
bad:
 mov dx,offset failed_text
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
good:
 mov dx,offset passed_text
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h

filename db 'SNAP.BIN',0
passed_text db 'RESERVET: PASS',13,10,'$'
failed_text db 'RESERVET: FAIL',13,10,'$'
report label byte
bda_kb dw 0
first_mcb dw 0
last_mcb dw 0
arena_end dw 0
last_owner dw 0
last_size dw 0
last_type dw 0
strategy dw 0
block_count dw 0
probe_psp dw 0
alloc_segment dw 0
alloc_size dw 0
alloc_end dw 0
alias_verified dw 0
mcb_verified dw 0
owner_open_handles dw 0
report_end label byte
hog_size dw 20h
hog_expect dw 9be0h
guard_segment dw 0
before_mcb db 16 dup(0)
even
 db 256 dup(0)
stack_end label byte
KEEP_PARAS equ (stack_end-entry+100h+15)/16
code ends
end entry
