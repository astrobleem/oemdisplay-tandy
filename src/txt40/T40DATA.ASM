; T40DATA.ASM - TXT40/TEXT80 presenter state (fragment for segment _T40).
; Geometry: the includer defines, before this fragment, T40_COLS (40 or
; 80), T40_NROWS (25 or 50), T40_NGLYPH (glyph dictionary entries, a power
; of two), T40_GLIMIT (< T40_NGLYPH: glyphs kept before a reset) and
; T40_SNAPB (snapshot buffer bytes). (MASM 5.1 rejects IFNDEF defaults here
; as forward references; its symbols are case-insensitive, hence NROWS.)
if (T40_COLS ne 40) and (T40_COLS ne 80)
.err T40_COLS must be 40 or 80
endif
if T40_GLIMIT ge T40_NGLYPH
.err T40_GLIMIT must be below T40_NGLYPH
endif
; T40_VISROWS (text rows shown: T40_NROWS, or 25 of 50 when panning) and the
; segment equates T40_SHSEG (shadow; 0 when the includer sets t40_sh0 and
; t40_sh1 at run time), T40_VSEG (video text buffer) and T40_LSEG (logical
; text buffer: T40_VSEG itself when nothing pans) come from the includer too.
T40_NCELL equ T40_COLS*T40_NROWS
T40_PANNED equ T40_VISROWS lt T40_NROWS      ; -1 (true) when the screen pans
T40_BANDS equ (T40_NROWS+24)/25         ; 200-row shadow segments (1 or 2)
T40_W equ 8*T40_COLS                ; pixels
T40_H equ 8*T40_NROWS
T40_ROWB equ 4*T40_COLS             ; shadow bytes per pixel row (4 planes)
if T40_COLS eq 40
T40_ROWSH equ 5                     ; T40_ROWB = 5 shl T40_ROWSH
else
T40_ROWSH equ 6
endif
; Hints (compact): each cell has two 4-byte slots, newest first, at
; cell*8 and cell*8+4: byte 0 = 80h (valid) | dy<<3 | dx, where the glyph's
; top-left pixel is (8cx-4+dx, 8cy-4+dy); bytes 1-2 = glyph dictionary
; index; byte 3 = CP437 code. The 8 glyph rows live once in t40_gly.
t40_slot    db T40_NCELL*8 dup (0)  ; t40_slot must stay first
t40_vst     db T40_NCELL dup (0)    ; per cell: 0 nothing shown, 1/2 slot shown;
                                    ; bit 7: slots changed since (stale);
                                    ; bit 6: changed in this flush (t40_present)
t40_vat     db T40_NCELL dup (0)    ; per cell: attribute of the shown hint
t40_guse    db T40_NGLYPH/8 dup (0) ; dictionary entries in use (bitmap)
t40_gcnt    dw 0                    ; entries in use
; t40_reset clears the T40_CLRB bytes above.
T40_CLRB equ T40_NCELL*10+T40_NGLYPH/8+2
t40_gly     db T40_NGLYPH*8 dup (0) ; glyph rows, 8 bytes per entry
t40_xs      db 14 dup (0)           ; one slot unpacked: x, y, rows 0-7,
                                    ; code, valid (t40_unpack)
t40_sh0     dw T40_SHSEG            ; shadow rows 0-199 (segment)
t40_sh1     dw 0                    ; shadow rows 200-399 (two bands only)
t40_vtop    dw 0                    ; first logical text row shown
t40_voff    dw 0                    ; t40_vtop * T40_COLS * 2
t40_gidx    dw 0                    ; t40_add: dictionary index
t40_acell   dw 0                    ; t40_add: the cell being written
t40_cnt     dw 16 dup (0)       ; colour counts of the cell being approximated
t40_pl      db 32 dup (0)       ; cell planes, 8 rows x (R,G,B,I)
t40_live    db 8 dup (0)        ; claimed rows, then unclaimed (live) rows
t40_mask    db 8 dup (0)        ; foreground pixels within live
t40_snap    db 28 dup (0)       ; t40_blit: one cell's two slots unpacked
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
t40_cpv     db 0                ; an aligned copy's ring is pending (t40_blit)
            db 0
t40_cpy0    dw 0                ; its destination: pixel rows, byte columns
t40_cpy1    dw 0                ; (exclusive ends)
t40_cpx0    dw 0
t40_cpx1    dw 0
t40_cir0    dw 0                ; its interior in cells (exclusive ends)
t40_cir1    dw 0
t40_cic0    dw 0
t40_cic1    dw 0
t40_cdr     dw 0                ; and its offset in cells
t40_cdc     dw 0
t40_qr0     dw 0                ; t40_present: dirty cells (rows, columns,
t40_qr1     dw 0                ; inclusive)
t40_qc0     dw 0
t40_qc1     dw 0
t40_or0     dw 0                ; and the output scan range
t40_or1     dw 0
t40_oc0     dw 0
t40_oc1     dw 0
