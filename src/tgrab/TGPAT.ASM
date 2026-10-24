; TGPAT.COM - Tandy 1000 grabber test picture (MIT).
; Sets BIOS mode 9 (320x200x16), draws a 64x40 test image at (128,80) on a
; black screen, waits for a key, restores mode 3 and exits.
; Image f(x,y), 0<=x<64, 0<=y<40:
;   border (x=0, x=63, y=0, y=39): 15
;   2<=x<10 and 2<=y<6: 12 (marker, top left)
;   y<20: x/4      else: 15 - x/4
; 8086 instructions only.
code		segment
		assume	cs:code, ds:code, es:code
		org	100h
start:
		mov	ax,0009h
		int	10h
		mov	ax,0B800h
		mov	es,ax
		xor	bp,bp			;bp = y
yloop:
		xor	si,si			;si = x
xloop:
		call	colour			;al = f(si,bp)
		call	plot
		inc	si
		cmp	si,64
		jb	xloop
		inc	bp
		cmp	bp,40
		jb	yloop
		xor	ah,ah
		int	16h
		mov	ax,0003h
		int	10h
		mov	ax,4C00h
		int	21h

colour		proc	near
		mov	al,15
		or	si,si
		jz	cDone
		cmp	si,63
		je	cDone
		or	bp,bp
		jz	cDone
		cmp	bp,39
		je	cDone
		mov	al,12
		cmp	si,2
		jb	cBars
		cmp	si,10
		jae	cBars
		cmp	bp,2
		jb	cBars
		cmp	bp,6
		jb	cDone
cBars:
		mov	ax,si
		shr	al,1
		shr	al,1
		cmp	bp,20
		jb	cDone
		mov	ah,15
		sub	ah,al
		mov	al,ah
cDone:
		ret
colour		endp

; plot colour al at screen (si+128, bp+80)
plot		proc	near
		push	ax
		mov	bx,bp
		add	bx,80
		mov	di,bx
		and	di,3
		mov	cl,13
		shl	di,cl			;bank * 8192
		shr	bx,1
		shr	bx,1
		mov	ax,160
		mul	bx
		add	di,ax
		mov	bx,si
		add	bx,128
		shr	bx,1
		add	di,bx
		pop	ax
		mov	ah,es:[di]
		test	si,1
		jnz	pOdd
		and	ah,0Fh
		mov	cl,4
		shl	al,cl
		or	ah,al
		jmp	short pPut
pOdd:
		and	ah,0F0h
		or	ah,al
pPut:
		mov	es:[di],ah
		ret
plot		endp

code		ends
		end	start
