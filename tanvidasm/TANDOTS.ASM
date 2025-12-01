; TANDOTS.ASM
;
; This is a screen saver for Tandy mode E (640x200 16-colors), which is
; available on the Tandy 1000 SL, SL/2, TL, TL/2, TL/3, RL, and RL-HD.
; We draw random dots of various colors, NDOTS at a time.  Pressing <esc>
; terminates the program.  This program demonstrates how to detect Tandy
; 1000SL/TL/RL video, how to enter and leave mode E, and how to set pixels
; in mode E.  This is not very neat code (maybe someone will provide better
; :-).
;
; Assemble this program to make TANDOTS.COM.  The shareware A86 assembler
; will assemble it as is; other assemblers will require you to add various
; useless junk ;-).
;
; NOTE:  The aspect ratio in this mode is approximately 5:12, which means
; that there are 12 horizontal pixels per 5 vertical pixels - in other words,
; pixels are 120% taller than they are wide.  Unlike VGA 640x480 mode, which
; has square pixels, you will have to adjust if you want shapes to come out
; right.  I don't deal with that here.
;

	JMP	START

;
; Data.
;
; Video types.
;
VID_MDA		EQU	0	; Monochrome Display Adapter or Hercules
VID_CGA		EQU	1	; Color Graphics Adapter
VID_1000	EQU	2	; Tandy 1000 or IBM PC-Jr
VID_SLTL	EQU	3	; Tandy 1000SL/TL/RL
VID_EGA		EQU	4	; Enhanced Graphics Adapter
VID_MCGA	EQU	5	; Multi-Color Graphics Adapter
VID_VGA		EQU	6	; Video Graphics Array
VID_OTHER	EQU	7	; Other, unknown, or no display
		;
		; Number of dots per color.
		;
NDOTS		EQU	30000
		;
		; Error message displayed if no Tandy video.
		;
NO_TANDY_MSG	DB	"This program requires a Tandy 1000 SL, SL/2, TL, "
		DB	"TL/2, TL/3, RL, or RL-HD,",0Dh,0Ah
		DB	"with a CGA monitor attached.",0Dh,0Ah,"$"
		;
		; Video mode in effect at startup, to be restored later.
		;
OLD_MODE	DB	0
		;
		; Seed for the random number generator.
		;
SEED		DW	0
		;
		; Current color.
		;
COLOR		DB	0

;
; Video detection routine.  Returns a code in AX corresponding to the video
; type:  0=MDA, 1=CGA, 2=Tandy 1000 or IBM PC-Jr, 3=Tandy 1000SL/TL/RL, 4=EGA, 
; 5=MCGA, 6=VGA, 7=other/unknown/none.  Other registers are unaffected.
;
VID_DETECT:
	;
	; Save registers other than AX.
	;
	PUSH	BX
	PUSH	CX
	PUSH	ES
	;
	; Try the VGA "Read Combination Code" function.
	;
	MOV	AX,1A00h
	MOV	BX,0EEEEh	; unused display code
	INT	10h
	;
	; If the function is supported, return the active display type.
	;
	CMP	BL,0
	JE	VID_DETECT_OTHER
	CMP	BL,1
	JE	VID_DETECT_MDA
	CMP	BL,2
	JE	VID_DETECT_CGA
	CMP	BL,3
	JE	VID_DETECT_OTHER
	CMP	BL,5
	JBE	VID_DETECT_EGA
	CMP	BL,6
	JE	VID_DETECT_OTHER
	CMP	BL,8
	JBE	VID_DETECT_VGA
	CMP	BL,9
	JE	VID_DETECT_OTHER
	CMP	BL,0Ch
	JBE	VID_DETECT_MCGA
	CMP	BX,0EEEEh
	JNE	VID_DETECT_OTHER
	;
	; The function was not supported, and it's not VGA.  Check for EGA.
	;
	MOV	AH,12h
	MOV	BL,10h
	INT	10h
	CMP	BL,10h
	JNE	VID_DETECT_EGA
	;
	; No EGA.  Check for mono.
	;
	MOV	AX,0F00h
	INT	10h
	CMP	AL,7
	JE	VID_DETECT_MDA
	;
	; Not mono.  Check for a Tandy 1000-series or IBM PC-Jr.  If not 
	; Tandy 1000, it must be CGA.
	;
	MOV	AX,0FFFFh
	MOV	ES,AX
	CMP	BYTE PTR ES:[0Eh],0FDh
	JE	VID_DETECT_1000		; IBM PC-Jr detected
	CMP	BYTE PTR ES:[0Eh],0FFh
	JNE	VID_DETECT_CGA
	MOV	AX,0FC00h
	MOV	ES,AX
	CMP	BYTE PTR ES:[0],21h
	JNE	VID_DETECT_CGA
	;
	; This is a Tandy 1000.  See if it is one of the 1000SL's, 1000TL's,
	; or 1000RL's.
	;
	MOV	AH,0C0h
	INT	15h
	JC	VID_DETECT_1000
	JMP	VID_DETECT_SLTL
	;
	; Other/unknown type detected.
	;
