; MIT, Copyright (c) 2026 Windows XT contributors.
; DOS 2+ guarded launcher. Does not reserve RAM or modify Windows files.
; Absolute paths make the guard independent of current directory/drive.
.8086
CODE SEGMENT PARA PUBLIC 'CODE'
ASSUME CS:CODE,DS:CODE,ES:CODE,SS:CODE
ORG 100h
start:
    mov ax,cs
    mov ds,ax
    mov es,ax
    cli
    mov ss,ax
    mov sp,OFFSET stack_top
    sti
    mov bx,OFFSET program_end
    add bx,15
    mov cl,4
    shr bx,cl
    mov ah,4Ah
    int 21h
    jnc memory_ok
    mov dx,OFFSET memory_msg
    jmp fail_one
memory_ok:
    mov word ptr params+4,cs
    mov word ptr params+8,cs
    mov word ptr params+12,cs
    mov dx,OFFSET guard_path
    call check_file
    jnc guard_present
    mov dx,OFFSET guard_missing
    jmp fail_one
guard_present:
    mov word ptr params+2,OFFSET empty_tail
    mov dx,OFFSET guard_path
    call run_child
    or ax,ax
    jz guard_ok
    mov exit_code,al
    mov dx,OFFSET guard_refused
    jmp message_exit
guard_ok:
    mov dx,OFFSET win_path
    call check_file
    jnc win_present
    mov dx,OFFSET win_missing
    jmp fail_one
win_present:
    mov dl,2
    mov ah,0Eh
    int 21h
    mov dx,OFFSET win_dir
    mov ah,3Bh
    int 21h
    jnc directory_ok
    mov dx,OFFSET directory_msg
    jmp fail_one
directory_ok:
    mov word ptr params+2,OFFSET win_tail
    mov dx,OFFSET win_path
    call run_child
    mov exit_code,al
    or ax,ax
    jz exit_now
    mov dx,OFFSET win_error
    jmp message_exit
fail_one:
    mov exit_code,1
message_exit:
    mov ah,09h
    int 21h
exit_now:
    mov al,exit_code
    mov ah,4Ch
    int 21h

check_file PROC NEAR
    mov ax,3D00h
    int 21h
    jc file_done
    mov bx,ax
    mov ah,3Eh
    int 21h
file_done:
    ret
check_file ENDP

run_child PROC NEAR
    ; DOS EXEC can destroy registers/stack; recover using CS overrides.
    push ds
    push es
    mov cs:saved_ss,ss
    mov cs:saved_sp,sp
    mov bx,OFFSET params
    mov ax,4B00h
    int 21h
    mov cs:exec_error,0
    jnc exec_returned
    mov cs:exec_error,1
exec_returned:
    cli
    mov ax,cs:saved_ss
    mov ss,ax
    mov sp,cs:saved_sp
    sti
    pop es
    pop ds
    cmp exec_error,0
    je child_status
    mov ax,1
    ret
child_status:
    mov ah,4Dh
    int 21h
    or ah,ah
    jz normal_status
    mov ax,1
    ret
normal_status:
    xor ah,ah
    ret
run_child ENDP

params          dw 0,OFFSET empty_tail,0,5Ch,0,6Ch,0
empty_tail      db 0,13
win_tail        db 3,' /R',13
exit_code       db 0
exec_error      db 0
saved_ss        dw 0
saved_sp        dw 0
guard_path      db 'C:\PCJREXP\JRGUARD.COM',0
win_path        db 'C:\WINDOWS\WIN.COM',0
win_dir         db 'C:\WINDOWS',0
memory_msg      db 'JRWIN: cannot shrink its DOS block. Windows not started.',13,10,'$'
guard_missing   db 'JRWIN: missing C:\PCJREXP\JRGUARD.COM. Windows not started.',13,10,'$'
guard_refused   db 'JRWIN: guard refused/failed. Windows not started.',13,10,'$'
win_missing     db 'JRWIN: missing C:\WINDOWS\WIN.COM. Windows not started.',13,10,'$'
directory_msg   db 'JRWIN: cannot enter C:\WINDOWS. Windows not started.',13,10,'$'
win_error       db 'JRWIN: Windows failed or terminated abnormally.',13,10,'$'
                dw 256 dup (0)
stack_top LABEL WORD
program_end LABEL BYTE
CODE ENDS
END start
