; TANDY.ASM - Tandy 1000 EX Display Driver Support
; Implements physical_enable, physical_disable, physical_device, info_table_base

	.xlist
	include cmacros.inc
	include gdidefs.inc
	include display.inc
	.list

	externFP AllocSelector
	externFP AllocCSToDSAlias
	externFP FreeSelector
    externNP TGA_Detect     ; In TGAVID.ASM? Or we implement it here?
    externNP TGA_SetMode    ; In TGAVID.ASM?

; Define constants if not in include files
STOP_IO_TRAP    equ 4000h
START_IO_TRAP   equ 4007h

; GDI constants (from gdidefs.inc)
DT_RASDISPLAY   equ 0001h
CC_NONE         equ 0000h
LC_POLYLINE     equ 0002h
LC_STYLED       equ 0020h
PC_SCANLINE     equ 0008h
TC_CP_STROKE    equ 0010h
TC_RA_ABLE      equ 0020h
CP_RECTANGLE    equ 0001h
RC_BITBLT       equ 0001h
RC_BITMAP64     equ 0008h
RC_GDI20_OUTPUT equ 0010h
RC_DI_BITMAP    equ 0080h
RC_DIBTODEV     equ 0200h
DC_IgnoreDFNP   equ 0001h

sBegin  _data_seg
    globalW _curMode,0               ; 0=320x200x16, 1=640x200x4
    globalW ScratchSel,0            ;have a scratch selector
    globalW ssb_mask,0FFFFh         ;Mask for save screen bitmap bit
    globalB enabled_flag,0          ;Display is enabled if non-zero
    globalW is_protected,0          ;LSB set in protected mode (WinFlags?)
    globalB bEquipmentFlag, 0       ;BYTE at 40:10 in ROM BIOS save area
    globalW ScreenSelector,0        ; Selector for video memory
    globalW WinFlags,0              ; Windows Flags
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
physical_device BITMAP <SCRSEL,W,H,WB,P,B,0B8000000H,0,0,0,0,0,0,0>

; --- info_table_base ---
public info_table_base
info_table_base label byte
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

createSeg _BLUEMOON,BlueMoonSeg,word,public,CODE
sBegin  BlueMoonSeg
public BlueMoonSeg_color_table
BlueMoonSeg_color_table label   dword
    dd  00000000h   ; 0 Black
    dd  000000AAh   ; 1 Blue
    dd  0000AA00h   ; 2 Green
    dd  0000AAAAh   ; 3 Cyan
    dd  00AA0000h   ; 4 Red
    dd  00AA00AAh   ; 5 Magenta
    dd  00AAAA00h   ; 6 Brown
    dd  00AAAAAAh   ; 7 Light Gray
    dd  00555555h   ; 8 Dark Gray
    dd  005555FFh   ; 9 Light Blue
    dd  0055FF55h   ; 10 Light Green
    dd  0055FFFFh   ; 11 Light Cyan
    dd  00FF5555h   ; 12 Light Red
    dd  00FF55FFh   ; 13 Light Magenta
    dd  00FFFF55h   ; 14 Yellow
    dd  00FFFFFFh   ; 15 White
sEnd    BlueMoonSeg

END
