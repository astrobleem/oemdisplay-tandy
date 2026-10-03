; TCURSOR.ASM - real-mode Tandy 320x200 monochrome software cursor.
; Cursor overlay lives only in VRAM. The renderer owns the shadow bitmap.
; cursor_hide / cursor_show nest and preserve all registers and FLAGS.
; MoveCursor defers while a flush or another cursor operation is active.

?PLM = 1
?WIN = 1
include cmacros.inc
include windefs.inc

sBegin Data
    externB enabled_flag
    tc_x            dw 160
    tc_y            dw 100
    tc_hot_x        dw 0
    tc_hot_y        dw 0
    tc_width        dw 0
    tc_height       dw 0
    tc_stride       dw 0
    tc_have         db 0
    tc_drawn        db 0
    tc_busy         db 0
    tc_pending      db 0
    tc_depth        dw 0
    tc_origin_x     dw 0
    tc_origin_y     dw 0
    tc_left         dw 0
    tc_right        dw 0
    tc_top          dw 0
    tc_bottom       dw 0
    tc_save_xbyte   dw 0
    tc_save_y       dw 0
    tc_save_rows    dw 0
    tc_save_bytes   dw 0
    tc_row_offset   dw 0
    tc_mask_row     dw 0
    tc_work_x       dw 0
    tc_work_y       dw 0
    tc_and          db 128 dup (0FFh)
    tc_xor          db 128 dup (0)
    tc_saved        db 544 dup (0)
sEnd Data

sBegin Code
assumes cs,Code
assumes ds,Data

; AX = Y (0..199), returns DI = banked scanline offset.
; Preserves BX, CX, DX; AX and DI are scratch.
tc_scan proc near
    push bx
    push cx
    push dx
    mov bx,ax
    and bx,3
    mov cl,13
    shl bx,cl
    shr ax,1
    shr ax,1
    mov dx,160
    mul dx
    mov di,ax
    add di,bx
    pop dx
    pop cx
    pop bx
    ret
tc_scan endp

; Restore only the byte rectangle saved under the previous cursor.
tc_erase proc near
    cmp tc_drawn,0
    je tce_done
    mov tc_drawn,0
    cmp enabled_flag,0
    je tce_done
    mov ax,0B800h
    mov es,ax
    mov si,offset tc_saved
    mov bx,tc_save_y
    mov bp,tc_save_rows
tce_row:
    mov ax,bx
    call tc_scan
    add di,tc_save_xbyte
    mov cx,tc_save_bytes
    cld
    rep movsb
    inc bx
    dec bp
    jnz tce_row
tce_done:
    ret
tc_erase endp

; Snapshot bounds were computed while tc_busy was acquired. Clip every edge.
tc_draw proc near
    cmp enabled_flag,0
    jne tcd_enabled
    ret
tcd_enabled:
    cmp tc_have,0
    jne tcd_have
    ret
tcd_have:
    mov ax,tc_origin_x
    mov tc_left,ax
    add ax,tc_width
    mov tc_right,ax
    mov ax,tc_origin_y
    mov tc_top,ax
    add ax,tc_height
    mov tc_bottom,ax
    cmp tc_left,0
    jge tcd_left
    mov tc_left,0
tcd_left:
    cmp tc_top,0
    jge tcd_top
    mov tc_top,0
tcd_top:
    cmp tc_right,320
    jle tcd_right
    mov tc_right,320
tcd_right:
    cmp tc_bottom,200
    jle tcd_bottom
    mov tc_bottom,200
tcd_bottom:
    mov ax,tc_left
    cmp ax,tc_right
    jl tcd_width_ok
    ret
tcd_width_ok:
    mov ax,tc_top
    cmp ax,tc_bottom
    jl tcd_visible
    ret
tcd_visible:
    mov tc_save_y,ax
    mov bx,tc_bottom
    sub bx,ax
    mov tc_save_rows,bx
    mov ax,tc_left
    shr ax,1
    mov tc_save_xbyte,ax
    mov bx,tc_right
    dec bx
    shr bx,1
    sub bx,ax
    inc bx
    mov tc_save_bytes,bx

    ; Save full touched bytes, including the unaffected edge nibble.
    mov ax,0B800h
    mov es,ax
    mov si,offset tc_saved
    mov bx,tc_save_y
    mov bp,tc_save_rows
