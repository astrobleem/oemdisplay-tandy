;	Static Name Aliases
;
	TITLE   GENDRAW.C
	.8086
INCLUDELIB	SLIBCE
_TEXT	SEGMENT  WORD PUBLIC 'CODE'
_TEXT	ENDS
_DATA	SEGMENT  WORD PUBLIC 'DATA'
_DATA	ENDS
CONST	SEGMENT  WORD PUBLIC 'CONST'
CONST	ENDS
_BSS	SEGMENT  WORD PUBLIC 'BSS'
_BSS	ENDS
DGROUP	GROUP	CONST, _BSS, _DATA
	ASSUME DS: DGROUP
	ASSUME  SS: NOTHING
EXTRN	GENFARPREPARE:FAR
EXTRN	GENFARNEXT:FAR
_TEXT      SEGMENT
	ASSUME	CS: _TEXT
; Line 1
; Line 3
; Line 8
range	PROC NEAR
	push	bp
	mov	bp,sp
	sub	sp,4
	push	di
	push	si
;	u = -4
;	end = 14
;	start = 10
;	size = 8
;	ptr = 4
; Line 9
	mov	ax,WORD PTR [bp+6]
	or	ax,WORD PTR [bp+4]	;ptr
	jne	$JCC15
	jmp	$I141
$JCC15:
	cmp	WORD PTR [bp+8],0	;size
	je	$JCC24
	jmp	$I140
$JCC24:
$I141:
	mov	ax,0
	jmp	$EX138
; Line 14
$I140:
	mov	ax,WORD PTR [bp+4]	;ptr
	mov	dx,WORD PTR [bp+6]
	mov	WORD PTR [bp-4],ax	;u
	mov	WORD PTR [bp-2],dx
; Line 15
	mov	ax,WORD PTR [bp-4]	;u
	sub	dx,dx
	add	ax,WORD PTR [bp+8]	;size
	adc	dx,0
	cmp	dx,1
	jae	$JCC61
	jmp	$I142
$JCC61:
	jbe	$JCC66
	jmp	$L20000
$JCC66:
	cmp	ax,0
	ja	$JCC74
	jmp	$I142
$JCC74:
$L20000:
	mov	ax,0
	jmp	$EX138
; Line 16
$I142:
	mov	ax,WORD PTR [bp-2]
	sub	dx,dx
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	shl	ax,1
	rcl	dx,1
	add	ax,WORD PTR [bp-4]	;u
	adc	dx,0
	mov	WORD PTR [bp-4],ax	;u
	mov	WORD PTR [bp-2],dx
; Line 17
	mov	ax,WORD PTR [bp-4]	;u
	mov	dx,WORD PTR [bp-2]
	add	ax,WORD PTR [bp+8]	;size
	adc	dx,0
	cmp	dx,16
	jae	$JCC133
	jmp	$I143
$JCC133:
	jbe	$JCC138
	jmp	$L20001
$JCC138:
	cmp	ax,0
	ja	$JCC146
	jmp	$I143
$JCC146:
$L20001:
	mov	ax,0
	jmp	$EX138
; Line 19
$I143:
	mov	ax,WORD PTR [bp-4]	;u
	mov	dx,WORD PTR [bp-2]
	les	bx,DWORD PTR [bp+10]	;start
	mov	WORD PTR es:[bx],ax
	mov	WORD PTR es:[bx+2],dx
	add	ax,WORD PTR [bp+8]	;size
	adc	dx,0
	les	bx,DWORD PTR [bp+14]	;end
	mov	WORD PTR es:[bx],ax
	mov	WORD PTR es:[bx+2],dx
	mov	ax,1
	jmp	$EX138
; Line 20
$EX138:
	pop	si
	pop	di
	mov	sp,bp
	pop	bp
	ret	

range	ENDP
; Line 21
memory	PROC NEAR
	push	bp
	mov	bp,sp
	sub	sp,44
	push	di
	push	si
;	begin = -20
;	end = -40
;	i = -42
;	j = -44
;	pair = 16
;	walk = 12
;	work = 8
;	ctx = 4
; Line 22
	lea	ax,WORD PTR [bp-40]	;end
	push	ss
	push	ax
	lea	ax,WORD PTR [bp-20]	;begin
	push	ss
	push	ax
	mov	ax,44
	push	ax
	push	WORD PTR [bp+6]
	push	WORD PTR [bp+4]	;ctx
	call	range
	add	sp,14
	cmp	ax,0
	je	$JCC239
	jmp	$I154
