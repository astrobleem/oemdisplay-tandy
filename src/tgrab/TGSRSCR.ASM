		page	,132
		%out	TgSrScr
		name	TGSRSCR
		title	TANDYGR Save/RestoreScreen, SetSwapDrive (MIT)

; TANDYGR.GR2: saving and restoring a DOS program's screen when the user
; switches away from it and back (grabber functions 6 and 7).
;
; WINOLDAP gives the grabber one save area per DOS session, sized once by
; InquireSave before the program starts and kept for the whole session.
; Text screens (at most 4 KB) are kept in that area. Graphics screens - 16 KB
; in modes 4, 5, 6, 8 and 32 KB in modes 9, 0Ah - go to a temporary file in
; WINOLDAP's swap directory (SetSwapDrive), else %TEMP%, else the root of
; the current drive, and the file is deleted when the screen is restored.
; So a session costs MAX_CDSIZE + 4 KB of DOS memory instead of 16 or 32 KB.
; The save area's 4 KB double as the file buffer: DOS never transfers
; directly to or from video memory.
;
; With the screen the area keeps the palette shadow (TGTANDY.ASM); after the
; BIOS mode set the palette registers are loaded from it again.
;
; The heap's last paragraph. KERNEL puts the global heap's end sentinel on
; the even paragraph below the end of its DOS memory ((end - 1) AND 0FFFEh).
; When that end is odd - as with RESERVE, whose block header is at 97FFh -
; the sentinel is the heap's very last paragraph, and WINOLDAP does not
; carry that paragraph between Windows and the DOS program: the program
; (COMMAND.COM's transient part lives there) overwrites it, and the next
; walk of the heap after the session loops for ever. So the grabber keeps
; that one paragraph for both sides, from the layout it finds:
;   EnableSave (program starts): the DOS block holding the grabber is
;     followed by the free block the program will get; its end is the
;     heap's end. Odd end and a 'Z' arena header there: keep Windows'
;     16 bytes.
;   SaveScreen (switching to Windows): keep the program's 16 bytes, put
;     Windows' back.   RestoreScreen (back to the program): the reverse.
;   DisableSave (program ended): put Windows' back.
; Even end, or anything unexpected: nothing is touched. Nothing is
; allocated and nothing stays behind when Windows exits.
;
; 8086 instructions only. MASM 5.10.

_TEXT		segment byte	public	'CODE'
		assume	cs:_TEXT

NO_STDGRABENTRY =	1

		.xlist
		include dc.inc
		include ic.inc
		include cgaherc.inc
		include abs0.inc
		include grabber.inc
		.list

		extrn	MAX_TOTTEXT:abs

		extrn	DC:byte
		extrn	IC:byte
		extrn	fBadMode:byte
		extrn	tgPalR:byte
		extrn	tgPalKnown:byte

		extrn	OemBeep:near
		extrn	GetMode:near
		extrn	SetMode:near

		public	SaveScreen
		public	RestoreScreen
		public	SetSwapDrive
		public	EnableSave
		public	DisableSave
		public	tgTempDir
		public	tgHeapP

FALSE		=	0
TRUE		=	1

TG_PALLEN	=	18			;tgPalR, tgPalBdr, tgPalKnown
TG_PATHLEN	=	80
TG_BUF		=	04*1024

SV_DC		=	0
SV_VBD		=	SV_DC + (SIZE DeviceContext) + (SIZE InfoContext)
SV_PAL		=	SV_VBD + (SIZE VideoBiosData)
SV_FILE 	=	SV_PAL + TG_PALLEN
SV_DATA 	=	SV_FILE + TG_PATHLEN
SV_SIZE 	=	SV_DATA + TG_BUF

tgSwapDir	db	64 dup (0)		;from SetSwapDrive, ends in '\'
tgTempKey	db	'TEMP='
tgVidLen	dw	0
tgHandle	dw	0
tgHeapP 	dw	0			;heap's last paragraph, 0: none
tgSwitched	db	FALSE			;TRUE between SaveScreen and
						;  RestoreScreen
tgWinPara	db	16 dup (0)		;Windows' 16 bytes there
tgAppPara	db	16 dup (0)		;the DOS program's
tgArea		dw	0			;save area offset
tgAreaSeg	dw	0			;  and segment


		subttl	SaveScreen
		page

;SaveScreen - ax = save area size, es:di -> save area, ds = cs.
;  Carry set (and a beep) if the screen cannot be kept: WINOLDAP then does
;  not switch away.
SaveScreen	proc	far
		assume	ds:_TEXT
		cld
		cmp	ax,SV_SIZE
		jb	ssErr
		call	GetMode
		cmp	[fBadMode],TRUE
		je	ssErr
		mov	[tgArea],di
		mov	si,offset DC		;contexts
		mov	cx,SV_VBD
		rep	movsb
		push	ds
		xor	ax,ax
		mov	ds,ax
		assume	ds:Abs0
		mov	si,offset CrtMode	;BIOS video data
		mov	cx,SIZE VideoBiosData
		rep	movsb
		pop	ds
		assume	ds:_TEXT
		mov	si,offset tgPalR	;palette shadow
		mov	cx,TG_PALLEN
		rep	movsb
		mov	di,[tgArea]
		mov	byte ptr es:[di][SV_FILE],0
		test	[IC.icScrType],ST_GRPH
		jnz	ssGrph
		mov	cx,[IC.icScrLen]	;text: into the area
		cmp	cx,TG_BUF
		ja	ssErr
		add	di,SV_DATA
		push	ds
		lds	si,[IC.iclpScr]
		assume	ds:nothing
		shr	cx,1
		rep	movsw
		rcl	cx,1
		rep	movsb
		pop	ds
		assume	ds:_TEXT
		call	tgParaToWin
		clc
		ret
ssGrph:
		call	tgSaveFile
		jc	ssErr
		call	tgParaToWin
		clc
		ret
ssErr:
		call	OemBeep
		stc
		ret
SaveScreen	endp


;tgSaveFile - graphics screen (B800:0, IC.icScrLen bytes) to a new
;  temporary file; its name stays in the save area. es:di -> area.
tgSaveFile	proc	near
		assume	ds:_TEXT
		push	di
		add	di,SV_FILE
		mov	cx,TG_PATHLEN - 14	;room for the name DOS adds
		call	tgTempDir
		pop	di
		jnc	sfDir
		jmp	sfX
sfDir:
		mov	ax,[IC.icScrLen]
		mov	[tgVidLen],ax
		push	ds
		push	es
		pop	ds
		assume	ds:nothing
		lea	dx,[di][SV_FILE]
		xor	cx,cx
		mov	ah,5Ah			;create a unique file
		int	21h
		pop	ds
		assume	ds:_TEXT
		jc	sfFail0
		mov	[tgHandle],ax
		xor	si,si			;video offset
sfLp:
		mov	cx,[tgVidLen]
		sub	cx,si
		jz	sfDone
		cmp	cx,TG_BUF
		jbe	sfPart
		mov	cx,TG_BUF
sfPart:
		push	cx
		push	di
		push	ds
		add	di,SV_DATA
		mov	ax,0B800h
		mov	ds,ax
		assume	ds:nothing
		shr	cx,1
		rep	movsw			;si advances
		rcl	cx,1
		rep	movsb
		pop	ds
		assume	ds:_TEXT
		pop	di
		pop	cx
		push	ds
		push	es
		pop	ds
		assume	ds:nothing
		lea	dx,[di][SV_DATA]
		mov	bx,cs:[tgHandle]
		mov	ah,40h
		int	21h
		pop	ds
		assume	ds:_TEXT
		jc	sfFail
		cmp	ax,cx
		jne	sfFail
		jmp	sfLp
sfDone:
		mov	bx,[tgHandle]
		mov	ah,3Eh
		int	21h
		jc	sfFail1
		clc
		ret
sfFail:
		mov	bx,[tgHandle]
		mov	ah,3Eh
		int	21h
sfFail1:
		push	ds
		push	es
		pop	ds
		assume	ds:nothing
		lea	dx,[di][SV_FILE]
		mov	ah,41h
		int	21h
		pop	ds
		assume	ds:_TEXT
sfFail0:
		mov	byte ptr es:[di][SV_FILE],0
		stc
sfX:
		ret
tgSaveFile	endp


		subttl	RestoreScreen
		page

;RestoreScreen - es:di -> save area, ds = cs. Always succeeds: if the file
;  has gone, the mode and palette are restored and the screen stays empty.
RestoreScreen	proc	far
		assume	ds:_TEXT
		cld
		mov	[tgArea],di
		mov	[tgAreaSeg],es
		push	ds
		push	es			;contexts back
		pop	ds
		assume	ds:nothing
		push	cs
		pop	es
		mov	si,di
		mov	di,offset DC
		mov	cx,SV_VBD
		rep	movsb
		pop	ds
		assume	ds:_TEXT
		call	SetMode 		;BIOS mode set, 3D8h, 3D9h, CRTC
		mov	si,[tgArea]
		add	si,SV_VBD
		push	ds
		mov	ds,[tgAreaSeg]
		assume	ds:nothing
		xor	ax,ax
		mov	es,ax
		assume	es:Abs0
		mov	di,offset CrtMode	;BIOS video data back
		mov	cx,SIZE VideoBiosData
		rep	movsb
		assume	es:nothing
		push	cs
		pop	es
		mov	di,offset tgPalR	;palette shadow back
		mov	cx,TG_PALLEN
		rep	movsb
		pop	ds
		assume	ds:_TEXT
		mov	es,[tgAreaSeg]
		mov	di,[tgArea]
		test	[IC.icScrType],ST_GRPH
		jnz	rsGrph
		mov	cx,[IC.icScrLen]	;text from the area
		cmp	cx,TG_BUF
		ja	rsScreenDone
		push	ds
		push	es
		push	es
		pop	ds
		assume	ds:nothing
		lea	si,[di][SV_DATA]
		les	di,cs:[IC.iclpScr]
		shr	cx,1
		rep	movsw
		rcl	cx,1
		rep	movsb
		pop	es
		pop	ds
		assume	ds:_TEXT
		jmp	short rsScreenDone
rsGrph:
		call	tgRestFile
rsScreenDone:
		loop	$			;let the screen settle
		loop	$
		mov	al,[DC.dcModeCtl]
		and	al,NOT MC_ENABLE_BLINK
		mov	dx,MODE_CONTROL
		out	dx,al
		call	tgLoadPalette
		call	tgParaToApp
		clc
		ret
RestoreScreen	endp


;tgRestFile - read the graphics file back into B800:0 and delete it.
;  es:di -> area.
tgRestFile	proc	near
		assume	ds:_TEXT
		cmp	byte ptr es:[di][SV_FILE],0
		je	rfX
		mov	ax,[IC.icScrLen]
		mov	[tgVidLen],ax
		push	ds
		push	es
		pop	ds
		assume	ds:nothing
		lea	dx,[di][SV_FILE]
		mov	ax,3D00h		;open for reading
		int	21h
		pop	ds
		assume	ds:_TEXT
		jc	rfDel
		mov	[tgHandle],ax
		xor	bx,bx			;video offset
rfLp:
		mov	cx,[tgVidLen]
		sub	cx,bx
		jz	rfClose
		cmp	cx,TG_BUF
		jbe	rfPart
		mov	cx,TG_BUF
rfPart:
		push	bx
		push	ds
		push	es
		pop	ds
		assume	ds:nothing
		lea	dx,[di][SV_DATA]
		mov	bx,cs:[tgHandle]
		mov	ah,3Fh
		int	21h
		pop	ds
		assume	ds:_TEXT
		pop	bx
		jc	rfClose
		or	ax,ax
		jz	rfClose
		mov	cx,ax
		push	di
		push	ds
		push	es
		push	es
		pop	ds
		assume	ds:nothing
		lea	si,[di][SV_DATA]
		mov	di,0B800h
		mov	es,di
		mov	di,bx
		add	bx,cx
		shr	cx,1
		rep	movsw
		rcl	cx,1
		rep	movsb
		pop	es
		pop	ds
		assume	ds:_TEXT
		pop	di
		jmp	rfLp
rfClose:
		mov	bx,[tgHandle]
		mov	ah,3Eh
		int	21h
rfDel:
		push	ds
		push	es
		pop	ds
		assume	ds:nothing
		lea	dx,[di][SV_FILE]
		mov	ah,41h
		int	21h
		pop	ds
		assume	ds:_TEXT
		mov	byte ptr es:[di][SV_FILE],0
rfX:
		ret
tgRestFile	endp


;tgLoadPalette - palette registers 10h-1Fh and the border from the shadow,
;  in vertical retrace, as the BIOS does. Only when the shadow follows the
;  BIOS; otherwise the BIOS mode set's palette stays.
tgLoadPalette	proc	near
		assume	ds:_TEXT
		cmp	[tgPalKnown],TRUE
		jne	lpX
		mov	dx,3DAh
lpW1:
		in	al,dx
		test	al,8
		jnz	lpW1
lpW2:
		in	al,dx
		test	al,8
		jz	lpW2
		cli
		xor	bx,bx
lpLp:
		mov	al,bl
		add	al,10h
		out	dx,al
		mov	al,[tgPalR][bx]
		add	dx,4
		out	dx,al
		sub	dx,4
		inc	bx
		cmp	bx,16
		jb	lpLp
		mov	al,2			;border
		out	dx,al
		mov	al,[tgPalR][16]
		add	dx,4
		out	dx,al
		sub	dx,4
		xor	al,al
		out	dx,al
		sti
lpX:
		ret
tgLoadPalette	endp



		subttl	The heap's last paragraph
		page

;EnableSave - WINOLDAP starts the program or switches back to it (ds = cs).
EnableSave	proc	near
		assume	ds:_TEXT
		cmp	[tgSwitched],TRUE
		je	esX			;switching back: RestoreScreen
		call	tgFindP
		mov	[tgHeapP],ax
		or	ax,ax
		jz	esX
		push	ds
		push	es
		push	si
		push	di
		push	cx
		mov	ds,ax			;Windows' 16 bytes
		assume	ds:nothing
		xor	si,si
		push	cs
		pop	es
		mov	di,offset tgWinPara
		mov	cx,8
		cld
		rep	movsw
		pop	cx
		pop	di
		pop	si
		pop	es
		pop	ds
		assume	ds:_TEXT
esX:
		ret
EnableSave	endp

;DisableSave - after switching to Windows (nothing to do: SaveScreen did
;  it) or after the program ended: Windows' 16 bytes back.
DisableSave	proc	near
		assume	ds:_TEXT
		cmp	[tgSwitched],TRUE
		je	dsX
		cmp	[tgHeapP],0
		je	dsX
		push	si
		mov	si,offset tgWinPara
		call	tgPut
		pop	si
		mov	[tgHeapP],0
dsX:
		ret
DisableSave	endp

;tgParaToWin - SaveScreen succeeded: keep the program's paragraph, put
;  Windows' back.
tgParaToWin	proc	near
		assume	ds:_TEXT
		mov	[tgSwitched],TRUE
		cmp	[tgHeapP],0
		je	pwX
		push	si
		push	di
		mov	di,offset tgAppPara
		call	tgGet
		mov	si,offset tgWinPara
		call	tgPut
		pop	di
		pop	si
pwX:
		ret
tgParaToWin	endp

;tgParaToApp - RestoreScreen: keep Windows' paragraph as it is now (its
;  heap has changed meanwhile), put the program's back.
tgParaToApp	proc	near
		assume	ds:_TEXT
		mov	[tgSwitched],FALSE
		cmp	[tgHeapP],0
		je	paX
		push	si
		push	di
		mov	di,offset tgWinPara
		call	tgGet
		mov	si,offset tgAppPara
		call	tgPut
		pop	di
		pop	si
