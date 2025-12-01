; TANBOX.ASM
;
; This is a little screen saver for Tandy mode 9 (320x200 16-colors).  It
; fills the screen with colored rectangles.  Pressing <esc> terminates the
; program.  This program demonstrates how to detect Tandy video, enter and
; leave Tandy mode, and set pixels in Tandy mode.
;
; Assemble this program to make TANBOX.COM.  The shareware A86 assembler
; will assemble it as is; other assemblers will require you to add various
; useless junk ;-).
;
; NOTE:  The aspect ratio in this mode is approximately 5:6, which means
; that there are 6 horizontal pixels per 5 vertical pixels - in other words,
; pixels are 20% taller than they are wide.  Unlike VGA 640x480 mode, which
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
		; Number of boxes per color.
		;
NBOXES		EQU	100
		;
		; Error message displayed if no Tandy video.
		;
NO_TANDY_MSG	DB	"This program requires Tandy 1000 or IBM PC-Jr video."
		DB	0Dh,0Ah,"$"
		;
		; Video mode in effect at startup, to be restored later.
		;
OLD_MODE	DB	0
		;
		; Seed for the random number generator.
		;
SEED		DW	0
		;
		; Variables for the rectangle generator.
		;
COLOR		DB	1	; color of the rectangle - initially blue
FIRST_COLUMN	DW	0	; leftmost pixel column in the rectangle
LAST_COLUMN	DW	0	; rightmost pixel column in the rectangle
FIRST_LINE	DW	0	; top scan line in the rectangle
LAST_LINE	DW	0	; bottom scan line in the rectangle

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
; Routine to set a pixel on the screen.  AL is the color (0-15), CX is the
; column (0-319), DX is the row (0-199).  Assumes the video is in mode 9
; (320x200x16 Tandy mode).  We write directly to the video buffer here for
; illustrative purposes, but it would be easier just to issue Int 10h (see
; ALT_SETPIXEL below).
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
	; ES addresses the video buffer.
	;
	MOV	BX,0B800h
	MOV	ES,BX
	;
	; Video is interleaved in this mode.  The top line and every 4th line
	; after that is at B800:0.  The second line and every 4th line after
	; that is at B800:2000.  The third line and every 4th line after that
	; is at B800:4000.  The fourth line and every 4th line after that is
	; at B800:6000.  Accordingly, we first need to compute which of the
	; 4 partial buffers to use and put its offset in BX.  At the same
	; time, DX is set equal to the number of the line within the partial
	; buffer.
	;
	XOR	BX,BX
	SHR	DX,1
	RCR	BX,1
	SHR	DX,1
	RCR	BX,1
	SHR	BX,1
	;
	; Each line takes 160 bytes (2 pixels per byte), so to compute the
	; offset of the line within the partial buffer, we multiply by 160.
	; We need to use AX for multiplication, so we swap to save the pixel
	; color in DL.  Add the offset of the line within the partial buffer
	; to the offset of the partial buffer to get the offset of the line
	; from the start of video RAM.
	;
	XCHG	AL,DL
	MOV	AH,160
	MUL	AH
	ADD	BX,AX
	;
	; Now we need to find the right pixel.  Divide by 2 to get the offset
	; of the pixel from the start of the line, and add that offset into
	; BX to get the offset of the pixel from the start of video RAM.
	; At the same time, save the carry flag, which will be set for an odd
	; pixel and clear for an even pixel.
	;
	SHR	CX,1
	PUSHF
	ADD	BX,CX
	;
	; The byte containing the pixel to set is at ES:[BX].  Get it in AL,
	; and recover the carry flag.
	;
	MOV	AL,ES:[BX]
	POPF
	;
	; If this is an even pixel, we need to set the left nibble to the
	; color in DL.
	;
	JC	SETPIXEL_ODD
	AND	AL,0Fh
	MOV	CL,4
	SHL	DL,CL
	OR	AL,DL
	JMP	SETPIXEL_WRITEBACK
	;
	; If this is an odd pixel, we need to set the right nibble to the
	; color in DL.
	;
SETPIXEL_ODD:
	AND	AL,0F0h
	OR	AL,DL
	;
	; Write the byte back to update the screen.
	;
SETPIXEL_WRITEBACK:
	MOV	ES:[BX],AL
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
; Alternate set pixel function.  This function uses the BIOS and is therefore
; simpler than the above, though perhaps a bit slower.  Wherever it says
; "CALL SETPIXEL" in function RECTANGLE below, "CALL ALT_SETPIXEL" could be
; used instead.
;
ALT_SETPIXEL:
	;
	; Save registers.  The BIOS may change them.
	;
	PUSH	AX
	PUSH	CX
	PUSH	DX
	;
	; Issue Int 10h with AH=0Ch, AL=color (0-15), DX=row (0-199),
	; CX=column (0-319).
	;
	MOV	AH,0Ch
	INT	10h
	;
	; Restore registers and return.
	;
	POP	DX
	POP	CX
	POP	AX
	RET

