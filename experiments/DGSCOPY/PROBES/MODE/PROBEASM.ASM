.8086
.MODEL SMALL, PASCAL
.CODE
PUBLIC BIOSMODE
BIOSMODE PROC FAR
    push bp
    push bx
    mov ah,0fh
    int 10h
    pop bx
    pop bp
    ret
BIOSMODE ENDP
END
