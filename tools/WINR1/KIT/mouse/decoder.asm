; First-party Win3realmode serial wheel decoder.
; Copyright (c) 2026. SPDX-License-Identifier: MIT
;
; This source is newly authored from the protocol and ABI contract documented
; in README.md. It contains no copied or adapted mouse-driver implementation.

.8086
.model small

_DATA SEGMENT WORD PUBLIC 'DATA'
PUBLIC dec_state, dec_buttons, dec_q_head, dec_q_tail, dec_q_count, dec_lost_word
dec_state       db 0                    ; 0 idle, 1 second byte, 2 third, 3 extension
dec_buttons     db 0                    ; bit 0 left, bit 1 right
dec_header      db 0
dec_xlow        db 0
dec_ylow        db 0
dec_x           dw 0
dec_y           dw 0
dec_tmpx        db 0
dec_tmpbuttons  db 0
dec_tmpflags    db 0
dec_feed_byte   db 0
dec_feed_lsr    db 0
dec_q_head      db 0
dec_q_tail      db 0
dec_q_count     db 0
dec_lost_word   dw 0
dec_queue       db 32 dup (0)
_DATA ENDS

_TEXT SEGMENT WORD PUBLIC 'CODE'
ASSUME CS:_TEXT, DS:DGROUP
PUBLIC dec_reset, dec_feed, dec_read, dec_lost

; Reset parser, button baseline, signed wheel queue, and saturating loss count.
dec_reset PROC NEAR
    mov byte ptr dec_state, 0
    mov byte ptr dec_buttons, 0
    mov byte ptr dec_q_head, 0
    mov byte ptr dec_q_tail, 0
    mov byte ptr dec_q_count, 0
    mov word ptr dec_lost_word, 0
    mov si, OFFSET dec_queue
    mov cx, 32
dr_clear:
    mov byte ptr [si], 0
    inc si
    loop dr_clear
    ret
dec_reset ENDP

; Input: AL=data byte, AH=UART LSR. Output: AX=Windows pointer flags,
; BX=signed dx, CX=signed dy, CF=1 iff AX is nonzero.
dec_feed PROC NEAR
    mov byte ptr dec_feed_byte, al
    mov byte ptr dec_feed_lsr, ah
    mov al, ah
    and al, 01Eh
    jz df_check_dr
    mov byte ptr dec_state, 0
    xor ax, ax
    clc
    ret
df_check_dr:
    test byte ptr dec_feed_lsr, 01h
    jnz df_have_byte
    xor ax, ax
    clc
    ret
df_have_byte:
    mov al, dec_feed_byte
    test al, 080h
    jz df_not_bad_byte
    mov byte ptr dec_state, 0
    xor ax, ax
    clc
    ret
df_not_bad_byte:
    test al, 040h
    jz df_not_header
    mov byte ptr dec_header, al
    mov byte ptr dec_state, 1
    xor ax, ax
    clc
    ret
df_not_header:
    cmp byte ptr dec_state, 0
    je df_no_event
    cmp byte ptr dec_state, 1
    je df_second
    cmp byte ptr dec_state, 2
    je df_third
    ; Optional fourth byte: bits 7, 6, and 5 must all be clear.
    test al, 0E0h
    jnz df_bad_extension
    mov byte ptr dec_state, 0
    and al, 00Fh
    cmp al, 8
    jb df_wheel_signed
    or al, 0F0h
df_wheel_signed:
    or al, al
    jz df_no_event
    cmp byte ptr dec_q_count, 31
    jae df_queue_full
    xor bx, bx
    mov bl, dec_q_head
    mov byte ptr dec_queue[bx], al
    inc bl
    and bl, 01Fh
    mov dec_q_head, bl
    inc byte ptr dec_q_count
    jmp df_no_event
df_queue_full:
    cmp word ptr dec_lost_word, 0FFFFh
    je df_no_event
    inc word ptr dec_lost_word
    jmp df_no_event
df_bad_extension:
    mov byte ptr dec_state, 0
    jmp df_no_event

df_second:
    and al, 03Fh
    mov dec_xlow, al
    mov byte ptr dec_state, 2
    jmp df_no_event

df_third:
    and al, 03Fh
    mov dec_ylow, al
    mov byte ptr dec_state, 3       ; allow a following optional wheel byte

    ; dx = ((header & 3) << 6) | second[5:0], interpreted as signed byte.
    mov al, dec_header
    and al, 003h
    shl al, 1
    shl al, 1
    shl al, 1
    shl al, 1
    shl al, 1
    shl al, 1
    mov dec_tmpx, al
    mov al, dec_xlow
    or al, dec_tmpx
    cbw
    mov dec_x, ax

    ; dy = (((header >> 2) & 3) << 6) | third[5:0], signed byte.
    mov al, dec_header
    shr al, 1
    shr al, 1
    and al, 003h
    shl al, 1
    shl al, 1
    shl al, 1
    shl al, 1
    shl al, 1
    shl al, 1
    mov bl, al
    mov al, dec_ylow
    or al, bl
    cbw
    mov dec_y, ax

    ; Snapshot L/R state and generate transition flags.
    mov al, dec_header
    xor ah, ah
    test al, 020h
    jz df_right_button
    or ah, 001h
df_right_button:
    test al, 010h
    jz df_buttons_ready
    or ah, 002h
df_buttons_ready:
    mov dec_tmpbuttons, ah
    mov byte ptr dec_tmpflags, 0
    cmp word ptr dec_x, 0
    jne df_movement
    cmp word ptr dec_y, 0
    je df_left_transition
df_movement:
    or byte ptr dec_tmpflags, 001h
df_left_transition:
    test byte ptr dec_tmpbuttons, 001h
    jz df_left_up
    test byte ptr dec_buttons, 001h
    jnz df_right_transition
    or byte ptr dec_tmpflags, 002h
    jmp df_right_transition
df_left_up:
    test byte ptr dec_buttons, 001h
    jz df_right_transition
    or byte ptr dec_tmpflags, 004h
df_right_transition:
    test byte ptr dec_tmpbuttons, 002h
    jz df_right_up
    test byte ptr dec_buttons, 002h
    jnz df_save_buttons
    or byte ptr dec_tmpflags, 008h
    jmp df_save_buttons
df_right_up:
    test byte ptr dec_buttons, 002h
    jz df_save_buttons
    or byte ptr dec_tmpflags, 010h
df_save_buttons:
    mov al, dec_tmpbuttons
    mov dec_buttons, al
    xor ax, ax
    mov al, dec_tmpflags
    mov bx, dec_x
    mov cx, dec_y
    or ax, ax
    jz df_zero_event
    stc
    ret
df_zero_event:
    clc
    ret

df_no_event:
    xor ax, ax
    clc
    ret
dec_feed ENDP

; Pop one signed wheel byte; empty queue returns AX=0.
dec_read PROC NEAR
    cmp byte ptr dec_q_count, 0
    je dq_empty
    xor bx, bx
    mov bl, dec_q_tail
    mov al, dec_queue[bx]
    cbw
    inc bl
    and bl, 01Fh
    mov dec_q_tail, bl
    dec byte ptr dec_q_count
    ret
dq_empty:
    xor ax, ax
    ret
dec_read ENDP

; Return the saturating dropped-newest count in AX.
dec_lost PROC NEAR
    mov ax, dec_lost_word
    ret
dec_lost ENDP

_TEXT ENDS
END
