; T2PROBE.ASM - Tandy Video II (SL/TL/RL) 640x200x16 mapping probe.
; MASM 5.1 syntax, .8086 only. Build as a COM (org 100h). See docs/TGA2.MD.
;
; Purpose: find out, on a real SL/TL/RL (or 86Box SL2), WHERE the 64KB
; 640x200x16 framebuffer lives in physical RAM, because that decides the
; memory reservation a Windows driver needs. It does this without writing
; through the unknown window first:
;
;  1. Shrink itself, allocate the largest free DOS block, and stamp every
;     paragraph of that OWN block with its physical segment and a tag.
;  2. BIOS mode 09h, then the hypothesis under test (two emulator models,
;     86Box vid_tandy.c and a commented DOSBox-X table entry, agree on it):
;       video array register 5 bit 0 = 1 (index -> 3DAh, data -> 3DEh)
;       64KB linear window at A000:0000, one scan line per CRTC row
;       CRTC R4=FFh R5=06h R6=C8h R7=E0h R9=00h (R0-R3 kept from mode 09h)
;  3. Read-only scan of A000:0000-FFFF for the tags: each tagged paragraph
;     names the physical RAM behind that window offset.
;  4. ONLY if every one of the 4096 window paragraphs maps, with one
;     constant offset, into this program's own block or into RAM above the
;     DOS arena (below A0000h), write a 640x200x16 linear test pattern
;     (320 bytes per row, high nibble = left pixel) and dump the window.
;     Otherwise nothing is written through the window.
;  5. Clear register 5, restore the original BIOS mode, free the block.
;
; Command line /W waits for a key while the pattern is on screen (for a
; photo on real hardware). Outputs: T2PROBE.TXT, and T2VRAM.BIN when the
; pattern step ran. Never stays resident. Reboot after testing on hardware.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

model_byte  db 0
tandy_tag   db 0
c0_cf       db 1
c0_model    db 0
c0_sub      db 0
c0_rev      db 0
port65      db 0
bios_kb     dw 0
arena_end   dw 0
arena_ok    db 0
mode_before db 3
mode_after  db 0
blk         dw 0
blk_size    dw 0
mapped      dw 0
mismatch    db 0
base_seg    dw 0
first_p     dw 0ffffh
safe        db 0
pattern_ran db 0
wait_key    db 0

f_txt  db 'T2PROBE.TXT',0
f_vram db 'T2VRAM.BIN',0
m_ok   db 'T2PROBE: done, see T2PROBE.TXT',13,10,'$'
m_err  db 'T2PROBE: setup failed (memory or file)',13,10,'$'

crtc_tab db 4,0ffh, 5,06h, 6,0c8h, 7,0e0h, 9,00h
CRTC_N equ 5

s1 db 'MODEL=',0
s2 db ' TANDYTAG=',0
s3 db ' INT15C0_CF=',0
s4 db ' C0_MODEL=',0
s5 db ' C0_SUB=',0
s6 db ' C0_REV=',0
s7 db ' PORT65=',0
s8 db 'BIOSKB=',0
s9 db ' ARENA_END=',0
s10 db ' ARENA_OK=',0
s11 db ' MODE_BEFORE=',0
s12 db ' MODE_AFTER=',0
s13 db 'BLOCK=',0
s14 db ' BLOCK_PARAS=',0
s15 db 'MAPPED_PARAS=',0
s16 db ' MAP_INCONSISTENT=',0
s17 db ' WINDOW_PHYS_SEG=',0
s18 db ' FIRST_MAPPED_P=',0
s19 db 'SAFE_TO_WRITE=',0
s20 db ' PATTERN_RAN=',0
s21 db 'COMPLETE=1',0

start:
 cli
 mov sp,offset stack_end
 sti
 push cs
 pop ds
 cld
 ; /W anywhere in the command tail
 mov si,81h
 mov cl,ds:[80h]
 xor ch,ch
tail:
 jcxz tail_done
 lodsb
 and al,0dfh
 cmp al,'W'
 jne tail_next
 mov wait_key,1
tail_next:
 loop tail
