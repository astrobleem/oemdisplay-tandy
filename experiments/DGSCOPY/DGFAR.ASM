;	Static Name Aliases
;
	TITLE   GENFAR.C
	.8087
INCLUDELIB	SLIBCE
_TEXT	SEGMENT  WORD PUBLIC 'CODE'
_TEXT	ENDS
_DATA	SEGMENT  WORD PUBLIC 'DATA'
_DATA	ENDS
CONST	SEGMENT  WORD PUBLIC 'CONST'
CONST	ENDS
_BSS	SEGMENT  WORD PUBLIC 'BSS'
_BSS	ENDS
DGROUP	GROUP	_DATA ; Empty CONST/_BSS must not absorb _SHADOW
	ASSUME DS: DGROUP
	ASSUME  SS: NOTHING
EXTRN	__aNlmul:NEAR
_TEXT      SEGMENT
	ASSUME	CS: _TEXT
; Line 1
; Line 4
; Line 3
; Line 5
radiusBuild	PROC NEAR
	push	bp
	mov	bp,sp
	sub	sp,28
	push	di
	push	si
;	x = -14
;	y = -18
;	i = -16
;	lastY = -28
;	aa = -4
;	bb = -12
;	dx = -22
;	dy = -26
;	d = -8
;	radius = 8
;	b = 6
;	a = 4
; Line 6
	mov	WORD PTR [bp-14],0	;x
	mov	WORD PTR [bp-28],-1	;lastY
	mov	ax,WORD PTR [bp+6]	;b
	mov	WORD PTR [bp-18],ax	;y
	imul	WORD PTR [bp+6]	;b
	mov	WORD PTR [bp-12],ax	;bb
	mov	WORD PTR [bp-10],dx
	sub	ax,ax
	mov	WORD PTR [bp-20],ax
	mov	WORD PTR [bp-22],ax	;dx
	mov	ax,WORD PTR [bp-18]	;y
	cwd	
	push	dx
	push	ax
	mov	ax,WORD PTR [bp+4]	;a
	cwd	
	push	dx
	push	ax
	push	dx
	push	ax
	call	__aNlmul
	mov	WORD PTR [bp-4],ax	;aa
	mov	WORD PTR [bp-2],dx
	push	dx
	push	ax
	call	__aNlmul
	shl	ax,1
	rcl	dx,1
	mov	WORD PTR [bp-26],ax	;dy
	mov	WORD PTR [bp-24],dx
; Line 7
	mov	WORD PTR [bp-16],0	;i
	jmp	$F139
$FC140:
	inc	WORD PTR [bp-16]	;i
$F139:
	mov	ax,WORD PTR [bp+6]	;b
	cmp	WORD PTR [bp-16],ax	;i
	jle	$JCC97
	jmp	$FB141
$JCC97:
	mov	bx,WORD PTR [bp-16]	;i
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	mov	WORD PTR es:[bx][si],-1
	jmp	$FC140
$FB141:
; Line 8
	push	WORD PTR [bp-2]
	push	WORD PTR [bp-4]	;aa
	mov	ax,WORD PTR [bp+6]	;b
	cwd	
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	mov	cx,1
	mov	bx,0
	sub	cx,ax
	sbb	bx,dx
	push	bx
	push	cx
	call	__aNlmul
	mov	cx,WORD PTR [bp-12]	;bb
	mov	bx,WORD PTR [bp-10]
	shl	cx,1
	rcl	bx,1
	shl	cx,1
	rcl	bx,1
	add	ax,cx
	adc	dx,bx
	mov	WORD PTR [bp-8],ax	;d
	mov	WORD PTR [bp-6],dx
; Line 9
	cmp	WORD PTR [bp+6],0	;b
	je	$JCC179
	jmp	$I142
$JCC179:
	mov	ax,WORD PTR [bp+4]	;a
	les	bx,DWORD PTR [bp+8]	;radius
	mov	WORD PTR es:[bx],ax
; Line 10
	jmp	$I143
$I142:
; Line 11
$FC145:
	mov	ax,WORD PTR [bp-22]	;dx
	mov	dx,WORD PTR [bp-20]
	cmp	WORD PTR [bp-24],dx
	jge	$JCC205
	jmp	$FB146
$JCC205:
	jle	$JCC210
	jmp	$L20001
$JCC210:
	cmp	WORD PTR [bp-26],ax	;dy
	ja	$JCC218
	jmp	$FB146
