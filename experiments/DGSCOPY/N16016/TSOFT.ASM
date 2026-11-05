; Reuses hatch/color/line-style tables from the existing Microsoft DDK
; DDK/286/DISPLAY/4PLANE/EGA/EGA.ASM; see PROVENANCE.md.
; Tandy software raster backend, 160x200x16, real mode Windows 3.0.
; All screen drawing goes to scan-interleaved four-plane RAM.
; Only FlushShadow touches Tandy VRAM. EGA hardware paths are unreachable.
?PLM=1
?WIN=1
incDevice=1
incControl=1
incFont=1
incDrawMode=1
include cmacros.inc
include gdidefs.inc
include display.inc
include mflags.inc
include ega.inc
include rlstrblt.inc
include rlfntseg.inc
externFP BitBlt
externFP Output
externFP GENDRAWKERNEL
externFP GENDECODE
externFP RealizeObject
externNP my_check_stack
externFP Pixel
externFP ScanLR
externFP RStrBlt
externFP RExtTextOut
externFP AllocSelector
externFP FreeSelector
externFP cursor_hide
externFP cursor_show
externFP cursor_begin_retain
externFP cursor_end_retain
externFP cursor_invalidate
public SCREEN_WIDTH,SCREEN_HEIGHT,SCREEN_W_BYTES,COLOR_FORMAT
public COLOR_DONT_CARE,COLOR_TBL_SIZE,PHYS_DEVICE_SIZE
SCREEN_WIDTH equ 160
SCREEN_HEIGHT equ 200
SCREEN_W_BYTES equ 20
COLOR_FORMAT equ 0104h
COLOR_DONT_CARE equ 0f07h
PHYS_DEVICE_SIZE equ size BITMAP
public PixelSeg_color_table,BlueMoonSeg_color_table
public H_HATCH_BR_0
public H_HATCH_BR_1
public H_HATCH_BR_2
public H_HATCH_BR_3
public H_HATCH_BR_4
public H_HATCH_BR_5
public H_HATCH_BR_6
public H_HATCH_BR_7
public V_HATCH_BR_0
public V_HATCH_BR_1
public V_HATCH_BR_2
public V_HATCH_BR_3
public V_HATCH_BR_4
public V_HATCH_BR_5
public V_HATCH_BR_6
public V_HATCH_BR_7
public D1_HATCH_BR_0
public D1_HATCH_BR_1
public D1_HATCH_BR_2
public D1_HATCH_BR_3
public D1_HATCH_BR_4
public D1_HATCH_BR_5
public D1_HATCH_BR_6
public D1_HATCH_BR_7
public D2_HATCH_BR_0
public D2_HATCH_BR_1
public D2_HATCH_BR_2
public D2_HATCH_BR_3
public D2_HATCH_BR_4
public D2_HATCH_BR_5
public D2_HATCH_BR_6
public D2_HATCH_BR_7
public CR_HATCH_BR_0
public CR_HATCH_BR_1
public CR_HATCH_BR_2
public CR_HATCH_BR_3
public CR_HATCH_BR_4
public CR_HATCH_BR_5
public CR_HATCH_BR_6
public CR_HATCH_BR_7
public DC_HATCH_BR_0
public DC_HATCH_BR_1
public DC_HATCH_BR_2
public DC_HATCH_BR_3
public DC_HATCH_BR_4
public DC_HATCH_BR_5
public DC_HATCH_BR_6
public DC_HATCH_BR_7
public HYPOTENUSE
public Y_MAJOR_DIST
public X_MAJOR_DIST
public Y_MINOR_DIST
public X_MINOR_DIST
public MAX_STYLE_ERR
public BW_THRESHOLD
H_HATCH_BR_0	equ	00000000b	;Horizontal Hatched brush
H_HATCH_BR_1	equ	00000000b
H_HATCH_BR_2	equ	00000000b
H_HATCH_BR_3	equ	00000000b
H_HATCH_BR_4	equ	11111111b
H_HATCH_BR_5	equ	00000000b
H_HATCH_BR_6	equ	00000000b
H_HATCH_BR_7	equ	00000000b

V_HATCH_BR_0	equ	00001000b	;Vertical Hatched brush
V_HATCH_BR_1	equ	00001000b
V_HATCH_BR_2	equ	00001000b
V_HATCH_BR_3	equ	00001000b
V_HATCH_BR_4	equ	00001000b
V_HATCH_BR_5	equ	00001000b
V_HATCH_BR_6	equ	00001000b
V_HATCH_BR_7	equ	00001000b

D1_HATCH_BR_0	equ	10000000b	;\ diagonal brush
D1_HATCH_BR_1	equ	01000000b
D1_HATCH_BR_2	equ	00100000b
D1_HATCH_BR_3	equ	00010000b
D1_HATCH_BR_4	equ	00001000b
D1_HATCH_BR_5	equ	00000100b
D1_HATCH_BR_6	equ	00000010b
D1_HATCH_BR_7	equ	00000001b

D2_HATCH_BR_0	equ	00000001b	;/ diagonal hatched brush
D2_HATCH_BR_1	equ	00000010b
D2_HATCH_BR_2	equ	00000100b
D2_HATCH_BR_3	equ	00001000b
D2_HATCH_BR_4	equ	00010000b
D2_HATCH_BR_5	equ	00100000b
D2_HATCH_BR_6	equ	01000000b
D2_HATCH_BR_7	equ	10000000b

CR_HATCH_BR_0	equ	00001000b	;+ hatched brush
CR_HATCH_BR_1	equ	00001000b
CR_HATCH_BR_2	equ	00001000b
CR_HATCH_BR_3	equ	00001000b
CR_HATCH_BR_4	equ	11111111b
CR_HATCH_BR_5	equ	00001000b
CR_HATCH_BR_6	equ	00001000b
CR_HATCH_BR_7	equ	00001000b

DC_HATCH_BR_0	equ	10000001b	;X hatched brush
DC_HATCH_BR_1	equ	01000010b
DC_HATCH_BR_2	equ	00100100b
DC_HATCH_BR_3	equ	00011000b
DC_HATCH_BR_4	equ	00011000b
DC_HATCH_BR_5	equ	00100100b
DC_HATCH_BR_6	equ	01000010b
DC_HATCH_BR_7	equ	10000001b



;-----------------------------------------------------------------------;
;	Line style definitions for the EGA Card
;
;	Since the style update code in the line DDA checks for a sign,
;	the values chosen for distances, HYPOTENUSE, and MAX_STYLE_ERR
;	must not be bigger than 127+min(X_MAJOR_DIST,Y_MAJOR_DIST).  If
;	this condition is met, then the sign bit will always be cleared
;	on the first subtraction after every add-back.
;-----------------------------------------------------------------------;


HYPOTENUSE	=	23		;Distance moving X and Y
Y_MAJOR_DIST	=	12		;Distance moving Y only
X_MAJOR_DIST	=	20		;Distance moving X only
Y_MINOR_DIST	=	HYPOTENUSE-X_MAJOR_DIST
X_MINOR_DIST	=	HYPOTENUSE-Y_MAJOR_DIST
MAX_STYLE_ERR	=	HYPOTENUSE*2	;Max error before updating
					;  rotating bit mask



;-----------------------------------------------------------------------;
;	The black/white threshold is used to determine the split
;	between black and white when summing an RGB Triplet
;-----------------------------------------------------------------------;


BW_THRESHOLD	equ	(3*0FFh)/2
page



; The absolute EGA workspace is referenced only by unused device paths.
EGAMem segment at 0
public current_brush,tonys_bar_n_grill,shadowed_mode,shadow_mem_status
public known_word,enable_test,plane_index,saved_latches
current_brush db 32 dup (?)
tonys_bar_n_grill db 32 dup (?)
shadowed_mode db ?
shadow_mem_status db ?
known_word dw ?
enable_test db ?
plane_index db ?
saved_latches db 4 dup (?)
EGAMem ends

createSeg _SHADOW,ShadowSeg,word,public,DATA
sBegin ShadowSeg
public shadow_bits
shadow_bits db 16000 dup (0)
sEnd ShadowSeg

sBegin Data
public enabled_flag,ScratchSel,is_protected,_cstods,diag_markers
ScratchSel dw 0
is_protected dw 0
enabled_flag db 0
old_mode db 3
diag_markers dw 0,0,0,0
public shadow_device
shadow_device BITMAP <0,160,200,20,4,1,0,4000,0,0,0,0,0,0>
sEnd Data

sBegin Code
assumes cs,Code
assumes ds,Data
public	PMatchTable1
public	PMatchTable2
public	PMatchTable3
public	PIndexTable1
public	PIndexTable2
public	PIndexTable3
public	PAccelTable
public	PColorTable
public	NUMBER_CL1_COLORS
public	NUMBER_CL2_COLORS
public	NUMBER_CL3_COLORS

