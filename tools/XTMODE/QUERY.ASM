; Original test-only far cdecl query bridge. MIT license. 8086 only.
.8086
_TEXT SEGMENT WORD PUBLIC 'CODE'
ASSUME CS:_TEXT
PUBLIC _query
_query PROC FAR
 PUSH BP
 MOV BP,SP
 PUSH BX
 PUSH CX
 PUSH DX
 PUSH SI
 PUSH DI
 PUSH DS
 PUSH ES
 MOV AX,[BP+6]
 INT 2FH
 POP ES
 POP DS
 POP DI
 POP SI
 POP DX
 POP CX
 POP BX
 POP BP
 RETF
_query ENDP
_TEXT ENDS
END