$JCC218:
$L20001:
; Line 12
	mov	ax,WORD PTR [bp-14]	;x
	mov	bx,WORD PTR [bp-18]	;y
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	cmp	WORD PTR es:[bx][si],ax
	jl	$JCC237
	jmp	$I147
$JCC237:
	mov	ax,WORD PTR [bp-14]	;x
	mov	bx,WORD PTR [bp-18]	;y
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	mov	WORD PTR es:[bx][si],ax
; Line 13
$I147:
	mov	ax,WORD PTR [bp-18]	;y
	mov	WORD PTR [bp-28],ax	;lastY
; Line 14
	inc	WORD PTR [bp-14]	;x
	mov	ax,WORD PTR [bp-12]	;bb
	mov	dx,WORD PTR [bp-10]
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-22],ax	;dx
	adc	WORD PTR [bp-20],dx
; Line 15
	cmp	WORD PTR [bp-6],0
	jl	$JCC285
	jmp	$I148
$JCC285:
	mov	ax,WORD PTR [bp-22]	;dx
	mov	dx,WORD PTR [bp-20]
	add	ax,WORD PTR [bp-12]	;bb
	adc	dx,WORD PTR [bp-10]
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
; Line 16
	jmp	$I149
$I148:
	dec	WORD PTR [bp-18]	;y
	mov	ax,WORD PTR [bp-22]	;dx
	mov	dx,WORD PTR [bp-20]
	mov	cx,WORD PTR [bp-4]	;aa
	mov	bx,WORD PTR [bp-2]
	shl	cx,1
	rcl	bx,1
	sub	WORD PTR [bp-26],cx	;dy
	sbb	WORD PTR [bp-24],bx
	sub	ax,WORD PTR [bp-26]	;dy
	sbb	dx,WORD PTR [bp-24]
	add	ax,WORD PTR [bp-12]	;bb
	adc	dx,WORD PTR [bp-10]
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
$I149:
; Line 17
	jmp	$FC145
$FB146:
; Line 18
	push	WORD PTR [bp-10]
	push	WORD PTR [bp-12]	;bb
	mov	ax,WORD PTR [bp-14]	;x
	cwd	
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	ax,3
	adc	dx,0
	push	dx
	push	ax
	call	__aNlmul
	push	WORD PTR [bp-2]
	push	WORD PTR [bp-4]	;aa
	mov	cx,ax
	mov	ax,WORD PTR [bp-18]	;y
	mov	bx,dx
	cwd	
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	mov	si,3
	mov	di,0
	sub	si,ax
	sbb	di,dx
	push	di
	push	si
	mov	si,cx
	mov	di,bx
	call	__aNlmul
	sub	ax,si
	sbb	dx,di
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
; Line 20
	mov	ax,WORD PTR [bp-18]	;y
	cmp	WORD PTR [bp-28],ax	;lastY
	je	$JCC459
	jmp	$I150
$JCC459:
; Line 21
	dec	WORD PTR [bp-18]	;y
	mov	ax,WORD PTR [bp-4]	;aa
	mov	dx,WORD PTR [bp-2]
	shl	ax,1
	rcl	dx,1
	sub	WORD PTR [bp-26],ax	;dy
	sbb	WORD PTR [bp-24],dx
; Line 22
	cmp	WORD PTR [bp-6],0
	jge	$JCC487
	jmp	$I151
$JCC487:
	jle	$JCC492
	jmp	$L20002
$JCC492:
	cmp	WORD PTR [bp-8],0	;d
	ja	$JCC501
	jmp	$I151
$JCC501:
$L20002:
	mov	ax,WORD PTR [bp-4]	;aa
	mov	dx,WORD PTR [bp-2]
	sub	ax,WORD PTR [bp-26]	;dy
	sbb	dx,WORD PTR [bp-24]
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
; Line 23
	jmp	$I152
$I151:
	inc	WORD PTR [bp-14]	;x
	mov	ax,WORD PTR [bp-12]	;bb
	mov	dx,WORD PTR [bp-10]
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-22],ax	;dx
	adc	WORD PTR [bp-20],dx
	mov	ax,WORD PTR [bp-22]	;dx
	mov	dx,WORD PTR [bp-20]
	sub	ax,WORD PTR [bp-26]	;dy
	sbb	dx,WORD PTR [bp-24]
	add	ax,WORD PTR [bp-4]	;aa
	adc	dx,WORD PTR [bp-2]
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
$I152:
; Line 24
; Line 25
$I150:
$FC154:
	cmp	WORD PTR [bp-18],0	;y
	jge	$JCC590
	jmp	$FB155