tcd_save_row:
    mov ax,bx
    call tc_scan
    add di,tc_save_xbyte
    mov cx,tc_save_bytes
tcd_save_byte:
    mov al,es:[di]
    mov [si],al
    inc si
    inc di
    loop tcd_save_byte
    inc bx
    dec bp
    jnz tcd_save_row
    mov tc_drawn,1

    mov ax,tc_top
    mov tc_work_y,ax
tcd_row:
    mov ax,tc_work_y
    call tc_scan
    mov tc_row_offset,di
    mov ax,tc_work_y
    sub ax,tc_origin_y
    mul tc_stride
    mov tc_mask_row,ax
    mov ax,tc_left
    mov tc_work_x,ax
tcd_pixel:
    mov ax,tc_work_x
    sub ax,tc_origin_x
    mov cx,ax
    and cx,7
    mov bl,80h
    shr bl,cl
    shr ax,1
    shr ax,1
    shr ax,1
    add ax,tc_mask_row
    mov si,ax
    mov ax,tc_work_x
    shr ax,1
    mov di,tc_row_offset
    add di,ax
    mov dl,es:[di]
    mov al,dl
    test tc_work_x,1
    jnz tcd_low_read
    mov cl,4
    shr al,cl
tcd_low_read:
    and al,0Fh
    test tc_and[si],bl
    jnz tcd_and_done
    xor al,al
tcd_and_done:
    test tc_xor[si],bl
    jz tcd_xor_done
    xor al,0Fh
tcd_xor_done:
    test tc_work_x,1
    jnz tcd_low_write
    mov cl,4
    shl al,cl
    and dl,0Fh
    jmp short tcd_write
tcd_low_write:
    and dl,0F0h
tcd_write:
    or al,dl
    mov es:[di],al
    inc tc_work_x
    mov ax,tc_work_x
    cmp ax,tc_right
    jge tcd_next_row
    jmp tcd_pixel
tcd_next_row:
    inc tc_work_y
    mov ax,tc_work_y
    cmp ax,tc_bottom
    jge tcd_finished
    jmp tcd_row
tcd_finished:
    ret
tc_draw endp

; Caller owns tc_busy. Keep mouse interrupts enabled during pixel work.
; An interrupting MoveCursor only updates tc_x/tc_y and tc_pending.
tc_refresh proc near
tcr_again:
    pushf
    cli
    cmp tc_depth,0
    jne tcr_release
    mov tc_pending,0
    mov ax,tc_x
    sub ax,tc_hot_x
    mov tc_origin_x,ax
    mov ax,tc_y
    sub ax,tc_hot_y
    mov tc_origin_y,ax
    popf
    call tc_erase
    call tc_draw
    pushf
    cli
    cmp tc_pending,0
    je tcr_release
    popf
    jmp tcr_again
tcr_release:
    mov tc_busy,0
    popf
    ret
tc_refresh endp

; These two entry points must preserve the drawing DDI's return registers.
public cursor_hide
cursor_hide proc far
    pushf
    cli
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov ax,seg tc_x
    mov ds,ax
    inc tc_depth
    call tc_erase
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
cursor_hide endp

public cursor_show
cursor_show proc far
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
    mov ax,seg tc_x
    mov ds,ax
    pushf
    cli
    cmp tc_depth,0
    je tcs_depth_zero
    dec tc_depth
tcs_depth_zero:
    cmp tc_depth,0
    jne tcs_locked
    cmp tc_busy,0
    jne tcs_locked
    mov tc_busy,1
    popf
    call tc_refresh
    jmp short tcs_done
tcs_locked:
    popf
tcs_done:
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
cursor_show endp

cProc Inquire,<FAR,PUBLIC,WIN,PASCAL>,<di>
    parmD lpInfo
