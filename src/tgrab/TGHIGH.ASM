; TGHIGH.COM - TEST TOOL: occupy n paragraphs at the top of free memory (MIT).
; Not part of the packet. "TGHIGH n" (n = 1..999, decimal) allocates n
; paragraphs with DOS last-fit strategy, so the largest free block ends n+1
; paragraphs lower (a different end, odd or even), and stays resident with
; its PSP only. Used to test the grabber's heap-end handling with different
; memory layouts. Prints the new block's segment. 8086 instructions only.
code		segment
		assume	cs:code, ds:code, es:code
		org	100h
start:
		mov	si,81h			;decimal argument
		xor	bx,bx
skip:		lodsb
		cmp	al,' '
		je	skip
num:		cmp	al,'0'
		jb	numEnd
		cmp	al,'9'
		ja	numEnd
		sub	al,'0'
		xor	ah,ah
		push	ax
		mov	ax,bx
		mov	cx,10
		mul	cx
		pop	cx
		add	ax,cx
		mov	bx,ax
		lodsb
		jmp	num
numEnd:
		or	bx,bx
		jz	usage
		cmp	bx,999
		ja	usage
		mov	[count],bx
		mov	ax,ds:[2Ch]		;free the environment
		mov	es,ax
		mov	ah,49h
		int	21h
		push	cs
		pop	es
		mov	bx,(prog_end - start + 100h + 15) / 16
		mov	ah,4Ah
		int	21h
		mov	ax,5800h
		int	21h
		mov	[strat],ax
		mov	ax,5801h
		mov	bx,2			;last fit
		int	21h
		mov	bx,[count]
		mov	ah,48h
		int	21h
		pushf
		push	ax
		mov	ax,5801h
		mov	bx,[strat]
		int	21h
		pop	ax
		popf
		jc	nomem
		mov	di,offset hex		;segment in hex
		mov	cx,4
hx:		push	cx
		mov	cl,4
		rol	ax,cl
		pop	cx
		push	ax
		and	al,0Fh
		add	al,'0'
		cmp	al,'9'
		jbe	hx1
		add	al,7
hx1:		mov	[di],al
		inc	di
		pop	ax
		loop	hx
		mov	dx,offset msg
		mov	ah,9
		int	21h
		mov	dx,10h			;keep the PSP (owner of the block)
		mov	ax,3100h
		int	21h
nomem:
		mov	dx,offset msgno
		jmp	short fail
usage:
		mov	dx,offset msgus
fail:
		mov	ah,9
		int	21h
		mov	ax,4C01h
		int	21h

count		dw	0
strat		dw	0
msg		db	'TGHIGH: block at '
hex		db	'0000',13,10,'$'
msgno		db	'TGHIGH: no memory',13,10,'$'
msgus		db	'TGHIGH n   (1..999 paragraphs)',13,10,'$'
prog_end	label	byte
code		ends
		end	start