$JCC590:
; Line 26
	mov	ax,WORD PTR [bp-14]	;x
	mov	bx,WORD PTR [bp-18]	;y
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	cmp	WORD PTR es:[bx][si],ax
	jl	$JCC609
	jmp	$I156
$JCC609:
	mov	ax,WORD PTR [bp-14]	;x
	mov	bx,WORD PTR [bp-18]	;y
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	mov	WORD PTR es:[bx][si],ax
; Line 27
$I156:
	dec	WORD PTR [bp-18]	;y
	mov	ax,WORD PTR [bp-4]	;aa
	mov	dx,WORD PTR [bp-2]
	shl	ax,1
	rcl	dx,1
	sub	WORD PTR [bp-26],ax	;dy
	sbb	WORD PTR [bp-24],dx
; Line 28
	cmp	WORD PTR [bp-6],0
	jge	$JCC651
	jmp	$I157
$JCC651:
	jle	$JCC656
	jmp	$L20003
$JCC656:
	cmp	WORD PTR [bp-8],0	;d
	ja	$JCC665
	jmp	$I157
$JCC665:
$L20003:
	mov	ax,WORD PTR [bp-4]	;aa
	mov	dx,WORD PTR [bp-2]
	sub	ax,WORD PTR [bp-26]	;dy
	sbb	dx,WORD PTR [bp-24]
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
; Line 29
	jmp	$I158
$I157:
	inc	WORD PTR [bp-14]	;x
	mov	ax,WORD PTR [bp-12]	;bb
	mov	dx,WORD PTR [bp-10]
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-22],ax	;dx
	adc	WORD PTR [bp-20],dx
	mov	ax,WORD PTR [bp-22]	;dx
	mov	dx,WORD PTR [bp-20]
	sub	ax,WORD PTR [bp-26]	;dy
	sbb	dx,WORD PTR [bp-24]
	add	ax,WORD PTR [bp-4]	;aa
	adc	dx,WORD PTR [bp-2]
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	WORD PTR [bp-8],ax	;d
	adc	WORD PTR [bp-6],dx
$I158:
; Line 30
	jmp	$FC154
$FB155:
; Line 31
$I143:
; Line 32
	mov	ax,WORD PTR [bp+4]	;a
	les	bx,DWORD PTR [bp+8]	;radius
	cmp	WORD PTR es:[bx],ax
	jne	$JCC762
	jmp	$I159
$JCC762:
	mov	ax,0
	jmp	$EX129
; Line 33
$I159:
	mov	WORD PTR [bp-16],0	;i
	jmp	$F160
$FC161:
	inc	WORD PTR [bp-16]	;i
$F160:
	mov	ax,WORD PTR [bp+6]	;b
	cmp	WORD PTR [bp-16],ax	;i
	jle	$JCC790
	jmp	$FB162
$JCC790:
	mov	bx,WORD PTR [bp-16]	;i
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	cmp	WORD PTR es:[bx][si],0
	jge	$JCC807
	jmp	$I164
$JCC807:
	mov	ax,WORD PTR [bp+4]	;a
	mov	bx,WORD PTR [bp-16]	;i
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	cmp	WORD PTR es:[bx][si],ax
	jle	$JCC826
	jmp	$I164
$JCC826:
	cmp	WORD PTR [bp-16],0	;i
	jne	$JCC835
	jmp	$I163
$JCC835:
	mov	bx,WORD PTR [bp-16]	;i
	shl	bx,1
	les	si,DWORD PTR [bp+8]	;radius
	mov	ax,WORD PTR es:[bx][si]
	mov	si,WORD PTR [bp-16]	;i
	shl	si,1
	les	bx,DWORD PTR [bp+8]	;radius
	cmp	WORD PTR es:[bx-2][si],ax
	jl	$JCC863
	jmp	$I163
$JCC863:
$I164:
	mov	ax,0
	jmp	$EX129
; Line 34
$I163:
	jmp	$FC161
$FB162:
	mov	ax,1
	jmp	$EX129
; Line 35
$EX129:
	pop	si
	pop	di
	mov	sp,bp
	pop	bp
	ret	

radiusBuild	ENDP
; Line 36
	PUBLIC	GENFARPREPARE
GENFARPREPARE	PROC FAR
	push	ds
	pop	ax
	nop	
	inc	bp
	push	bp
	mov	bp,sp
	push	ds
	mov	ds,ax
	sub	sp,6
	push	di
	push	si