paX:
		ret
tgParaToApp	endp

;tgGet - cs:di <- the 16 bytes at tgHeapP:0
tgGet		proc	near
		push	ds
		push	es
		push	si
		push	cx
		mov	ds,cs:[tgHeapP]
		assume	ds:nothing
		push	cs
		pop	es
		xor	si,si
		mov	cx,8
		cld
		rep	movsw
		pop	cx
		pop	si
		pop	es
		pop	ds
		assume	ds:_TEXT
		ret
tgGet		endp

;tgPut - 16 bytes at tgHeapP:0 <- cs:si
tgPut		proc	near
		push	es
		push	di
		push	cx
		mov	es,cs:[tgHeapP]
		xor	di,di
		mov	cx,8
		cld
		rep	movsw
		pop	cx
		pop	di
		pop	es
		ret
tgPut		endp

;tgFindP - ax = the heap's last paragraph if the layout needs it, else 0.
;  Walks the DOS memory chain read-only.
tgFindP 	proc	near
		assume	ds:_TEXT
		push	bx
		push	cx
		push	dx
		push	es
		mov	ah,52h
		int	21h
		mov	ax,es:[bx-2]		;first memory block
		mov	dx,cs
fpWalk:
		mov	es,ax
		mov	cl,es:[0]
		cmp	cl,'M'
		je	fpSig
		cmp	cl,'Z'
		jne	fpNone