tail_done:
 push cs
 pop es
 mov bx,(stack_end - entry + 100h + 15) / 16
 mov ah,4ah
 int 21h
 jc setup_fail

 ; ---- identity ----------------------------------------------------------
 mov ax,0f000h
 mov es,ax
 mov al,es:[0fffeh]
 mov model_byte,al
 mov ax,0fc00h
 mov es,ax
 mov al,es:[0]
 mov tandy_tag,al
 push ds
 stc
 mov ah,0c0h
 int 15h
 pop ds
 jc c0_done
 mov c0_cf,0
 mov al,es:[bx+2]
 mov c0_model,al
 mov al,es:[bx+3]
 mov c0_sub,al
 mov al,es:[bx+4]
 mov c0_rev,al
c0_done:
 in al,65h
 mov port65,al
 mov ax,40h
 mov es,ax
 mov ax,es:[13h]
 mov bios_kb,ax

 ; ---- arena end (read only) ----------------------------------------------
 mov ah,52h
 int 21h
 mov ax,es:[bx-2]
walk:
 mov es,ax
 mov bl,es:[0]
 cmp bl,'M'
 je walk_ok
 cmp bl,'Z'
 jne walk_done
walk_ok:
 mov dx,es:[3]
 add dx,ax
 inc dx
 mov arena_end,dx
 cmp bl,'Z'
 je walk_last
 mov ax,dx
 jmp short walk
walk_last:
 mov arena_ok,1
walk_done:

 ; ---- own the largest free block and tag it ------------------------------
 mov ah,48h
 mov bx,0ffffh
 int 21h                  ; fails; BX = largest available
 or bx,bx
 jz setup_fail
 mov ah,48h
 int 21h
 jc setup_fail
 mov blk,ax
 mov blk_size,bx
 mov cx,bx
 mov dx,ax
tag:
 mov es,dx
 mov es:[0],dx
 mov ax,dx
 not ax
 mov es:[2],ax
 mov word ptr es:[4],3254h        ; 'T2'
 inc dx
 loop tag

 ; ---- mode 09h, then the 640x200x16 hypothesis ----------------------------
 mov ah,0fh
 int 10h
 mov mode_before,al
 mov ax,9
 int 10h
 mov ah,0fh
 int 10h
 mov mode_after,al
 cli
 mov dx,3dah
 in al,dx
 mov al,5
 out dx,al
 mov dx,3deh
 mov al,1
 out dx,al
 mov si,offset crtc_tab
 mov cx,CRTC_N
crtc_loop:
 lodsb
 mov dx,3d4h
 out dx,al
 lodsb
 inc dx
 out dx,al
 loop crtc_loop
 sti

 ; ---- read-only scan of the A000 window ----------------------------------
 xor bp,bp                ; window paragraph p
scan:
 mov ax,0a000h
 add ax,bp
 mov es,ax
 mov ax,es:[0]
 mov bx,es:[2]
 not bx
 cmp ax,bx
 jne scan_next
 cmp word ptr es:[4],3254h
 jne scan_next
 mov bx,ax
 sub bx,blk
 cmp bx,blk_size
 jae scan_next            ; not one of ours
 inc mapped
 sub ax,bp                ; physical segment of window offset 0
 cmp first_p,0ffffh
 jne scan_cmp
 mov first_p,bp
 mov base_seg,ax
 jmp short scan_next
scan_cmp:
 cmp ax,base_seg
 je scan_next
 mov mismatch,1
scan_next:
 inc bp
 cmp bp,1000h
 jb scan

 ; ---- decide whether a pattern write is provably harmless ----------------
 cmp mapped,0
 je decided
 cmp mismatch,0
 jne decided
 xor bp,bp
check:
 mov ax,base_seg
 add ax,bp
 jc decided               ; wrapped past 1MB
 cmp ax,0a000h
 jae decided              ; window must not alias ROM/adapter space
 mov bx,ax
 sub bx,blk
 cmp bx,blk_size
 jb check_ok              ; inside our own block
 cmp arena_ok,1
 jne decided
 cmp ax,arena_end
 jb decided               ; DOS memory we do not own
check_ok:
 inc bp
 cmp bp,1000h
 jb check
 mov safe,1
decided:
 cmp safe,1
 jne restore

 ; ---- linear 640x200x16 pattern: offset = y*320 + xb ---------------------
 ; c = ((xb >> 4) + y) & 15; byte = (c << 4) | (c xor 15)
 mov ax,0a000h
 mov es,ax
 xor di,di
 xor bp,bp
