; TGEVEN.COM - keep Windows 3.0 real mode's memory block even-ended (MIT).
;
; Run it after RESERVE and before WIN /R. Windows 3.0 real mode takes the
; largest free DOS block. Its KERNEL puts the global heap's end sentinel on
; the even paragraph below the block's end ((end - 1) AND 0FFFEh). When the
; block ends at an odd segment - as it does after RESERVE, whose block
; header sits at 97FFh - the sentinel is the block's last paragraph. A
; full-screen DOS program run from Windows then overwrites that paragraph,
; WINOLDAP does not put it back, and the next walk of the heap (a DOS text
; grab's Clipboard allocation is the first) loops for ever.
;
; TGEVEN finds the largest free block. If its end is odd it allocates two
; paragraphs (plus their header) at the top of it, so the block Windows
; gets ends at an even segment, and stays resident with just its PSP
; (304 bytes in all). If the end is already even it changes nothing.
; Exit code 0 = done or nothing needed, 1 = refused (message says why).
; DOS 3.0 or newer. 8086 instructions only. Never edits an MCB.

code		segment
		assume	cs:code, ds:code, es:code
		org	100h
start:		jmp	begin

msg_even	db	'TGEVEN: the free memory already ends at an even segment; nothing changed.',13,10,'$'
msg_done	db	'TGEVEN: two paragraphs reserved; Windows memory now ends at an even segment.',13,10,'$'
msg_dos		db	'TGEVEN: needs DOS 3.0 or newer.',13,10,'$'
msg_chain	db	'TGEVEN: unexpected DOS memory chain; nothing changed.',13,10,'$'
msg_alloc	db	'TGEVEN: allocation not at the top of the free block; nothing changed.',13,10,'$'
old_strat	dw	0
best_mcb	dw	0
best_size	dw	0

begin:
		mov	ah,30h
		int	21h
		cmp	al,3
		jae	dos_ok
		mov	dx,offset msg_dos
		jmp	fail
dos_ok:
		mov	ax,ds:[2ch]		;free the environment
		or	ax,ax
		jz	env_done
		mov	es,ax
		mov	ah,49h
		int	21h
		mov	word ptr ds:[2ch],0
env_done:
		push	cs			;keep only the PSP and this code
		pop	es
		mov	bx,(prog_end - start + 100h + 15) / 16
		mov	ah,4ah
		int	21h
		mov	ah,52h			;first MCB at [es:bx-2]
		int	21h
		mov	ax,es:[bx-2]
walk:
		mov	es,ax
		mov	cl,es:[0]
		cmp	cl,'M'
		je	walk_ok
		cmp	cl,'Z'
		je	walk_ok
		mov	dx,offset msg_chain
		jmp	fail
walk_ok:
		cmp	word ptr es:[1],0	;free?
		jne	walk_next
		mov	dx,es:[3]
		cmp	dx,[best_size]
		jbe	walk_next
		mov	[best_size],dx
		mov	[best_mcb],ax
walk_next:
		add	ax,es:[3]
		inc	ax
		cmp	cl,'Z'
		jne	walk
		mov	ax,[best_mcb]
		or	ax,ax
		jnz	have_best
		mov	dx,offset msg_chain
		jmp	fail
have_best:
		add	ax,[best_size]
		inc	ax			;ax = end of the largest free block
		test	al,1
		jnz	need_guard
		mov	dx,offset msg_even
		mov	ah,9
		int	21h
		mov	ax,4C00h
		int	21h
need_guard:
		push	ax
		mov	ax,5800h		;last fit for one allocation
		int	21h
		mov	[old_strat],ax
		mov	ax,5801h
		mov	bx,2
		int	21h
		mov	ah,48h
		mov	bx,2
		int	21h
		pushf
		push	ax
		mov	ax,5801h
		mov	bx,[old_strat]
		int	21h
		pop	bx			;bx = guard segment
		popf
		pop	ax			;ax = old end
		jc	bad_alloc
		add	bx,2
		cmp	bx,ax			;guard must end exactly at the old end
		je	guard_ok
		sub	bx,2
		mov	es,bx
		mov	ah,49h
		int	21h
bad_alloc:
		mov	dx,offset msg_alloc
		jmp	fail
guard_ok:
		mov	dx,offset msg_done
		mov	ah,9
		int	21h
		mov	dx,10h			;resident: the PSP only (owner of the guard)
		mov	ax,3100h
		int	21h
fail:
		mov	ah,9
		int	21h
		mov	ax,4C01h
		int	21h
prog_end	label	byte
code		ends
		end	start