fpSig:
		mov	bx,ax
		add	bx,es:[3]		;bx = last paragraph of the block
		jc	fpNone
		cmp	dx,ax
		jbe	fpNext
		cmp	dx,bx
		jbe	fpOurs
fpNext:
		cmp	cl,'Z'
		je	fpNone
		mov	ax,bx
		inc	ax
		jmp	fpWalk
fpOurs:
		cmp	cl,'Z'			;the block after it: free
		je	fpNone
		inc	bx
		mov	es,bx
		cmp	byte ptr es:[0],'M'
		je	fpFree
		cmp	byte ptr es:[0],'Z'
		jne	fpNone
fpFree:
		cmp	word ptr es:[1],0
		jne	fpNone
		mov	ax,bx
		add	ax,es:[3]
		jc	fpNone
		inc	ax			;ax = end of the heap
		test	al,1
		jz	fpNone
		dec	ax			;odd end: the last paragraph
		mov	es,ax
		cmp	byte ptr es:[0],'Z'	;KERNEL's end sentinel
		je	fpX
fpNone:
		xor	ax,ax
fpX:
		pop	es
		pop	dx
		pop	cx
		pop	bx
		ret
tgFindP 	endp

		subttl	SetSwapDrive
		page

;SetSwapDrive - bl = swap drive (0FFh: none), es:di -> WINOLDAP's swap
;  file path. Keep its directory for the screen files.
SetSwapDrive	proc	near
		assume	ds:_TEXT
		cmp	bl,0FFh
		je	sdX
		push	si
		push	di
		mov	si,di			;find the last '\'
		xor	bx,bx
		xor	cx,cx
