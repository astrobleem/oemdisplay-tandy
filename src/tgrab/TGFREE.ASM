; TGFREE.COM - TEST TOOL: largest free DOS block, for the grabber tests (MIT).
; Not part of the packet. Shrinks itself to 4 KB, asks DOS for the largest
; free block (INT 21h AH=48h, BX=FFFFh), prints "DOS free=nnnnnn" and
; appends that line to C:\TGCLOG\DOS.TXT. 8086 instructions only.
code		segment
		assume	cs:code, ds:code, es:code
		org	100h
start:
		mov	sp,offset stk
		mov	bx,1000h / 16
		mov	ah,4Ah
		int	21h
		mov	bx,0FFFFh
		mov	ah,48h
		int	21h			;fails, bx = largest (paragraphs)
		mov	ax,bx
		mov	cx,16
		mul	cx			;dx:ax = bytes
		mov	di,offset digits + 6
		mov	cx,6
		mov	bx,10
cvt:
		push	ax			;dx:ax / 10
		mov	ax,dx
		xor	dx,dx
		div	bx
		mov	si,ax			;high quotient
		pop	ax
		div	bx
		add	dl,'0'
		dec	di
		mov	[di],dl
		mov	dx,si
		loop	cvt
		mov	dx,offset line
		mov	cx,LINELEN
		mov	bx,1
		mov	ah,40h
		int	21h
		mov	dx,offset fname
		mov	ax,3D01h		;open for writing
		int	21h
		jnc	opened
		mov	dx,offset fname
		xor	cx,cx
		mov	ah,3Ch
		int	21h
		jc	done
opened:
		mov	bx,ax
		xor	cx,cx
		xor	dx,dx
		mov	ax,4202h		;append
		int	21h
		mov	dx,offset line
		mov	cx,LINELEN
		mov	ah,40h
		int	21h
		mov	ah,3Eh
		int	21h
done:
		mov	ax,4C00h
		int	21h

fname		db	'C:\TGCLOG\DOS.TXT',0
line		db	'DOS free='
digits		db	'000000',13,10
LINELEN 	equ	$ - line
		db	256 dup (0)
stk		label	byte
code		ends
		end	start
