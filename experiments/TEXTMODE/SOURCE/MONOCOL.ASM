; Black/white matcher for the retained four-plane software renderer.
; MONOCOL.PY installs this as staged COLORS.ASM for 640x200x2.
; MASM 5.10 / 8086 only. Historical DDK and frozen V1 remain untouched.
;
; Squared RGB distances to black/white differ by 195075-510*(R+G+B).
; Thus white wins iff R+G+B >= 383; an integer RGB triplet cannot tie.
; Internal indices 0 and 15 duplicate the physical C0 into all four planes.
; This invariant is closed under every per-plane Boolean ROP, including NOT.
;
; rgb_to_ipc takes AL=R, AH=G, DL=B. Returns the nearest logical RGB in
; AL/AH/DL and DH=canonical index|accelerators. BX,CX,SI,DI,ES,BP,SP are
; preserved. DS becomes Data, matching the audited historical DDK contract.
.8086
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
    mov bx,ax                   ; BX = red
    mov al,dh
    mov cx,ax                   ; CX = green
    xor dh,dh
    add dx,bx
    add dx,cx                   ; DX = red+green+blue (0..765)
    xor bx,bx                   ; canonical black index
    cmp dx,383
    jb short bw_rgb_result
    mov bx,15                   ; canonical white index
bw_rgb_result:
    mov ax,bx
    mov dh,al
    or dh,cs:[bx].PAccelTable
    shl bx,1
    add bx,ax
    mov ax,word ptr cs:[bx].PColorTable
    mov dl,cs:[bx].PColorTable[2]
    mov ds,_cstods               ; historical caller-visible DS contract
cEnd

; Every raw four-plane DDB index aliases by C0, exactly as FlushShadow.
; Ignore incoming accelerator bits and canonicalize the returned index.
cProc IndexToColor,<FAR,PUBLIC>,<bx,si>
cBegin nogen
    push bx
    push si
    mov al,dh
    and ax,1
    neg ax
    and ax,15                   ; canonical index = 15*(index & 1)
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