sdScan:
		mov	al,es:[si]
		or	al,al
		jz	sdEnd
		inc	si
		inc	cx
		cmp	cx,64
		jae	sdNone
		cmp	al,'\'
		jne	sdScan
		mov	bx,cx			;length up to and with '\'
		jmp	sdScan
sdEnd:
		or	bx,bx
		jz	sdNone
		cmp	bx,63
		ja	sdNone
		mov	si,di
		xor	di,di
sdCopy:
		mov	al,es:[si]
		mov	[tgSwapDir][di],al
		inc	si
		inc	di
		cmp	di,bx
		jb	sdCopy
		mov	[tgSwapDir][di],0
		jmp	short sdOk
sdNone:
		mov	[tgSwapDir],0
sdOk:
		pop	di
		pop	si
sdX:
		ret
SetSwapDrive	endp


;tgTempDir - es:di <- directory for temporary files, ending in '\', ASCIZ
;  terminated: WINOLDAP's swap directory, else %TEMP%, else the root of
;  the current drive. cx = room (bytes). Returns di -> the terminating 0,
;  carry set if it does not fit. ds = cs.
tgTempDir	proc	near
		assume	ds:_TEXT
		push	ax
		push	bx
		push	si
		push	dx
		mov	dx,di
		add	dx,cx			;limit
		dec	dx
		cmp	[tgSwapDir],0
		je	tdTemp
		mov	si,offset tgSwapDir