$JCC239:
	mov	ax,0
	jmp	$EX149
; Line 23
$I154:
	lea	ax,WORD PTR [bp-36]
	push	ss
	push	ax
	lea	ax,WORD PTR [bp-16]
	push	ss
	push	ax
	mov	ax,32000
	push	ax
	les	bx,DWORD PTR [bp+4]	;ctx
	push	WORD PTR es:[bx+2]
	push	WORD PTR es:[bx]
	call	range
	add	sp,14
	cmp	ax,0
	jne	$JCC283
	jmp	$I156
$JCC283:
	lea	ax,WORD PTR [bp-32]
	push	ss
	push	ax
	lea	ax,WORD PTR [bp-12]
	push	ss
	push	ax
	mov	ax,640
	push	ax
	push	WORD PTR [bp+10]
	push	WORD PTR [bp+8]	;work
	call	range
	add	sp,14
	cmp	ax,0
	jne	$JCC317
	jmp	$I156
$JCC317:
	lea	ax,WORD PTR [bp-28]
	push	ss
	push	ax
	lea	ax,WORD PTR [bp-8]
	push	ss
	push	ax
	mov	ax,16
	push	ax
	push	WORD PTR [bp+14]
	push	WORD PTR [bp+12]	;walk
	call	range
	add	sp,14
	cmp	ax,0
	jne	$JCC351
	jmp	$I156
$JCC351:
	lea	ax,WORD PTR [bp-24]
	push	ss
	push	ax
	lea	ax,WORD PTR [bp-4]
	push	ss
	push	ax
	mov	ax,12
	push	ax
	push	WORD PTR [bp+18]
	push	WORD PTR [bp+16]	;pair
	call	range
	add	sp,14
	cmp	ax,0
	je	$JCC385
	jmp	$I155
$JCC385:
$I156:
	mov	ax,0
	jmp	$EX149
; Line 24
$I155:
	mov	WORD PTR [bp-42],0	;i
	jmp	$F157
$FC158:
	inc	WORD PTR [bp-42]	;i
$F157:
	cmp	WORD PTR [bp-42],5	;i
	jl	$JCC411
	jmp	$FB159
$JCC411:
	mov	ax,WORD PTR [bp-42]	;i
	inc	ax
	mov	WORD PTR [bp-44],ax	;j
	jmp	$F160
$FC161:
	inc	WORD PTR [bp-44]	;j
$F160:
	cmp	WORD PTR [bp-44],5	;j
	jl	$JCC433
	jmp	$FB162
$JCC433:
	mov	si,WORD PTR [bp-42]	;i
	shl	si,1
	shl	si,1
	mov	ax,WORD PTR [bp-20][si]
	mov	dx,WORD PTR [bp-18][si]
	mov	si,WORD PTR [bp-44]	;j
	shl	si,1
	shl	si,1
	cmp	WORD PTR [bp-38][si],dx
	jae	$JCC461
	jmp	$I163
$JCC461:
	jbe	$JCC466
	jmp	$L20002
$JCC466:
	cmp	WORD PTR [bp-40][si],ax
	ja	$JCC474
	jmp	$I163
$JCC474:
$L20002:
	mov	si,WORD PTR [bp-42]	;i
	shl	si,1
	shl	si,1
	mov	ax,WORD PTR [bp-40][si]
	mov	dx,WORD PTR [bp-38][si]
	mov	si,WORD PTR [bp-44]	;j
	shl	si,1
	shl	si,1
	cmp	WORD PTR [bp-18][si],dx
	jbe	$JCC502
	jmp	$I163
$JCC502:
	jae	$JCC507
	jmp	$L20003
$JCC507:
	cmp	WORD PTR [bp-20][si],ax
	jb	$JCC515
	jmp	$I163
$JCC515:
$L20003:
	mov	ax,0
	jmp	$EX149
; Line 25
$I163:
	jmp	$FC161
$FB162:
	jmp	$FC158
$FB159:
	mov	ax,1
	jmp	$EX149
; Line 26
$EX149:
	pop	si
	pop	di
	mov	sp,bp
	pop	bp
	ret	

memory	ENDP
; Line 27
span	PROC NEAR
	push	bp
	mov	bp,sp
	sub	sp,14
	push	di
	push	si