;
; Routine to draw a rectangle on the screen.  COLOR is the color of the
; rectangle.  The top and bottom limits of the rectangle are given by
; FIRST_LINE and LAST_LINE; the left and right limits are given by
; FIRST_COLUMN and LAST_COLUMN.
;
RECTANGLE:
	;
	; Save registers.
	;
	PUSH	AX
	PUSH	CX
	PUSH	DX
	;
	; Get the pixel color in AL.
	;
	MOV	AL,COLOR
	;
	; Draw a line across the top of the rectangle.
	;
	MOV	DX,FIRST_LINE
	MOV	CX,FIRST_COLUMN
RECTANGLE_TOPLOOP:
	CALL	SETPIXEL
	INC	CX
	CMP	CX,LAST_COLUMN
	JBE	RECTANGLE_TOPLOOP
	;
	; Draw lines down the sides of the rectangle.
	;
RECTANGLE_SIDELOOP:
	INC	DX
	CMP	DX,LAST_LINE
	JE	RECTANGLE_SIDEEND
	MOV	CX,FIRST_COLUMN
	CALL	SETPIXEL
	MOV	CX,LAST_COLUMN
	CALL	SETPIXEL
	JMP	RECTANGLE_SIDELOOP
	;
	; Draw a line across the bottom of the rectangle.
	;
RECTANGLE_SIDEEND:
	MOV	CX,FIRST_COLUMN
RECTANGLE_BOTTOMLOOP:
	CALL	SETPIXEL
	INC	CX
	CMP	CX,LAST_COLUMN
	JBE	RECTANGLE_BOTTOMLOOP
	;
	; Restore registers and return.
	;
	POP	DX
	POP	CX
	POP	AX
	RET

;
; Routine to draw a random rectangle of a random color.
;
RANDOM_RECTANGLE:
	;
	; Save registers.
	;
	PUSH	AX
	PUSH	CX
	PUSH	DX
	;
	; Get random right and left limits for the rectangle.
	;
	MOV	AX,1			; get a point inside the rectangle
	MOV	DX,320
	CALL	GET_RANDOM_RANGE
	MOV	CX,AX			; 1 <= middle < 320
	CALL	GET_RANDOM_LESS
	MOV	FIRST_COLUMN,AX		; 0 <= FIRST_COLUMN < middle
	MOV	AX,CX
	CALL	GET_RANDOM_RANGE
	MOV	LAST_COLUMN,AX		; middle <= LAST_COLUMN < 320
	;
	; Get random top and bottom limits for the rectangle.
	;
	MOV	AX,1			; get a point inside the rectangle
	MOV	DX,200
	CALL	GET_RANDOM_RANGE
	MOV	CX,AX			; 1 <= middle < 200
	CALL	GET_RANDOM_LESS
	MOV	FIRST_LINE,AX		; 0 <= FIRST_LINE < middle
	MOV	AX,CX
	CALL	GET_RANDOM_RANGE
	MOV	LAST_LINE,AX		; middle <= LAST_LINE < 200
	;
	; Draw the rectangle.
	;
	CALL	RECTANGLE
	;
	; Restore registers and exit.
	;
	POP	DX
	POP	CX
	POP	AX
	RET

;
; Main program.
;
START:
	;
	; Detect the video type.  If not Tandy 1000, display a message and
	; exit.
	;
	CALL	VID_DETECT
	CMP	AX,VID_1000
	JE	HAVE_TANDY
	CMP	AX,VID_SLTL
	JE	HAVE_TANDY
	MOV	AH,9
	MOV	DX,OFFSET NO_TANDY_MSG
	INT	21h
	JMP	TERMINATE
	;
	; We have a Tandy 1000 or IBM PC-Jr.  Get and save the current video 
	; mode.
	;
HAVE_TANDY:
	MOV	AH,0Fh
	INT	10h
	MOV	OLD_MODE,AL
	;
	; Enter Tandy 320x200x16 mode (also clears the screen).
	;
	MOV	AX,9
	INT	10h
	;
	; Flush the keyboard buffer, and set the seed for the random number
	; generator.  Initialize the box count.
	;
	CALL	FLUSHKEY
	CALL	SET_SEED
	MOV	CX,NBOXES
	;
	; Check for keyboard input and loop while the key pressed is not
	; the <esc> key.  On each pass through the loop, draw a rectangle.
	; If NBOXES rectangles have been drawn, change the color.
	;
KEYLOOP:
	CALL	RANDOM_RECTANGLE
	DEC	CX
	JNZ	SAME_COLOR
	MOV	CX,NBOXES
	MOV	AX,16
	CALL	GET_RANDOM_LESS
	MOV	COLOR,AL
SAME_COLOR:
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