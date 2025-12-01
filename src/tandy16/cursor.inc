; cursor.inc - Constants for Tandy cursor

EVEN_SCAN_INC equ 80
ODD_SCAN_INC  equ 2000h
INTERLACE_WRAP equ 0
IBM_CGA_DEFINED equ 1

; Cursor dimensions
CUR_HEIGHT      equ 32
CUR_WIDTH       equ 32
CUR_ICON_WIDTH  equ 4   ; 32 pixels / 8 bits per byte = 4 bytes
MASK_LENGTH     equ (CUR_HEIGHT * CUR_ICON_WIDTH)
SAVE_WIDTH      equ 4   ; Bytes to save per line (same as icon width)
BUF_WIDTH       equ 4
MAX_BUF_HEIGHT  equ 64  ; Buffer for cursor + background

; Mouse acceleration (dummy values)
X_RATE          equ 1
Y_RATE          equ 1

; Rounding
CUR_ROUND_LEFT  equ 0
CUR_ROUND_RIGHT equ 0

; Initial position
INIT_CURSOR_X   equ 160
INIT_CURSOR_Y   equ 100

; Screen dimensions (Mode 9/A)
SCREEN_WIDTH    equ 320
; cursor.inc - Constants for Tandy cursor

EVEN_SCAN_INC equ 80
ODD_SCAN_INC  equ 2000h
INTERLACE_WRAP equ 0
IBM_CGA_DEFINED equ 1

; Cursor dimensions
CUR_HEIGHT      equ 32
CUR_WIDTH       equ 32
CUR_ICON_WIDTH  equ 4   ; 32 pixels / 8 bits per byte = 4 bytes
MASK_LENGTH     equ (CUR_HEIGHT * CUR_ICON_WIDTH)
SAVE_WIDTH      equ 4   ; Bytes to save per line (same as icon width)
BUF_WIDTH       equ 4
MAX_BUF_HEIGHT  equ 64  ; Buffer for cursor + background

; Mouse acceleration (dummy values)
X_RATE          equ 1
Y_RATE          equ 1

; Rounding
CUR_ROUND_LEFT  equ 0
CUR_ROUND_RIGHT equ 0

; Initial position
INIT_CURSOR_X   equ 160
INIT_CURSOR_Y   equ 100

; Screen dimensions (Mode 9/A)
SCREEN_WIDTH    equ 320
SCREEN_HEIGHT   equ 200

; Segment aliases
; Segment aliases
;SCREENSELECTOR  equ ScreenSelector
DATABASE        equ _data_seg
FARTHEST equ far
