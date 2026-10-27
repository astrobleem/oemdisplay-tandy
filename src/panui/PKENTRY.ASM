; No CRT and no local heap. Windows enters with DS=DGROUP, DI=instance,
; CX=heap size, ES:SI=command line. All instructions are 8086 compatible.
.8086
.MODEL SMALL
EXTRN LIBMAIN:FAR
.CODE
LibEntry PROC FAR
    push di
    push ds
    push cx
    push es
    push si
    call LIBMAIN
    retf
LibEntry ENDP
END LibEntry
