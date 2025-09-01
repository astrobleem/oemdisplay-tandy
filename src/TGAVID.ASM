; tga_video.asm Tandy/PCjr graphics tiny HW layer
; Model: 16-bit, MASM 5.x
; Exports (Pascal far):
;   int  TGA_Detect(void);
;   int  TGA_SetMode(TGA_MODE mode);   ; AX=mode (0 or 1), returns AX=1 on success
;   void TGA_SetTextMode(void);
;   void TGA_GetPlaneInfo(TGAPlaneInfo far *out);

.MODEL LARGE, PASCAL
OPTION PROLOGUE:NONE, EPILOGUE:NONE

INCLUDE windows.inc

.DATA
_curMode        DW  0               ; 0=320x200x16, 1=640x200x4
; Default plane info; we adjust at SetMode time if needed
; Note: VRAM segment is B800h on Tandy graphics modes.
_planeInfo      LABEL BYTE
_pi_vramSeg     DW  0B800h
_pi_planeOfs0   DW  0000h
_pi_planeOfs1   DW  2000h           ; placeholders; adjust once verified
_pi_planeOfs2   DW  4000h
_pi_planeOfs3   DW  6000h
_pi_stride      DW  40              ; 40 bytes/scanline per plane (320 wide)
_pi_active      DB  4

_textMode       DB  3               ; BIOS text mode 80x25

.CODE

; --- int TGA_Detect(void) ---
PUBLIC TGA_Detect
TGA_Detect PROC FAR
    push bp
    mov  bp, sp

    ; Minimal detection: check for presence of Tandy/PCjr video BIOS extension.
    ; Pragmatic early version: assume present if segment B800h responds.
    ; You can strengthen this later (e.g., BIOS model ID, machine=tandy in DOSBox, etc.)

    ; Probe: attempt to read from B800:0000 safely (real HW this is OK in graphics/text).
    push ds
    mov  ax, 0B800h
    mov  ds, ax
    mov  al, [0000h]        ; read
    ; We don't validate content; assume success if no fault.
    pop  ds

    mov  ax, 1              ; say “present”
    pop  bp
    ret
TGA_Detect ENDP

; --- int TGA_SetMode(TGA_MODE mode) ---
PUBLIC TGA_SetMode
TGA_SetMode PROC FAR
    push bp
    mov  bp, sp
    push ds

    mov  ax, [bp+6]         ; param: mode (int)
    mov  _curMode, ax

    ; Try BIOS first. Many Tandy BIOSes provide INT 10h modes compatible with PCjr.
    ; Mode mapping (fill once verified on EX):
    ; - 320x200x16: PCjr/Tandy graphics mode (often INT10 AL=09h or AL=0Fh on some models)
    ; - 640x200x4 : PCjr/Tandy 640×200 4-color (often AL=0Eh)
    ; We keep placeholders and return success; you will put real AL here after confirming.

    mov  ah, 0               ; Set Video Mode
    cmp  ax, 0               ; 0 => 320x200x16
    jne  @mode640

@mode320:
    mov  al, 0Fh             ; TODO: verify on EX (common for PCjr/Tandy 16-color 320x200)
    int  10h
    ; Plane info for 320×200×16:
    mov  _pi_stride, 40
    mov  _pi_active, 4
    jmp  @ok

@mode640:
    mov  al, 0Eh             ; TODO: verify 640x200x4 on EX
    int  10h
    ; Plane info for 640×200×4:
    mov  _pi_stride, 80
    mov  _pi_active, 2
    ; Offsets may differ; keep same base spacing initially.
    ; On some models planes pack differently—adjust once tested.

@ok:
    mov  ax, 1               ; success
    pop  ds
    pop  bp
    ret
TGA_SetMode ENDP

; --- void TGA_SetTextMode(void) ---
PUBLIC TGA_SetTextMode
TGA_SetTextMode PROC FAR
    push bp
    mov  bp, sp
    mov  ah, 0
    mov  al, _textMode       ; 03h: 80×25 color text
    int  10h
    pop  bp
    ret
TGA_SetTextMode ENDP

; --- void TGA_GetPlaneInfo(TGAPlaneInfo far *out) ---
PUBLIC TGA_GetPlaneInfo
TGA_GetPlaneInfo PROC FAR
    push bp
    mov  bp, sp
    push ds
    push si
    push di

    ; DS:SI -> _planeInfo
    ; ES:DI -> out
    push ds
    pop  es                  ; ES = DS (we’ll set DS to DGROUP)
    mov  ax, @DATA
    mov  ds, ax

    lea  si, _pi_vramSeg
    les  di, [bp+6]          ; far *out in stack
    ; copy struct: 2 + (4*2) + 2 + 1 = 13 bytes (round to 14)
    mov  cx, 7               ; copy 7 words = 14 bytes (over-copies 1 pad byte, OK)
copy_words:
    mov  ax, [si]
    mov  es:[di], ax
    add  si, 2
    add  di, 2
    loop copy_words

    pop  di
    pop  si
    pop  ds
    pop  bp
    ret
TGA_GetPlaneInfo ENDP

END