;	first = -8
;	last = -4
;	n = -14
;	plane = -2
;	offset = -6
;	mask = -10
;	value = -12
;	invert = 16
;	color = 14
;	r = 12
;	l = 10
;	y = 8
;	c = 4
; Line 28
	cmp	WORD PTR [bp+8],0	;y
	jge	$JCC557
	jmp	$I180
$JCC557:
	cmp	WORD PTR [bp+8],200	;y
	jl	$JCC567
	jmp	$I180
$JCC567:
	mov	ax,WORD PTR [bp+8]	;y
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+36],ax
	jle	$JCC582
	jmp	$I180
$JCC582:
	mov	ax,WORD PTR [bp+8]	;y
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+40],ax
	jle	$JCC597
	jmp	$I179
$JCC597:
$I180:
	jmp	$EX171
; Line 29
$I179:
	cmp	WORD PTR [bp+10],0	;l
	jl	$JCC609
	jmp	$I181
$JCC609:
	mov	WORD PTR [bp+10],0	;l
; Line 30
$I181:
	cmp	WORD PTR [bp+12],320	;r
	jg	$JCC624
	jmp	$I182
$JCC624:
	mov	WORD PTR [bp+12],320	;r
; Line 31
$I182:
	mov	ax,WORD PTR [bp+10]	;l
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+34],ax
	jg	$JCC644
	jmp	$I183
$JCC644:
	les	bx,DWORD PTR [bp+4]	;c
	mov	ax,WORD PTR es:[bx+34]
	mov	WORD PTR [bp+10],ax	;l
; Line 32
$I183:
	mov	ax,WORD PTR [bp+12]	;r
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+38],ax
	jl	$JCC669
	jmp	$I184
$JCC669:
	les	bx,DWORD PTR [bp+4]	;c
	mov	ax,WORD PTR es:[bx+38]
	mov	WORD PTR [bp+12],ax	;r
; Line 33
$I184:
	mov	ax,WORD PTR [bp+10]	;l
	cmp	WORD PTR [bp+12],ax	;r
	jle	$JCC690
	jmp	$I185
$JCC690:
	jmp	$EX171
; Line 34
$I185:
	mov	cl,3
	mov	ax,WORD PTR [bp+10]	;l
	shr	ax,cl
	mov	WORD PTR [bp-8],ax	;first
	mov	ax,WORD PTR [bp+12]	;r
	dec	ax
	shr	ax,cl
	mov	WORD PTR [bp-4],ax	;last
; Line 38
	cmp	WORD PTR [bp+16],0	;invert
	je	$JCC721
	jmp	$I186
$JCC721:
	mov	ax,WORD PTR [bp-8]	;first
	cmp	WORD PTR [bp-4],ax	;last
	je	$JCC732
	jmp	$I186
$JCC732:
; Line 39
	mov	cl,7
	mov	al,BYTE PTR [bp+12]	;r
	dec	al
	and	al,7
	sub	cl,al
	mov	ax,255
	mov	dx,cx
	mov	cl,BYTE PTR [bp+10]	;l
	and	cl,7
	shr	ax,cl
	mov	cl,dl
	mov	dx,255
	shl	dx,cl
	and	dl,al
	sub	dh,dh
	mov	WORD PTR [bp-10],dx	;mask
; Line 40
	mov	ax,160
	imul	WORD PTR [bp+8]	;y
	add	ax,WORD PTR [bp-8]	;first
	mov	WORD PTR [bp-6],ax	;offset
; Line 41
	mov	WORD PTR [bp-2],0	;plane
	jmp	$F187
$FC188:
	inc	WORD PTR [bp-2]	;plane
$F187:
	cmp	WORD PTR [bp-2],4	;plane
	jb	$JCC802
	jmp	$FB189
$JCC802:
; Line 42
	les	bx,DWORD PTR [bp+4]	;c
	les	bx,DWORD PTR es:[bx]
	mov	si,WORD PTR [bp-6]	;offset
	mov	al,BYTE PTR es:[bx][si]
	mov	BYTE PTR [bp-12],al	;value
; Line 43
	test	BYTE PTR [bp+14],1	;color
	jne	$JCC826
	jmp	$I190
$JCC826:
	mov	al,BYTE PTR [bp-10]	;mask
	or	BYTE PTR [bp-12],al	;value
; Line 44
	jmp	$I191
$I190:
	mov	al,BYTE PTR [bp-10]	;mask
	not	al
	and	BYTE PTR [bp-12],al	;value