;	a = -4
;	b = -6
;	width = 16
;	height = 14
;	work = 10
;	walk = 6
; Line 37
	cmp	WORD PTR [bp+16],2	;width
	jge	$JCC909
	jmp	$I173
$JCC909:
	cmp	WORD PTR [bp+16],640	;width
	jle	$JCC919
	jmp	$I173
$JCC919:
	cmp	WORD PTR [bp+14],2	;height
	jge	$JCC928
	jmp	$I173
$JCC928:
	cmp	WORD PTR [bp+14],480	;height
	jle	$JCC938
	jmp	$I173
$JCC938:
	mov	ax,WORD PTR [bp+12]
	or	ax,WORD PTR [bp+10]	;work
	jne	$JCC949
	jmp	$I173
$JCC949:
	mov	ax,WORD PTR [bp+8]
	or	ax,WORD PTR [bp+6]	;walk
	je	$JCC960
	jmp	$I172
$JCC960:
$I173:
	mov	ax,0
	jmp	$EX169
; Line 38
$I172:
	mov	ax,WORD PTR [bp+14]	;height
	cmp	ax,WORD PTR [bp+16]	;width
	jg	$JCC977
	jmp	$L20004
$JCC977:
	mov	ax,WORD PTR [bp+16]	;width
$L20004:
	dec	ax
	cwd	
	sub	ax,dx
	sar	ax,1
	mov	WORD PTR [bp-4],ax	;a
	mov	ax,WORD PTR [bp+14]	;height
	cmp	ax,WORD PTR [bp+16]	;width
	jl	$JCC1000
	jmp	$L20005
$JCC1000:
	mov	ax,WORD PTR [bp+16]	;width
$L20005:
	dec	ax
	cwd	
	sub	ax,dx
	sar	ax,1
	mov	WORD PTR [bp-6],ax	;b
; Line 39
	push	WORD PTR [bp+12]
	push	WORD PTR [bp+10]	;work
	push	WORD PTR [bp-6]	;b
	push	WORD PTR [bp-4]	;a
	call	radiusBuild
	add	sp,8
	cmp	ax,0
	je	$JCC1038
	jmp	$I174
$JCC1038:
	mov	ax,0
	jmp	$EX169
; Line 40
$I174:
	mov	ax,WORD PTR [bp+16]	;width
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx],ax
	mov	ax,WORD PTR [bp+14]	;height
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+2],ax
	mov	ax,WORD PTR [bp-4]	;a
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+4],ax
	mov	ax,WORD PTR [bp-6]	;b
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+6],ax
; Line 41
	mov	ax,WORD PTR [bp+16]	;width
	cmp	WORD PTR [bp+14],ax	;height
	jl	$JCC1094
	jmp	$L20006
$JCC1094:
	mov	ax,1
	jmp	$L20007
$L20006:
	mov	ax,0
$L20007:
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+8],ax
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+10],0
	mov	ax,-1
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+14],ax
	les	bx,DWORD PTR [bp+6]	;walk
	mov	WORD PTR es:[bx+12],ax
; Line 42
	mov	ax,1
	jmp	$EX169
; Line 43
$EX169:
	pop	si
	pop	di
	sub	bp,2
	mov	sp,bp
	pop	ds
	pop	bp
	dec	bp
	ret	12

GENFARPREPARE	ENDP
; Line 44
	PUBLIC	GENFARNEXT
GENFARNEXT	PROC FAR
	push	ds
	pop	ax
	nop	
	inc	bp
	push	bp
	mov	bp,sp
	push	ds
	mov	ds,ax
	sub	sp,28
	push	di
	push	si
;	a = -4
;	b = -8
;	y = -14
;	k = -22
;	inner = -26
;	l = -24
;	r = -6
;	il = -10
;	ir = -20
;	outerK = -16
;	innerK = -12
;	distance = -18
;	walk = 14
;	work = 10
;	pair = 6
; Line 45
	mov	ax,0
	mov	WORD PTR [bp-10],ax	;il
	mov	WORD PTR [bp-20],ax	;ir
; Line 46
	mov	ax,WORD PTR [bp+16]
	or	ax,WORD PTR [bp+14]	;walk
	jne	$JCC1191
	jmp	$I192
$JCC1191:
	mov	ax,WORD PTR [bp+12]
	or	ax,WORD PTR [bp+10]	;work
	jne	$JCC1202
	jmp	$I192