cBegin
    les di,lpInfo
    mov word ptr es:[di],1
    mov word ptr es:[di+2],1
    mov ax,4
cEnd

cProc SetCursor,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD lpShape
cBegin
    pushf
    cli
    cmp tc_busy,0
    je tcset_acquire
    jmp tcset_busy
tcset_acquire:
    mov tc_busy,1
    popf
    ; Helpers use BP as a row counter, so retain the Windows frame pointer.
    push bp
    call tc_erase
    pop bp
    mov tc_have,0
    les si,lpShape
    mov ax,es
    or ax,si
    jnz tcset_nonnull
    jmp tcset_finish
tcset_nonnull:
    mov ax,es:[si].csWidth
    or ax,ax
    jg tcset_valid1
    jmp tcset_invalid
tcset_valid1:
    cmp ax,32
    jle tcset_valid2
    jmp tcset_invalid
tcset_valid2:
    mov tc_width,ax
    mov bx,es:[si].csHeight
    or bx,bx
    jg tcset_valid3
    jmp tcset_invalid
tcset_valid3:
    cmp bx,32
    jle tcset_valid4
    jmp tcset_invalid
tcset_valid4:
    mov tc_height,bx
    mov dx,es:[si].csWidthBytes
    cmp dx,1
    jge tcset_valid5
    jmp tcset_invalid
tcset_valid5:
    cmp dx,4
    jle tcset_valid6
    jmp tcset_invalid
tcset_valid6:
    add ax,7
    shr ax,1
    shr ax,1
    shr ax,1
    cmp dx,ax
    jge tcset_valid7
    jmp tcset_invalid
tcset_valid7:
    mov tc_stride,dx
    mov ax,es:[si].csHotX
    or ax,ax
    jge tcset_valid8
    jmp tcset_invalid
tcset_valid8:
    cmp ax,tc_width
    jl tcset_valid9
    jmp tcset_invalid
tcset_valid9:
    mov tc_hot_x,ax
    mov ax,es:[si].csHotY
    or ax,ax
    jge tcset_valid10
    jmp tcset_invalid
tcset_valid10:
    cmp ax,tc_height
    jl tcset_valid11
    jmp tcset_invalid
tcset_valid11:
    mov tc_hot_y,ax
    mov ax,tc_height
    mul tc_stride
    mov cx,ax
    push cx
    add si,size cursorShape
    mov di,offset tc_and
tcset_and:
    mov al,es:[si]
    mov [di],al
    inc si
    inc di
    loop tcset_and
    pop cx
    mov di,offset tc_xor
tcset_xor:
    mov al,es:[si]
    mov [di],al
    inc si
    inc di
    loop tcset_xor
    mov tc_have,1
tcset_finish:
    push bp
    call tc_refresh
    pop bp
    mov ax,1
    jmp short tcset_end
tcset_invalid:
    mov tc_busy,0
    xor ax,ax
    jmp short tcset_end
tcset_busy:
    popf
    xor ax,ax
tcset_end:
cEnd

cProc MoveCursor,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmW absX
    parmW absY
cBegin
    pushf
    cli
    mov ax,absX
    mov tc_x,ax
    mov ax,absY
    mov tc_y,ax
    mov tc_pending,1
    cmp tc_depth,0
    jne tcm_defer
    cmp tc_busy,0
    jne tcm_defer
    mov tc_busy,1
    popf
    push bp
    call tc_refresh
    pop bp
    jmp short tcm_done
tcm_defer:
    popf
tcm_done:
    mov ax,1
cEnd

cProc CheckCursor,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
cBegin
    pushf
    cli
    cmp tc_depth,0
    jne tcc_defer
    cmp tc_busy,0
    jne tcc_defer
    cmp tc_pending,0
    jne tcc_refresh
    cmp tc_drawn,0
    jne tcc_defer
    cmp tc_have,0
    je tcc_defer
tcc_refresh:
    mov tc_busy,1
    popf
    push bp
    call tc_refresh
    pop bp
    jmp short tcc_done
tcc_defer:
    popf
tcc_done:
    mov ax,1
cEnd

sEnd Code
end