VID_DETECT_OTHER:
	MOV	AX,VID_OTHER
	JMP	VID_DETECT_RETURN
	;
	; CGA detected.
	;
VID_DETECT_CGA:
	MOV	AX,VID_CGA
	JMP	VID_DETECT_RETURN
	;
	; MDA/Hercules detected.
	;
VID_DETECT_MDA:
	MOV	AX,VID_MDA
	JMP	VID_DETECT_RETURN
	;
	; VGA detected.
	;
VID_DETECT_VGA:
	MOV	AX,VID_VGA
	JMP	VID_DETECT_RETURN
	;
	; MCGA detected.
	;
VID_DETECT_MCGA:
	MOV	AX,VID_MCGA
	JMP	VID_DETECT_RETURN
	;
	; EGA detected.
	;
VID_DETECT_EGA:
	MOV	AX,VID_EGA
	JMP	VID_DETECT_RETURN
	;
	; Tandy 1000SL/TL/RL detected.
	;
VID_DETECT_SLTL:
	MOV	AX,VID_SLTL
	JMP	VID_DETECT_RETURN
	;
	; Tandy 1000 detected.
	;
VID_DETECT_1000:
	MOV	AX,VID_1000
	JMP	VID_DETECT_RETURN
	;
	; Restore registers and return.
	;
VID_DETECT_RETURN:
	POP	ES
	POP	CX
	POP	BX
	RET

;
; Routine to flush the keyboard buffer.  Preserves all registers.
;
FLUSHKEY:
	PUSH	AX
FLUSHKEY_LOOP:
	MOV	AH,1
	INT	16h
	JZ	FLUSHKEY_DONE
	MOV	AH,0
	INT	16h
	JMP	FLUSHKEY_LOOP
FLUSHKEY_DONE:
	POP	AX
	RET

;
; Routine to set the random seed.  The seed is set based on the low word
; of the current clock count.  Changes no registers.
;
SET_SEED:
	PUSH	AX
	PUSH	CX
	PUSH	DX
	MOV	AH,0
	INT	1Ah
	MOV	SEED,DX
	POP	DX
	POP	CX
	POP	AX
	RET

;
; Routine to get a random integer in the range 0-65535 in AX.
;
GET_RANDOM:
	PUSH	DX
	MOV	AX,42933
	MUL	SEED
	INC	AX
	MOV	SEED,AX
	POP	DX
	RET

;
; Routine to get a random integer in the range 0..(k-1), where AX=k on
; entry.  Returns the integer in AX.
;
GET_RANDOM_LESS:
	PUSH	DX
	MOV	DX,AX
	CALL	GET_RANDOM
	MUL	DX
	MOV	AX,DX
	POP	DX
	RET

;
; Routine to get a random integer in the range m..(n-1), where on entry
; AX=m, DX=n.  The random integer is returned in AX.
;
GET_RANDOM_RANGE:
	PUSH	DX
	XCHG	AX,DX		; AX=n, DX=m
	SUB	AX,DX		; AX=n-m, DX=m
	CALL	GET_RANDOM_LESS	; AX=random number 0..n-m-1, DX=m
	ADD	AX,DX		; AX=random number m..n-1
	POP	DX
	RET

;
; Routine to clear the screen in Tandy 1000SL/TL/RL 640x200x16 video mode.
;
CLEAR_SCREEN:
	;
	; Save registers.
	;
	PUSH	AX
	PUSH	CX
	PUSH	DI
	PUSH	ES
	;
	; Fill the screen with black pixels.
	;
	CLD
	MOV	AX,0A000h
	MOV	ES,AX
	XOR	DI,DI
	XOR	AX,AX
	MOV	CX,32000
	REP	STOSW	
	;
	; Restore registers and return.
	;
	POP	ES
	POP	DI
	POP	CX
	POP	AX
	RET