$JCC1202:
	mov	ax,WORD PTR [bp+8]
	or	ax,WORD PTR [bp+6]	;pair
	je	$JCC1213
	jmp	$I191
$JCC1213:
$I192:
	mov	ax,-1
	jmp	$EX178
; Line 47
$I191:
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+4]
	mov	WORD PTR [bp-4],ax	;a
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+6]
	mov	WORD PTR [bp-8],ax	;b
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+10]
	mov	WORD PTR [bp-14],ax	;y
; Line 48
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx],2
	jge	$JCC1261
	jmp	$I194
$JCC1261:
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx],640
	jle	$JCC1274
	jmp	$I194
$JCC1274:
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx+2],2
	jge	$JCC1287
	jmp	$I194
$JCC1287:
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx+2],480
	jle	$JCC1301
	jmp	$I194
$JCC1301:
	cmp	WORD PTR [bp-4],0	;a
	jge	$JCC1310
	jmp	$I194
$JCC1310:
	mov	ax,WORD PTR [bp-4]	;a
	cmp	WORD PTR [bp-8],ax	;b
	jge	$JCC1321
	jmp	$I194
$JCC1321:
	cmp	WORD PTR [bp-8],320	;b
	jl	$JCC1331
	jmp	$I194
$JCC1331:
	cmp	WORD PTR [bp-14],0	;y
	jl	$JCC1340
	jmp	$I193
$JCC1340:
$I194:
	mov	ax,-1
	jmp	$EX178
; Line 49
$I193:
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+2]
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	ax,WORD PTR es:[bx]
	jg	$JCC1364
	jmp	$L20010
$JCC1364:
	mov	ax,WORD PTR es:[bx]
$L20010:
	dec	ax
	cwd	
	sub	ax,dx
	sar	ax,1
	cmp	ax,WORD PTR [bp-4]	;a
	je	$JCC1381
	jmp	$I196
$JCC1381:
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+2]
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	ax,WORD PTR es:[bx]
	jl	$JCC1399
	jmp	$L20011
$JCC1399:
	mov	ax,WORD PTR es:[bx]
$L20011:
	dec	ax
	cwd	
	sub	ax,dx
	sar	ax,1
	cmp	ax,WORD PTR [bp-8]	;b
	je	$JCC1416
	jmp	$I196
$JCC1416:
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx]
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx+2],ax
	jl	$JCC1434
	jmp	$L20008
$JCC1434:
	mov	ax,1
	jmp	$L20009
$L20008:
	mov	ax,0
$L20009:
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	ax,WORD PTR es:[bx+8]
	jne	$JCC1455
	jmp	$I195
$JCC1455:
$I196:
	mov	ax,-1
	jmp	$EX178
; Line 50
$I195:
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx+8],0
	jne	$JCC1474
	jmp	$L20012
$JCC1474:
	mov	ax,WORD PTR [bp-4]	;a
	jmp	$L20013
$L20012:
	mov	ax,WORD PTR [bp-8]	;b
$L20013:
	sub	ax,WORD PTR [bp-14]	;y
	inc	ax
	je	$JCC1492
	jmp	$I197
$JCC1492:
	mov	ax,0
	jmp	$EX178
; Line 51
$I197:
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx+8],0
	jne	$JCC1511
	jmp	$L20014
$JCC1511:
	mov	ax,WORD PTR [bp-4]	;a
	jmp	$L20015
$L20014:
	mov	ax,WORD PTR [bp-8]	;b
$L20015:
	inc	ax
	cmp	ax,WORD PTR [bp-14]	;y
	jl	$JCC1529
	jmp	$I198
$JCC1529:
	mov	ax,-1
	jmp	$EX178
; Line 52
$I198:
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+12]
	mov	WORD PTR [bp-16],ax	;outerK
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+14]
	mov	WORD PTR [bp-12],ax	;innerK
; Line 53
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx+8],0
	je	$JCC1568
	jmp	$I199
$JCC1568:
; Line 54
	cmp	WORD PTR [bp-16],-1	;outerK
	je	$JCC1577
	jmp	$I201
$JCC1577:
	cmp	WORD PTR [bp-12],-1	;innerK
	jne	$JCC1586
	jmp	$I200
$JCC1586:
$I201:
	mov	ax,-1
	jmp	$EX178
