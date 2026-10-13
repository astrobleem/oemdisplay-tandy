; T40DATA.ASM - TXT40/TEXT80 presenter state (fragment for segment _T40).
; Geometry: the includer may define T40_COLS (40 or 80), T40_ROWS (25) and
; T40_SLOTB (hint slot bytes: 16, or 14 to fit 80x25 in one segment);
; without them this is TXT40's 40x25 with 16-byte slots.
ifndef T40_COLS
T40_COLS equ 40
endif
ifndef T40_ROWS
T40_ROWS equ 25
endif
ifndef T40_SLOTB
T40_SLOTB equ 16
endif
if (T40_COLS ne 40) and (T40_COLS ne 80)
.err T40_COLS must be 40 or 80
endif
if (T40_SLOTB ne 16) and (T40_SLOTB ne 14)
.err T40_SLOTB must be 16 or 14
endif
ifndef T40_SNAPB
T40_SNAPB equ 8192                  ; snapshot buffer bytes (segment T40_SNSEG)
endif
T40_NCELL equ T40_COLS*T40_ROWS
T40_CELLB equ 2*T40_SLOTB           ; two slots per cell
T40_W equ 8*T40_COLS                ; pixels
T40_H equ 8*T40_ROWS
T40_ROWB equ 4*T40_COLS             ; shadow bytes per pixel row (4 planes)
if T40_COLS eq 40
T40_ROWSH equ 5                     ; T40_ROWB = 5 shl T40_ROWSH
else
T40_ROWSH equ 6
endif
; t40_slot must stay first: slot addresses are cell*T40_CELLB from offset 0.
t40_slot    db T40_NCELL*T40_CELLB dup (0)  ; 2 hint slots per cell
t40_vst     db T40_NCELL dup (0)    ; per cell: 0 nothing shown, 1/2 slot shown;
                                    ; bit 7: slots changed since (stale)
t40_vat     db T40_NCELL dup (0)    ; per cell: attribute of the shown hint
; t40_reset clears the T40_NCELL*(T40_CELLB+2) bytes above.
t40_cnt     dw 16 dup (0)       ; colour counts of the cell being approximated
t40_pl      db 32 dup (0)       ; cell planes, 8 rows x (R,G,B,I)
t40_live    db 8 dup (0)        ; claimed rows, then unclaimed (live) rows
t40_mask    db 8 dup (0)        ; foreground pixels within live
t40_snap    db T40_CELLB dup (0) ; t40_blit: copy of one cell's slots
t40_eqa     db 8 dup (0)        ; t40_two: live pixels of the first colour
t40_eqb     db 8 dup (0)        ; t40_two: live pixels of the second colour
t40_rem     db 8 dup (0)        ; t40_two: live pixels not of the first
t40_ca      db 0
t40_cb      db 0
t40_na      db 0
t40_nbf     db 0                ; t40_cell: which neighbours exist
t40_rows    db 0                ; t40_vrows: rows to check, bit r = row r
t40_fm      db 4 dup (0)        ; t40_setfm: plane masks of one colour
t40_v       db 4 dup (0)        ; t40_verify: one window row, R,G,B,I
t40_x       dw 0
t40_b0      dw 0
t40_sh      dw 0
t40_cm      db 0
t40_fg      db 0
t40_bg      db 0
t40_r7      db 0
t40_cbg     db 0
t40_bgc     db 0
t40_fgc     db 0
t40_rf      db 0
t40_rl      db 0
t40_colm    db 0
t40_best    db 0
            db 0
t40_bestd   dw 0
t40_n       dw 0
t40_on      dw 0
t40_cy      dw 0
t40_cx      dw 0
t40_ny      dw 0
t40_nx      dw 0
t40_r0      dw 0
t40_r1      dw 0
t40_c0      dw 0
t40_c1      dw 0
t40_ax      dw 0
t40_ay      dw 0
t40_sx      dw 0
t40_sy      dw 0
t40_ex      dw 0
t40_ey      dw 0
t40_ddx     dw 0
t40_ddy     dw 0
if T40_SLOTB ne 16
t40_tmp     dw 0                ; t40_slotof scratch
t40_acell   dw 0                ; t40_add: the cell being written
endif
t40_snv     db 0                ; t40_snap: a snapshot is held
            db 0
t40_sy0     dw 0                ; its rectangle (clamped): rows, bytes
t40_sy1     dw 0
t40_sx0     dw 0
t40_sx1     dw 0
t40_snc     dw 0                ; its bytes per plane row
t40_dy0     dw 0                ; t40_pdiff: the flush rectangle
t40_dy1     dw 0
t40_dx0     dw 0
t40_dx1     dw 0
t40_dr0     dw 0                ; its output range (cells)
t40_dr1     dw 0
t40_dc0     dw 0
t40_dc1     dw 0
t40_dcy     dw 0                ; current cell row and column
t40_dcx     dw 0
t40_drun    dw 0                ; first column of the open run, -1 none
t40_px0     dw 0                ; t40_present: dirty pixels, columns
t40_px1     dw 0
t40_py0     dw 0                ; and rows (end exclusive)
t40_py1     dw 0