;
; Routine to enter Tandy 1000SL/TL/RL 640x200x16 video mode.
;
SET_SLTL_MODE:
	PUSH	AX
	PUSH	DX
	;
	; Switch to mode 3 (80-column color text) so that the BIOS data will
	; be valid when we switch back.
	;
	MOV	AX,3
	INT	10h
	;
	; Switch to mode E:
	; Disable video display while loading controller registers.	
	;
	MOV	DX,3D8H
	MOV	AL,13H
	OUT	DX,AL
	;
	; Set horizontal and vertical total registers.
	;
	MOV	DX,3D4H
	MOV	AL,10H
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,18H
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,0
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,71H
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,1
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,50H
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,2
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,5AH
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,3
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0EH
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,4
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0FFH
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,5
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,06H
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,6
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0C8H
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,7
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0E2H
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,9
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,0CH
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,0DH
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,11H
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,0
	OUT	DX,AL

	MOV	DX,3D4H
	MOV	AL,12H
	OUT	DX,AL
	MOV	DX,3D5H
	MOV	AL,46H
	OUT	DX,AL
	;
	; Set control bits.
	;
	MOV	DX,3DAH
	MOV	AL,1
	OUT	DX,AL
	MOV	DX,3DEH
	MOV	AL,0FH
	OUT	DX,AL
	
	MOV	DX,3DAH
	MOV	AL,2
	OUT	DX,AL
	MOV	DX,3DEH
	MOV	AL,0
	OUT	DX,AL
	
	MOV	DX,3DAH
	MOV	AL,3
	OUT	DX,AL
	MOV	DX,3DEH
	MOV	AL,10H
	OUT	DX,AL
	
	MOV	DX,3DAH
	MOV	AL,5
	OUT	DX,AL
	MOV	DX,3DEH
	MOV	AL,01H
	OUT	DX,AL
	
	MOV	DX,3DAH
	MOV	AL,8
	OUT	DX,AL
	MOV	DX,3DEH
	MOV	AL,2
	OUT	DX,AL
	;
	; Set border color (?).  (See docs.)
	;
	MOV	DX,3D9H
	MOV	AL,0
	OUT	DX,AL
	;
	; Set extended RAM paging off.
	;
	MOV	DX,3DDH
	MOV	AL,0
	OUT	DX,AL
	;
	; Set the addressing mode, select page 2.
	;
	MOV	DX,3DFH
	MOV	AL,24H
	OUT	DX,AL	
	;
	; Clear the screen.
	;
	CALL	CLEAR_SCREEN
	;
	; Reenable video.
	;
	MOV	DX,3D8H
	MOV	AL,1BH
	OUT	DX,AL
	;
	; Restore registers and return.
	;
	POP	DX
	POP	AX
	RET

