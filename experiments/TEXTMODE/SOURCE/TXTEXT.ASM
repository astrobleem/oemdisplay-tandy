; Semantic text mirror: preserves canonical GDI bitmap, uses text cells for labels.
; Deliberately experimental: cell clipping and bitmap restore can lose semantics.
cProc TxString,<FAR,PUBLIC,WIN,PASCAL>,<ax,bx,cx,dx,si,di,es>
    parmW tx
    parmW ty
    parmD tclip
    parmD tstring
    parmW tcount
    parmD tfont
    parmD tmode
    localW pitch
    localW rowoff
    localW attr
cBegin
    cmp tcount,0
    jg txs_start
    jmp txs_done
 txs_start:
    cmp ty,0
    jge txs_posy
    jmp txs_done
 txs_posy:
    cmp ty,196
    jl txs_yok
    jmp txs_done
 txs_yok:
    mov ax,ty
    add ax,4
    shr ax,1
    shr ax,1
    shr ax,1
    mov bx,160
    mul bx
    mov rowoff,ax
    les bx,tfont
    mov ax,es:[bx].dfPixWidth
    or ax,ax
    jnz txs_pitch
    mov ax,es:[bx].dfAvgWidth
 txs_pitch:
    or ax,ax
    jnz txs_pitchok
    mov ax,8
 txs_pitchok:
    mov pitch,ax
    mov attr,0700h
    les bx,tmode
    mov ax,word ptr es:[bx].LTextColor
    or ax,word ptr es:[bx].LTextColor+2
    jnz txs_color
    mov attr,7000h
 txs_color:
    call cursor_hide
    xor si,si
 txs_char:
    cmp si,tcount
    jl txs_more
    jmp txs_finish
 txs_more:
    mov ax,tx
    cmp ax,0
    jl txs_next
    cmp ax,636
    jge txs_finish
    les bx,tclip
    mov dx,es
    or dx,bx
    jz txs_unclipped
    cmp ax,es:[bx]
    jl txs_next
    cmp ax,es:[bx+4]
    jge txs_next
    mov dx,ty
    cmp dx,es:[bx+2]
    jl txs_next
    cmp dx,es:[bx+6]
    jge txs_next
 txs_unclipped:
    add ax,4
    shr ax,1
    shr ax,1
    shr ax,1
    shl ax,1
    add ax,rowoff
    mov di,ax
    les bx,tstring
    add bx,si
    mov al,es:[bx]
    cmp al,32
    jb txs_next
    cmp al,127
    jae txs_next
    mov dx,attr
    mov ah,dh
    mov dx,0b800h
    mov es,dx
    mov tx_overlay[di],ax
    mov es:[di],ax
 txs_next:
    mov ax,pitch
    add tx,ax
    inc si
    jmp txs_char
 txs_finish:
    call cursor_show
 txs_done:
cEnd
