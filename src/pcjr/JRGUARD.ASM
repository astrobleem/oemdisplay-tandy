; JRGUARD.ASM - pre-Windows guard for the proposed PCjr driver (TNDYJR).
; MASM 5.1 syntax, .8086 only. Build as a COM (org 100h).
; See ../../docs/PCJR.MD.
;
; Read-only. It never allocates, never edits an MCB, never changes the video
; mode, and never stays resident. It only answers one question:
;
;   Is the 32KB page at physical 18000h-1FFFFh (segment 1800h, the page the
;   PCjr BIOS chose for mode 09h in every probe so far) protected from DOS
;   allocations before Windows starts?
;
; PASS (exit 0) when either
;   a) the DOS arena ends at or below segment 1800h, or
;   b) one MCB owned by DOS itself (owner 0008h) covers paragraphs
;      1800h-1FFFh entirely. Any other owner fails: a program, TSR or the
;      launching COMMAND.COM may free or reuse its memory.
; Anything else, including a corrupt chain, a non-PCjr machine or DOS < 3,
; fails closed with exit 1. The launcher must not start Windows on failure.
;
; This is deliberately narrower than the Tandy RESERVE helper: it does not
; try to create the reservation itself. Real PCjr memory-expansion drivers
; differ; the first job is to learn which ones already protect the page.

.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
entry: jmp start

PAGE_LO equ 1800h
PAGE_HI equ 2000h

m_notjr  db 'JRGUARD: not an IBM PCjr (F000:FFFE is not FDh).',13,10,'$'
m_dos    db 'JRGUARD: DOS 3.0 or newer is required.',13,10,'$'
m_chain  db 'JRGUARD: DOS memory chain is not valid. Not starting.',13,10,'$'
m_free   db 'JRGUARD: video page 18000h-1FFFFh is not reserved by DOS.',13,10
         db '         Load a PCjr memory driver that reserves it, see PCJR.MD.',13,10,'$'
m_above  db 'JRGUARD: OK, DOS memory ends below the video page.',13,10,'$'
m_owned  db 'JRGUARD: OK, video page is held by a DOS system block.',13,10,'$'

start:
 cli
 mov sp,offset stack_end
 sti
 push cs
 pop ds
 ; A COM owns the largest free block when it starts, which may be the very
 ; page we are judging. Give the tail back first, so our own allocation can
 ; never be mistaken for a protecting owner (it is also excluded below).
 push cs
 pop es
 mov bx,(stack_end - entry + 100h + 15) / 16  ; label difference is a constant
 mov ah,4ah
 int 21h
 mov dx,offset m_chain
 jc fail
 mov ax,0f000h
 mov es,ax
 mov dx,offset m_notjr
 cmp byte ptr es:[0fffeh],0fdh
 jne fail
 mov ah,30h
 int 21h
 mov dx,offset m_dos
 cmp al,3
 jb fail

 mov ah,52h
 int 21h
 mov ax,es:[bx-2]
 mov dx,offset m_chain
walk:
 mov es,ax
 mov bl,es:[0]
 cmp bl,'M'
 je walk_ok
 cmp bl,'Z'
 jne fail
walk_ok:
 mov cx,es:[3]
 mov si,ax
 inc si                   ; SI = first data paragraph
 add cx,si                ; CX = first paragraph after the block
 jc fail                  ; size wraps past 1MB: corrupt
 ; Does this block cover the whole page?
 cmp si,PAGE_LO
 ja next
 cmp cx,PAGE_HI
 jb next
 ; Only DOS's own system blocks (owner 0008h) count as protection. Free
 ; memory (0), this program, its parent COMMAND.COM, a TSR or any other
 ; program's allocation could be released or reused while Windows runs.
 mov dx,offset m_free
 cmp word ptr es:[1],0008h
 jne fail
 mov dx,offset m_owned
 jmp short pass
next:
 cmp bl,'Z'
 je last
 mov ax,cx
 jmp short walk
last:
 ; Arena ended without one block covering the page.
 mov dx,offset m_above
 cmp cx,PAGE_LO
 jbe pass
 mov dx,offset m_free
fail:
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
pass:
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h

 even
stack_area db 256 dup(0)
stack_end label word

code ends
end entry