NUMBER_CL1_COLORS	equ	3
NUMBER_CL2_COLORS	equ	3
NUMBER_CL3_COLORS	equ	4

PMatchTable1	label	byte
PMatchTable2	label	byte
	db	0
	db	80h
	db	0ffh

PMatchTable3	label	byte
	db	0
	db	40h
	db	082h
	db	0ffh

PIndexTable1	label	byte
	db	0
	db	1
	db	9

PIndexTable2	label	byte
	db	0
	db	3
	db	0bh

PIndexTable3	label	byte
	db	0
	db	8
	db	7
	db	0fh

PAccelTable label   byte
	db	20h
	db	00h
	db	00h
	db	00h
	db	00h
	db	00h
	db	00h
	db	00h
	db	00h
	db	00h
	db	10h
	db	10h
	db	00h
	db	10h
	db	10h
	db	30h

PColorTable label   byte
	db	0, 0, 0
	db	80h, 0, 0
	db	0, 80h, 0
	db	80h, 80h, 0
	db	0, 0, 80h
	db	80h, 0, 80h
	db	0, 80h, 80h
	db	080h, 080h, 080h
	db	40h, 40h, 40h
	db	0ffh, 0, 0
	db	0, 0ffh, 0
	db	0ffh, 0ffh, 0
	db	0, 0, 0ffh
	db	0ffh, 0, 0ffh
	db	0, 0ffh, 0ffh
	db	0ffh, 0ffh, 0ffh

;----------------------------------------------------------------------------;
; define two hack routines for EGA color tranalation. The first one makes    ;
; sure that we never return index 8 for a color in dh and next one forces    ;
; the brush pattern for solid brush to use index 7.			     ;
;----------------------------------------------------------------------------;
	
	public	EGAindex8to7
	public	RGB192Brush

EGAindex8to7	proc near

	cmp	dh,8			;are we about to return index 8
	jnz	@f			;no, we are ok
	mov	dh,7			;force it to be 7
@@:
	ret

EGAindex8to7	endp

RGB192Brush	proc near

	mov	ax,0ffffh		;value for the 3 color planes
	mov	cx,12			;12 words for 3 planes
	rep	stosw			;fill in the color planes
	inc	ax			;intensity is all 0's
	mov	cx,4			;4 word here
	rep	stosw			;do the intensity plane
	ret

RGB192Brush	endp
;----------------------------------------------------------------------------;



sEnd	Code
page

;-----------------------------------------------------------------------;
;	Color Table contains the color table definition.  The color
;	table is used for the GetColorTable Escape function and for
;	pen and brush enumeration.
;
;	This table must match the palette register values issued to
;	the EGA palette registers to get the colors in the color table.
;
;	The table is also used to take the color index which is
;	created for a GetPixel and turn it into a color which
;	sum_RGB_colors_alt can deal with.
;-----------------------------------------------------------------------;


COLOR_TBL_SIZE	equ	16		;16 entries in the table


createSeg _PIXEL,PixelSeg,word,public,CODE
sBegin	PixelSeg

PixelSeg_color_table	label	dword

;		dd	xxbbggrr
 		dd	00000000h	;Black
		dd	00000080h	;Dark Red
		dd	00008000h	;Dark Green
		dd	00008080h	;Mustard
		dd	00800000h	;Dark Blue
		dd	00800080h	;Purple
		dd	00808000h	;Turquoise
		dd	00808080h	;Gray
		dd	00404040h	;same color for user (dark in palette)
		dd	000000ffh	;Red
		dd	0000ff00h	;Green
		dd	0000ffffh	;Yellow
		dd	00ff0000h	;Blue
		dd	00ff00ffh	;Magenta
		dd	00FFFF00h	;Cyan
		dd	00ffffffh	;White

sEnd	PixelSeg
page

createSeg _BLUEMOON,BlueMoonSeg,word,public,CODE
sBegin	BlueMoonSeg

BlueMoonSeg_color_table label	dword

;		dd	xxbbggrr
		dd	00000000h	;Black
		dd	00000080h	;Dark Red
		dd	00008000h	;Dark Green
		dd	00008080h	;Mustard
		dd	00800000h	;Dark Blue
		dd	00800080h	;Purple
		dd	00808000h	;Turquoise
		dd	00808080h	;Gray
		dd	00404040h	;same color for user (dark in palette)
		dd	000000ffh	;Red
		dd	0000ff00h	;Green
		dd	0000ffffh	;Yellow
		dd	00ff0000h	;Blue
		dd	00ff00ffh	;Magenta
		dd	00FFFF00h	;Cyan
		dd	00ffffffh	;White

sEnd	BlueMoonSeg




sBegin Code
assumes cs,Code
assumes ds,Data

; The NE loader enters with DS pointing to automatic data.
_cstods dw seg enabled_flag
public driver_initialization
driver_initialization proc far
    mov ax,1
    retf
driver_initialization endp

; Convert red/green/blue/intensity planes into Tandy RGBI nibbles.
; 0=red,1=green,2=blue is the DDK's plane order, unlike Tandy BGRI.
get_nibble macro
    xor al,al
    shl dh,1
    rcl al,1
    shl ah,1
    rcl al,1
    shl bl,1
    rcl al,1
    shl bh,1
    rcl al,1
endm
public FlushShadow,FlushRows
FlushShadow proc near
    ; Full-screen callers retain the original synchronous conversion.
    push ax
    push bx
    xor ax,ax
    mov bx,SCREEN_HEIGHT
    call FlushRows
    pop bx
    pop ax
    ret

; AX is signed first row; BX is exclusive last row. Both are already
; overflow-checked by the caller. Clamp before touching the shadow.
; Preserve every register, and hide/show the cursor even for empty bounds.
FlushRows label near
    cmp enabled_flag,0
    jne flush_start
    ret
flush_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    cmp ax,0
    jge flush_first_clamped
    xor ax,ax
flush_first_clamped:
    cmp bx,SCREEN_HEIGHT
    jle flush_last_clamped
    mov bx,SCREEN_HEIGHT
flush_last_clamped:
    call cursor_hide
    cld
    cmp ax,bx
    jl flush_nonempty
    jmp flush_finished
flush_nonempty:
    mov bp,ax
    push bx
    mov cx,SCREEN_W_BYTES*4
    mul cx
    mov si,ax
    mov ax,seg shadow_bits
    mov ds,ax
    mov ax,0b800h
    mov es,ax
flush_row:
    mov ax,bp
    and ax,1
    mov cl,13
    shl ax,cl
    mov di,ax
    mov ax,bp
    shr ax,1
    mov cx,80
    mul cx
    add di,ax
    mov cx,20
flush_byte:
    mov ah,[si]
    mov bl,[si+20]
    mov bh,[si+40]
    mov dh,[si+60]
    rept 4
      get_nibble
      shl al,1
      shl al,1
      shl al,1
      shl al,1
      mov dl,al
      get_nibble
      or al,dl
      stosb
    endm
    inc si
    dec cx
    jz flush_next_row
    jmp flush_byte
flush_next_row:
    add si,60
    inc bp
    ; Keep the exclusive limit on our private stack across conversion.
    pop ax
    push ax
    cmp bp,ax
    jae flush_rows_finished
    jmp flush_row
flush_rows_finished:
    pop ax
flush_finished:
    pop es
    pop ds
    call cursor_show
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
flush_done:
    ret
FlushShadow endp

; CURKEEP: opt-in full physical rows. Two-byte token on caller SS.
public FlushRetainRows
FlushRetainRows proc near
    cmp enabled_flag,0
    jne keep_start
    ret
keep_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    sub sp,2
    cmp ax,0
    jge keep_first_clamped
    xor ax,ax
keep_first_clamped:
    cmp bx,SCREEN_HEIGHT
    jle keep_last_clamped
    mov bx,SCREEN_HEIGHT
keep_last_clamped:
    mov si,sp
    xor cx,cx
    mov dx,80
    call cursor_begin_retain
    cld
    cmp ax,bx
    jl keep_nonempty
    jmp keep_finished
keep_nonempty:
    mov bp,ax
    push bx
    mov cx,SCREEN_W_BYTES*4
    mul cx
    mov si,ax
    mov ax,seg shadow_bits
    mov ds,ax
    mov ax,0b800h
    mov es,ax
keep_row:
    mov ax,bp
    and ax,1
    mov cl,13
    shl ax,cl
    mov di,ax
    mov ax,bp
    shr ax,1
    mov cx,80
    mul cx
    add di,ax
    mov cx,20
keep_byte:
    mov ah,[si]
    mov bl,[si+20]
    mov bh,[si+40]
    mov dh,[si+60]
    rept 4
      get_nibble
      shl al,1
      shl al,1
      shl al,1
      shl al,1
      mov dl,al
      get_nibble
      or al,dl
      stosb
    endm
    inc si
    dec cx
    jz keep_next_row
    jmp keep_byte