; Line 55
$I200:
	mov	ax,WORD PTR [bp-4]	;a
	mov	bx,WORD PTR [bp-8]	;b
	sub	bx,WORD PTR [bp-14]	;y
	mov	WORD PTR [bp-22],bx	;k
	shl	bx,1
	les	si,DWORD PTR [bp+10]	;work
	sub	ax,WORD PTR es:[bx][si]
	mov	WORD PTR [bp-24],ax	;l
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx]
	sub	ax,WORD PTR [bp-24]	;l
	mov	WORD PTR [bp-6],ax	;r
; Line 56
	mov	ax,WORD PTR [bp-8]	;b
	cmp	WORD PTR [bp-22],ax	;k
	jl	$JCC1638
	jmp	$I202
$JCC1638:
	mov	bx,WORD PTR [bp-22]	;k
	shl	bx,1
	les	si,DWORD PTR [bp+10]	;work
	mov	ax,WORD PTR es:[bx][si]
	dec	ax
	mov	WORD PTR [bp-26],ax	;inner
	mov	ax,WORD PTR [bp-26]	;inner
	mov	si,WORD PTR [bp-22]	;k
	shl	si,1
	les	bx,DWORD PTR [bp+10]	;work
	cmp	WORD PTR es:[bx+2][si],ax
	jl	$JCC1673
	jmp	$I203
$JCC1673:
	mov	si,WORD PTR [bp-22]	;k
	shl	si,1
	les	bx,DWORD PTR [bp+10]	;work
	mov	ax,WORD PTR es:[bx+2][si]
	mov	WORD PTR [bp-26],ax	;inner
$I203:
	cmp	WORD PTR [bp-26],0	;inner
	jge	$JCC1697
	jmp	$I204
$JCC1697:
	mov	ax,WORD PTR [bp-4]	;a
	sub	ax,WORD PTR [bp-26]	;inner
	mov	WORD PTR [bp-10],ax	;il
	les	bx,DWORD PTR [bp+14]	;walk
	sub	ax,WORD PTR es:[bx]
	neg	ax
	mov	WORD PTR [bp-20],ax	;ir
$I204:
; Line 57
$I202:
	jmp	$I205
$I199:
; Line 58
	cmp	WORD PTR [bp-16],-1	;outerK
	jge	$JCC1729
	jmp	$I207
$JCC1729:
	mov	ax,WORD PTR [bp-16]	;outerK
	cmp	WORD PTR [bp-8],ax	;b
	jge	$JCC1740
	jmp	$I207
$JCC1740:
	cmp	WORD PTR [bp-12],-1	;innerK
	jge	$JCC1749
	jmp	$I207
$JCC1749:
	mov	ax,WORD PTR [bp-12]	;innerK
	cmp	WORD PTR [bp-8],ax	;b
	jg	$JCC1760
	jmp	$I207
$JCC1760:
	mov	ax,WORD PTR [bp-16]	;outerK
	cmp	WORD PTR [bp-12],ax	;innerK
	jg	$JCC1771
	jmp	$I206
$JCC1771:
$I207:
	mov	ax,-1
	jmp	$EX178
; Line 59
$I206:
	mov	ax,WORD PTR [bp-4]	;a
	sub	ax,WORD PTR [bp-14]	;y
	mov	WORD PTR [bp-18],ax	;distance
; Line 60
$FC209:
	mov	ax,WORD PTR [bp-16]	;outerK
	inc	ax
	cmp	ax,WORD PTR [bp-8]	;b
	jle	$JCC1798
	jmp	$FB210
$JCC1798:
	mov	ax,WORD PTR [bp-18]	;distance
	mov	si,WORD PTR [bp-16]	;outerK
	shl	si,1
	les	bx,DWORD PTR [bp+10]	;work
	cmp	WORD PTR es:[bx+2][si],ax
	jge	$JCC1818
	jmp	$FB210
$JCC1818:
	inc	WORD PTR [bp-16]	;outerK
	jmp	$FC209
$FB210:
; Line 61
$FC212:
	mov	ax,WORD PTR [bp-12]	;innerK
	inc	ax
	cmp	ax,WORD PTR [bp-8]	;b
	jl	$JCC1836
	jmp	$FB213
$JCC1836:
	mov	si,WORD PTR [bp-12]	;innerK
	shl	si,1
	les	bx,DWORD PTR [bp+10]	;work
	mov	ax,WORD PTR es:[bx+2][si]
	dec	ax
	mov	WORD PTR [bp-26],ax	;inner
	mov	ax,WORD PTR [bp-26]	;inner
	mov	si,WORD PTR [bp-12]	;innerK
	shl	si,1
	les	bx,DWORD PTR [bp+10]	;work
	cmp	WORD PTR es:[bx+4][si],ax
	jl	$JCC1872
	jmp	$I214