;
; Routine to exit Tandy 1000SL/TL/RL 640x200x16 video mode.
;
UNSET_SLTL_MODE:
	PUSH	AX
	PUSH	CX
	PUSH	DX
	PUSH	DI
	PUSH	ES
	;
	; Set the video mode to 80-column color text:
	; Disable video display while loading controller registers.	
	;
	MOV	DX,3D8H
	MOV	AL,1
	OUT	DX,AL
	;
	; Load the CRTC registers.
	;
	MOV	DX,3D4H
	MOV	AL,0
	OUT	DX,AL
	INC	DX
	MOV	AL,71H
	OUT	DX,AL
	DEC	DX

	MOV	AL,1
	OUT	DX,AL
	INC	DX
	MOV	AL,50H
	OUT	DX,AL
	DEC	DX

	MOV	AL,2
	OUT	DX,AL
	INC	DX
	MOV	AL,5AH
	OUT	DX,AL
	DEC	DX

	MOV	AL,3
	OUT	DX,AL
	INC	DX
	MOV	AL,0FEH
	OUT	DX,AL
	DEC	DX

	MOV	AL,4
	OUT	DX,AL
	INC	DX
	MOV	AL,1CH
	OUT	DX,AL
	DEC	DX

	MOV	AL,5
	OUT	DX,AL
	INC	DX
	MOV	AL,01H
	OUT	DX,AL
	DEC	DX

	MOV	AL,6
	OUT	DX,AL
	INC	DX
	MOV	AL,19H
	OUT	DX,AL
	DEC	DX

	MOV	AL,7
	OUT	DX,AL
	INC	DX
	MOV	AL,1AH
	OUT	DX,AL
	DEC	DX

	MOV	AL,9
	OUT	DX,AL
	INC	DX
	MOV	AL,8
	OUT	DX,AL
	DEC	DX

	MOV	AL,0AH
	OUT	DX,AL
	INC	DX
	MOV	AL,6
	OUT	DX,AL
	DEC	DX

	MOV	AL,0BH
	OUT	DX,AL
	INC	DX
	MOV	AL,07H
	OUT	DX,AL
	DEC	DX

	MOV	AL,0CH
	OUT	DX,AL
	INC	DX
	MOV	AL,0
	OUT	DX,AL
	DEC	DX

	MOV	AL,0DH
	OUT	DX,AL
	INC	DX
	MOV	AL,0
	OUT	DX,AL
	DEC	DX

	MOV	AL,0EH
	OUT	DX,AL
	INC	DX
	MOV	AL,0
	OUT	DX,AL
	DEC	DX

	MOV	AL,0FH	
	OUT	DX,AL
	INC	DX
	MOV	AL,0
	OUT	DX,AL
	DEC	DX

	MOV	AL,10H
	OUT	DX,AL
	INC	DX
	MOV	AL,18H
	OUT	DX,AL
	DEC	DX

	MOV	AL,11H		; this one is doubtful
	OUT	DX,AL
	INC	DX
	MOV	AL,20H
	OUT	DX,AL
	DEC	DX

	MOV	AL,12H
	OUT	DX,AL
	INC	DX
	MOV	AL,07H
	OUT	DX,AL
	DEC	DX

	MOV	AL,13H
	OUT	DX,AL
	INC	DX
	MOV	AL,0
	OUT	DX,AL
	;
	; Set border color register.
	;
	MOV	DX,3D9H
	MOV	AL,0
	OUT	DX,AL
	;
	; Set the extended addressing mode register.
	;
	MOV	DX,3DDH
	MOV	AL,0
	OUT	DX,AL
	;
	; Set the video array registers.
	;
	MOV	DX,3DAH
	MOV	CX,3DEH
	MOV	AL,1
	OUT	DX,AL
	XCHG	DX,CX
	MOV	AL,0FH
	OUT	DX,AL
	XCHG	DX,CX

	MOV	AL,2
	OUT	DX,AL
	XCHG	DX,CX
	MOV	AL,0
	OUT	DX,AL
	XCHG	DX,CX

	MOV	AL,3
	OUT	DX,AL
	XCHG	DX,CX
	MOV	AL,10H
	OUT	DX,AL
	XCHG	DX,CX

	MOV	AL,5
	OUT	DX,AL
	XCHG	DX,CX
	MOV	AL,0
	OUT	DX,AL
	XCHG	DX,CX

	MOV	AL,8
	OUT	DX,AL
	XCHG	DX,CX
	MOV	AL,0
	OUT	DX,AL
	;
	; Set the CRT/Processor Page Register.
	;
	MOV	DX,3DFH
	MOV	AL,3FH
	OUT	DX,AL
	;
	; Fill the screen with blanks, attribute white on black.
	;
	CLD
	MOV	AX,0B800H
	MOV	ES,AX
	XOR	DI,DI
	MOV	AX,0720H
	MOV	CX,2000H
	REP	STOSW	
	;
	; Reenable video (blink enabled).
	;
	MOV	DX,3D8H
	MOV	AL,29H
	OUT	DX,AL
	;
	; Restore registers and return.
	;
	POP	ES
	POP	DI
	POP	DX
	POP	CX
	POP	AX
	RET