keep_next_row:
    add si,60
    inc bp
    ; Keep the exclusive limit on our private stack across conversion.
    pop ax
    push ax
    cmp bp,ax
    jae keep_rows_finished
    jmp keep_row
keep_rows_finished:
    pop ax
keep_finished:
    mov si,sp
    call cursor_end_retain
    add sp,2
    pop es
    pop ds
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
keep_done:
    ret
FlushRetainRows endp

; CURKEEP: opt-in logical-byte columns; begin compares scaled physical bytes.
; SS:BP-12 token, other private locals identical to FlushColumns.
public FlushRetainColumns
FlushRetainColumns proc near
    cmp enabled_flag,0
    jne kcols_start
    ret
kcols_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bp,sp
    sub sp,12
    cmp ax,0
    jge kcols_first_row
    xor ax,ax
kcols_first_row:
    cmp bx,SCREEN_HEIGHT
    jle kcols_last_row
    mov bx,SCREEN_HEIGHT
kcols_last_row:
    cmp cx,0
    jge kcols_first_byte
    xor cx,cx
kcols_first_byte:
    cmp dx,SCREEN_W_BYTES
    jle kcols_last_byte
    mov dx,SCREEN_W_BYTES
kcols_last_byte:
    push cx
    push dx
    shl cx,1
    shl dx,1
    shl cx,1
    shl dx,1
    lea si,[bp-12]
    call cursor_begin_retain
    pop dx
    pop cx
    cld
    cmp ax,bx
    jl kcols_check_bytes
    jmp kcols_finished
kcols_check_bytes:
    cmp cx,dx
    jl kcols_nonempty
    jmp kcols_finished
kcols_nonempty:
    mov ss:[bp-2],ax
    mov ss:[bp-4],bx
    mov ss:[bp-6],cx
    sub dx,cx
    mov ss:[bp-8],dx
    mov bx,SCREEN_W_BYTES*4
    sub bx,dx
    mov ss:[bp-10],bx
    mov bx,SCREEN_W_BYTES*4
    mul bx
    mov si,ax
    add si,cx
    mov ax,seg shadow_bits
    mov ds,ax
    mov ax,0b800h
    mov es,ax
kcols_row:
    mov ax,ss:[bp-2]
    and ax,1
    mov cl,13
    shl ax,cl
    mov di,ax
    mov ax,ss:[bp-2]
    shr ax,1
    mov cx,80
    mul cx
    add di,ax
    mov ax,ss:[bp-6]
    shl ax,1
    shl ax,1
    add di,ax
    mov cx,ss:[bp-8]
kcols_byte:
    mov ah,[si]
    mov bl,[si+20]
    mov bh,[si+40]
    mov dh,[si+60]
    rept 4
      get_nibble
      shl al,1
      shl al,1
      shl al,1
      shl al,1
      mov dl,al
      get_nibble
      or al,dl
      stosb
    endm
    inc si
    dec cx
    jz kcols_next_row
    jmp kcols_byte
kcols_next_row:
    add si,ss:[bp-10]
    inc word ptr ss:[bp-2]
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jae kcols_finished
    jmp kcols_row
kcols_finished:
    lea si,[bp-12]
    call cursor_end_retain
    mov sp,bp
    pop es
    pop ds
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
FlushRetainColumns endp

; BYTECOL: synchronous logical-byte rectangle, independently clamped.
; AX=first row, BX=exclusive last row, CX=first byte, DX=exclusive last byte.
; Signed bounds; one logical byte represents eight horizontal pixels.
; Preserve all GPRs/segments/SP; CLD and enabled/empty behavior match FlushRows.
; Private SS:BP locals: -2 row, -4 last row, -6 first byte, -8 byte count,
; -10 shadow stride minus byte count. Never assume DS equals SS.
public FlushColumns
FlushColumns proc near
    cmp enabled_flag,0
    jne cols_start
    ret
cols_start:
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push bp
    push ds
    push es
    mov bp,sp
    sub sp,10
    cmp ax,0
    jge cols_first_row
    xor ax,ax
cols_first_row:
    cmp bx,SCREEN_HEIGHT
    jle cols_last_row
    mov bx,SCREEN_HEIGHT
cols_last_row:
    cmp cx,0
    jge cols_first_byte
    xor cx,cx
cols_first_byte:
    cmp dx,SCREEN_W_BYTES
    jle cols_last_byte
    mov dx,SCREEN_W_BYTES
cols_last_byte:
    call cursor_hide
    cld
    cmp ax,bx
    jl cols_check_bytes
    jmp cols_finished
cols_check_bytes:
    cmp cx,dx
    jl cols_nonempty
    jmp cols_finished
cols_nonempty:
    mov ss:[bp-2],ax
    mov ss:[bp-4],bx
    mov ss:[bp-6],cx
    sub dx,cx
    mov ss:[bp-8],dx
    mov bx,SCREEN_W_BYTES*4
    sub bx,dx
    mov ss:[bp-10],bx
    mov bx,SCREEN_W_BYTES*4
    mul bx
    mov si,ax
    add si,cx
    mov ax,seg shadow_bits
    mov ds,ax
    mov ax,0b800h
    mov es,ax
cols_row:
    mov ax,ss:[bp-2]
    and ax,1
    mov cl,13
    shl ax,cl
    mov di,ax
    mov ax,ss:[bp-2]
    shr ax,1
    mov cx,80
    mul cx
    add di,ax
    mov ax,ss:[bp-6]
    shl ax,1
    shl ax,1
    add di,ax
    mov cx,ss:[bp-8]
cols_byte:
    mov ah,[si]
    mov bl,[si+20]
    mov bh,[si+40]
    mov dh,[si+60]
    rept 4
      get_nibble
      shl al,1
      shl al,1
      shl al,1
      shl al,1
      mov dl,al
      get_nibble
      or al,dl
      stosb
    endm
    inc si
    dec cx
    jz cols_next_row
    jmp cols_byte
cols_next_row:
    add si,ss:[bp-10]
    inc word ptr ss:[bp-2]
    mov ax,ss:[bp-2]
    cmp ax,ss:[bp-4]
    jae cols_finished
    jmp cols_row
cols_finished:
    mov sp,bp
    pop es
    pop ds
    call cursor_show
    pop bp
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
FlushColumns endp

; Translate a screen argument in our private stack frame. The caller's
; descriptor is never modified. Ordinary and null bitmap pointers pass.
map_device macro arg,writes
local mapped
    les di,arg
    mov ax,es
    or ax,di
    jz mapped
    cmp word ptr es:[di],0
    je mapped
    mov word ptr arg,offset shadow_device
    mov word ptr arg+2,ds
    if writes
    mov dirty,1
    endif
mapped:
endm

cProc TBitBlt,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW dstx
    parmW dsty
    parmD src
    parmW sx
    parmW sy
    parmW xextent
    parmW yextent
    parmD rop
    parmD brush
    parmD mode
    localW dirty
    localW resync
cBegin
    mov dirty,0
    mov resync,0
    ; Fullscreen clients restore direct VRAM writes with an identity
    ; screen SRCCOPY (even 1x1). Keep that full shadow-resync contract.
    ; Inspect both real devices before map_device replaces descriptors.
    cmp word ptr rop,0020h
    jne TBitBlt_mapped
    cmp word ptr rop+2,00cch
    jne TBitBlt_mapped
    mov ax,dstx
    cmp ax,sx
    jne TBitBlt_mapped
    mov ax,dsty
    cmp ax,sy
    jne TBitBlt_mapped
    les di,dst
    mov ax,es
    or ax,di
    jz TBitBlt_mapped
    cmp word ptr es:[di],0
    je TBitBlt_mapped
    les di,src
    mov ax,es
    or ax,di
    jz TBitBlt_mapped
    cmp word ptr es:[di],0
    je TBitBlt_mapped
    mov resync,1
TBitBlt_mapped:
    map_device dst,1
    map_device src,0
    cCall BitBlt,<dst,dstx,dsty,src,sx,sy,xextent,yextent,rop,brush,mode>
    cmp dirty,0
    jne TBitBlt_dirty
    jmp TBitBlt_done
TBitBlt_dirty:
    ; DDK BitBlt relies on GDI-clipped destination geometry. Only an
    ; in-screen rectangle with positive, non-overflowing extents proves
    ; dirty row bounds. Anything outside that contract gets a full flush.
    ; Save the renderer return value while calculating dirty scanlines.
    push ax
    push bx
    push cx
    push dx
    cmp resync,0
    jne TBitBlt_full
    mov bx,xextent
    or bx,bx
    jle TBitBlt_full
    mov ax,dstx
    or ax,ax
    js TBitBlt_full
    add ax,bx
    jo TBitBlt_full
    cmp ax,SCREEN_WIDTH
    jg TBitBlt_full
    mov dx,ax
    mov bx,yextent
    or bx,bx
    jle TBitBlt_full
    mov ax,dsty
    or ax,ax
    js TBitBlt_full
    add bx,ax
    jo TBitBlt_full
    cmp bx,SCREEN_HEIGHT
    jg TBitBlt_full
    ; Proven in-screen geometry cannot overflow the byte rounding.
    ; Full-width spans retain the original FlushRows fast path.
    add dx,7
    shr dx,1
    shr dx,1
    shr dx,1
    mov cx,dstx
    shr cx,1
    shr cx,1
    shr cx,1
    or cx,cx
    jne TBitBlt_columns
    cmp dx,SCREEN_W_BYTES
    jne TBitBlt_columns
    call FlushRetainRows
    jmp short TBitBlt_flushed
