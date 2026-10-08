; Original isolated 8086 prototype. Raw module, no third-party code copied.
.8086
code segment para public 'CODE'
assume cs:code,ds:code
org 0
db 'LOGO'
jmp near ptr show
; Offset 7, all hide references are relative to this relocated CS.
hide:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push es
 push ds
 push cs
 pop ds
 cmp byte ptr active,0
 je hide_done
 mov byte ptr active,0
 mov ax,3
 int 10h
hide_done:
 pop ds
 pop es
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
active db 0
db 48-($-hide+7) dup(0)
resident_end label byte
show:
 pushf
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 push cs
 pop ds
 cld
 mov byte ptr active,0
 ; Original Tandy platform signatures, then normal 624K BIOS layout.
 mov ax,0ffffh
 mov es,ax
 cmp byte ptr es:[0eh],0ffh
 jne refuse_a
 mov ax,0fc00h
 mov es,ax
 cmp byte ptr es:[0],21h
 jne refuse_a
 mov ax,40h
 mov es,ax
 cmp word ptr es:[13h],624
 jne refuse_a
 mov ah,0fh
 int 10h
 cmp al,3
 jne refuse_a
 or bh,bh
 jne refuse_a
 ; Fail closed unless the existing RESERVE owns the overlap block.
 mov ax,97ffh
 mov es,ax
 cmp byte ptr es:[0],'Z'
 jne refuse_a
 cmp word ptr es:[3],400h
 jne refuse_a
 mov ax,es:[1]
 cmp ax,50h
 jb refuse_a
 cmp ax,97ffh
 jae refuse_a
 ; Validate the owner's own low-memory MCB, not only its marker bytes.
 mov bp,ax
 dec ax
 mov es,ax
 cmp byte ptr es:[0],'M'
 jne refuse_a
 cmp word ptr es:[1],bp
 jne refuse_a
 cmp word ptr es:[3],111
 jne refuse_a
 mov ax,bp
 add ax,111
 jc refuse_a
 cmp ax,97ffh
 ja refuse_a
 mov ax,bp
 mov es,ax
 cmp word ptr es:[103h],4e54h
 jne refuse_a
 cmp word ptr es:[105h],5944h
 jne refuse_a
 cmp word ptr es:[107h],5352h
 jne refuse_a
 cmp word ptr es:[109h],3130h
 jne refuse_a
 cmp word ptr es:[10bh],9800h
 jne refuse_a
 cmp word ptr es:[10dh],400h
 je begin_draw
refuse_a:
 jmp finish
begin_draw:
 mov ax,9
 int 10h
 mov byte ptr active,1
 call retrace
 call fixed_palette
 mov ax,0b800h
 mov es,ax
 xor di,di
 mov si,offset frame
 mov cx,16384
 rep movsw
 ; Accepted16-phase3.2-second wave:12 retrace edges per phase at60Hz.
 ; Palette stays fixed. Only precomputed flag-edge bytes change after draw.
 mov bp,16
 mov si,offset patches
 xor bx,bx
animate:
 mov di,12
hold_phase:
 mov ah,1
 int 16h
 jnz settle
 call retrace
 jc settle
 dec di
 jnz hold_phase
 call patch_next
 inc bx
 and bx,15
 dec bp
 jnz animate
settle:
 ; Restore exact accepted rest geometry on pending key or retrace timeout.
 ; Already phase0 needs no writes. No palette activity after initial setup.
 or bx,bx
 jz finish
 shl bx,1
 mov si,settle_offsets[bx]
 call patch_next
finish:
 mov ax,offset resident_end
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 popf
 retf
; Poll for an edge, bounded even if video status becomes stuck.
retrace proc near
 mov dx,03dah
 mov cx,0ffffh
wait_off:
 in al,dx
 test al,8
 jz off_ok
 loop wait_off
 stc
 ret
off_ok:
 mov cx,0ffffh
wait_on:
 in al,dx
 test al,8
 jnz on_ok
 loop wait_on
 stc
 ret
on_ok:
 clc
 ret
retrace endp
; Address 10h+index at 3DA, RGBI data at 3DE. No IRQ hooks.
fixed_palette proc near
 xor bx,bx
 mov di,1
 mov cx,4
palette_next:
 pushf
 cli
 mov dx,03dah
 in al,dx
 mov ax,di
 add al,10h
 out dx,al
 mov al,colors[bx]
 mov dx,03deh
 out dx,al
 ; Manual requires leaving a non-palette address selected before retrace ends.
 mov dx,03dah
 xor al,al
 out dx,al
 popf
 inc bx
 and bx,3
 inc di
 loop palette_next
 ret
fixed_palette endp
; DS:SI is count plus (banked framebuffer offset word,packed byte) records.
; Tables are host-verified and internal to this module. No DOS or IRQ hooks.
patch_next proc near
 push ax
 push cx
 push di
 push es
 mov ax,0b800h
 mov es,ax
 lodsw
 mov cx,ax
 jcxz patch_done
patch_byte:
 lodsw
 mov di,ax
 lodsb
 stosb
 loop patch_byte
patch_done:
 pop es
 pop di
 pop cx
 pop ax
 ret
patch_next endp
colors db 12,10,9,14
include WAVE.INC
include FRAME.INC
code ends
end