$JCC1872:
	mov	si,WORD PTR [bp-12]	;innerK
	shl	si,1
	les	bx,DWORD PTR [bp+10]	;work
	mov	ax,WORD PTR es:[bx+4][si]
	mov	WORD PTR [bp-26],ax	;inner
$I214:
	mov	ax,WORD PTR [bp-18]	;distance
	cmp	WORD PTR [bp-26],ax	;inner
	jl	$JCC1898
	jmp	$I215
$JCC1898:
	jmp	$FB213
$I215:
	inc	WORD PTR [bp-12]	;innerK
	jmp	$FC212
$FB213:
; Line 62
	mov	ax,WORD PTR [bp-8]	;b
	sub	ax,WORD PTR [bp-16]	;outerK
	mov	WORD PTR [bp-24],ax	;l
	les	bx,DWORD PTR [bp+14]	;walk
	sub	ax,WORD PTR es:[bx]
	neg	ax
	mov	WORD PTR [bp-6],ax	;r
	cmp	WORD PTR [bp-12],0	;innerK
	jge	$JCC1936
	jmp	$I216
$JCC1936:
	mov	ax,WORD PTR [bp-8]	;b
	sub	ax,WORD PTR [bp-12]	;innerK
	mov	WORD PTR [bp-10],ax	;il
	les	bx,DWORD PTR [bp+14]	;walk
	sub	ax,WORD PTR es:[bx]
	neg	ax
	mov	WORD PTR [bp-20],ax	;ir
; Line 63
$I216:
$I205:
; Line 64
	cmp	WORD PTR [bp-24],0	;l
	jge	$JCC1965
	jmp	$I218
$JCC1965:
	mov	ax,WORD PTR [bp-6]	;r
	cmp	WORD PTR [bp-24],ax	;l
	jl	$JCC1976
	jmp	$I218
$JCC1976:
	mov	ax,WORD PTR [bp-6]	;r
	les	bx,DWORD PTR [bp+14]	;walk
	cmp	WORD PTR es:[bx],ax
	jge	$JCC1990
	jmp	$I218
$JCC1990:
	cmp	WORD PTR [bp-10],0	;il
	je	$JCC1999
	jmp	$I219
$JCC1999:
	cmp	WORD PTR [bp-20],0	;ir
	jne	$JCC2008
	jmp	$I217
$JCC2008:
$I219:
	mov	ax,WORD PTR [bp-10]	;il
	cmp	WORD PTR [bp-24],ax	;l
	jl	$JCC2019
	jmp	$I220
$JCC2019:
	mov	ax,WORD PTR [bp-10]	;il
	cmp	WORD PTR [bp-20],ax	;ir
	jg	$JCC2030
	jmp	$I220
$JCC2030:
	mov	ax,WORD PTR [bp-6]	;r
	cmp	WORD PTR [bp-20],ax	;ir
	jge	$JCC2041
	jmp	$I217
$JCC2041:
$I220:
$I218:
	mov	ax,-1
	jmp	$EX178
; Line 65
$I217:
	mov	ax,WORD PTR [bp-14]	;y
	les	bx,DWORD PTR [bp+6]	;pair
	mov	WORD PTR es:[bx],ax
	les	bx,DWORD PTR [bp+14]	;walk
	mov	ax,WORD PTR es:[bx+2]
	sub	ax,WORD PTR [bp-14]	;y
	dec	ax
	les	bx,DWORD PTR [bp+6]	;pair
	mov	WORD PTR es:[bx+2],ax
	mov	ax,WORD PTR [bp-24]	;l
	les	bx,DWORD PTR [bp+6]	;pair
	mov	WORD PTR es:[bx+4],ax
	mov	ax,WORD PTR [bp-6]	;r
	les	bx,DWORD PTR [bp+6]	;pair
	mov	WORD PTR es:[bx+6],ax
	mov	ax,WORD PTR [bp-10]	;il
	les	bx,DWORD PTR [bp+6]	;pair
	mov	WORD PTR es:[bx+8],ax
	mov	ax,WORD PTR [bp-20]	;ir
	les	bx,DWORD PTR [bp+6]	;pair
	mov	WORD PTR es:[bx+10],ax
