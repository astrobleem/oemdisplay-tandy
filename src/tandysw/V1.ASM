; Reuses hatch/color/line-style tables from the existing Microsoft DDK
; DDK/286/DISPLAY/4PLANE/EGA/EGA.ASM; see PROVENANCE.md.
; Tandy software raster backend, 320x200x16, real mode Windows 3.0.
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
externFP Pixel
externFP ScanLR
externFP RStrBlt
externFP RExtTextOut
externFP AllocSelector
externFP FreeSelector
externFP cursor_hide
externFP cursor_show
public SCREEN_WIDTH,SCREEN_HEIGHT,SCREEN_W_BYTES,COLOR_FORMAT
public COLOR_DONT_CARE,COLOR_TBL_SIZE,PHYS_DEVICE_SIZE
SCREEN_WIDTH equ 320
SCREEN_HEIGHT equ 200
SCREEN_W_BYTES equ 40
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


HYPOTENUSE	=	61		;Distance moving X and Y
Y_MAJOR_DIST	=	48		;Distance moving Y only
X_MAJOR_DIST	=	38		;Distance moving X only
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
shadow_bits db 32000 dup (0)
sEnd ShadowSeg

sBegin Data
public enabled_flag,ScratchSel,is_protected,_cstods,diag_markers
ScratchSel dw 0
is_protected dw 0
enabled_flag db 0
old_mode db 3
diag_markers dw 0,0,0,0
public shadow_device
shadow_device BITMAP <0,320,200,40,4,1,0,8000,0,0,0,0,0,0>
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
    mov cx,40
flush_byte:
    mov ah,[si]
    mov bl,[si+40]
    mov bh,[si+80]
    mov dh,[si+120]
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
    add si,120
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
    je TBitBlt_done
    ; DDK BitBlt relies on GDI-clipped destination geometry. Only an
    ; in-screen rectangle with positive, non-overflowing extents proves
    ; dirty row bounds. Anything outside that contract gets a full flush.
    ; Save the renderer return value while calculating dirty scanlines.
    push ax
    push bx
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
    call FlushRows
    jmp short TBitBlt_flushed
TBitBlt_full:
    call FlushShadow
TBitBlt_flushed:
    pop bx
    pop ax
TBitBlt_done:
cEnd

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
cBegin
    mov dirty,0
    map_device dst,1
    cCall Output,<dst,style,count,points,pen,brush,mode,clip>
    cmp dirty,0
    je TOutput_done
    call FlushShadow
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
    ; The renderer clips SetPixel to the destination bitmap dimensions.
    ; Out-of-bounds pixels still pair cursor hide/show but convert no row.
    xor ax,ax
    xor bx,bx
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
TPixel_flush:
    call FlushRows
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
physical_device BITMAP <1,320,200,40,4,1,0,8000,0,0,0,0,0,0>
info_table label byte
    dw 0300h,DT_RASDISPLAY,240,180,320,200,1,4
    dw -1,80,0,0,16,size BITMAP
    dw CC_NONE,LC_POLYLINE+LC_STYLED,PC_SCANLINE
    dw TC_CP_STROKE+TC_RA_ABLE,CP_RECTANGLE
    dw RC_BITBLT+RC_BITMAP64+RC_GDI20_OUTPUT+RC_OP_DX_OUTPUT
    dw X_MAJOR_DIST,Y_MAJOR_DIST,HYPOTENUSE,MAX_STYLE_ERR
    dw 2400,1800,320,-200
    dw 24000,18000,320,-200
    dw 1200,900,406,-254
    dw 12000,9000,406,-254
    dw 17280,12960,406,-254
    dw 96,72,DC_IgnoreDFNP
    dw 0,0,0,0,0,0,0,0
.errnz ($-info_table)-(size GDIINFO)

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
    xor ax,ax
    cCall AllocSelector,<ax>
    mov ScratchSel,ax
    mov ah,0fh
    int 10h
    mov old_mode,al
    mov ax,9
    int 10h
    mov ax,seg shadow_bits
    mov es,ax
    xor di,di
    xor ax,ax
    mov cx,16000
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
    mov enabled_flag,0
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
end driver_initialization
