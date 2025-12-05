	page	,132
;-----------------------------Module-Header-----------------------------;
; Module Name:	INQUIRE.ASM
;
; This module contains the routine which returns pointer shape
; information to the Window Manager.
;
; Created: 16-Jan-1987
; Author:  Walt Moore [waltm]
;
; Copyright (c) 1983-1987 Microsoft Corporation
;
; Exported Functions:	Inquire
;
; Public Functions:	none
;
; Public Data:		none
;
; General Description:
;
; Restrictions:
;
;-----------------------------------------------------------------------;

	.xlist
	include cmacros.inc
	include windefs.inc
	include cursor.inc
	include macros.mac
	.list

createSeg _BLUEMOON,BlueMoonSeg,word,public,CODE
sBegin	BlueMoonSeg
assumes cs,_BLUEMOON

	public inquire_data
inquire_data CURSORINFO <X_RATE, Y_RATE>

page
;--------------------------Exported-Routine-----------------------------;
; WORD Inquire(lpCURSORINFO)
; CURSORINFO far *lpCURSORINFO; //pointer where cursor info goes
; 
; Information about the pointer is returned to the caller in the
; given buffer.  The number of bytes copied into lpCURSORINFO
; is returned.
;
; Warnings:
;	Destroys AX,CX,ES,FLAGS
; Effects:
;	none
; Calls:
;	none
; History:
;	Wed 12-Aug-1987 17:29:30 -by-  Walt Moore [waltm]
;	Made non-resident
;
;	Fri 16-Jan-1987 17:52:12 -by-  Walt Moore [waltm]
;	Initial version
;-----------------------------------------------------------------------;

;------------------------------Pseudo-Code------------------------------;
; WORD Inquire(lpCURSORINFO)
; CURSORINFO far *lpCURSORINFO; 	//pointer where cursor info goes
; {
;   *lpCURSORINFO = inquire_data;	//copy entire structure
;   return (sizeof(CURSORINFO));
; }
;-----------------------------------------------------------------------;

	assumes ds,_DATA_SEG

cProc	Inquire,<PUBLIC,FAR,WIN,PASCAL>,<si,di>

	parmD	lp_cursor_info		;Where to put the data

cBegin
	push	cs
	pop	ds
	assumes ds,_BLUEMOON

	les	di,lp_cursor_info	;--> destination area
	assumes es,nothing

	mov	si,BlueMoonSegOFFSET inquire_data
	mov	ax,size CURSORINFO	;Return code is # of bytes moved
	mov	cx,ax
	cld
	rep	movsb

cEnd

sEnd	BlueMoonSeg
end