TBitBlt_columns:
    call FlushRetainColumns
    jmp short TBitBlt_flushed
TBitBlt_full:
    call FlushShadow
TBitBlt_flushed:
    pop dx
    pop cx
    pop bx
    pop ax
TBitBlt_done:
cEnd


; OUTROWS: conservative far-span gate. ES:DI, CX=size (6/8/32/54).
; CF clear means nonnull, no offset/20-bit wrap, no canonical-shadow alias.
; Preserve every GPR and segment. SS:BP private locals; DS need not equal SS.
; No dereference, interrupt masking, callbacks, or persistent state.
or_require macro condition,failed
local accepted
    condition accepted
    jmp failed
accepted:
endm

public ORowsSpanSafe
ORowsSpanSafe proc near
    push bp
    mov bp,sp
    sub sp,12
    push ax
    push bx
    push cx
    push dx
    mov ax,es
    or ax,di
    or_require jnz,ors_bad
    mov ax,cx
    dec ax
    add ax,di
    or_require jnc,ors_bad
    mov ax,es
    mov bx,16
    mul bx
    add ax,di
    adc dx,0
    mov ss:[bp-2],ax
    mov ss:[bp-4],dx
    add ax,cx
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_input_ok
    or ax,ax
    or_require jz,ors_bad
ors_input_ok:
    mov ss:[bp-6],ax
    mov ss:[bp-8],dx
    mov ax,seg shadow_bits
    mul bx
    add ax,offset shadow_bits
    adc dx,0
    mov ss:[bp-10],ax
    mov ss:[bp-12],dx
    add ax,SCREEN_W_BYTES*4*SCREEN_HEIGHT
    adc dx,0
    cmp dx,10h
    or_require jbe,ors_bad
    jb ors_shadow_ok
    or ax,ax
    or_require jz,ors_bad
ors_shadow_ok:
    ; Object start >= shadow end, or object end <= shadow start.
    cmp ss:[bp-4],dx
    ja ors_good
    jb ors_before_end
    cmp ss:[bp-2],ax
    jae ors_good
ors_before_end:
    mov dx,ss:[bp-12]
    cmp ss:[bp-8],dx
    jb ors_good
    ja ors_bad
    mov ax,ss:[bp-10]
    cmp ss:[bp-6],ax
    jbe ors_good
ors_bad:
    stc
    jmp short ors_done
ors_good:
    clc
ors_done:
    pop dx
    pop cx
    pop bx
    pop ax
    mov sp,bp
    pop bp
    ret
ORowsSpanSafe endp


; Private ordinal501. One far pointer to30 bytes of request WORDs:
; x,y,w,h,logicalWidth,penStyle,penIndex,brushStyle,brushIndex,rop,
; clipLeft,clipTop,clipRight,clipBottom,complexClip.
; This is NOT Output; no physical pen can stand in for logicalWidth.
; No caller-supplied shadow, target, enabled flag or workspace is accepted.
; Provisional total stack budget2048 MUST be audited in native listings before run.
public TGenEllipse
TGenEllipse proc far
    push bp
    mov bp,sp
    pushf
    push bx
    push si
    push di
    push ds
    push es
    mov ax,seg enabled_flag
    mov ds,ax
    cmp enabled_flag,0
    jne GEntry_enabled
    jmp GEntry_reject
GEntry_enabled:
    cmp is_protected,0
    je GEntry_real
    jmp GEntry_reject
GEntry_real:
    mov ax,offset shadow_bits
    or ax,ax
    jz GEntry_shadow_origin_ok
    jmp GEntry_reject
GEntry_shadow_origin_ok:
    cmp bp,65525
    jbe GEntry_frame_valid
    jmp GEntry_reject
GEntry_frame_valid:
    ; my_check_stack ALLOCATES2048 on success. Restore only on success,
    ; then allocate712 bytes; remaining bound covers helper/flush call depth.
    mov ax,2048
    call my_check_stack
    jnc GEntry_stack_ok
    jmp GEntry_reject
GEntry_stack_ok:
    lea sp,[bp-12]
    les di,dword ptr ss:[bp+6]
    mov cx,30
    call ORowsSpanSafe
    jnc GEntry_source_range
    jmp GEntry_reject
GEntry_source_range:
    ; Reject any request intersecting reserved stack [BP-2060,BP+10).
    ; Compare physical20-bit addresses, so alternate-segment aliases reject.
    mov ax,es
    mov bx,16
    mul bx
    add ax,di
    adc dx,0
    mov si,ax
    mov cx,dx
    add ax,30
    adc dx,0
    push dx
    push ax
    mov ax,ss
    mul bx
    mov bx,bp
    sub bx,2060
    add ax,bx
    adc dx,0
    cmp word ptr ss:[bp-14],dx
    jb GEntry_source_good_pop
    ja GEntry_source_check_start
    cmp word ptr ss:[bp-16],ax
    jbe GEntry_source_good_pop
GEntry_source_check_start:
    add ax,2070
    adc dx,0
    cmp cx,dx
    ja GEntry_source_good_pop
    jb GEntry_source_bad_pop
    cmp si,ax
    jae GEntry_source_good_pop
GEntry_source_bad_pop:
    add sp,4
    jmp GEntry_reject
GEntry_source_good_pop:
    add sp,4
    sub sp,712
    ; Snapshot request into private SS context before any shadow mutation.
    ; Context[-56..-13], work[-696..-57], walk[-712..-697], pair[-724..-713].
    mov word ptr ss:[bp-56],offset shadow_bits
    mov ax,seg shadow_bits
    mov word ptr ss:[bp-54],ax
    mov word ptr ss:[bp-52],160
    mov word ptr ss:[bp-50],200
    mov word ptr ss:[bp-48],16
    mov word ptr ss:[bp-46],1
    mov word ptr ss:[bp-44],1
    mov si,di
    mov ax,es
    mov ds,ax
    mov ax,ss
    mov es,ax
    lea di,[bp-42]
    mov cx,15
    cld
    rep movsw
    mov ax,seg enabled_flag
    mov ds,ax
    ; FAR PASCAL explicit SS pointers; callee pops16 argument bytes.
    push ss
    lea ax,[bp-56]
    push ax
    push ss
    lea ax,[bp-696]
    push ax
    push ss
    lea ax,[bp-712]
    push ax
    push ss
    lea ax,[bp-724]
    push ax
    call GENDRAWKERNEL
    cmp ax,1
    je GEntry_complete
    ; Preserve -1 prewrite rejection or0 fatal. Never replay after partial draw.
    jmp GEntry_cleanup
GEntry_complete:
    mov ax,ss:[bp-40]
    mov bx,ax
    add bx,ss:[bp-36]
    mov cx,ss:[bp-42]
    mov dx,cx
    add dx,ss:[bp-38]
    push ss
    pop es
    lea di,[bp-22]
    call GEntryFlush
    mov ax,1
    jmp GEntry_cleanup
GEntry_reject:
    mov ax,-1
GEntry_cleanup:
    lea sp,[bp-12]
    pop es
    pop ds
    pop di
    pop si
    pop bx
    popf
    pop bp
    retf 4
TGenEllipse endp

GEntryFlush proc near
    push ax
    push bx
    push cx
    push dx
    push si
    cmp ax,0
    jge GEntry_top_screen
    xor ax,ax
GEntry_top_screen:
    cmp bx,SCREEN_HEIGHT
    jle GEntry_bottom_screen
    mov bx,SCREEN_HEIGHT
GEntry_bottom_screen:
    cmp cx,0
    jge GEntry_left_screen
    xor cx,cx
GEntry_left_screen:
    cmp dx,SCREEN_WIDTH
    jle GEntry_right_screen
    mov dx,SCREEN_WIDTH
GEntry_right_screen:
    mov si,es
    or si,di
    jz GEntry_bounds_ready
    cmp ax,es:[di+2]
    jge GEntry_top_clip
    mov ax,es:[di+2]
GEntry_top_clip:
    cmp bx,es:[di+6]
    jle GEntry_bottom_clip
    mov bx,es:[di+6]
GEntry_bottom_clip:
    cmp cx,es:[di]
    jge GEntry_left_clip
    mov cx,es:[di]
