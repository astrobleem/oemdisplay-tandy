; T40DATA.ASM - TXT40 presenter state (fragment for segment _T40).
; t40_slot must stay first: slot addresses are cell*32 from offset 0.
t40_slot    db 32000 dup (0)    ; 1000 cells x 2 hint slots x 16 bytes
t40_vst     db 1000 dup (0)     ; per cell: 0 nothing shown, 1/2 slot shown
t40_vat     db 1000 dup (0)     ; per cell: attribute of the shown hint
t40_cnt     dw 16 dup (0)       ; colour counts of the cell being approximated
t40_pl      db 32 dup (0)       ; cell planes, 8 rows x (R,G,B,I)
t40_live    db 8 dup (0)        ; claimed rows, then unclaimed (live) rows
t40_mask    db 8 dup (0)        ; foreground pixels within live
t40_snap    db 32 dup (0)       ; t40_blit: copy of one cell's slots
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
