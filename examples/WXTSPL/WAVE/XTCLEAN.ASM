; Original private 8086 DOS wrapper. Never patch installed WIN.COM.
.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:code,ss:code
org 100h
JFAIL macro condition,target
 local taken,done
 condition taken
 jmp short done
taken:
 jmp near ptr target
done:
endm
entry:
 mov sp,offset stack_end
 push cs
 pop ds
 push cs
 pop es
 mov ax,0ffffh
 mov es,ax
 cmp byte ptr es:[0eh],0ffh
 JFAIL jne,refuse
 mov ax,0fc00h
 mov es,ax
 cmp byte ptr es:[0],21h
 JFAIL jne,refuse
 mov ax,40h
 mov es,ax
 cmp word ptr es:[13h],624
 JFAIL jne,refuse
 mov ah,0fh
 int 10h
 mov start_mode,ax
 mov start_page,bx
 cmp al,3
 JFAIL jne,refuse
 cmp bh,0
 JFAIL jne,refuse
 call reservation
 JFAIL jc,refuse
 mov owner_before,ax
 push cs
 pop es
 mov bx,offset stack_end
 add bx,15
 mov cl,4
 shr bx,cl
 mov ah,4ah
 int 21h
 JFAIL jc,resize_fail
 mov ax,cs
 mov word ptr params+4,ax
 mov word ptr params+8,ax
 mov word ptr params+12,ax
 mov saved_ss,ss
 mov saved_sp,sp
 pushf
 pop saved_flags
 mov dx,offset child
 mov bx,offset params
 mov ax,4b00h
 int 21h
 ; No stack/DS/ES access before restoring our own stack after DOS EXEC.
 jc exec_bad
 mov byte ptr cs:exec_ok,1
 jmp short restore_stack
exec_bad:
 mov cs:exec_error,ax
restore_stack:
 cli
 mov ax,cs:saved_ss
 mov ss,ax
 mov sp,cs:saved_sp
 push word ptr cs:saved_flags
 popf
 push cs
 pop ds
 push cs
 pop es
 cmp byte ptr exec_ok,0
 je exec_failed
 mov ah,4dh
 int 21h
 mov child_status,ax
 mov exit_code,al
 mov byte ptr outcome,1
 jmp short cleanup
exec_failed:
 mov byte ptr exit_code,0ffh
 mov byte ptr outcome,2
cleanup:
 ; Current mode/page is enough for our known mode09-to-mode03 contract.
 ; Already text3/page0 keeps child error text intact. Custom palette/screen
 ; restoration is outside this prototype's supported starting state.
 mov ah,0fh
 int 10h
 cmp al,3
 jne reset_text
 cmp bh,0
 je after_cleanup
reset_text:
 mov byte ptr cleanup_action,1
 mov ax,3
 int 10h
after_cleanup:
 mov ah,0fh
 int 10h
 mov post_mode,ax
 mov post_page,bx
 call reservation
 jc damaged
 cmp ax,owner_before
 jne damaged
 mov owner_after,ax
 jmp short report
damaged:
 mov byte ptr outcome,3
 mov byte ptr exit_code,0f3h
 jmp short report
resize_fail:
 mov exec_error,ax
 mov byte ptr outcome,4
 mov byte ptr exit_code,0f2h
 jmp short report
refuse:
 mov byte ptr outcome,5
 mov byte ptr exit_code,0f1h
report:
 ; Original wrapper's telemetry, not executable child pointers.
 push cs
 pop ds
 mov dx,offset logfile
 xor cx,cx
 mov ah,3ch
 int 21h
 jc exit_dos
 mov bx,ax
 mov dx,offset outcome
 mov cx,21
 mov ah,40h
 int 21h
 mov ah,3eh
 int 21h
exit_dos:
 mov al,exit_code
 mov ah,4ch
 int 21h
reservation proc near
 ; Read-only validation of the exact owned TSR and shared-video reservation.
 mov ax,97ffh
 mov es,ax
 cmp byte ptr es:[0],'Z'
 jne invalid
 cmp word ptr es:[3],400h
 jne invalid
 mov ax,es:[1]
 cmp ax,50h
 jb invalid
 cmp ax,97ffh
 jae invalid
 mov bp,ax
 dec ax
 mov es,ax
 cmp byte ptr es:[0],'M'
 jne invalid
 cmp word ptr es:[1],bp
 jne invalid
 cmp word ptr es:[3],111
 jne invalid
 mov ax,bp
 add ax,111
 jc invalid
 cmp ax,97ffh
 ja invalid
 mov es,bp
 cmp word ptr es:[103h],4e54h
 jne invalid
 cmp word ptr es:[105h],5944h
 jne invalid
 cmp word ptr es:[107h],5352h
 jne invalid
 cmp word ptr es:[109h],3130h
 jne invalid
 cmp word ptr es:[10bh],9800h
 jne invalid
 cmp word ptr es:[10dh],400h
 jne invalid
 mov ax,bp
 clc
 ret
invalid:
 stc
 ret
reservation endp
; 21-byte record: outcome byte, exit byte, cleanup byte, 9 words below.
outcome db 0
exit_code db 0
cleanup_action db 0
start_mode dw 0
start_page dw 0
owner_before dw 0
exec_error dw 0
child_status dw 0ffffh
post_mode dw 0
post_page dw 0
owner_after dw 0
saved_flags dw 0
exec_ok db 0
saved_ss dw 0
saved_sp dw 0
params dw 0,offset tail,0,5ch,0,6ch,0
ifdef GUIFIX
tail db 22,' /R C:\EXJOY.EXE /test',13
else
tail db 3,' /R',13
endif
child db 'XTTEST.COM',0
logfile db 'WRAP.BIN',0
db 512 dup(0)
stack_end label byte
code ends
end entry