GEntry_left_clip:
    cmp dx,es:[di+4]
    jle GEntry_bounds_ready
    mov dx,es:[di+4]
GEntry_bounds_ready:
    cmp ax,bx
    jge GEntry_flush_done
    cmp cx,dx
    jge GEntry_flush_done
    shr cx,1
    shr cx,1
    shr cx,1
    add dx,7
    shr dx,1
    shr dx,1
    shr dx,1
    call FlushRetainColumns
GEntry_flush_done:
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    ret
GEntryFlush endp


; Controlled native fixture only: action1 query/realize, action-1 delete.
; Logical input is static10 bytes; output NULL or owned16-byte interior.
; This is not an ellipse handler or a production validation boundary.
public TPenFactory
TPenFactory proc far
    push bp
    mov bp,sp
    pushf
    push bx
    push si
    push di
    push ds
    push es
    mov ax,seg enabled_flag
    mov ds,ax
    cmp enabled_flag,0
    jne PTag_enabled
    jmp PTag_reject
PTag_enabled:
    cmp is_protected,0
    je PTag_real
    jmp PTag_reject
PTag_real:
    mov si,10
    mov dx,16
    cmp word ptr ss:[bp+14],1
    je PTag_action_ok
    cmp word ptr ss:[bp+14],-1
    je PTag_action_ok
    mov si,8
    mov dx,54
    cmp word ptr ss:[bp+14],2
    je PTag_action_ok
    cmp word ptr ss:[bp+14],-2
    je PTag_action_ok
    jmp PTag_reject
PTag_action_ok:
    mov ax,2048
    call my_check_stack
    jnc PTag_stack_ok
    jmp PTag_reject
PTag_stack_ok:
    lea sp,[bp-12]
    les di,dword ptr ss:[bp+10]
    mov cx,si
    call ORowsSpanSafe
    jnc PTag_logical_ok
    jmp PTag_reject
PTag_logical_ok:
    les di,dword ptr ss:[bp+6]
    mov ax,es
    or ax,di
    jz PTag_call
    mov cx,dx
    call ORowsSpanSafe
    jnc PTag_call
    jmp PTag_reject
PTag_call:
    push ds
    mov ax,offset shadow_device
    push ax
    push word ptr ss:[bp+14]
    push word ptr ss:[bp+12]
    push word ptr ss:[bp+10]
    push word ptr ss:[bp+8]
    push word ptr ss:[bp+6]
    xor ax,ax
    push ax
    push ax
    call RealizeObject
    jmp PTag_cleanup
PTag_reject:
    mov ax,-1
PTag_cleanup:
    lea sp,[bp-12]
    pop es
    pop ds
    pop di
    pop si
    pop bx
    popf
    pop bp
    retf 10
TPenFactory endp


; PRIVATE physical-object qualification only. Ordinary Output remains unchanged.
; One pointer to28-byte GenObjects. NULL device selects our genuine template;
; supplied device is validated as data and decoded (bitmap targets reject).
public TDecodeEllipse
TDecodeEllipse proc far
    push bp
    mov bp,sp
    pushf
    push bx
    push si
    push di
    push ds
    push es
    mov ax,seg enabled_flag
    mov ds,ax
    cmp enabled_flag,0
    or_require jne,DObj_reject
    cmp is_protected,0
    or_require je,DObj_reject
    cmp bp,65525
    or_require jbe,DObj_reject
    mov ax,offset shadow_bits
    or ax,ax
    or_require jz,DObj_reject
    ; Provisional outer budget includes nested TGenEllipse2048 probe.
    mov ax,2560
    call my_check_stack
    or_require jnc,DObj_reject
    lea sp,[bp-12]
    les di,dword ptr ss:[bp+6]
    mov cx,28
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
    sub sp,58
    ; SS packet[-40..-13], request[-70..-41].
    mov si,di
    mov ax,es
    mov ds,ax
    push ss
    pop es
    lea di,[bp-40]
    mov cx,14
    cld
    rep movsw
    mov ax,seg enabled_flag
    mov ds,ax
    mov ax,ss:[bp-36]
    or ax,ss:[bp-34]
    jnz DObj_external_device
    mov word ptr ss:[bp-36],offset physical_device
    mov ax,seg physical_device
    mov word ptr ss:[bp-34],ax
    jmp short DObj_points
DObj_external_device:
    les di,dword ptr ss:[bp-36]
    mov cx,32
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
DObj_points:
    les di,dword ptr ss:[bp-32]
    mov cx,8
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
    les di,dword ptr ss:[bp-28]
    mov cx,16
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
    les di,dword ptr ss:[bp-20]
    mov cx,32
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
    les di,dword ptr ss:[bp-24]
    mov ax,es
    or ax,di
    jz DObj_clip
    mov cx,54
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
DObj_clip:
    les di,dword ptr ss:[bp-16]
    mov ax,es
    or ax,di
    jz DObj_decode
    mov cx,8
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,DObj_reject
DObj_decode:
    push ss
    lea ax,[bp-40]
    push ax
    push ss
    lea ax,[bp-70]
    push ax
    call GENDECODE
    cmp ax,1
    jne DObj_cleanup
    push ss
    lea ax,[bp-70]
    push ax
    call TGenEllipse
    jmp short DObj_cleanup
DObj_reject:
    mov ax,-1
DObj_cleanup:
    lea sp,[bp-12]
    pop es
    pop ds
    pop di
    pop si
    pop bx
    popf
    pop bp
    retf 4
TDecodeEllipse endp

; AX=outer frame BP; ES:DI/CX=client object. Exclude shadow and complete reserved
; stack/frame physical range [outerBP-2572,outerBP+10), including aliases.
DObjSpanSafe proc near
    call ORowsSpanSafe
    jnc DObj_span_range
    ret
DObj_span_range:
    push bp
    mov bp,sp
    sub sp,14
    push ax
    push bx
    push cx
    push dx
    push si
    mov ss:[bp-2],ax
    mov ax,es
    mov bx,16
    mul bx
    add ax,di
    adc dx,0
    mov ss:[bp-4],ax
    mov ss:[bp-6],dx
    add ax,cx
    adc dx,0
    mov ss:[bp-8],ax
    mov ss:[bp-10],dx
    mov ax,ss
    mul bx
    mov bx,ss:[bp-2]
    sub bx,2572
    add ax,bx
    adc dx,0
    mov ss:[bp-12],ax
    mov ss:[bp-14],dx
    add ax,2582
    adc dx,0
    cmp ss:[bp-6],dx
    ja DObj_span_good
    jb DObj_span_before_end
    cmp ss:[bp-4],ax
    jae DObj_span_good
DObj_span_before_end:
    mov dx,ss:[bp-14]
    cmp ss:[bp-10],dx
    jb DObj_span_good
    ja DObj_span_bad
    mov ax,ss:[bp-12]
    cmp ss:[bp-8],ax
    jbe DObj_span_good
DObj_span_bad:
    stc
    jmp short DObj_span_cleanup
DObj_span_good:
    clc
DObj_span_cleanup:
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    mov sp,bp
    pop bp
    ret
DObjSpanSafe endp


; Private ordinal504. Read and clear the per-ellipse entry count.
public TCurveCount
TCurveCount proc far
    push ds
    mov ax,seg enabled_flag
    mov ds,ax
    mov ax,diag_markers+6
    mov word ptr diag_markers+6,0
    pop ds
    retf
TCurveCount endp
cProc TOutput,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW style
    parmW count
    parmD points
    parmD pen
    parmD brush
    parmD mode
    parmD clip
    localW dirty
    localW outrows
    localW firstrow
    localW lastrow
    localW firstcol
    localW lastcol
    localW routeResult
cBegin
    mov dirty,0
    mov outrows,0
    map_device dst,1
    ; Capture bounds before rendering. FULL is the fail-closed default.
    ; Restore all validation scratch state before the exact renderer call.
    pushf
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    cmp dirty,0
    or_require jne,TOutput_render
    ; WIDESCAN: bounded scan lists only. Thin-line gate stays count=2.
    cmp style,4
    jne TOutput_thin_count
    cmp count,2
    or_require jae,TOutput_render
    cmp count,64
    or_require jbe,TOutput_render
    jmp short TOutput_style_ok
TOutput_thin_count:
    ; Keep ellipse admission off the existing SCANLINES hot path.
    cmp style,7
    jne TOutput_nonellipse
    jmp GDIHook_from_bounds
TOutput_nonellipse:
    ; RRECT: GDI's OS_BEGINNSCAN/OS_ENDNSCAN markers draw nothing (the
    ; renderer returns -1 for them untouched): no copy, no cursor work.
    cmp style,80
    je TOutput_marker
    cmp style,81
    jne TOutput_not_marker
TOutput_marker:
    mov dirty,0
    jmp TOutput_render
