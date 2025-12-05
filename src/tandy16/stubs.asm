; STUBS.ASM - Minimal stub implementations for missing exports
; Only includes exports that are NOT provided by other object files

	?PLM = 1		; Pascal calling convention (no underscores)
	?WIN = 1		; Windows driver

	.xlist
	include cmacros.inc
	.list

;=============================================================================
; STUB CODE SEGMENT - Stubs for missing GDI exports
;=============================================================================

createSeg _STUBCODE,StubCode2,word,public,CODE
sBegin	StubCode2
assumes cs,_STUBCODE

; RealizeObject - Realize GDI logical objects (pens, brushes)
; Entry: Various GDI parameters
; Returns: 0 (not implemented)
cProc	RealizeObject,<FAR,PUBLIC,WIN,PASCAL>
cBegin
	xor	ax, ax		; Return 0 (failure)
cEnd

; Output - GDI graphics output operations (lines, polygons, etc.)
; Entry: Various GDI parameters
; Returns: 0 (not implemented)  
cProc	Output,<FAR,PUBLIC,WIN,PASCAL>
cBegin
	xor	ax, ax		; Return 0 (failure)
cEnd

sEnd	StubCode2

;=============================================================================
; PUBLIC DATA SEGMENT
;=============================================================================
sBegin  _data_seg
    public  COLOR_FORMAT
    COLOR_FORMAT dw 0104h   ; 4 planes, 1 bit/pixel (standard branding for 4-plane)
sEnd    _data_seg

;=============================================================================
; GENERIC CODE STUBS (Called by internal modules like COLORINF.ASM)
;=============================================================================
sBegin  _code_seg   ; Standard code segment
assumes cs,_TEXT_SEG

; _sum_RGB_colors_alt
; Called by COLORINF.ASM
; Helper to sum RGB colors or map them.
; Simplest stub: Return some default physical color or just return.
; Inputs: ES:DI -> phys color struct (maybe), DX:AX = RGB?
; Returns: DX:AX or modifies ES:DI
    public  _sum_RGB_colors_alt
_sum_RGB_colors_alt label near
cProc   sum_RGB_colors_alt,<NEAR,PUBLIC>
cBegin
    ; Minimal stub: preserve registers
    ; Just return.
    xor ax, ax
    xor dx, dx
cEnd

sEnd    _code_seg

end