$I191:
; Line 45
	mov	al,BYTE PTR [bp-12]	;value
	les	bx,DWORD PTR [bp+4]	;c
	les	bx,DWORD PTR es:[bx]
	mov	si,WORD PTR [bp-6]	;offset
	mov	BYTE PTR es:[bx][si],al
; Line 46
	sar	WORD PTR [bp+14],1	;color
	add	WORD PTR [bp-6],40	;offset
; Line 47
	jmp	$FC188
$FB189:
; Line 48
	jmp	$EX171
; Line 49
; Line 50
$I186:
	mov	WORD PTR [bp-2],0	;plane
	jmp	$F192
$FC193:
	inc	WORD PTR [bp-2]	;plane
$F192:
	cmp	WORD PTR [bp-2],4	;plane
	jb	$JCC891
	jmp	$FB194
$JCC891:
; Line 51
	cmp	WORD PTR [bp+16],2	;invert
	je	$JCC900
	jmp	$I195
$JCC900:
	mov	cl,BYTE PTR [bp-2]	;plane
	mov	ax,1
	shl	ax,cl
	test	ax,WORD PTR [bp+14]	;color
	je	$JCC916
	jmp	$I195
$JCC916:
	jmp	$FC193
; Line 52
$I195:
	mov	ax,WORD PTR [bp-8]	;first
	mov	WORD PTR [bp-14],ax	;n
	jmp	$F196
$FC197:
	inc	WORD PTR [bp-14]	;n
$F196:
	mov	ax,WORD PTR [bp-4]	;last
	cmp	WORD PTR [bp-14],ax	;n
	jbe	$JCC942
	jmp	$FB198
$JCC942:
; Line 53
	mov	WORD PTR [bp-10],255	;mask
; Line 54
	mov	ax,WORD PTR [bp-8]	;first
	cmp	WORD PTR [bp-14],ax	;n
	je	$JCC958
	jmp	$I199
$JCC958:
	mov	cl,BYTE PTR [bp+10]	;l
	and	cl,7
	mov	ax,255
	shr	ax,cl
	and	WORD PTR [bp-10],ax	;mask
; Line 55
$I199:
	mov	ax,WORD PTR [bp-4]	;last
	cmp	WORD PTR [bp-14],ax	;n
	je	$JCC983
	jmp	$I200
$JCC983:
	mov	cl,7
	mov	al,BYTE PTR [bp+12]	;r
	dec	al
	and	al,7
	sub	cl,al
	mov	ax,255
	shl	ax,cl
	sub	ah,ah
	and	WORD PTR [bp-10],ax	;mask
; Line 56
$I200:
	mov	ax,WORD PTR [bp+8]	;y
	shl	ax,1
	shl	ax,1
	add	ax,WORD PTR [bp-2]	;plane
	mov	cx,40
	mul	cx
	mov	bx,ax
	add	bx,WORD PTR [bp-14]	;n
	mov	WORD PTR [bp-6],bx	;offset
	les	si,DWORD PTR [bp+4]	;c
	les	si,DWORD PTR es:[si]
	mov	al,BYTE PTR es:[bx][si]
	mov	BYTE PTR [bp-12],al	;value
; Line 57
	cmp	WORD PTR [bp+16],0	;invert
	jne	$JCC1048
	jmp	$I201
$JCC1048:
	mov	al,BYTE PTR [bp-10]	;mask
	xor	BYTE PTR [bp-12],al	;value
; Line 58
	jmp	$I202
$I201:
	mov	cl,BYTE PTR [bp-2]	;plane
	mov	ax,1
	shl	ax,cl
	test	ax,WORD PTR [bp+14]	;color
	jne	$JCC1073
	jmp	$I203
$JCC1073:
	mov	al,BYTE PTR [bp-10]	;mask
	or	BYTE PTR [bp-12],al	;value
; Line 59
	jmp	$I204
$I203:
	mov	al,BYTE PTR [bp-10]	;mask
	not	al
	and	BYTE PTR [bp-12],al	;value
$I204:
$I202:
; Line 60
	mov	al,BYTE PTR [bp-12]	;value
	les	bx,DWORD PTR [bp+4]	;c
	les	bx,DWORD PTR es:[bx]
	mov	si,WORD PTR [bp-6]	;offset
	mov	BYTE PTR es:[bx][si],al
; Line 61
	jmp	$FC197
$FB198:
; Line 62
	jmp	$FC193
