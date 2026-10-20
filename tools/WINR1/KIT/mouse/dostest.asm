; First-party DOS test harness for decoder.asm.
; Copyright (c) 2026. SPDX-License-Identifier: MIT
; Reads fixed 12-byte VECTORS.BIN records and checks the real decoder object.

.8086
.model small
.stack 2048

_DATA SEGMENT WORD PUBLIC 'DATA'
vectors_name    db 'VECTORS.BIN',0
pass_prefix     db 'PASS records '
pass_prefix_len equ $-pass_prefix
fail_prefix     db 'FAIL record '
fail_prefix_len equ $-fail_prefix
fail_code_text  db ' code '
fail_code_len   equ $-fail_code_text
crlf            db 13,10
crlf_len        equ $-crlf
hex_out         db '0000'
input_buffer    db 504 dup (0)        ; 42 whole 12-byte records per DOS read
vec_handle      dw 0
read_bytes      dw 0
remaining       dw 0
record_lo       dw 0
record_hi       dw 0
failure_code    dw 0
actual_cf       db 0
actual_ax       dw 0
actual_bx       dw 0
actual_cx       dw 0
_DATA ENDS

_TEXT SEGMENT WORD PUBLIC 'CODE'
ASSUME CS:_TEXT, DS:DGROUP
EXTRN dec_reset:NEAR, dec_feed:NEAR, dec_read:NEAR, dec_lost:NEAR
PUBLIC start

start:
    mov ax, @data
    mov ds, ax
    mov ax, cs
    mov es, ax
    mov dx, OFFSET vectors_name
    mov ax, 03D00h
    int 21h
    jnc open_ok
    mov word ptr failure_code, 1
    jmp fail_exit
open_ok:
    mov vec_handle, ax

read_more:
    mov bx, vec_handle
    mov ah, 03Fh
    mov cx, 504
    mov dx, OFFSET input_buffer
    int 21h
    jnc read_ok
    mov word ptr failure_code, 1
    jmp fail_exit
read_ok:
    or ax, ax
    jnz read_nonempty
    jmp pass_exit
read_nonempty:
    mov read_bytes, ax
    xor dx, dx
    mov bx, 12
    div bx
    or dx, dx
    jz records_aligned
    mov word ptr failure_code, 1
    jmp fail_exit
records_aligned:
    mov ax, read_bytes
    mov remaining, ax
    mov si, OFFSET input_buffer

record_loop:
    cmp remaining, 0
    jne have_record
    jmp read_more
have_record:
    mov al, byte ptr [si]
    cmp al, 0
    je op_reset
    cmp al, 1
    je op_feed
    cmp al, 2
    je op_read
    cmp al, 3
    je op_lost
    mov word ptr failure_code, 2
    jmp fail_exit

op_reset:
    push si
    mov bp, 0A55Ah
    mov ax, cs
    mov es, ax
    call dec_reset
    call check_registers
    pop si
    jc bad_registers
    jmp record_passed

op_feed:
    push si
    mov bp, 0A55Ah
    mov ax, cs
    mov es, ax
    mov al, byte ptr [si+1]
    mov ah, byte ptr [si+2]
    call dec_feed
    mov actual_ax, ax
    mov actual_bx, bx
    mov actual_cx, cx
    pushf
    pop dx
    and dl, 1
    mov actual_cf, dl
    call check_registers
    pop si
    jc bad_registers
    mov al, actual_cf
    cmp al, byte ptr [si+3]
    jne bad_feed_cf
    mov ax, actual_ax
    cmp ax, word ptr [si+4]
    jne bad_feed_ax
    cmp word ptr [si+10], 0
    je record_passed
    mov ax, actual_bx
    cmp ax, word ptr [si+6]
    jne bad_feed_bx
    mov ax, actual_cx
    cmp ax, word ptr [si+8]
    jne bad_feed_cx
    jmp record_passed