pat_row:
 xor si,si
pat_byte:
 mov ax,si
 mov cl,4
 shr ax,cl
 add ax,bp
 and al,0fh
 mov ah,al
 xor ah,0fh
 shl al,cl
 or al,ah
 stosb
 inc si
 cmp si,320
 jb pat_byte
 inc bp
 cmp bp,200
 jb pat_row
 mov pattern_ran,1
 cmp wait_key,1
 jne dump
 xor ah,ah
 int 16h
dump:
 mov dx,offset f_vram
 mov ah,3ch
 xor cx,cx
 int 21h
 jc restore
 mov bx,ax
 push ds
 mov ax,0a000h
 mov ds,ax
 xor dx,dx
 mov cx,8000h
 mov ah,40h
 int 21h
 mov ax,0a800h
 mov ds,ax
 xor dx,dx
 mov cx,8000h
 mov ah,40h
 int 21h
 pop ds
 mov ah,3eh
 int 21h

 ; ---- restore ------------------------------------------------------------
restore:
 cli
 mov dx,3dah
 in al,dx
 mov al,5
 out dx,al
 mov dx,3deh
 xor al,al
 out dx,al
 sti
 mov al,mode_before
 xor ah,ah
 int 10h
 mov es,blk
 mov ah,49h
 int 21h

 ; ---- report -------------------------------------------------------------
 mov di,offset report
 mov si,offset s1
 mov al,model_byte
 call kv2
 mov si,offset s2
 mov al,tandy_tag
 call kv2
 mov si,offset s3
 mov al,c0_cf
 call kv2
 mov si,offset s4
 mov al,c0_model
 call kv2
 mov si,offset s5
 mov al,c0_sub
 call kv2
 mov si,offset s6
 mov al,c0_rev
 call kv2
 mov si,offset s7
 mov al,port65
 call kv2
 call crlf
 mov si,offset s8
 mov ax,bios_kb
 call kv4
 mov si,offset s9
 mov ax,arena_end
 call kv4
 mov si,offset s10
 mov al,arena_ok
 call kv2
 mov si,offset s11
 mov al,mode_before
 call kv2
 mov si,offset s12
 mov al,mode_after
 call kv2
 call crlf
 mov si,offset s13
 mov ax,blk
 call kv4
 mov si,offset s14
 mov ax,blk_size
 call kv4
 call crlf
 mov si,offset s15
 mov ax,mapped
 call kv4
 mov si,offset s16
 mov al,mismatch
 call kv2
 mov si,offset s17
 mov ax,base_seg
 call kv4
 mov si,offset s18
 mov ax,first_p
 call kv4
 call crlf
 mov si,offset s19
 mov al,safe
 call kv2
 mov si,offset s20
 mov al,pattern_ran
 call kv2
 call crlf
 mov si,offset s21
 call puts
 call crlf

 mov dx,offset f_txt
 mov ah,3ch
 xor cx,cx
 int 21h
 jc setup_fail
 mov bx,ax
 mov cx,di
 sub cx,offset report
 mov dx,offset report
 mov ah,40h
 int 21h
 mov ah,3eh
 int 21h
 mov dx,offset m_ok
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h

setup_fail:
 push cs
 pop ds
 mov dx,offset m_err
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h

; SI = label, AL / AX = value. Appends at DS:DI.
kv2 proc near
 push ax
 call puts
 pop ax
 jmp hex2
kv2 endp

kv4 proc near
 push ax
 call puts
 pop ax
 jmp hex4
kv4 endp

puts proc near
 lodsb
 or al,al
 jz puts_done
 mov [di],al
 inc di
 jmp short puts
puts_done:
 ret
puts endp

crlf proc near
 mov word ptr [di],0a0dh
 add di,2
 ret
crlf endp

hex4 proc near
 push ax
 mov al,ah
 call hex2
 pop ax
hex2 label near
 push ax
 mov cl,4
 shr al,cl
 call hex1
 pop ax
hex1 label near
 and al,0fh
 add al,'0'
 cmp al,'9'
 jbe hex1_store
 add al,7
hex1_store:
 mov [di],al
 inc di
 ret
hex4 endp

report db 640 dup(0)
 even
stack_area db 512 dup(0)
stack_end label word
code ends
end entry