$FB194:
; Line 63
$EX171:
	pop	si
	pop	di
	mov	sp,bp
	pop	bp
	ret	

span	ENDP
; Line 64
row	PROC NEAR
	push	bp
	mov	bp,sp
	sub	sp,10
	push	di
	push	si
;	l = -10
;	r = -2
;	il = -4
;	ir = -8
;	invert = -6
;	y = 12
;	p = 8
;	c = 4
	les	bx,DWORD PTR [bp+8]	;p
	mov	ax,WORD PTR es:[bx+4]
	les	bx,DWORD PTR [bp+4]	;c
	add	ax,WORD PTR es:[bx+14]
	mov	WORD PTR [bp-10],ax	;l
	les	bx,DWORD PTR [bp+4]	;c
	mov	ax,WORD PTR es:[bx+14]
	les	bx,DWORD PTR [bp+8]	;p
	add	ax,WORD PTR es:[bx+6]
	mov	WORD PTR [bp-2],ax	;r
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+32],7
	je	$JCC1173
	jmp	$L20004
$JCC1173:
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+26],15
	je	$JCC1186
	jmp	$L20006
$JCC1186:
	mov	ax,1
	jmp	$L20007
$L20006:
	mov	ax,2
$L20007:
	jmp	$L20005
$L20004:
	mov	ax,0
$L20005:
	mov	WORD PTR [bp-6],ax	;invert
; Line 65
	les	bx,DWORD PTR [bp+8]	;p
	cmp	WORD PTR es:[bx+10],0
	je	$JCC1217
	jmp	$I215
$JCC1217:
	push	WORD PTR [bp-6]	;invert
	les	bx,DWORD PTR [bp+4]	;c
	push	WORD PTR es:[bx+26]
	push	WORD PTR [bp-2]	;r
	push	WORD PTR [bp-10]	;l
	push	WORD PTR [bp+12]	;y
	push	WORD PTR [bp+6]
	push	WORD PTR [bp+4]	;c
	call	span
	add	sp,14
; Line 66
	jmp	$I216
$I215:
; Line 67
	les	bx,DWORD PTR [bp+8]	;p
	mov	ax,WORD PTR es:[bx+8]
	les	bx,DWORD PTR [bp+4]	;c
	add	ax,WORD PTR es:[bx+14]
	mov	WORD PTR [bp-4],ax	;il
	les	bx,DWORD PTR [bp+8]	;p
	mov	ax,WORD PTR es:[bx+10]
	les	bx,DWORD PTR [bp+4]	;c
	add	ax,WORD PTR es:[bx+14]
	mov	WORD PTR [bp-8],ax	;ir
; Line 68
	push	WORD PTR [bp-6]	;invert
	les	bx,DWORD PTR [bp+4]	;c
	push	WORD PTR es:[bx+26]
	push	WORD PTR [bp-4]	;il
	push	WORD PTR [bp-10]	;l
	push	WORD PTR [bp+12]	;y
	push	WORD PTR [bp+6]
	push	WORD PTR [bp+4]	;c
	call	span
	add	sp,14
	push	WORD PTR [bp-6]	;invert
	les	bx,DWORD PTR [bp+4]	;c
	push	WORD PTR es:[bx+26]
	push	WORD PTR [bp-2]	;r
	push	WORD PTR [bp-8]	;ir
	push	WORD PTR [bp+12]	;y
	push	WORD PTR [bp+6]
	push	WORD PTR [bp+4]	;c
	call	span
	add	sp,14
; Line 69
	les	bx,DWORD PTR [bp+4]	;c
	cmp	WORD PTR es:[bx+28],0
	je	$JCC1360
	jmp	$I217
$JCC1360:
	mov	ax,0
	push	ax
	les	bx,DWORD PTR [bp+4]	;c
	push	WORD PTR es:[bx+30]
	push	WORD PTR [bp-8]	;ir
	push	WORD PTR [bp-4]	;il
	push	WORD PTR [bp+12]	;y
	push	WORD PTR [bp+6]
	push	WORD PTR [bp+4]	;c
	call	span
	add	sp,14
; Line 70
$I217:
$I216:
; Line 71
$EX209:
	pop	si
	pop	di
	mov	sp,bp
	pop	bp
	ret	

row	ENDP
; Line 72
	PUBLIC	GENDRAWKERNEL
