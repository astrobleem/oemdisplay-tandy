	page	,132
;-----------------------------Module-Header-----------------------------;
; Module Name:	TANDY.ASM
;
; This module contains the physical device structure and initialization
;
;-----------------------------------------------------------------------;

	?PLM = 1
	?WIN = 1

	.xlist
	include cmacros.inc
	incDevice = 1
	include gdidefs.inc
	include display.inc
	include windefs.inc
	.list

DT_RASDISPLAY	equ 1
;INT_PHYS_DEVICE	equ 0
CC_NONE		equ 0


;LC_POLYLINE     equ 0002h
;LC_STYLED       equ 0020h
;PC_SCANLINE     equ 0008h
;TC_CP_STROKE    equ 0010h
;TC_RA_ABLE      equ 0020h
;CP_RECTANGLE    equ 0001h
;RC_BITBLT       equ 0001h
;RC_BITMAP64     equ 0008h
;RC_GDI20_OUTPUT equ 0010h
;RC_DI_BITMAP    equ 0080h
;RC_DIBTODEV     equ 0200h
;DC_IgnoreDFNP   equ 0001h

sBegin  _data_seg
    public _curMode
    _curMode dw 0               ; 0=320x200x16, 1=640x200x4
    
    public ScratchSel
    ScratchSel dw 0            ;have a scratch selector
    
    public ssb_mask
    ssb_mask dw 0FFFFh         ;Mask for save screen bitmap bit
    
    public enabled_flag
    enabled_flag db 0          ;Display is enabled if non-zero
    
    public is_protected
    is_protected dw 0          ;LSB set in protected mode (WinFlags?)
    
    public bEquipmentFlag
    bEquipmentFlag db 0       ;BYTE at 40:10 in ROM BIOS save area
    
    public TandyScreenSelector
    TandyScreenSelector dw 0        ; Selector for video memory
    
    public WinFlags
    WinFlags dw 0              ; Windows Flags
    
    public cstods
    cstods dw 0               ; CS to DS alias selector
sEnd    _data_seg

createSeg _INIT,InitSeg,word,public,CODE
sBegin  InitSeg
assumes cs,_INIT
assumes ds,DGROUP

; --- physical_device ---
PHYS_DEVICE_SIZE equ size BITMAP

SCRSEL  equ 0 ; ScreenSelector will be filled at runtime? Or 0 for now.
P       equ 1                   ; 1 plane (packed)
B       equ 4                   ; 4 bits per pixel
H       equ 200
W       equ 320
WB      equ 160

public  physical_device
public  _physical_device
_physical_device label byte
physical_device BITMAP <SCRSEL,W,H,WB,P,B,0B8000000H,0,0,0,0,0,0,0>

; --- info_table_base ---
public info_table_base
public _info_table_base
info_table_base label byte
_info_table_base label byte
    dw  300h                    ; Version 3.00
    dw  DT_RASDISPLAY           ; Technology
    dw  240, 180                ; Size in mm (approx)
    dw  W, H                    ; Resolution
    dw  B                       ; Bits/pixel
    dw  P                       ; Planes
    dw  -1                      ; NumBrushes (lots)
    dw  16                      ; NumPens (16 colors)
    dw  0                       ; Reserved
    dw  0                       ; NumFonts
    dw  16                      ; NumColors
    dw  size int_phys_device    ; DeviceSize
    dw  CC_NONE                 ; Curves
    dw  LC_POLYLINE+LC_STYLED   ; Lines
    dw  PC_SCANLINE             ; Polygonals
    dw  TC_CP_STROKE+TC_RA_ABLE ; Text
    dw  CP_RECTANGLE            ; Clip
    dw  RC_BITBLT+RC_BITMAP64+RC_GDI20_OUTPUT+RC_DI_BITMAP+RC_DIBTODEV ; Raster
    dw  36, 36, 51              ; Aspect X, Y, XY
    dw  10                      ; StyleLen
    dw  0,0,0,0                 ; Metric Lo
    dw  0,0,0,0                 ; Metric Hi
    dw  0,0,0,0                 ; English Lo
    dw  0,0,0,0                 ; English Hi
    dw  0,0,0,0                 ; Twips
    dw  96, 96                  ; LogPixels X, Y
    dw  DC_IgnoreDFNP           ; DCManage
    dw  0,0,0,0,0               ; Reserved
    dw  0                       ; NumPalReg
    dw  0                       ; PalReserved
    dw  0                       ; ColorRes

; --- physical_enable ---
cProc physical_enable,<PUBLIC,NEAR>
cBegin
    push si
    push di
    push ds
    
    ; 1. Detect Tandy (Simple check for now)
    mov ax, 1A00h
    int 10h
    cmp bl, 0FFh
    jne @not_tandy
    
    ; 2. Set Mode (Default to 320x200x16)
    mov ax, 0009h
    int 10h
    
    mov enabled_flag, 0FFh
    mov ax, 1
    jmp @exit

@not_tandy:
    xor ax, ax

@exit:
    pop ds
    pop di
    pop si
cEnd

; --- physical_disable ---
cProc physical_disable,<PUBLIC,NEAR>
cBegin
    ; Restore text mode?
    mov ax, 0003h
    int 10h
    mov enabled_flag, 0
    mov ax, 1
cEnd

sEnd InitSeg



END
