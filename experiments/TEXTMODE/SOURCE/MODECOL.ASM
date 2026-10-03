; Four-color matcher for the shared, four-plane software renderer.
; MODECOL.PY installs this as staged COLORS.ASM for four-color profiles.
; MASM 5.10 / 8086 only. The historical DDK source is never modified.
;
; Palettes: black/cyan/magenta/white or black/red/green/white.
; Tandy RGBI registers: 0,11,13,15 or 0,12,10,15 respectively.
; Logical RGB uses idealized 0/255 components; monitor levels differ.
; Internal indices 0,5,10,15 duplicate each physical bit across two planes.
; This set is closed under every per-plane Boolean ROP, including NOT.
;
; Each palette component is 0 or 255. Comparing Manhattan distances to
; these corners gives EXACTLY the same winner as squared RGB distance:
; each squared distance equals a common term + 255*Manhattan distance.
; Thus no multiply or 32-bit arithmetic is necessary. All distances are
; 0..765. Equal distances retain the earliest palette entry.
;
; rgb_to_ipc takes AL=R, AH=G, DL=B and returns AL=R, AH=G, DL=B of the
; nearest color, DH=index|accelerators. BX,CX,SI,DI,ES,BP are preserved;
; DS becomes Data, matching the original DDK contract.
.8086
MODECOL_RG equ 0 ; MODECOL.PY sets 1 for black/red/green/white
.xlist
include cmacros.inc
.list
sBegin Code
assumes cs,Code
assumes ds,nothing
assumes es,nothing
externB PAccelTable
externB PColorTable
externW _cstods

cProc rgb_to_ipc,<NEAR,PUBLIC>,<bx,cx,si,di>
cBegin
    mov dh,ah
    xor ah,ah
    mov bx,ax                   ; BX = R
    mov al,dh
    mov cx,ax                   ; CX = G
    xor dh,dh
    add dx,bx
    add dx,cx                   ; DX = R+G+B
    mov di,dx                   ; black distance
    xor si,si                   ; canonical black index

if MODECOL_RG
    mov ax,255
    add ax,dx
    sub ax,bx
    sub ax,bx                   ; red: (255-R)+G+B
else
    mov ax,510
    sub ax,dx
    add ax,bx
    add ax,bx                   ; cyan: R+(255-G)+(255-B)
endif
    cmp ax,di
    jae short mc_try_magenta
    mov di,ax
    mov si,5
mc_try_magenta:
if MODECOL_RG
    mov ax,255
    add ax,dx
    sub ax,cx
    sub ax,cx                   ; green: R+(255-G)+B
else
    mov ax,510
    sub ax,dx
    add ax,cx
    add ax,cx                   ; magenta: (255-R)+G+(255-B)
endif
    cmp ax,di
    jae short mc_try_white
    mov di,ax
    mov si,10
mc_try_white:
    mov ax,765
    sub ax,dx                   ; white: 765-R-G-B
    cmp ax,di
    jae short mc_rgb_result
    mov si,15
mc_rgb_result:
    mov bx,si
    mov ax,si
    mov dh,al
    or dh,cs:[bx].PAccelTable
    shl bx,1
    add bx,ax
    mov ax,word ptr cs:[bx].PColorTable
    mov dl,cs:[bx].PColorTable[2]
    mov ds,_cstods               ; historical caller-visible DS contract
cEnd

; Raw 4-plane DDB indices alias according to their low two bits, exactly
; as the physical flush does. Canonicalize the return value to 0/5/10/15.
; Ignore incoming accelerator bits, which could describe a different color.
cProc IndexToColor,<FAR,PUBLIC>,<bx,si>
cBegin nogen
    push bx
    push si
    mov al,dh
    and ax,3
    mov si,ax
    shl ax,1
    shl ax,1
    add ax,si                   ; canonical index = 5*(index & 3)
    mov bx,ax
    mov dh,al
    or dh,cs:[bx].PAccelTable
    mov si,bx
    shl bx,1
    add bx,si
    mov ax,word ptr cs:[bx].PColorTable
    mov dl,cs:[bx].PColorTable[2]
    pop si
    pop bx
    retf
cEnd nogen
sEnd Code
end
