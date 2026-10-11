; JRPROBE.ASM - PCjr/Tandy video memory probe for the proposed PCjr driver.
; MASM 5.1 syntax, .8086 only. Build as a COM (org 100h).
; See ../../docs/PCJR.MD. DOS-only; no Windows, no TSR, no MCB writes.
;
; What it records (JRPROBE.TXT, JRVRAM.BIN, JRB800.BIN in the current dir):
;  - BIOS model byte F000:FFFE (FDh = PCjr) and the Tandy FC00:0000 = 21h tag
;  - BIOS memory size (40:13) and the real DOS MCB arena end
;  - 40:8A (PCjr CRT/CPU page register copy) before and after INT 10h mode 9
;  - the physical segment of the displayed 32KB page, and whether that page
;    lies inside the DOS arena and which MCB owner holds it
;  - a 320x200x16 test pattern written with TANDY88's bank formula through
;    the page's PHYSICAL segment (PCjr) or B800h (others), then dumped back
;  - a separate 32KB dump of B800:0000 to measure B800/BC00 aliasing
;
; WARNING: on PCjr the page usually lives inside DOS memory. This probe
; writes the pattern there. Run it from a fresh boot with nothing resident
; you care about, and reboot afterwards.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

model_byte  db 0
tandy_tag   db 0
bios_kb     dw 0
arena_first dw 0
arena_end   dw 0
arena_ok    db 0
page_before db 0
page_after  db 0
mode_before db 0
mode_after  db 0
target_seg  dw 0b800h
video_mcb   dw 0
video_owner dw 0ffffh
video_size  dw 0
video_in    db 0

f_txt  db 'JRPROBE.TXT',0
f_vram db 'JRVRAM.BIN',0
f_b800 db 'JRB800.BIN',0

s_model db 'MODEL=',0
s_tag   db ' TANDYTAG=',0
s_kb    db 'BIOSKB=',0
s_first db ' ARENA_FIRST=',0
s_end   db ' ARENA_END=',0
s_aok   db ' ARENA_OK=',0
s_pb    db 'PAGE8A_BEFORE=',0
s_mb    db ' MODE_BEFORE=',0
s_ma    db ' MODE_AFTER=',0
s_pa    db ' PAGE8A_AFTER=',0
s_tseg  db 'TARGET_SEG=',0
s_vmcb  db ' VIDEO_MCB=',0
s_vown  db ' VIDEO_OWNER=',0
s_vin   db ' VIDEO_IN_ARENA=',0
s_vsz   db ' VIDEO_MCB_PARAS=',0
s_done  db 'COMPLETE=1',0
s_fail  db 'JRPROBE: file write failed',13,10,'$'
s_ok    db 'JRPROBE: wrote JRPROBE.TXT JRVRAM.BIN JRB800.BIN',13,10,'$'

start:
 push cs
 pop ds
 cld

 ; ---- machine identity -------------------------------------------------
 mov ax,0f000h
 mov es,ax
 mov al,es:[0fffeh]
 mov model_byte,al
 mov ax,0fc00h
 mov es,ax
 mov al,es:[0]
 mov tandy_tag,al
 mov ax,40h
 mov es,ax
 mov ax,es:[13h]
 mov bios_kb,ax
 mov al,es:[8ah]
 mov page_before,al

 ; ---- walk the real DOS arena (read only) ------------------------------
 mov ah,52h
 int 21h
 mov ax,es:[bx-2]
 mov arena_first,ax
walk:
 mov es,ax
 mov bl,es:[0]
 cmp bl,'M'
 je walk_ok
 cmp bl,'Z'
 jne walk_done            ; corrupt chain: arena_ok stays 0
walk_ok:
 mov dx,es:[3]
 add dx,ax
 inc dx                   ; DX = first paragraph after this block
 mov arena_end,dx
 cmp bl,'Z'
 je walk_last
 mov ax,dx
 jmp short walk
walk_last:
 mov arena_ok,1
walk_done:

 ; ---- enter mode 9 ----------------------------------------------------
 mov ah,0fh
 int 10h
 mov mode_before,al
 mov ax,9
 int 10h
 mov ah,0fh
 int 10h
 mov mode_after,al
 mov ax,40h
 mov es,ax
 mov al,es:[8ah]
 mov page_after,al
 cmp model_byte,0fdh
 jne target_ready
 ; PCjr: CRT page in bits 0-2, 16KB units -> paragraphs = page * 400h.
 and al,7
 xor ah,ah
 mov cl,10
 shl ax,cl
 mov target_seg,ax
