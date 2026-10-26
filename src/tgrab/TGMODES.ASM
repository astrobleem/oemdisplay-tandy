; TGMODES.COM - Tandy 1000 grabber test pictures in every graphics mode (MIT).
;
;   TGMODES m [p]
;     m  BIOS mode: 4, 5, 6 (CGA), 8, 9, A (Tandy)
;     p  palette: 0 = the mode's BIOS default (also when omitted)
;                 1 = a different palette loaded through the BIOS (INT 10h)
;                 2 = the same palette written with OUT instructions
;
; Sets the mode, applies the palette, draws a full-screen picture, waits for
; a key, sets mode 3 and exits. With n colours and width W, pixel (x, y):
;   x < W/16 and y < 20      : 1                (marker, top left)
;   x = W-1 or y = 199       : n-1              (right and bottom edges)
;   otherwise                : (x*n/W + (y >= 100) * n/2) mod n
; so every pixel value appears in both halves and the picture is not
; symmetric. Palette 1 (16 colours): register i = (7*i + 3) mod 16;
; 640x200x4: registers 0-3 = 1, 14, 4, 10 (AH=10h AL=2 / the same OUTs);
; 4 and 5: background 11h (blue, intense colours), palette 0, register
; 0Ah = 0Fh (AH=0Bh, AH=10h AL=0); with OUTs registers 0 = 1, 0Ah = 0Fh.
; 6: foreground 0Eh (AH=0Bh BH=0); with OUTs register 0Fh = 1.
; 8086 instructions only. MASM 5.10.

code		segment
		assume	cs:code, ds:code, es:code
		org	100h
start:		jmp	begin

usage		db	'TGMODES m [p]  (m = 4 5 6 8 9 A, p = 0 1 2)',13,10,'$'
mode		db	0
pal		db	0
ncol		dw	0			;colours
wid		dw	0			;pixels per line
bpp		db	0			;bits per pixel (2 = planar in A)
rowb		dw	0			;bytes per line
ishift		db	0			;interlace: bank = y AND imask,
imask		db	0			;  line = y SHR ishift
half		dw	0			;n/2
pal16		db	16 dup (0)		;palette 1, 16 colours
		db	0			;border
palA		db	1,14,4,10,4,5,6,7,8,9,10,11,12,13,14,15,0
row		db	320 dup (0)
rowM		db	320 dup (0)
rowU		db	320 dup (0)
rowL		db	320 dup (0)
rowE		db	320 dup (0)

begin:
		cld
		mov	si,81h
		call	skipsp
		call	hexdig
		jc	bad
		mov	[mode],al
		call	skipsp
		cmp	byte ptr [si],13
		je	args_ok
		call	hexdig
		jc	bad
		cmp	al,2
		ja	bad
		mov	[pal],al
args_ok:
		mov	al,[mode]
		mov	bx,offset mtab
mfind:
		cmp	byte ptr [bx],0FFh
		je	bad
		cmp	[bx],al
		je	mfound
		add	bx,7
		jmp	mfind
bad:
		mov	dx,offset usage
		mov	ah,9
		int	21h
		mov	ax,4C01h
		int	21h
mfound:
		mov	al,[bx+1]
		xor	ah,ah
		mov	[ncol],ax
		shr	ax,1
		mov	[half],ax
		mov	ax,[bx+2]
		mov	[wid],ax
		mov	al,[bx+4]
		mov	[bpp],al
		mov	al,[bx+5]
		mov	[ishift],al
		mov	al,[bx+6]
		mov	[imask],al
		mov	al,[bpp]		;bytes per line
		xor	ah,ah
		mul	[wid]
		mov	cl,3
		shr	ax,cl
		mov	[rowb],ax
		xor	bx,bx			;palette 1 table