GENDRAWKERNEL	PROC FAR
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
;	mode = -6
;	status = -4
;	c = 18
;	work = 14
;	walk = 10
;	pair = 6
; Line 73
	push	WORD PTR [bp+8]
	push	WORD PTR [bp+6]	;pair
	push	WORD PTR [bp+12]
	push	WORD PTR [bp+10]	;walk
	push	WORD PTR [bp+16]
	push	WORD PTR [bp+14]	;work
	push	WORD PTR [bp+20]
	push	WORD PTR [bp+18]	;c
	call	memory
	add	sp,16
	cmp	ax,0
	je	$JCC1452
	jmp	$I225
$JCC1452:
	mov	ax,-1
	jmp	$EX222
; Line 74
$I225:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+4],320
	je	$JCC1472
	jmp	$I227
$JCC1472:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+6],200
	je	$JCC1486
	jmp	$I227
$JCC1486:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+8],16
	je	$JCC1499
	jmp	$I227
$JCC1499:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+10],1
	je	$JCC1512
	jmp	$I227
$JCC1512:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+12],1
	je	$JCC1525
	jmp	$I227
$JCC1525:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+42],0
	je	$JCC1538
	jmp	$I227
$JCC1538:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+22],1
	je	$JCC1551
	jmp	$I227
$JCC1551:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+24],0
	jne	$JCC1564
	jmp	$I226
$JCC1564:
$I227:
	mov	ax,-1
	jmp	$EX222
; Line 75
$I226:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+18],2
	jge	$JCC1583
	jmp	$I229
$JCC1583:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+18],320
	jle	$JCC1597
	jmp	$I229
$JCC1597:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+20],2
	jge	$JCC1610
	jmp	$I229
$JCC1610:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+20],200
	jle	$JCC1624
	jmp	$I229
$JCC1624:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+14],-320
	jge	$JCC1638
	jmp	$I229
$JCC1638:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+14],320
	jle	$JCC1652
	jmp	$I229
$JCC1652:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+16],-200
	jge	$JCC1666
	jmp	$I229
$JCC1666:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+16],200
	jg	$JCC1680
	jmp	$I228
$JCC1680:
$I229:
	mov	ax,-1
	jmp	$EX222
; Line 76
$I228:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+34],0
	jge	$JCC1699
	jmp	$I231
$JCC1699:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+34]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+38],ax
	jge	$JCC1718
	jmp	$I231
$JCC1718:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+38],320
	jle	$JCC1732
	jmp	$I231
$JCC1732:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+36],0
	jge	$JCC1745
	jmp	$I231
$JCC1745:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+40]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+36],ax
	jle	$JCC1764
	jmp	$I231
$JCC1764:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+40],200
	jg	$JCC1778
	jmp	$I230
$JCC1778:
$I231:
	mov	ax,-1
	jmp	$EX222
; Line 77
$I230:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+32],13
	je	$JCC1797
	jmp	$L20008
$JCC1797:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+26],0
	je	$JCC1810
	jmp	$L20008
$JCC1810:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+28],1
	jne	$JCC1823
	jmp	$L20010
$JCC1823:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+28],0
	je	$JCC1836
	jmp	$L20008
$JCC1836:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+30],9
	je	$JCC1849
	jmp	$L20008
$JCC1849:
$L20010:
	mov	WORD PTR [bp-6],1	;mode
	jmp	$L20009
$L20008:
	mov	WORD PTR [bp-6],0	;mode
$L20009:
; Line 78
	cmp	WORD PTR [bp-6],0	;mode
	je	$JCC1871
	jmp	$I232
$JCC1871:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+32],7
	je	$JCC1884
	jmp	$L20011
$JCC1884:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+26],1
	jge	$JCC1897
	jmp	$L20011
$JCC1897:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+26],15
	jle	$JCC1910
	jmp	$L20011
$JCC1910:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+28],1
	je	$JCC1923
	jmp	$L20011
$JCC1923:
	mov	WORD PTR [bp-6],1	;mode
	jmp	$L20012
$L20011:
	mov	WORD PTR [bp-6],0	;mode
$L20012:
; Line 80
$I232:
	cmp	WORD PTR [bp-6],0	;mode
	je	$JCC1945
	jmp	$I233
$JCC1945:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+32],13
	je	$JCC1958
	jmp	$L20013
$JCC1958:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+26],1
	jge	$JCC1971
	jmp	$L20013
$JCC1971:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+26],15
	jle	$JCC1984
	jmp	$L20013