;
; Routine to set a pixel on the screen.  AL is the color (0-15), CX is the
; column (0-639), DX is the row (0-199).  Assumes the video is in mode E
; (640x200x16 Tandy mode).  We write directly to the video buffer here; the
; BIOS doesn't support this mode.
;
SETPIXEL:
	;
	; Save registers.
	;
	PUSH	AX
	PUSH	BX
	PUSH	CX
	PUSH	DX
	PUSH	ES
	;
	; ES addresses the video buffer at 0A000h.
	;
	MOV	BX,0A000h
	MOV	ES,BX
	;
	; Memory is linear in this mode, and there are 320 bytes per line.
	; Compute the offset of the start of the line from the beginning of
	; the buffer.
	;
	PUSH	AX	; save color
	MOV	AX,320
	MUL	DX
	MOV	BX,AX
	POP	AX	; restore color
	;
	; There are 2 pixels per byte, so divide the column by 2 and add to
	; the offset to get the address of the byte containing the pixel to
	; be set.  At the same time, save the carry flag, which is 1 if the
	; pixel is odd.
	;
	SHR	CX,1
	PUSHF
	ADD	BX,CX
	;
	; Get the byte in DL, and get back the carry flag.
	;
	MOV	DL,ES:[BX]
	POPF
	;
	; If the pixel is even, set the left nibble of the byte to the color
	; in AL.
	;
	JC	SETPIXEL_ODD
	AND	DL,0Fh
	MOV	CL,4
	SHL	AL,CL
	OR	DL,AL
	JMP	SETPIXEL_WRITEBACK
	;
	; If the pixel is odd, set the right nibble of the byte to the color
	; in AL.
	;
SETPIXEL_ODD:
	AND	DL,0F0h
	OR	DL,AL
	;
	; Write the byte back to the video buffer.
	;
SETPIXEL_WRITEBACK:
	MOV	ES:[BX],DL
	;
	; Restore registers and return.
	;
	POP	ES
	POP	DX
	POP	CX
	POP	BX
	POP	AX
	RET

;
; Routine to draw NDOTS random dots on the screen.  COLOR is the color to use.
;
RANDOM_DOTS:
	;
	; Save registers.
	;
	PUSH	AX
	PUSH	CX
	PUSH	DX
	;
	; Loop NDOTS times.
	;
	MOV	CX,NDOTS
RANDOM_DOTS_LOOP:
	PUSH	CX		; save CX; we need it for the column
	MOV	AX,620		; get the column
	CALL	GET_RANDOM_LESS
	MOV	CX,AX
	MOV	AX,200		; get the row
	CALL	GET_RANDOM_LESS
	MOV	DX,AX
	MOV	AL,COLOR	; put color in AL
	CALL	SETPIXEL	; set the pixel
	POP	CX		; restore CX
	LOOP	RANDOM_DOTS_LOOP
	;
	; Restore registers and return.
	;
	POP	DX
	POP	CX
	POP	AX
	RET

;
; Routine to get the next color.
;
NEXT_COLOR:
	PUSH	AX
	MOV	AX,16
	CALL	GET_RANDOM_LESS
	MOV	COLOR,AL
	POP	AX
	RET

;
; Main program.
;
START:
	;
	; Detect the video type.  If not Tandy 1000SL/TL/RL, display a message
	; and exit.
	;
	CALL	VID_DETECT
	CMP	AX,VID_SLTL
	JE	HAVE_TANDY
	MOV	AH,9
	MOV	DX,OFFSET NO_TANDY_MSG
	INT	21h
	JMP	TERMINATE
	;
	; We have a Tandy 1000 SL, SL/2, TL, TL/2, TL/3, RL, or RL-HD.  Get
	; and save the current video mode.
	;
HAVE_TANDY:
	MOV	AH,0Fh
	INT	10h
	MOV	OLD_MODE,AL
	;
	; Enter Tandy 640x200x16 mode (also clears the screen).
	;
	CALL	SET_SLTL_MODE
	;
	; Flush the keyboard buffer, and set the seed for the random number
	; generator.  Set the initial color to blue.
	;
	CALL	FLUSHKEY
	CALL	SET_SEED
	MOV	COLOR,1
	;
	; Check for keyboard input and loop while the key pressed is not
	; the <esc> key.  On each pass through the loop, draw NDOTS random
	; dots and change the color.
	;
KEYLOOP:
	CALL	RANDOM_DOTS
	CALL	NEXT_COLOR
	MOV	AH,1
	INT	16h
	JZ	KEYLOOP
	MOV	AH,0
	INT	16h
	CMP	AL,1Bh
	JNE	KEYLOOP
	;
	; Restore the original video before exit.
	;
	CALL	UNSET_SLTL_MODE
	MOV	AH,0
	MOV	AL,OLD_MODE
	INT	10h
	;
	; Terminate the program.
	;
TERMINATE:
	MOV	AX,4C00h
	INT	21h