op_read:
    push si
    mov bp, 0A55Ah
    mov ax, cs
    mov es, ax
    call dec_read
    mov actual_ax, ax
    call check_registers
    pop si
    jc bad_registers
    mov ax, actual_ax
    cmp ax, word ptr [si+4]
    jne bad_read_ax
    jmp record_passed

op_lost:
    push si
    mov bp, 0A55Ah
    mov ax, cs
    mov es, ax
    call dec_lost
    mov actual_ax, ax
    call check_registers
    pop si
    jc bad_registers
    mov ax, actual_ax
    cmp ax, word ptr [si+4]
    jne bad_lost_ax
    jmp record_passed

bad_registers:
    ; Restore the harness data segments before formatting the diagnostic.
    mov ax, @data
    mov ds, ax
    mov ax, cs
    mov es, ax
    mov word ptr failure_code, 3
    jmp fail_exit
bad_feed_cf:
    mov word ptr failure_code, 4
    jmp fail_exit
bad_feed_ax:
    mov word ptr failure_code, 5
    jmp fail_exit
bad_feed_bx:
    mov word ptr failure_code, 6
    jmp fail_exit
bad_feed_cx:
    mov word ptr failure_code, 7
    jmp fail_exit
bad_read_ax:
    mov word ptr failure_code, 8
    jmp fail_exit
bad_lost_ax:
    mov word ptr failure_code, 9
    jmp fail_exit

record_passed:
    add si, 12
    sub remaining, 12
    inc word ptr record_lo
    jnz record_index_done
    inc word ptr record_hi
record_index_done:
    jmp record_loop

; Carry set if any required callee-preserved segment/base register changed.
check_registers PROC NEAR
    cmp bp, 0A55Ah
    jne cr_bad
    mov dx, ds
    mov ax, @data
    cmp dx, ax
    jne cr_bad
    mov dx, es
    mov ax, cs
    cmp dx, ax
    jne cr_bad
    clc
    ret
cr_bad:
    stc
    ret
check_registers ENDP

pass_exit:
    mov bx, vec_handle
    mov ah, 03Eh
    int 21h
    mov dx, OFFSET pass_prefix
    mov cx, pass_prefix_len
    call write_stdout
    mov ax, record_hi
    call print_hex16
    mov ax, record_lo
    call print_hex16
    mov dx, OFFSET crlf
    mov cx, crlf_len
    call write_stdout
    mov ax, 04C00h
    int 21h

fail_exit:
    mov dx, OFFSET fail_prefix
    mov cx, fail_prefix_len
    call write_stdout
    mov ax, record_hi
    call print_hex16
    mov ax, record_lo
    call print_hex16
    mov dx, OFFSET fail_code_text
    mov cx, fail_code_len
    call write_stdout
    mov ax, failure_code
    call print_hex16
    mov dx, OFFSET crlf
    mov cx, crlf_len
    call write_stdout
    mov ax, 04C01h
    int 21h

; Write DS:DX, CX bytes to stdout (handle 1).
write_stdout PROC NEAR
    mov bx, 1
    mov ah, 040h
    int 21h
    ret
write_stdout ENDP

; Print AX as four uppercase hexadecimal digits.
print_hex16 PROC NEAR
    mov bx, ax
    mov di, OFFSET hex_out
    mov si, 4
ph_loop:
    mov ax, bx
    mov cl, 12
    shr ax, cl
    and al, 00Fh
    cmp al, 9
    jbe ph_digit
    add al, 'A'-10
    jmp ph_store
ph_digit:
    add al, '0'
ph_store:
    mov byte ptr [di], al
    inc di
    shl bx, 1
    shl bx, 1
    shl bx, 1
    shl bx, 1
    dec si
    jnz ph_loop
    mov dx, OFFSET hex_out
    mov cx, 4
    call write_stdout
    ret
print_hex16 ENDP

_TEXT ENDS
END start