TOutput_not_marker:
    cmp style,18
    or_require je,TOutput_render
    ; RRECT: two-point lines as before, and 3..N-point polylines.
    cmp count,2
    or_require jae,TOutput_render
    cmp count,1024
    or_require jbe,TOutput_render
TOutput_style_ok:
    les di,points
    mov cx,count
    shl cx,1
    shl cx,1
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    les di,mode
    mov cx,32
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    dec ax
    cmp ax,15
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    dec ax
    cmp ax,1
    or_require jbe,TOutput_render
    ; SCANLINE never reads clip. Do not newly dereference an ignored input.
    cmp style,4
    je TOutput_clip_ok
    les di,clip
    mov ax,es
    or ax,di
    jz TOutput_clip_ok
    mov cx,8
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    mov ax,es:[di]
    mov bx,es:[di+4]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    mov ax,es:[di+2]
    mov bx,es:[di+6]
    cmp ax,bx
    or_require jb,TOutput_render
    cmp bx,SCREEN_HEIGHT
    or_require jbe,TOutput_render
TOutput_clip_ok:
    cmp style,18
    je TOutput_check_pen
    les di,brush
    mov ax,es
    or ax,di
    jz TOutput_check_pen
    mov cx,54
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+40],0
    or_require je,TOutput_render
    jmp short TOutput_objects_ok
TOutput_check_pen:
    les di,pen
    mov cx,6
    call ORowsSpanSafe
    or_require jnc,TOutput_render
    cmp word ptr es:[di+4],4
    or_require jbe,TOutput_render
TOutput_objects_ok:
    les di,points
    cmp style,18
    je TOutput_polyline
    ; One Y shared by count-1 intervals. Rendering order/overlap unchanged.
    ; Validate the complete far span above, then every exclusive-X pair.
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov firstrow,ax
    inc ax
    mov lastrow,ax
    ; Points/mode spans and Y are already validated. For count=2,
    ; the exact [0,SCREEN_WIDTH) interval proves both X predicates.
    cmp count,2
    jne TOutput_scan_collect
    cmp word ptr es:[di+4],0
    jne TOutput_scan_collect
    cmp word ptr es:[di+6],SCREEN_WIDTH
    jne TOutput_scan_collect
    mov outrows,2
    jmp TOutput_render
TOutput_scan_collect:
    mov firstcol,SCREEN_WIDTH
    mov lastcol,0
    mov cx,count
    dec cx
TOutput_scan_interval:
    add di,4
    mov bx,es:[di]
    mov dx,es:[di+2]
    cmp bx,dx
    or_require jb,TOutput_render
    cmp dx,SCREEN_WIDTH
    or_require jbe,TOutput_render
    cmp bx,firstcol
    jae TOutput_scan_min
    mov firstcol,bx
TOutput_scan_min:
    cmp dx,lastcol
    jbe TOutput_scan_max
    mov lastcol,dx
TOutput_scan_max:
    loop TOutput_scan_interval
    jmp TOutput_bounded
TOutput_polyline:
    cmp count,2
    je TOutput_two_point
    ; RRECT: every point on the screen; rows = lowest..highest Y.
    mov firstcol,SCREEN_WIDTH
    mov lastcol,0
    mov cx,count
    mov ax,7fffh
    xor bx,bx
TOutput_poly_point:
    mov dx,es:[di]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    cmp dx,firstcol
    jae TOutput_poly_xmin
    mov firstcol,dx
TOutput_poly_xmin:
    inc dx
    cmp dx,lastcol
    jbe TOutput_poly_xmax
    mov lastcol,dx
TOutput_poly_xmax:
    mov dx,es:[di+2]
    cmp dx,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp dx,ax
    jae TOutput_poly_notmin
    mov ax,dx
TOutput_poly_notmin:
    cmp dx,bx
    jbe TOutput_poly_notmax
    mov bx,dx
TOutput_poly_notmax:
    add di,4
    loop TOutput_poly_point
    mov firstrow,ax
    inc bx
    mov lastrow,bx
    jmp TOutput_bounded
TOutput_two_point:
    mov cx,es:[di]
    cmp cx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov dx,es:[di+4]
    cmp dx,SCREEN_WIDTH
    or_require jb,TOutput_render
    mov ax,es:[di+2]
    cmp ax,SCREEN_HEIGHT
    or_require jb,TOutput_render
    mov bx,es:[di+6]
    cmp bx,SCREEN_HEIGHT
    or_require jb,TOutput_render
    cmp ax,bx
    jne TOutput_line_nonempty
    cmp cx,dx
    or_require jne,TOutput_render
TOutput_line_nonempty:
    cmp ax,bx
    jbe TOutput_line_ordered
    xchg ax,bx
TOutput_line_ordered:
    cmp cx,dx
    jbe TOutput_x_ordered
    xchg cx,dx
TOutput_x_ordered:
    mov firstcol,cx
    inc dx
    mov lastcol,dx
    mov firstrow,ax
    inc bx
    mov lastrow,bx
    jmp TOutput_bounded

GDIHook_from_bounds:
    ; Restore the exact post-map stack, registers and FLAGS before
    ; the unchanged native admission checks and private allocation.
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    ; GDIHOOK experimental native ellipse attempt. Every fallback restores
    ; incoming registers/flags before the original Output call.
    pushf
    cmp style,7
    or_require je,GDIHook_legacy_flags
    cmp dirty,1
    or_require je,GDIHook_legacy_flags
    ; Prevent 16-bit SS offset wrap before private packet/copy allocation.
    cmp sp,160
    or_require jae,GDIHook_legacy_flags
    cmp bp,2580
    or_require jae,GDIHook_legacy_flags
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push ds
    push es
    sub sp,36
    mov di,sp
    mov ax,style
    mov ss:[di],ax
    mov ax,count
    mov ss:[di+2],ax
    mov word ptr ss:[di+4],offset physical_device
    mov ax,seg physical_device
    mov ss:[di+6],ax
    mov ax,word ptr points
    mov ss:[di+8],ax
    mov ax,word ptr points+2
    mov ss:[di+10],ax
    mov ax,word ptr pen
    mov ss:[di+12],ax
    mov ax,word ptr pen+2
    mov ss:[di+14],ax
    mov ax,word ptr brush
    mov ss:[di+16],ax
    mov ax,word ptr brush+2
    mov ss:[di+18],ax
    mov ax,word ptr mode
    mov ss:[di+20],ax
    mov ax,word ptr mode+2
    mov ss:[di+22],ax
    mov ax,word ptr clip
    mov ss:[di+24],ax
    mov ax,word ptr clip+2
    mov ss:[di+26],ax
    ; Validate the ORIGINAL GDI point span before reading it. SS packet
    ; occupies28 bytes and the copied point buffer follows at +28..+35.
    les di,points
    mov cx,8
    mov ax,bp
    call DObjSpanSafe
    or_require jnc,GDIHook_norm_abort
    mov bx,sp
    les si,points
    mov ax,es
    push ds
    mov ds,ax
    push ss
    pop es
    lea di,[bx+28]
    mov cx,4
    cld
    rep movsw
    pop ds
    mov di,sp
    ; The observed GDI terminal point is inclusive. Do not overflow a
    ; signed WORD before passing the copy to the exclusive-end decoder.
    cmp word ptr ss:[di+32],7fffh
    je GDIHook_norm_abort
    cmp word ptr ss:[di+34],7fffh
    je GDIHook_norm_abort
    inc word ptr ss:[di+32]
    inc word ptr ss:[di+34]
    lea ax,[di+28]
    mov ss:[di+8],ax
    mov ax,ss
    mov ss:[di+10],ax
    push ss
    push di
    call TDecodeEllipse
    mov routeResult,ax
    jmp short GDIHook_norm_after
GDIHook_norm_abort:
    mov routeResult,-1
GDIHook_norm_after:
    add sp,36
    pop es
    pop ds
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    cmp routeResult,-1
    je GDIHook_fallback
    cmp routeResult,1
    jne GDIHook_return
    inc word ptr diag_markers+6
GDIHook_return:
    mov ax,routeResult
    popf
    jmp TOutput_done
GDIHook_fallback:
    popf
    jmp GDIHook_fallback_output
GDIHook_legacy_flags:
    popf
GDIHook_fallback_output:
    ; Only ellipse fallback can suppress a prewrite rejection flush.
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp ax,-1
    or_require jne,TOutput_done
    jmp TOutput_after_render

TOutput_bounded:
    mov outrows,1
TOutput_render:
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
    popf
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
TOutput_after_render:
    cmp dirty,0
    je TOutput_done
    ; Preserve the actual renderer result and all post-render GPRs.
    push ax
    push bx
    cmp outrows,0
    je TOutput_full
    mov ax,firstrow
    mov bx,lastrow
    cmp outrows,2
    je TOutput_rows
    cmp firstcol,0
    jne TOutput_columns
    cmp lastcol,SCREEN_WIDTH
    je TOutput_rows