; Line 66
	mov	ax,WORD PTR [bp-16]	;outerK
	les	bx,DWORD PTR [bp+14]	;walk
	mov	WORD PTR es:[bx+12],ax
	mov	ax,WORD PTR [bp-12]	;innerK
	les	bx,DWORD PTR [bp+14]	;walk
	mov	WORD PTR es:[bx+14],ax
	mov	ax,WORD PTR [bp-14]	;y
	inc	ax
	les	bx,DWORD PTR [bp+14]	;walk
	mov	WORD PTR es:[bx+10],ax
; Line 67
	mov	ax,1
	jmp	$EX178
; Line 68
$EX178:
	pop	si
	pop	di
	sub	bp,2
	mov	sp,bp
	pop	ds
	pop	bp
	dec	bp
	ret	12

GENFARNEXT	ENDP
; Line 69
	PUBLIC	GENFARMAKE
GENFARMAKE	PROC FAR
	push	ds
	pop	ax
	nop	
	inc	bp
	push	bp
	mov	bp,sp
	push	ds
	mov	ds,ax
	sub	sp,32
	push	di
	push	si
;	walk = -32
;	pair = -16
;	status = -4
;	width = 16
;	height = 14
;	work = 10
;	out = 6
; Line 71
	mov	ax,WORD PTR [bp+8]
	or	ax,WORD PTR [bp+6]	;out
	je	$JCC2191
	jmp	$I229
$JCC2191:
	mov	ax,0
	jmp	$EX225
; Line 72
$I229:
	push	WORD PTR [bp+16]	;width
	push	WORD PTR [bp+14]	;height
	push	WORD PTR [bp+12]
	push	WORD PTR [bp+10]	;work
	lea	ax,WORD PTR [bp-32]	;walk
	push	ss
	push	ax
	call	FAR PTR GENFARPREPARE
	cmp	ax,0
	je	$JCC2227
	jmp	$I230
$JCC2227:
	mov	ax,0
	jmp	$EX225
; Line 73
$I230:
$FC232:
	lea	ax,WORD PTR [bp-32]	;walk
	push	ss
	push	ax
	push	WORD PTR [bp+12]
	push	WORD PTR [bp+10]	;work
	lea	ax,WORD PTR [bp-16]	;pair
	push	ss
	push	ax
	call	FAR PTR GENFARNEXT
	mov	WORD PTR [bp-4],ax	;status
	cmp	ax,0
	jg	$JCC2265
	jmp	$FB233
$JCC2265:
; Line 74
	mov	ax,WORD PTR [bp-12]
	mov	cl,3
	mov	bx,WORD PTR [bp-16]	;pair
	shl	bx,cl
	les	si,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx][si],ax
	mov	ax,WORD PTR [bp-10]
	mov	si,WORD PTR [bp-16]	;pair
	shl	si,cl
	les	bx,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx+2][si],ax
	mov	ax,WORD PTR [bp-8]
	mov	si,WORD PTR [bp-16]	;pair
	shl	si,cl
	les	bx,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx+4][si],ax
	mov	ax,WORD PTR [bp-6]
	mov	si,WORD PTR [bp-16]	;pair
	shl	si,cl
	les	bx,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx+6][si],ax
; Line 75
	mov	ax,WORD PTR [bp-16]	;pair
	cmp	WORD PTR [bp-14],ax
	jne	$JCC2337
	jmp	$I234
$JCC2337:
	mov	ax,WORD PTR [bp-12]
	mov	bx,WORD PTR [bp-14]
	shl	bx,cl
	les	si,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx][si],ax
	mov	ax,WORD PTR [bp-10]
	mov	si,WORD PTR [bp-14]
	shl	si,cl
	les	bx,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx+2][si],ax
	mov	ax,WORD PTR [bp-8]
	mov	si,WORD PTR [bp-14]
	shl	si,cl
	les	bx,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx+4][si],ax
	mov	ax,WORD PTR [bp-6]
	mov	si,WORD PTR [bp-14]
	shl	si,cl
	les	bx,DWORD PTR [bp+6]	;out
	mov	WORD PTR es:[bx+6][si],ax
; Line 76
$I234:
	jmp	$FC232
$FB233:
; Line 77
	cmp	WORD PTR [bp-4],1	;status
	sbb	ax,ax
	neg	ax
	jmp	$EX225
; Line 78
$EX225:
	pop	si
	pop	di
	sub	bp,2
	mov	sp,bp
	pop	ds
	pop	bp
	dec	bp
	ret	12

GENFARMAKE	ENDP
_TEXT	ENDS
END
