		page	,132
		%out	TgBmp
		name	TGBMP
		title	TANDYGR graphics grab to a BMP file (MIT)

; TANDYGR.GR2: Print Screen in a DOS graphics program (grabber GetBlock).
;
; Windows 3.0 real-mode WINOLDAP puts only OEM text on the Clipboard. So a
; graphics screen - CGA modes 4, 5, 6, Tandy modes 8, 9, 0Ah - is written
; to a 4-bit BMP file (TEMP directory, else WINOLDAP's swap directory, else
; the root of the current drive) and WINOLDAP gets one text line:
;   TANDYGR <path>
; TGCLIP.EXE turns that line into a Clipboard bitmap.
;
; Every BMP pixel is the Windows device index of the colour the pixel shows
; (TGTANDY.ASM tgBuildMap: the mode's colour logic and the palette shadow),
; and the BMP palette is the display driver's colour table, so 4-, 2- and
; 16-colour screens all come out as the colours on the screen. The BMP's
; reserved header word says where the palette came from: 'TK' = the BIOS
; palette state followed by the INT 10h shadow, 'TA' = the mode's BIOS
; default assumed (no INT 10h mode set seen in this session).
;
; Pixel layouts (one scan line, bytes left to right, high bits first):
;   8, 9   two 4-bit pixels per byte
;   4, 5   four 2-bit pixels per byte
;   6      eight 1-bit pixels per byte
;   0Ah    byte pairs: even byte bit 0 of eight pixels, odd byte bit 1
;
; 8086 instructions only. MASM 5.10.

_TEXT		segment byte	public	'CODE'
		assume	cs:_TEXT

		.xlist
		include dc.inc
		include ic.inc
		include grabber.inc
		.list

		extrn	DC:byte
		extrn	IC:byte
		extrn	tgMap:byte
		extrn	tgBuildMap:near
		extrn	tgTempDir:near
		extrn	ComputeYBufPos:near

		public	GrabBmp

tgPre		db	'TANDYGR '
tgPath		db	80 dup (0)
tgLen		dw	0			;bytes of 'TANDYGR path',13,10
tgName		db	'TANDYGR.BMP',0
tgHandle	dw	0
tgY		dw	0
tgOutW		dw	0			;BMP bytes per row
tgT16		db	16 dup (0)		;4 source bits -> one BMP byte
tgTbl		db	256 dup (0)		;8 source bits -> one BMP byte
tgRow		db	320 dup (0)
tgHdr		db	'BM'
tgFSize 	dd	0
tgSrc		dw	0			;'TK' or 'TA'
		dw	0
		dd	118
		dd	40
tgW		dd	0
tgH		dd	0
		dw	1,4
		dd	0
tgISize 	dd	0
		dd	0,0,16,16
		db	000h, 000h, 000h, 000h, 000h, 000h, 080h, 000h, 000h, 080h, 000h, 000h, 000h, 080h, 080h, 000h
		db	080h, 000h, 000h, 000h, 080h, 000h, 080h, 000h, 080h, 080h, 000h, 000h, 080h, 080h, 080h, 000h
		db	040h, 040h, 040h, 000h, 000h, 000h, 0FFh, 000h, 000h, 0FFh, 000h, 000h, 000h, 0FFh, 0FFh, 000h
		db	0FFh, 000h, 000h, 000h, 0FFh, 000h, 0FFh, 000h, 0FFh, 0FFh, 000h, 000h, 0FFh, 0FFh, 0FFh, 000h
TGHDRLEN	equ	$ - tgHdr


;tgBmpPath - tgPath = temporary directory + TANDYGR.BMP, tgLen set
tgBmpPath	proc	near
		assume	ds:_TEXT
		push	es
		push	di
		push	si
		push	cx
		push	cs
		pop	es
		mov	di,offset tgPath
		mov	cx,80 - 12
		call	tgTempDir
		jnc	bpName
		mov	di,offset tgPath	;too long: current drive root
		mov	ah,19h
		int	21h
		add	al,'A'
		stosb
		mov	ax,'\:'
		stosw
bpName:
		mov	si,offset tgName
bpCopy:
		lodsb
		stosb
		or	al,al
		jnz	bpCopy
		sub	di,offset tgPath + 1	;path length
		add	di,8 + 2		;'TANDYGR ' and CR LF
		mov	[tgLen],di
		pop	cx
		pop	si
		pop	di
		pop	es
		ret
tgBmpPath	endp


;tgTables - conversion tables for the current mode from tgMap.
tgTables	proc	near
		assume	ds:_TEXT
		push	ax
		push	bx
		push	cx
		push	si
		mov	al,[DC.dcScrMode]
		cmp	al,0Ah
		je	ttPlanar
		cmp	[IC.icBitsPixel],2
		je	ttTwo
		cmp	[IC.icBitsPixel],1
		je	ttOne
		xor	bx,bx			;4 bits: byte -> byte
ttFour:
		mov	si,bx
		mov	cl,4
		shr	si,cl
		mov	al,[tgMap][si]
		shl	al,cl
		mov	si,bx
		and	si,0Fh
		or	al,[tgMap][si]
		mov	[tgTbl][bx],al
		inc	bx
		cmp	bx,256
		jb	ttFour
		jmp	ttX
ttTwo:						;two 2-bit pixels -> byte
		xor	bx,bx
ttTwoLp:
		mov	si,bx
		shr	si,1
		shr	si,1
		mov	al,[tgMap][si]
		mov	cl,4
		shl	al,cl
		mov	si,bx
		and	si,3
		or	al,[tgMap][si]
		mov	[tgT16][bx],al
		inc	bx
		cmp	bx,16
		jb	ttTwoLp
		jmp	short ttX
ttOne:						;two 1-bit pixels -> byte
		xor	bx,bx
ttOneLp:
		mov	si,bx
		shr	si,1
		mov	al,[tgMap][si]
		mov	cl,4
		shl	al,cl
		mov	si,bx
		and	si,1
		or	al,[tgMap][si]
		mov	[tgT16][bx],al
		inc	bx
		cmp	bx,4
		jb	ttOneLp
		jmp	short ttX
ttPlanar:					;index = b1 bits (2) : b0 bits (2)
		xor	bx,bx
ttPlLp:
		mov	al,bl			;first pixel: b1 bit 3, b0 bit 1
		and	al,8
		shr	al,1
		shr	al,1
		mov	ah,bl
		and	ah,2
		shr	ah,1
		or	al,ah
		xor	ah,ah
		mov	si,ax
		mov	cl,[tgMap][si]
		shl	cl,1
		shl	cl,1
		shl	cl,1
		shl	cl,1
		mov	al,bl			;second pixel: b1 bit 2, b0 bit 0
		and	al,4
		shr	al,1
		mov	ah,bl
		and	ah,1
		or	al,ah
		xor	ah,ah
		mov	si,ax
		or	cl,[tgMap][si]
		mov	[tgT16][bx],cl
		inc	bx
		cmp	bx,16
		jb	ttPlLp
ttX:
		pop	si
		pop	cx
		pop	bx
		pop	ax
		ret
tgTables	endp


;tgConvRow - ds:si -> source scan line; fills tgRow (tgOutW bytes).
tgConvRow	proc	near
		assume	ds:nothing
		push	es
		push	cs
		pop	es
		mov	di,offset tgRow
		mov	cx,cs:[IC.icWidthBytes]
		mov	al,cs:[DC.dcScrMode]
		cmp	al,0Ah
		je	crPlanar
		cmp	cs:[IC.icBitsPixel],2
		je	crTwo
		cmp	cs:[IC.icBitsPixel],1
		je	crOne
		mov	bx,offset tgTbl
crFour:
		lodsb
		xlat	cs:tgTbl
		stosb
		loop	crFour
		jmp	crX
crTwo:
		mov	bx,offset tgT16
crTwoLp:
		lodsb
		mov	ah,al
		shr	al,1
		shr	al,1
		shr	al,1
		shr	al,1
		xlat	cs:tgT16
		stosb
		mov	al,ah
		and	al,0Fh
		xlat	cs:tgT16
		stosb
		loop	crTwoLp
		jmp	short crX
crOne:
		mov	bx,offset tgT16
crOneLp:
		lodsb
		mov	ah,al
		mov	dl,4
crOneBit:
		mov	al,ah
		rol	al,1
		rol	al,1
		mov	ah,al
		and	al,3
		xlat	cs:tgT16
		stosb
		dec	dl
		jnz	crOneBit
		loop	crOneLp
		jmp	short crX
crPlanar:
		shr	cx,1			;byte pairs
		mov	bx,offset tgT16
crPlLp:
		lodsw				;al = bit 0 plane, ah = bit 1 plane
		mov	dx,ax
		push	cx
		mov	cx,4
crPlPix:
		mov	al,dh			;top 2 bits of each plane
		rol	al,1
		rol	al,1
		and	al,3
		shl	al,1
		shl	al,1
		mov	ah,dl
		rol	ah,1
		rol	ah,1
		and	ah,3
		or	al,ah
		xlat	cs:tgT16
		stosb
		shl	dl,1
		shl	dl,1
		shl	dh,1
		shl	dh,1
		loop	crPlPix
		pop	cx
		loop	crPlLp
crX:
		pop	es
		ret
tgConvRow	endp


		subttl	GrabBmp
		page

;GrabBmp - full-screen grab of a graphics mode.
;  ENTRY es:di -> GrabRequest, ds = cs. EXIT ax = record size, carry set if
;  the file could not be written. Called from GetBlock, which WINOLDAP
;  calls with DOS idle (it writes its own grab file next).
GrabBmp 	proc	near
		assume	ds:_TEXT
		cld
		call	tgBmpPath
		mov	ax,es:[di]
		or	ax,es:[di][2]
		jnz	gbGo
		mov	ax,[tgLen]		;size query
		add	ax,4 + 1
		clc
		ret
gbGo:
		push	es
		push	di
		call	tgBuildMap
		mov	[tgSrc],'KT'
		or	ax,ax
		jz	gbKnown
		mov	[tgSrc],'AT'
gbKnown:
		call	tgTables
		mov	ax,[IC.icPixelsX]
		mov	word ptr [tgW],ax
		shr	ax,1
		mov	[tgOutW],ax
		mov	ax,[IC.icPixelsY]
		mov	word ptr [tgH],ax
		mul	[tgOutW]
		mov	word ptr [tgISize],ax
		mov	word ptr [tgISize][2],dx
		add	ax,TGHDRLEN
		adc	dx,0
		mov	word ptr [tgFSize],ax
		mov	word ptr [tgFSize][2],dx
		mov	dx,offset tgPath	;create the file
		xor	cx,cx
		mov	ah,3Ch
		int	21h
		jnc	gbOpen
		jmp	gbFail0
gbOpen:
		mov	[tgHandle],ax
		mov	bx,ax
		mov	dx,offset tgHdr
		mov	cx,TGHDRLEN
		mov	ah,40h
		int	21h
		jc	gbFail
		mov	ax,[IC.icPixelsY]	;rows bottom-up
		mov	[tgY],ax
gbRowLp:
		dec	[tgY]
		mov	bx,[tgY]
		push	ds
		lds	si,[IC.iclpScr]
		assume	ds:nothing
		xor	si,si
		call	ComputeYBufPos
		call	tgConvRow
		pop	ds
		assume	ds:_TEXT
		mov	bx,[tgHandle]
		mov	dx,offset tgRow
		mov	cx,[tgOutW]
		mov	ah,40h
		int	21h
		jc	gbFail
		cmp	ax,cx
		jne	gbFail
		cmp	[tgY],0
		jne	gbRowLp
		mov	bx,[tgHandle]
		mov	ah,3Eh
		int	21h
		pop	di			;the text record for WINOLDAP
		pop	es
		les	di,es:[di][grlpData]
		mov	ax,GT_TEXT
		stosw
		mov	ax,[tgLen]
		add	ax,4 + 1
		stosw
		mov	si,offset tgPre
		mov	cx,[tgLen]
		sub	cx,2
		rep	movsb
		mov	ax,0A0Dh
		stosw
		xor	al,al
		stosb
		mov	ax,[tgLen]
		add	ax,4 + 1
		clc
		ret
gbFail:
		mov	bx,[tgHandle]
		mov	ah,3Eh
		int	21h
gbFail0:
		pop	di
		pop	es
		stc
		ret
GrabBmp 	endp


_TEXT		ends
		end