TOutput_columns:
    push cx
    push dx
    mov cx,firstcol
    mov dx,lastcol
    add dx,7
    shr cx,1
    shr cx,1
    shr cx,1
    shr dx,1
    shr dx,1
    shr dx,1
    call FlushRetainColumns
    pop dx
    pop cx
    jmp short TOutput_flushed
TOutput_rows:
    call FlushRetainRows
    jmp short TOutput_flushed
TOutput_full:
    call FlushShadow
TOutput_flushed:
    pop bx
    pop ax
TOutput_done:
cEnd

cProc TPixel,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW x
    parmW y
    parmD color
    parmD mode
    localW dirty
cBegin
    mov dirty,0
    map_device dst,1
    ; NULL draw mode means GetPixel: the renderer only reads shadow RAM.
    mov ax,word ptr mode
    or ax,word ptr mode+2
    jnz TPixel_render
    mov dirty,0
TPixel_render:
    cCall Pixel,<dst,x,y,color,mode>
    cmp dirty,0
    je TPixel_done
    push ax
    push bx
    push cx
    push dx
    ; The renderer clips SetPixel to the destination bitmap dimensions.
    ; Out-of-bounds pixels still pair cursor hide/show but convert no row.
    xor ax,ax
    xor bx,bx
    xor cx,cx
    xor dx,dx
    cmp x,0
    jl TPixel_flush
    cmp x,SCREEN_WIDTH
    jge TPixel_flush
    cmp y,0
    jl TPixel_flush
    cmp y,SCREEN_HEIGHT
    jge TPixel_flush
    mov ax,y
    mov bx,ax
    inc bx
    mov cx,x
    shr cx,1
    shr cx,1
    shr cx,1
    mov dx,cx
    inc dx
    call FlushRetainColumns
    jmp short TPixel_flushed
TPixel_flush:
    call FlushColumns
TPixel_flushed:
    pop dx
    pop cx
    pop bx
    pop ax
TPixel_done:
cEnd

cProc TScanLR,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW x
    parmW y
    parmD color
    parmW style
    localW dirty
cBegin
    mov dirty,0
    map_device dst,1
    cCall ScanLR,<dst,x,y,color,style>
cEnd

; Text bounds are deliberately conservative. FONTINFO starts at fsType,
; not the file header. Use the renderer's actual DDK structures and assert
; their relationship. The real-mode GDI caller still owns pointer validity;
; these checks reject null/segment-wrapping descriptors, not arbitrary RAM.
.errnz (offset fsType)-42h
.errnz (offset fsVersion)
.errnz dfType
.errnz PF_RASTER_TYPE
.errnz dfPixHeight-16h
.errnz ftAccelerator-0fh
.errnz (offset fsPixHeight)-(offset fsType)-dfPixHeight
.errnz (offset fsWeight)-(offset fsType)-dfWeight
.errnz ETO_OPAQUE_FILL-2
.errnz ETO_OPAQUE_CLIP-4

; 8086 conditionals cannot branch beyond 128 bytes. Use a nearby accepted
; branch followed by a near failure jump. All MASM 5 arguments are explicit.
text_require macro condition,failed
local accepted
    condition accepted
    jmp failed
accepted:
endm

text_pointer macro pointer,span,failed
    les di,pointer
    mov ax,es
    or ax,ax
    text_require jnz,failed
    cmp di,0ffffh-(span-1)
    text_require jbe,failed
endm

; Read the entire RECT only after the far-pointer boundary check. Empty
; ordered rectangles are safe; reducing the interval by clipping is optional.
text_rectangle macro pointer,failed
    text_pointer pointer,<size RECT>,failed
    mov ax,es:[di].left
    or ax,ax
    text_require jns,failed
    cmp ax,es:[di].right
    text_require jle,failed
    cmp word ptr es:[di].right,SCREEN_WIDTH
    text_require jle,failed
    mov ax,es:[di].top
    or ax,ax
    text_require jns,failed
    cmp ax,es:[di].bottom
    text_require jle,failed
    cmp word ptr es:[di].bottom,SCREEN_HEIGHT
    text_require jle,failed
endm

; Snapshot only final row endpoints before the unchanged renderer call.
; dirty=0 means no flush, 1 full flush, and 2 proven full-width row interval.
; The last three macro arguments are explicit even for ordinary StrBlt.
text_bounds macro extended,optr,opts
local finished,restore,top_kept,bottom_kept,widths_checked
    cmp dirty,0
    text_require jne,finished
    cmp count,0
    text_require jg,finished
    push ax
    push bx
    push cx
    push dx
    push si
    push di
    push es
    ; Positive strings must not wrap their segment. This is a selector
    ; guard only; real-mode GDI still guarantees the allocation is readable.
    les di,string
    mov ax,es
    or ax,ax
    text_require jnz,restore
    mov ax,count
    dec ax
    add ax,di
    text_require jnc,restore
    if extended
    ; A null width vector is normal. A supplied vector has count WORDs.
    les di,dxs
    mov ax,es
    or ax,di
    jz widths_checked
    mov ax,es
    or ax,ax
    text_require jnz,restore
    mov ax,count
    shl ax,1
    text_require jnc,restore
    dec ax
    add ax,di
    text_require jnc,restore
 widths_checked:
    endif
    ; Font: the exact raster FONTINFO layout accepted by get_font.
    text_pointer font,<size FONTINFO>,restore
    cmp di,offset fsType
    text_require je,restore
    cmp word ptr es:fsVersion,0200h
    text_require je,restore
    test word ptr es:[di].dfType,not PF_BITS_IS_ADDRESS
    text_require jz,restore
    cmp byte ptr es:[di].dfItalic,0
    text_require je,restore
    cmp byte ptr es:[di].dfUnderline,0
    text_require je,restore
    cmp byte ptr es:[di].dfStrikeOut,0
    text_require je,restore
    mov bx,es:[di].dfPixHeight
    or bx,bx
    text_require jg,restore
    mov cx,es:[di].dfWeight
    ; No rotation, scaling in Y, synthetic weight, or decoration. Width
    ; is intentionally unconstrained: SYSTEM_FONT is proportional.
    text_pointer xform,<size TEXTXFORM>,restore
    cmp es:[di].ftHeight,bx
    text_require je,restore
    cmp word ptr es:[di].ftEscapement,0
    text_require je,restore
    cmp word ptr es:[di].ftOrientation,0
    text_require je,restore
    cmp es:[di].ftWeight,cx
    text_require je,restore
    cmp byte ptr es:[di].ftItalic,0
    text_require je,restore
    cmp byte ptr es:[di].ftUnderline,0
    text_require je,restore
    cmp byte ptr es:[di].ftStrikeOut,0
    text_require je,restore
    cmp word ptr es:[di].ftAccelerator,0
    text_require je,restore
    cmp word ptr es:[di].ftOverhang,0
    text_require je,restore
    text_pointer mode,<size DRAWMODE>,restore
    cmp word ptr es:[di].bkMode,TRANSPARENT
    text_require jge,restore
    cmp word ptr es:[di].bkMode,OPAQUE
    text_require jle,restore
    text_rectangle clip,restore
    ; Prove signed y+h cannot overflow and is wholly on screen.
    mov si,y
    or si,si
    text_require jns,restore
    mov dx,si
    add dx,bx
    text_require jno,restore
    cmp dx,SCREEN_HEIGHT
    text_require jle,restore
    if extended
    test opts,not (ETO_OPAQUE_FILL+ETO_OPAQUE_CLIP)
    text_require jz,restore
    test opts,ETO_OPAQUE_FILL+ETO_OPAQUE_CLIP
    jz bottom_kept
    text_rectangle optr,restore
    ; Bit 2 fills, bit 4 only clips (the archived prose reverses these).
    test opts,ETO_OPAQUE_FILL
    jz bottom_kept
    mov ax,es:[di].top
    cmp si,ax
    jle top_kept
    mov si,ax
 top_kept:
    mov ax,es:[di].bottom
    cmp dx,ax
    jge bottom_kept
    mov dx,ax
 bottom_kept:
    endif
    mov rowfirst,si
    mov rowlast,dx
    mov dirty,2
 restore:
    pop es
    pop di
    pop si
    pop dx
    pop cx
    pop bx
    pop ax
 finished:
endm

text_flush macro
local full,done
    push ax
    push bx
    cmp dirty,2
    jne full
    mov ax,rowfirst
    mov bx,rowlast
    call FlushRows
    jmp short done
 full:
    call FlushShadow
 done:
    pop bx
    pop ax
endm

cProc TStrBlt,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW x
    parmW y
    parmD clip
    parmD string
    parmW count
    parmD font
    parmD mode
    parmD xform
    localW dirty
    localW rowfirst
    localW rowlast
cBegin
    mov dirty,0
    map_device dst,1
    ; Negative count requests extents. Zero can still paint an opaque rect.
    cmp count,0
    jge TStrBlt_render
    mov dirty,0