tdSwap:
		lodsb
		or	al,al
		jz	tdFin
		cmp	di,dx
		jae	tdFail
		stosb
		jmp	tdSwap
tdTemp:
		push	ds
		push	es
		mov	ah,62h			;current PSP's environment
		int	21h
		mov	ds,bx
		assume	ds:nothing
		mov	bx,ds:[2Ch]
		pop	es
		pop	ds
		assume	ds:_TEXT
		or	bx,bx
		jz	tdRoot
		push	ds
		mov	ds,bx
		assume	ds:nothing
		xor	si,si
tdVar:
		cmp	byte ptr [si],0
		je	tdNoVar
		push	si
		push	di
		mov	di,offset tgTempKey
		mov	cx,5
tdCmp:
		mov	al,[si]
		cmp	al,cs:[di]
		jne	tdNe
		inc	si
		inc	di
		loop	tdCmp
tdNe:
		pop	di
		pop	ax			;start of this variable
		jcxz	tdFound
		mov	si,ax
tdSkip:
		lodsb
		or	al,al
		jnz	tdSkip
		jmp	tdVar
tdFound:
		mov	cx,di			;value: copy it
tdVal:
		lodsb
		or	al,al
		jz	tdValEnd
		cmp	di,dx
		jae	tdFailEnv
		stosb
		jmp	tdVal
tdValEnd:
		pop	ds
		assume	ds:_TEXT
		cmp	di,cx
		je	tdRoot			;TEMP= with nothing
		jmp	short tdFin
tdNoVar:
		pop	ds
		assume	ds:_TEXT
tdRoot:
		mov	ah,19h			;current drive
		int	21h
		add	al,'A'
		stosb
		mov	al,':'
		stosb
tdFin:
		cmp	byte ptr es:[di-1],'\'
		je	tdTerm
		cmp	di,dx
		jae	tdFail
		mov	al,'\'
		stosb
tdTerm:
		mov	byte ptr es:[di],0
		clc
		jmp	short tdX
tdFailEnv:
		pop	ds
tdFail:
		stc
tdX:
		pop	dx
		pop	si
		pop	bx
		pop	ax
		ret
tgTempDir	endp


_TEXT		ends
		end
