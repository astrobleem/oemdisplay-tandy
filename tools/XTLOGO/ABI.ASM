; Original MIT static LGO ABI test harness, not WIN.COM.
; Adapted from the project first-party independent-wave harness.
.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
; Explicit 8086 far-condition expansion; avoids Watcom's stale +3 skip after
; shrinking an automatically generated E9 to EB at a range boundary.
JFAIL macro condition,target
 local taken,done
 condition taken
 jmp short done
taken:
 jmp near ptr target
done:
endm
NOTE macro value
 mov byte ptr cs:record_stage,value
 call logstate
endm
entry:
 mov sp,offset stack_end
 push cs
 pop ds
 push cs
 pop es
 cld
 mov dx,offset tracename
 xor cx,cx
 mov ah,3ch
 int 21h
 JFAIL jc,fail
 mov trace_handle,ax
 mov al,0feh
 cmp byte ptr ds:[80h],2
 jb expectation_ready
 mov al,ds:[82h]
 cmp al,'A'
 jne maybe_fallback
 mov al,3
 jmp short expectation_ready
maybe_fallback:
 cmp al,'F'
 jne unspecified
 mov al,0ffh
 jmp short expectation_ready
unspecified:
 mov al,0feh
expectation_ready:
 mov expected_active,al
 mov ax,cs
 mov bx,offset logo
 mov cl,4
 shr bx,cl
 add ax,bx
 mov word ptr showptr+2,ax
 mov word ptr hideptr+2,ax
 mov word ptr expected_sp,sp
 NOTE 10
ifdef KEYFIX
 ; Controlled BIOS-queue fixture: require empty, insert scan39h/ASCII20h.
 push es
 mov ax,40h
 mov es,ax
 mov bx,es:[1ch]
 cmp bx,es:[1ah]
 JFAIL jne,bad_state
 cmp bx,1eh
 JFAIL jb,bad_state
 cmp bx,3ch
 JFAIL ja,bad_state
 mov old_head,bx
 mov old_tail,bx
 mov ax,es:[bx]
 mov old_slot,ax
 pushf
 cli
 mov word ptr es:[bx],3920h
 add bx,2
 cmp bx,3eh
 jb queue_tail_ready
 mov bx,1eh
queue_tail_ready:
 mov es:[1ch],bx
 mov new_tail,bx
 popf
 pop es
 NOTE 20
endif
 call dword ptr showptr
 NOTE 30
 cmp ax,48
 JFAIL jne,fail
 cmp sp,expected_sp
 JFAIL jne,fail
 ; Validate preserved DS/ES and expected active state before copying.
 mov ax,ds
 mov bx,cs
 cmp ax,bx
 JFAIL jne,fail
 mov ax,es
 cmp ax,bx
 JFAIL jne,fail
 push es
 mov es,word ptr showptr+2
 mov al,expected_active
 cmp al,0feh
 je state_ready
 cmp es:[46],al
 JFAIL jne,bad_state
state_ready:
 pop es
 mov ax,48
 NOTE 40
ifdef KEYFIX
 NOTE 50
 mov ah,1
 int 16h
 NOTE 51
 JFAIL jz,fail
 cmp ax,3920h
 JFAIL jne,fail
 ; Restore only the exact empty queue/slot owned by this synthetic fixture.
 ; No blocking AH=00 read: that is a separate real keyboard acceptance test.
 pushf
 cli
 push es
 mov ax,40h
 mov es,ax
 mov bx,old_head
 cmp es:[1ah],bx
 JFAIL jne,key_bad
 mov ax,new_tail
 cmp es:[1ch],ax
 JFAIL jne,key_bad
 cmp word ptr es:[bx],3920h
 JFAIL jne,key_bad
 mov ax,old_tail
 mov es:[1ch],ax
 mov ax,old_slot
 mov es:[bx],ax
 pop es
 popf
 mov ax,48
 NOTE 60
endif
 ; Observe settled graphics for eighteen bounded retrace edges before hide.
 cmp byte ptr expected_active,3
 jne no_observe
 call observe
 JFAIL jc,fail
