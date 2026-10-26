		page	,132
		%out	TgTandy
		name	TGTANDY
		title	TANDYGR palette tracking and colour mapping (MIT)

; TANDYGR.GR2 (Windows 3.0 real-mode grabber for the Tandy 1000): what is
; on the screen in colours, and where those colours come from.
;
; The Tandy 1000 video array (port 3DAh index, 3DEh data) is write-only:
; palette registers 10h-1Fh cannot be read back, and the Tandy 1000 HX BIOS
; (v02.00.00, INT 10h AH=00h/0Bh/10h) programs them without keeping a copy
; in RAM. So the grabber keeps its own copy ("shadow") of what the BIOS was
; asked to load: it hooks INT 10h inside a DOS session and repeats, on the
; shadow, exactly what that BIOS does for AH=00h (mode set: identity
; palette, 640x200x4 = 0,3,5,15, monochrome table when 0:4B4h = FFh),
; AH=0Bh (background / palette select) and AH=10h (AL=0, 1, 2).
; A program that writes the registers with OUT instructions instead cannot
; be observed (an 8088 cannot trap port writes); tgPalKnown then still
; describes the last BIOS state, see docs/GRABBER.MD.
;
; The INT 10h hook is installed only in a DOS session's own interrupt
; table: InitScreen hooks only when INT 21h belongs to the caller
; (WINOLDAP's DOS-side code), which is true when WINOLDAP starts or ends
; the program and false when it switches back to Windows. WINOLDAP saves
; the session's whole vector table when it switches away and puts back
; Windows' table, so the hook never runs in Windows.
;
; 8086 instructions only. MASM 5.10.

_TEXT		segment byte	public	'CODE'
		assume	cs:_TEXT

		.xlist
		include dc.inc
		include ic.inc
		.list

		extrn	DC:byte
		extrn	IC:byte

		public	InitScreen
		public	tgPalR
		public	tgPalBdr
		public	tgPalKnown
		public	tgMap
		public	tgBuildMap
		public	tgPalDefault
		public	tgSwap

FALSE		=	0
TRUE		=	1

tgOld10 	dd	0			;previous INT 10h
t10AX		dw	0			;INT 10h inputs of the call
t10BX		dw	0
t10DX		dw	0
t10ES		dw	0
tgPalR		db	16 dup (0)		;palette registers 10h-1Fh
tgPalBdr	db	0			;border register
tgPalKnown	db	FALSE			;TRUE: shadow follows the BIOS
tgMap		db	16 dup (0)		;pixel value -> Windows index

;Tandy 1000 HX BIOS monochrome palette (loaded when 0:4B4h = 0FFh)
tgMonoTbl	db	000h,007h,007h,007h,007h,007h,007h,007h
		db	008h,00Fh,00Fh,00Fh,00Fh,00Fh,00Fh,00Fh


		subttl	InitScreen
		page

;InitScreen - text mode 3 for the DOS program (grabber function 8).
;  WINOLDAP calls this when it starts a program, when the program ends and
;  when it switches back to Windows. Only when INT 21h is WINOLDAP's own
;  (the caller's code segment) is this the session's vector table; then
;  INT 10h is hooked there before the mode is set, so the shadow starts
;  from a BIOS mode set.
InitScreen	proc	far
		push	bp
		mov	bp,sp
		push	ax
		push	bx
		push	dx
		push	es
		xor	ax,ax
		mov	es,ax
		mov	dx,[bp+4]		;caller's code segment
		cmp	dx,es:[21h*4+2]
		jne	isNoHook
		cli
		mov	ax,es:[10h*4]
		mov	bx,es:[10h*4+2]
		cmp	ax,offset tgInt10
		jne	isHook
		mov	dx,cs
		cmp	bx,dx
		je	isHooked
isHook:
		mov	word ptr cs:[tgOld10],ax
		mov	word ptr cs:[tgOld10][2],bx
		mov	word ptr es:[10h*4],offset tgInt10
		mov	es:[10h*4+2],cs
		mov	cs:[tgPalKnown],FALSE
isHooked:
		sti
isNoHook:
		mov	ax,00003h
		int	010h
		pop	es
		pop	dx
		pop	bx
		pop	ax
		pop	bp
		ret
InitScreen	endp


		subttl	tgInt10
		page

;tgInt10 - INT 10h hook of a DOS session: AH=00h, 0Bh and 10h go to the
;  BIOS first, then the shadow repeats what the BIOS did. Everything else
;  goes straight on. Flags and registers are the BIOS's.
tgInt10 	proc	far
		cmp	ah,000h
		je	t10Go
		cmp	ah,00Bh
		je	t10Go
		cmp	ah,010h
		je	t10Go
		jmp	dword ptr cs:[tgOld10]
t10Go:
		mov	cs:[t10AX],ax
		mov	cs:[t10BX],bx
		mov	cs:[t10DX],dx
		mov	cs:[t10ES],es
		pushf
		call	dword ptr cs:[tgOld10]
		pushf
		push	ax
		push	bx
		push	cx
		push	dx
		push	si
		push	di
		push	ds
		push	es
		push	cs
		pop	ds
		assume	ds:_TEXT
		call	tgTrack
		pop	es
		pop	ds
		assume	ds:nothing
		pop	di
		pop	si
		pop	dx
		pop	cx
		pop	bx
		pop	ax
		popf
		ret	2
tgInt10 	endp


;tgTrack - repeat the BIOS's palette work on the shadow (ds = cs).
tgTrack 	proc	near
		assume	ds:_TEXT
		xor	ax,ax
		mov	es,ax
		mov	al,es:[449h]		;mode after the call
		mov	cx,[t10AX]
		cmp	ch,000h
		jne	trNotMode
		jmp	tgPalDefault
trNotMode:
		cmp	al,7			;BIOS: no palette work in mode 7
		je	trX
		test	byte ptr es:[4B5h],10h	;  or with 0:4B5h bit 4
		jnz	trX
		mov	bx,[t10BX]
		cmp	ch,00Bh
		jne	trF10
		or	bh,bh
		jnz	trSelect
		cmp	al,8			;background: register 0 in 8-0Ah
		jb	trBorder
		mov	ah,bl
		and	ah,0Fh
		mov	[tgPalR],ah
trBorder:
		cmp	al,6
		je	trX
		mov	[tgPalBdr],bl
trX:
		ret
trSelect:
		cmp	al,0Ah			;palette select: 640x200x4 only
		jne	trX
		mov	word ptr [tgPalR][1],0503h
		mov	[tgPalR][3],0Fh
		or	bl,bl
		jnz	trX
		mov	word ptr [tgPalR][1],0402h
		mov	[tgPalR][3],06h
		ret
trF10:
		cmp	cl,1			;AH=10h AL=1: border
		jne	trF10a
		mov	[tgPalBdr],bh
		ret
trF10a:
		cmp	cl,2			;AL=2: 16 registers + border
		je	trAll
		or	cl,cl			;AL=0: one register
		jnz	trX
		cmp	al,6			;BIOS register remapping
		jne	trNot6
		cmp	bl,1
		jne	trSet
		mov	bl,0Fh
		jmp	short trSet
trNot6:
		ja	trSet
		cmp	al,4
		jb	trSet
		test	byte ptr es:[466h],20h
		mov	ah,0Ah
		jz	trPal0
		inc	ah			;0Bh, 0Dh, 0Fh
trPal0:
		cmp	bl,1
		je	trRemap
		add	ah,2
		cmp	bl,2
		je	trRemap
		add	ah,2
		cmp	bl,3
		jne	trSet
trRemap:
		mov	bl,ah
trSet:
		cmp	bl,10h
		jae	trX
		mov	al,bh
		and	al,0Fh
		xor	bh,bh
		mov	[tgPalR][bx],al
		ret
trAll:
		mov	si,[t10DX]
		mov	es,[t10ES]
		xor	bx,bx
trAllLp:
		mov	al,es:[si][bx]
		and	al,0Fh
		mov	[tgPalR][bx],al
		inc	bx
		cmp	bx,16
		jb	trAllLp
		mov	al,es:[si][bx]
		mov	[tgPalBdr],al
		ret
tgTrack 	endp


;tgPalDefault - the palette the BIOS loads for mode AL (ds = cs).
;  Sets tgPalKnown only when this BIOS really loads one.
tgPalDefault	proc	near
		assume	ds:_TEXT
		push	ax
		push	bx
		push	es
		xor	bx,bx
		mov	es,bx
pdLp:
		mov	[tgPalR][bx],bl
		inc	bx
		cmp	bx,16
		jb	pdLp
		mov	[tgPalBdr],0
		mov	[tgPalKnown],FALSE
		cmp	al,7
		je	pdX
		test	byte ptr es:[4B5h],10h
		jnz	pdX
		mov	[tgPalKnown],TRUE
		cmp	al,0Ah
		jne	pdMono
		mov	word ptr [tgPalR][1],0503h
		mov	[tgPalR][3],0Fh
pdMono:
		cmp	byte ptr es:[4B4h],0FFh
		jne	pdX
		xor	bx,bx
pdMonoLp:
		mov	al,[tgMonoTbl][bx]
		mov	[tgPalR][bx],al
		inc	bx
		cmp	bx,16
		jb	pdMonoLp
pdX:
		pop	es
		pop	bx
		pop	ax
		ret
tgPalDefault	endp


		subttl	tgBuildMap
		page

;tgBuildMap - tgMap[p] = Windows device index of the colour a pixel value
;  p shows in the current mode (DC.dcScrMode). ds = cs.
;    8, 9, 0Ah  register[p]
;    4, 5       register[CGA colour code], the code from 0:466h (colour
;               select) and the 3D8h B/W bit (0:465h bit 2), as CGA
;    6          0 -> register[0], 1 -> register[0:466h AND 0Fh]
;  If the shadow does not follow the BIOS (no INT 10h mode set seen), the
;  BIOS default palette of the mode is assumed; AX = 1 then, else 0.
tgBuildMap	proc	near
		assume	ds:_TEXT
		push	bx
		push	cx
		push	dx
		push	si
		push	es
		xor	ax,ax
		mov	es,ax
		xor	dx,dx			;dx = 1 if assumed
		cmp	[tgPalKnown],TRUE
		je	bmKnown
		mov	al,[DC.dcScrMode]
		call	tgPalDefault
		mov	[tgPalKnown],FALSE
		inc	dx
bmKnown:
		mov	al,[DC.dcScrMode]
		cmp	al,4
		je	bmCga
		cmp	al,5
		je	bmCga
		cmp	al,6
		je	bmHi
		xor	bx,bx			;8, 9, 0Ah: identity codes
bmIdLp:
		mov	al,[tgPalR][bx]
		call	tgSwap
		mov	[tgMap][bx],al
		inc	bx
		cmp	bx,16
		jb	bmIdLp
		jmp	short bmX
bmHi:
		mov	al,[tgPalR]
		call	tgSwap
		mov	[tgMap],al
		mov	bl,es:[466h]
		and	bx,0Fh
		mov	al,[tgPalR][bx]
		call	tgSwap
		mov	[tgMap][1],al
		jmp	short bmX
bmCga:
		mov	cl,es:[466h]		;colour select
		mov	bl,cl
		and	bx,0Fh			;0: background colour
		mov	al,[tgPalR][bx]
		call	tgSwap
		mov	[tgMap],al
		xor	ch,ch
		test	cl,10h			;intensity of colours 1-3
		jz	bmNoInt
		mov	ch,8
bmNoInt:
		mov	si,offset tgCga0	;green, red, brown
		test	byte ptr es:[465h],04h
		jz	bmNotBw
		mov	si,offset tgCgaBw	;cyan, red, white
		jmp	short bmCodes
bmNotBw:
		test	cl,20h
		jz	bmCodes
		mov	si,offset tgCga1	;cyan, magenta, white
bmCodes:
		mov	bx,1
bmCgaLp:
		mov	al,[si][bx-1]
		or	al,ch
		push	bx
		mov	bl,al
		xor	bh,bh
		mov	al,[tgPalR][bx]
		pop	bx
		call	tgSwap
		mov	[tgMap][bx],al
		inc	bx
		cmp	bx,4
		jb	bmCgaLp
bmX:
		mov	ax,dx
		pop	es
		pop	si
		pop	dx
		pop	cx
		pop	bx
		ret
tgBuildMap	endp

tgCga0		db	2,4,6
tgCga1		db	3,5,7
tgCgaBw 	db	3,4,7


;tgSwap - al = Tandy IRGB colour -> Windows device index (bits 0, 2 swapped)
tgSwap		proc	near
		push	dx
		mov	dl,al
		and	dl,0Ah
		test	al,1
		jz	swS1
		or	dl,4
swS1:
		test	al,4
		jz	swS2
		or	dl,1
swS2:
		mov	al,dl
		pop	dx
		ret
tgSwap		endp


_TEXT		ends
		end