$JCC1984:
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+28],1
	je	$JCC1997
	jmp	$L20013
$JCC1997:
	mov	WORD PTR [bp-6],1	;mode
	jmp	$L20014
$L20013:
	mov	WORD PTR [bp-6],0	;mode
$L20014:
; Line 81
$I233:
	cmp	WORD PTR [bp-6],0	;mode
	je	$JCC2019
	jmp	$I234
$JCC2019:
	mov	ax,-1
	jmp	$EX222
; Line 82
$I234:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+34]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+38],ax
	jne	$JCC2044
	jmp	$I236
$JCC2044:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+40]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+36],ax
	jne	$JCC2063
	jmp	$I236
$JCC2063:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+14]
	les	bx,DWORD PTR [bp+18]	;c
	add	ax,WORD PTR es:[bx+18]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	ax,WORD PTR es:[bx+34]
	jg	$JCC2089
	jmp	$I236
$JCC2089:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+14]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+38],ax
	jg	$JCC2108
	jmp	$I236
$JCC2108:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+20]
	les	bx,DWORD PTR [bp+18]	;c
	add	ax,WORD PTR es:[bx+16]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	ax,WORD PTR es:[bx+36]
	jg	$JCC2134
	jmp	$I236
$JCC2134:
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+16]
	les	bx,DWORD PTR [bp+18]	;c
	cmp	WORD PTR es:[bx+40],ax
	jle	$JCC2153
	jmp	$I235
$JCC2153:
$I236:
	mov	ax,1
	jmp	$EX222
; Line 83
$I235:
	les	bx,DWORD PTR [bp+18]	;c
	push	WORD PTR es:[bx+18]
	les	bx,DWORD PTR [bp+18]	;c
	push	WORD PTR es:[bx+20]
	push	WORD PTR [bp+16]
	push	WORD PTR [bp+14]	;work
	push	WORD PTR [bp+12]
	push	WORD PTR [bp+10]	;walk
	call	FAR PTR GENFARPREPARE
	cmp	ax,0
	je	$JCC2198
	jmp	$I237
$JCC2198:
	mov	ax,-1
	jmp	$EX222
; Line 84
$I237:
$FC239:
	push	WORD PTR [bp+12]
	push	WORD PTR [bp+10]	;walk
	push	WORD PTR [bp+16]
	push	WORD PTR [bp+14]	;work
	push	WORD PTR [bp+8]
	push	WORD PTR [bp+6]	;pair
	call	FAR PTR GENFARNEXT
	mov	WORD PTR [bp-4],ax	;status
	cmp	ax,0
	jg	$JCC2238
	jmp	$FB240
$JCC2238:
; Line 85
	les	bx,DWORD PTR [bp+18]	;c
	mov	ax,WORD PTR es:[bx+16]
	les	bx,DWORD PTR [bp+6]	;pair
	add	ax,WORD PTR es:[bx]
	push	ax
	push	WORD PTR [bp+8]
	push	WORD PTR [bp+6]	;pair
	push	WORD PTR [bp+20]
	push	WORD PTR [bp+18]	;c
	call	row
	add	sp,10
; Line 86
	les	bx,DWORD PTR [bp+6]	;pair
	mov	ax,WORD PTR es:[bx]
	les	bx,DWORD PTR [bp+6]	;pair
	cmp	WORD PTR es:[bx+2],ax
	jne	$JCC2288
	jmp	$I241
$JCC2288:
	les	bx,DWORD PTR [bp+6]	;pair
	mov	ax,WORD PTR es:[bx+2]
	les	bx,DWORD PTR [bp+18]	;c
	add	ax,WORD PTR es:[bx+16]
	push	ax
	push	WORD PTR [bp+8]
	push	WORD PTR [bp+6]	;pair
	push	WORD PTR [bp+20]
	push	WORD PTR [bp+18]	;c
	call	row
	add	sp,10
; Line 87
$I241:
	jmp	$FC239
$FB240:
; Line 88
	cmp	WORD PTR [bp-4],0	;status
	jge	$JCC2333
	jmp	$L20015
$JCC2333:
	mov	ax,1
	jmp	$L20016
$L20015:
	mov	ax,0
$L20016:
	jmp	$EX222
; Line 89
$EX222:
	pop	si
	pop	di
	sub	bp,2
	mov	sp,bp
	pop	ds
	pop	bp
	dec	bp
	ret	16

GENDRAWKERNEL	ENDP
_TEXT	ENDS
END
