; Original MIT 8086 static Windows 3.0 logo module. No Microsoft code copied.
.8086
code segment para public 'CODE'
assume cs:code,ds:code
org 0
db 'LOGO'
jmp near ptr show
; Relocated resident prefix: all state and instructions below fit 48 bytes.
hide:
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 mov al,cs:old_mode
 cmp al,0ffh
 je hide_done
 mov byte ptr cs:old_mode,0ffh
 xor ah,ah
 int 10h
hide_done:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 retf
old_mode db 0ffh
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
 mov byte ptr old_mode,0ffh
 mov ah,0fh
 int 10h
 cmp al,3
 jne show_done
 or bh,bh
 jne show_done
 call validate
 jc show_done
 mov byte ptr old_mode,3
 mov ax,6
 int 10h
 mov ax,0b800h
 mov es,ax
 mov si,offset rle+62
 mov bp,199
row_next:
 ; CGA row offset = (y/2)*80 + (y mod 2)*8192.
 mov ax,bp
 shr ax,1
 mov cx,80
 mul cx
 mov di,ax
 test bp,1
 jz bank_ready
 add di,2000h
bank_ready:
 xor bx,bx
pair_next:
 lodsw
 or al,al
 jz row_end
 xor ch,ch
 mov cl,al
 cmp ah,11h
 jne black_run
white_run:
 push cx
 mov ax,bx
 mov cx,ax
 and cx,7
 shr ax,1
 shr ax,1
 shr ax,1
 push di
 add di,ax
 mov al,80h
 shr al,cl
 or es:[di],al
 pop di
 inc bx
 pop cx
 loop white_run
 jmp pair_next
black_run:
 add bx,cx
 jmp pair_next
row_end:
 dec bp
 jns row_next
show_done:
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
; Verify the entire fixed original-art stream before touching video memory.
validate proc near
 mov si,offset rle
 mov di,offset header
 mov cx,31
check_header:
 lodsw
 cmp ax,[di]
 jne invalid
 add di,2
 loop check_header
 xor bx,bx
 xor dx,dx
check_pair:
 cmp si,offset rle+4060
 ja invalid
 lodsw
 or al,al
 jz command
 cmp ah,0
 je value_ok
 cmp ah,11h
 jne invalid
value_ok:
 cmp dx,200
 jae invalid
 xor ah,ah
 add bx,ax
 cmp bx,640
 ja invalid
 jmp check_pair
command:
 or ah,ah
 jnz end_bitmap
 cmp bx,640
 jne invalid
 inc dx
 cmp dx,200
 ja invalid
 xor bx,bx
 jmp check_pair
end_bitmap:
 cmp ah,1
 jne invalid
 cmp dx,200
 jne invalid
 or bx,bx
 jnz invalid
 cmp si,offset rle+4062
 jne invalid
 clc
 ret
invalid:
 stc
 ret
validate endp
; Header bytes are original format metadata, not third-party executable code.
header db 42h,4dh,0deh,0fh,0,0,0,0,0,0,3eh,0,0,0
 db 28h,0,0,0,80h,2,0,0,0c8h,0,0,0,1,0,1,0
 db 2,0,0,0,0a0h,0fh,0,0,0,0,0,0,0,0,0,0,2,0,0,0,0,0,0,0
 db 0,0,0,0,0ffh,0ffh,0ffh,0
rle label byte
code ends
end