TStrBlt_render:
    text_bounds 0,0,0
    cCall RStrBlt,<dst,x,y,clip,string,count,font,mode,xform>
    cmp dirty,0
    je TStrBlt_done
    text_flush
TStrBlt_done:
cEnd

cProc TExtTextOut,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD dst
    parmW x
    parmW y
    parmD clip
    parmD string
    parmW count
    parmD font
    parmD mode
    parmD xform
    parmD dxs
    parmD opaquerect
    parmW options
    localW dirty
    localW rowfirst
    localW rowlast
cBegin
    mov dirty,0
    map_device dst,1
    ; Negative count requests extents. Zero can still paint an opaque rect.
    cmp count,0
    jge TExtTextOut_render
    mov dirty,0
TExtTextOut_render:
    text_bounds 1,opaquerect,options
    cCall RExtTextOut,<dst,x,y,clip,string,count,font,mode,xform,dxs,opaquerect,options>
    cmp dirty,0
    je TExtTextOut_done
    text_flush
TExtTextOut_done:
cEnd

sEnd Code

createSeg _INIT,InitSeg,word,public,CODE
sBegin InitSeg
assumes cs,InitSeg
assumes ds,Data
physical_device BITMAP <1,160,200,20,4,1,0,4000,0,0,0,0,0,0>
info_table label byte
    dw 0300h,DT_RASDISPLAY,240,180,160,200,1,4
    dw -1,80,0,0,16,size BITMAP
    dw CC_ELLIPSES,LC_POLYLINE+LC_STYLED,PC_SCANLINE
    dw TC_CP_STROKE+TC_RA_ABLE,CP_RECTANGLE
    dw RC_BITBLT+RC_BITMAP64+RC_GDI20_OUTPUT+RC_OP_DX_OUTPUT+RC_DI_BITMAP+RC_DIBTODEV
    dw X_MAJOR_DIST,Y_MAJOR_DIST,HYPOTENUSE,MAX_STYLE_ERR
    dw 2400,1800,160,-200
    dw 24000,18000,160,-200
    dw 1500,900,254,-254
    dw 15000,9000,254,-254
    dw 21600,6480,254,-127
    dw 96,48,DC_IgnoreDFNP
    dw 0,0,0,0,0,0,0,0
.errnz ($-info_table)-(size GDIINFO)


; V6355D hardware transaction. BIOS initializes CGA timing first. No writes to
; Yamaha timing/centering registers 64h..67h: preserve monitor calibration.
; All ports require DX: an immediate OUT would truncate 03DDh to DDh.
; RGB333 applies to analog RGB/SCART. Digital RGBI remains fixed 16 colors.
yam_palette db 000h,000h,000h,005h,000h,050h,000h,055h,005h,000h,005h,005h,005h,020h,005h,055h,002h,022h,002h,027h,002h,072h,002h,077h,007h,022h,007h,027h,007h,072h,007h,077h
YamEnter proc near
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
    mov ax,0004h
    int 10h
    cli
    mov dx,03d8h
    mov al,04ah
    out dx,al
    mov dx,03d9h
    xor al,al
    out dx,al
    mov dx,03ddh
    mov al,040h
    out dx,al
    mov dx,03deh
    mov si,offset yam_palette
    mov cx,32
YamPaletteLoop:
    mov al,cs:[si]
    out dx,al
    inc si
    loop YamPaletteLoop
    mov dx,03ddh
    mov al,080h
    out dx,al
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
    ret
YamEnter endp

; Close any extended transaction, then BIOS restores the saved ordinary mode.
; Preserve FLAGS, including a caller which entered with interrupts disabled.
YamLeave proc near
    pushf
    push ax
    push dx
    cli
    mov dx,03ddh
    mov al,080h
    out dx,al
    pop dx
    pop ax
    popf
    ret
YamLeave endp

cProc TEnable,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD device
    parmW style
    parmD devtype
    parmD outfile
    parmD stuff
cBegin
    mov word ptr diag_markers,1111h
    cld
    les di,device
    test style,1
    jz enable_device
    push ds
    push cs
    pop ds
    mov si,offset info_table
    mov cx,size GDIINFO
    rep movsb
    pop ds
    mov ax,size GDIINFO
    jmp enable_done
enable_device:
    push ds
    push cs
    pop ds
    mov si,offset physical_device
    mov cx,size BITMAP
    rep movsb
    pop ds
    mov ax,seg shadow_bits
    mov word ptr shadow_device.bmBits+2,ax
    mov word ptr shadow_device.bmBits,offset shadow_bits
    cmp enabled_flag,0
    jne enable_ok
    call cursor_invalidate
    xor ax,ax
    cCall AllocSelector,<ax>
    mov ScratchSel,ax
    mov ah,0fh
    int 10h
    mov old_mode,al
    call YamEnter
    mov ax,seg shadow_bits
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,8000
    cld
    rep stosw
    mov enabled_flag,1
    mov word ptr diag_markers+4,3333h
enable_ok:
    mov ax,1
enable_done:
cEnd

cProc TDisable,<FAR,PUBLIC,WIN,PASCAL>
    parmD device
cBegin
    mov word ptr diag_markers+2,2222h
    pushf
    cli
    mov enabled_flag,0
    call cursor_invalidate
    popf
    call YamLeave
    mov al,old_mode
    xor ah,ah
    int 10h
    mov ax,ScratchSel
    or ax,ax
    jz disable_done
    cCall FreeSelector,<ax>
    mov ScratchSel,0
disable_done:
    mov ax,1
cEnd
sEnd InitSeg

createSeg _BLUEMOON,BlueMoonSeg,word,public,CODE
sBegin BlueMoonSeg
assumes cs,BlueMoonSeg
cProc TControl,<FAR,PUBLIC,WIN,PASCAL>,<si,di>
    parmD device
    parmW function
    parmD input
    parmD output
cBegin
    xor ax,ax
    les di,input
    mov bx,function
    cmp bx,QUERYESCSUPPORT
    jne control_color
    mov bx,es:[di]
    cmp bx,QUERYESCSUPPORT
    je control_ok
    cmp bx,GETCOLORTABLE
    je control_ok
    jmp control_done
control_color:
    cmp bx,GETCOLORTABLE
    jne control_done
    mov si,es:[di]
    cmp si,16
    jae control_done
    shl si,1
    shl si,1
    les di,output
    mov ax,word ptr cs:BlueMoonSeg_color_table[si]
    mov es:[di],ax
    mov ax,word ptr cs:BlueMoonSeg_color_table[si+2]
    mov es:[di+2],ax
control_ok:
    mov ax,1
control_done:
cEnd

cProc DeviceBitmap,<FAR,PUBLIC,WIN,PASCAL>
    parmD lpDevice
    parmW command
    parmD lpBitmap
    parmD lpBits
cBegin
    xor ax,ax
cEnd
cProc SetAttribute,<FAR,PUBLIC,WIN,PASCAL>
    parmD lpDevice
    parmW stateNum
    parmW index
    parmD attribute
cBegin
    xor ax,ax
cEnd
cProc UserRepaintDisable,<FAR,PUBLIC,WIN,PASCAL>
    parmW flag
cBegin
    xor ax,ax
cEnd
sEnd BlueMoonSeg
createSeg  _DIMAPS,DIMapSeg,word,public,code
sBegin	DIMapSeg
;--------------------------------------------------------------------------
;This color table is copied into the DIB on a GetDIBitmap call.  The color
;entries in a DIB (RGBQUAD structure) are reversed from the colortables 
;maintained in this driver.  Therefore, any changes to the colortables 
;above should be made to the following table as well but in a reversed 
;order, i.e., xxbbggrr => xxrrggbb.
;--------------------------------------------------------------------------
public DIMapSeg_color_table
DIMapSeg_color_table label	dword

if NUMBER_PLANES eq 4

;		dd	xxrrggbb
		dd	00000000h		;Black
		dd	00800000h		;Dark Red
		dd	00008000h		;Dark Green
		dd	00808000h		;Mustard
		dd	00000080h		;Dark Blue
		dd	00800080h		;Purple
		dd	00008080h		;Turquoise
		dd	00808080h		;grey
		dd	00404040h		;same color for user (dark in palette)
		dd	00ff0000h		;Red
		dd	0000ff00h		;Green
		dd	00ffff00h		;Yellow
		dd	000000ffh		;Blue
		dd	00ff00ffh		;Magenta
		dd	0000ffffh		;Cyan
		dd	00ffffffh		;White

else

		dd	00000000h		;Black
		dd	00ff0000h		;Red
		dd	0000ff00h		;Green
		dd	00ffff00h		;Yellow
		dd	000000ffh		;Blue
		dd	00ff00ffh		;Magenta
		dd	0000ffffh		;Cyan
		dd	00ffffffh		;White

endif
sEnd	DIMapSeg

end driver_initialization