no_observe:
 NOTE 70
 call dumpframe
 JFAIL jc,fail
 ; Copy AX bytes to paragraph-aligned destination, poison original prefix.
 push ds
 mov ds,word ptr showptr+2
 xor si,si
 mov di,offset resident
 mov cx,ax
 rep movsb
 pop ds
 ; Destroy original hide/state to catch accidental references after relocation.
 push es
 mov es,word ptr showptr+2
 xor di,di
 mov cx,48
 mov al,0cch
 rep stosb
 pop es
 mov ax,cs
 mov bx,offset resident
 mov cl,4
 shr bx,cl
 add ax,bx
 mov word ptr hideptr+2,ax
 NOTE 80
 call dword ptr hideptr
 cmp sp,expected_sp
 JFAIL jne,fail
 ; Repeated hide must return safely as a no-op.
 call dword ptr hideptr
 NOTE 90
 mov bx,trace_handle
 mov ah,3eh
 int 21h
 mov dx,offset okmsg
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
ifdef KEYFIX
key_bad:
 pop es
 popf
 jmp near ptr fail
endif
bad_state:
 pop es
fail:
 NOTE 0ffh
 mov ax,3
 int 10h
 mov ax,4c01h
 int 21h
showptr dw 4,0
hideptr dw 7,0
expected_sp dw 0
expected_active db 0feh
trace_handle dw 0ffffh
tracename db 'HTRACE.BIN',0
old_head dw 0
old_tail dw 0
new_tail dw 0
old_slot dw 0
; Records: stage byte, AX FLAGS DS ES SS SP MODE-AX PAGE-BX HEAD TAIL KEY words.
record_stage db 0
record_ax dw 0
record_flags dw 0
record_ds dw 0
record_es dw 0
record_ss dw 0
record_sp dw 0
record_mode dw 0
record_page dw 0
record_head dw 0
record_tail dw 0
record_key dw 0
logstate proc near
 pushf
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push bp
 push ds
 push es
 push cs
 pop ds
 mov record_ax,ax
 mov bp,sp
 mov ax,ss:[bp+18]
 mov record_flags,ax
 mov ax,ss:[bp+2]
 mov record_ds,ax
 mov ax,ss:[bp]
 mov record_es,ax
 mov ax,ss
 mov record_ss,ax
 mov ax,sp
 add ax,22
 mov record_sp,ax
 mov ah,0fh
 int 10h
 mov record_mode,ax
 mov record_page,bx
 mov ax,40h
 mov es,ax
 mov bx,es:[1ah]
 mov record_head,bx
 mov ax,es:[1ch]
 mov record_tail,ax
 xor ax,ax
 cmp bx,1eh
 jb no_key_word
 cmp bx,3ch
 ja no_key_word
 mov ax,es:[bx]
no_key_word:
 mov record_key,ax
 mov bx,trace_handle
 cmp bx,0ffffh
 je log_done
 mov dx,offset record_stage
 mov cx,23
 mov ah,40h
 int 21h
log_done:
 pop es
 pop ds
 pop bp
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 popf
 ret
logstate endp
observe proc near
 push ax
 push bx
 push cx
 push dx
 mov bx,18
 mov dx,03dah
obs_edge:
 mov cx,0ffffh
obs_off:
 in al,dx
 test al,8
 jz obs_wait_on
 loop obs_off
 jmp short obs_bad
obs_wait_on:
 mov cx,0ffffh
obs_on:
 in al,dx
 test al,8
 jnz obs_next
 loop obs_on
 jmp short obs_bad
obs_next:
 dec bx
 jnz obs_edge
 clc
 jmp short obs_done
obs_bad:
 stc
obs_done:
 pop dx
 pop cx
 pop bx
 pop ax
 ret
observe endp
frame_name db 'STATIC.BIN',0
frame_ok db 0
dumpframe proc near
 push ax
 push bx
 push cx
 push dx
 push ds
 push cs
 pop ds
 mov byte ptr frame_ok,0
 mov dx,offset frame_name
 xor cx,cx
 mov ah,3ch
 int 21h
 jc frame_exit
 mov bx,ax
 mov ax,0b800h
 mov ds,ax
 xor dx,dx
 mov cx,4000h
 mov ah,40h
 int 21h
 jc frame_close
 cmp ax,4000h
 jne frame_close
 mov byte ptr cs:frame_ok,1
frame_close:
 mov ah,3eh
 int 21h
 jnc frame_exit
 mov byte ptr cs:frame_ok,0
frame_exit:
 pop ds
 pop dx
 pop cx
 pop bx
 pop ax
 cmp byte ptr cs:frame_ok,1
 jne frame_bad
 clc
 ret
frame_bad:
 stc
 ret
dumpframe endp
okmsg db 'Resident hide returned after relocation.',13,10,'$'
align 16
resident db 48 dup(0)
db 512 dup(0)
stack_end label byte
align 16
logo label byte
; BUILDABI.PY appends XTSTATIC.LGO + original RLE to the paragraph-aligned COM image.
db 'LEND'
code ends
end entry