p16:
		mov	al,bl
		mov	ah,7
		mul	ah
		add	al,3
		and	al,0Fh
		mov	[pal16][bx],al
		inc	bx
		cmp	bx,16
		jb	p16

		xor	ah,ah			;set the mode
		mov	al,[mode]
		int	10h
		call	setpal

		mov	bp,0			;the four kinds of line: build each
		mov	di,offset rowM		;  once (marker, upper, lower, edge)
		call	mkrow
		mov	bp,20
		mov	di,offset rowU
		call	mkrow
		mov	bp,100
		mov	di,offset rowL
		call	mkrow
		mov	bp,199
		mov	di,offset rowE
		call	mkrow
		xor	bp,bp			;bp = y
yloop:
		mov	si,offset rowM
		cmp	bp,20
		jb	ypick
		mov	si,offset rowU
		cmp	bp,100
		jb	ypick
		mov	si,offset rowL
		cmp	bp,199
		jb	ypick
		mov	si,offset rowE
ypick:
		call	putrow
		inc	bp
		cmp	bp,200
		jb	yloop

		xor	ah,ah
		int	16h
		mov	ax,0003h
		int	10h
		mov	ax,4C00h
		int	21h

;mode, colours, width, bits per pixel, interlace shift, interlace mask
mtab		db	4,4
		dw	320
		db	2,1,1
		db	5,4
		dw	320
		db	2,1,1
		db	6,2
		dw	640
		db	1,1,1
		db	8,16
		dw	160
		db	4,1,1
		db	9,16
		dw	320
		db	4,2,3
		db	0Ah,4
		dw	640
		db	2,2,3
		db	0FFh

skipsp		proc	near
ss1:		cmp	byte ptr [si],' '
		jne	ss2
		inc	si
		jmp	ss1
ss2:		ret
skipsp		endp

;al <- hex digit at [si] (si advances), carry if none
hexdig		proc	near
		mov	al,[si]
		cmp	al,'0'
		jb	hdBad
		cmp	al,'9'
		jbe	hdDec
		and	al,0DFh
		cmp	al,'A'
		jb	hdBad
		cmp	al,'F'
		ja	hdBad
		sub	al,'A' - 10
		jmp	short hdOk
hdDec:
		sub	al,'0'
hdOk:
		inc	si
		clc
		ret
hdBad:
		stc
		ret
hexdig		endp

;setpal - palette variant [pal] for [mode]
setpal		proc	near
		cmp	[pal],0
		jne	sp1
		ret
sp1:
		mov	al,[mode]
		cmp	al,6
		je	sp6
		jb	sp45
		mov	si,offset pal16		;8, 9: 16 registers + border
		cmp	al,0Ah
		jne	spAll
		mov	si,offset palA
spAll:
		cmp	[pal],2
		je	spOut
		mov	dx,si
		mov	ax,1002h
		int	10h
		ret
spOut:
		mov	dx,3DAh
spW1:		in	al,dx
		test	al,8
		jnz	spW1
spW2:		in	al,dx
		test	al,8
		jz	spW2
		cli
		xor	bx,bx
spOutLp:
		mov	al,bl
		add	al,10h
		out	dx,al
		mov	al,[si][bx]
		add	dx,4
		out	dx,al
		sub	dx,4
		inc	bx
		cmp	bx,16
		jb	spOutLp
		xor	al,al
		out	dx,al
		sti
		ret
sp45:
		cmp	[pal],2
		je	sp45Out
		mov	ah,0Bh			;background blue, intense 1-3
		mov	bx,0011h
		int	10h
		mov	ah,0Bh			;palette 0
		mov	bx,0100h
		int	10h
		mov	ax,1000h		;register 0Ah (pixel 1 of palette 0
		mov	bx,0F01h		;  after the BIOS remap) = white
		int	10h
		ret
sp45Out:
		mov	al,10h			;register 0 = blue
		mov	ah,1
		call	outreg
		mov	al,1Ah			;register 0Ah = white
		mov	ah,0Fh
		call	outreg
		ret
sp6:
		cmp	[pal],2
		je	sp6Out
		mov	ah,0Bh			;foreground yellow
		mov	bx,000Eh
		int	10h
		ret
