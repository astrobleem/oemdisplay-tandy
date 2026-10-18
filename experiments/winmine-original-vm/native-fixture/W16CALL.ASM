.8086
_TEXT SEGMENT BYTE PUBLIC 'CODE'
ASSUME CS:_TEXT
ORG 0

start:
    ; CALL FAR 1000:0006, followed by the caller's HLT.
    DB 09Ah, 006h, 000h, 000h, 010h
    HLT

callback:
    PUSH BP
    MOV BP, SP
    CMP WORD PTR [BP+10], 0
    JZ return_false
    CMP WORD PTR [BP+6], 09BDFh
    JNZ return_false
    CMP WORD PTR [BP+8], 01357h
    JNZ return_false
    CMP CX, 0
    JNZ return_false
    MOV AX, 1
    POP BP
    RETF 6

return_false:
    MOV AX, 0
    POP BP
    RETF 6

_TEXT ENDS
END start