target_ready:

 ; ---- which MCB holds the target page? (read only) ---------------------
 cmp arena_ok,1
 jne pattern
 mov ax,arena_first
find:
 mov es,ax
 mov dx,es:[3]
 add dx,ax
 inc dx
 mov bx,target_seg
 cmp bx,ax
 jbe find_next
 cmp bx,dx
 jae find_next
 mov video_mcb,ax
 mov bx,es:[1]
 mov video_owner,bx
 mov bx,es:[3]
 mov video_size,bx
 mov video_in,1
 jmp short pattern
find_next:
 cmp byte ptr es:[0],'Z'
 je pattern
 mov ax,dx
 jmp short find

 ; ---- write the 320x200x16 pattern with the TANDY88 formula -----------
 ; base = (y & 3) * 8192 + (y >> 2) * 160 + xb
 ; high nibble c = ((xb >> 3) + y) & 15, low nibble = c xor 15
; (y, not y>>3: every bank must differ so B800/BC00 aliasing is visible)
pattern:
 mov es,target_seg
 xor bp,bp                ; y
pat_row:
 mov ax,bp
 and ax,3
 mov cl,13
 shl ax,cl
 mov di,ax
 mov ax,bp
 shr ax,1
 shr ax,1
 mov cx,160
 mul cx
 add di,ax
 xor si,si                ; xb
pat_byte:
 mov ax,si
 mov cl,3
 shr ax,cl
 add ax,bp
 and al,0fh
 mov ah,al
 xor ah,0fh
 mov cl,4
 shl al,cl
 or al,ah
 stosb
 inc si
 cmp si,160
 jb pat_byte
 inc bp
 cmp bp,200
 jb pat_row

 ; ---- dump target page and the B800 window ---------------------------
 mov dx,offset f_vram
 mov ax,target_seg
 call dump32k
 jc failed
 mov dx,offset f_b800
 mov ax,0b800h
 call dump32k
 jc failed

 ; ---- back to the original mode ---------------------------------------
 mov al,mode_before
 xor ah,ah
 int 10h

 ; ---- text report ------------------------------------------------------
 mov di,offset report
 mov si,offset s_model
 call puts
 mov al,model_byte
 call hex2
 mov si,offset s_tag
 call puts
 mov al,tandy_tag
 call hex2
 call crlf
 mov si,offset s_kb
 call puts
 mov ax,bios_kb
 call hex4
 mov si,offset s_first
 call puts
 mov ax,arena_first
 call hex4
 mov si,offset s_end
 call puts
 mov ax,arena_end
 call hex4
 mov si,offset s_aok
 call puts
 mov al,arena_ok
 call hex2
 call crlf
 mov si,offset s_pb
 call puts
 mov al,page_before
 call hex2
 mov si,offset s_mb
 call puts
 mov al,mode_before
 call hex2
 mov si,offset s_ma
 call puts
 mov al,mode_after
 call hex2
 mov si,offset s_pa
 call puts
 mov al,page_after
 call hex2
 call crlf
 mov si,offset s_tseg
 call puts
 mov ax,target_seg
 call hex4
 mov si,offset s_vmcb
 call puts
 mov ax,video_mcb
 call hex4
 mov si,offset s_vown
 call puts
 mov ax,video_owner
 call hex4
 mov si,offset s_vin
 call puts
 mov al,video_in
 call hex2
 mov si,offset s_vsz
 call puts
 mov ax,video_size
 call hex4
 call crlf
 mov si,offset s_done
 call puts
 call crlf

 mov dx,offset f_txt
 mov ah,3ch
 xor cx,cx
 int 21h
 jc failed
 mov bx,ax
 mov cx,di
 sub cx,offset report
 mov dx,offset report
 mov ah,40h
 int 21h
 jc failed
 mov ah,3eh
 int 21h
 mov dx,offset s_ok
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h

failed:
 push cs
 pop ds
 mov al,mode_before
 xor ah,ah
 int 10h
 mov dx,offset s_fail
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h

; DS:DX = name (in CS), AX = source segment. Writes AX:0000-7FFF. CF on error.
dump32k proc near
 push ax
 mov ah,3ch
 xor cx,cx
 int 21h
 pop cx                   ; CX = source segment
 jc dump_err
 mov bx,ax
 push ds
 mov ds,cx
 xor dx,dx
 mov cx,8000h
 mov ah,40h
 int 21h
 pop ds
 jc dump_err
 mov ah,3eh
 int 21h
 clc
 ret
dump_err:
 stc
 ret
dump32k endp

; Append zero-terminated DS:SI at DS:DI.
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

report db 512 dup(0)
code ends
end entry