sp6Out:
		mov	al,1Fh			;register 0Fh (the foreground) = 1
		mov	ah,1
		call	outreg
		ret
setpal		endp

;outreg - video array register al = ah, in vertical retrace
outreg		proc	near
		push	ax
		mov	dx,3DAh
or1:		in	al,dx
		test	al,8
		jnz	or1
or2:		in	al,dx
		test	al,8
		jz	or2
		pop	ax
		cli
		out	dx,al
		mov	al,ah
		add	dx,4
		out	dx,al
		sub	dx,4
		xor	al,al
		out	dx,al
		sti
		ret
outreg		endp

;value - al <- pixel value at (si = x, bp = y)
value		proc	near
		mov	ax,[wid]
		mov	cl,4
		shr	ax,cl			;W/16
		cmp	si,ax
		jae	vNotMark
		cmp	bp,20
		jae	vNotMark
		mov	al,1
		ret
vNotMark:
		mov	ax,[wid]
		dec	ax
		cmp	si,ax
		je	vEdge
		cmp	bp,199
		jne	vBars
vEdge:
		mov	ax,[ncol]
		dec	al
		ret
vBars:
		mov	ax,si
		mul	[ncol]
		div	[wid]			;ax = x*n/W
		cmp	bp,100
		jb	vNoHalf
		add	ax,[half]
vNoHalf:
		mov	cx,[ncol]
		dec	cx
		and	ax,cx			;n is a power of 2
		ret
value		endp

;mkrow - packed line bp into row[], then copied to di
mkrow		proc	near
		push	di
		push	cs
		pop	es
		mov	di,offset row
		mov	cx,[rowb]
		xor	al,al
		rep	stosb
		xor	si,si			;si = x
mrLp:
		call	value
		call	pack
		inc	si
		cmp	si,[wid]
		jb	mrLp
		pop	di
		mov	si,offset row
		mov	cx,[rowb]
		rep	movsb
		ret
mkrow		endp

;pack - put pixel value al at x = si into row[]
pack		proc	near
		mov	dl,al
		cmp	[mode],0Ah
		je	pkPlanar
		mov	al,[bpp]
		cmp	al,4
		je	pk4
		cmp	al,2
		je	pk2
		mov	bx,si			;1 bit
		mov	cl,3
		shr	bx,cl
		mov	cx,si
		and	cl,7
		mov	al,80h
		shr	al,cl
		test	dl,1
		jz	pkX
		or	[row][bx],al
pkX:
		ret
pk4:
		mov	bx,si
		shr	bx,1
		test	si,1
		jnz	pk4Lo
		mov	cl,4
		shl	dl,cl
pk4Lo:
		or	[row][bx],dl
		ret
pk2:
		mov	bx,si
		shr	bx,1
		shr	bx,1
		mov	cx,si
		and	cx,3
		neg	cx
		add	cx,3
		shl	cx,1			;shift = 2*(3 - x mod 4)
		shl	dl,cl
		or	[row][bx],dl
		ret
pkPlanar:
		mov	bx,si			;byte pair x/8
		mov	cl,3
		shr	bx,cl
		shl	bx,1
		mov	cx,si
		and	cl,7
		mov	al,80h
		shr	al,cl
		test	dl,1
		jz	pkP1
		or	[row][bx],al
pkP1:
		test	dl,2
		jz	pkP2
		or	[row][bx+1],al
pkP2:
		ret
pack		endp

;putrow - si -> a packed line, to video memory line bp
putrow		proc	near
		push	si
		mov	ax,bp
		and	al,[imask]
		xor	ah,ah
		mov	cl,13
		shl	ax,cl
		mov	di,ax
		mov	ax,bp
		mov	cl,[ishift]
		shr	ax,cl
		mul	[rowb]
		add	di,ax
		mov	ax,0B800h
		mov	es,ax
		pop	si
		mov	cx,[rowb]
		rep	movsb
		push	cs
		pop	es
		ret
putrow		endp

code		ends
		end	start
