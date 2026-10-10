; Original MIT test-only Setup keyboard controller. Never a runtime payload.
; Reads the active visible mode-3 text page, queues BIOS keys only while the queue is empty.
; No DOS/BIOS calls inside INT 1Ch, no disk writes in an interrupt, no graphics use.
; Install: SKCTRL 0..5. Remove/dump from DOS: SKCTRL /D. Maximum 40-second arm.
.8086
code segment para public 'CODE'
assume cs:code,ds:code
org 100h
public copy_latch,copy_token,foundoff,pageoff,pageend,observe,view,tick,row,phase,age,actions,armed,cool,qlen,qpos,queue,tracecount,trace,screen,resident_end
entry:
 jmp near ptr install
signature db 'SKY1'
JLONG macro condition,target
 local taken,done
 condition taken
 jmp short done
taken:
 jmp near ptr target
done:
endm
old1c dd 0
row db 0
phase db 0
age dw 0
actions dw 0
armed db 1
busy db 0
cool dw 0
qlen dw 0
qpos dw 0
queue dw 64 dup(0)
prompt_latch db 0
copy_latch db 0
foundoff dw 0
copy_token db 32 dup(0)
copy_next db 32 dup(0)
tracecount dw 0
trace db 256 dup(0)
pageoff dw 0
pageend dw 4000
observe db 0
view dw 4 dup(0ffffh)
view_name db 'C:\KEYVIEW.BIN',0
screen db 4000 dup(0)
main_msg db 'System Information',0
list_msg db 'Select a Display from the following list:',0
source_msg db 'Please insert your display driver disk',0
anysource_msg db 'Please insert',0
media_msg db 'Windows XT All-in-One',0
copy_msg db 'Copying',0
oem_msg db 'Tandy EX/HX 320x200 16 colors',0
config_msg db 'The new display driver you have chosen',0
trace_name db 'C:\KEYTRACE.BIN',0
screen_name db 'C:\KEYSCR.BIN',0

tick proc far
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
 cld
 push cs
 pop ds
 cmp busy,0
 JLONG jne,tickdone
 mov busy,1
 cmp armed,0
 JLONG je,tickclear
 inc age
 cmp age,728
 JLONG jae,expire
 mov ax,40h
 mov es,ax
 cmp byte ptr es:[49h],3
 JLONG jne,tickclear
 mov ax,es:[4eh]
 cmp ax,12384
 JLONG ja,tickclear
 mov pageoff,ax
 mov view+2,ax
 add ax,4000
 mov pageend,ax
 xor ax,ax
 mov al,es:[62h]
 mov view+4,ax
 mov ax,es:[49h]
 mov view,ax
 mov ax,age
 mov view+6,ax
 cmp cool,0
 je cooled
 dec cool
 jmp near ptr tickclear
cooled:
 cmp observe,0
 JLONG jne,observer
 mov bx,qpos
 cmp bx,qlen
 JLONG jb,inject
 mov qlen,0
 mov qpos,0
 mov ax,0b800h
 mov es,ax
 cmp phase,4
 jb dispatch
 cmp phase,6
 ja dispatch
 call copycheck
 cmp ax,2
 JLONG je,changed
 cmp ax,1
 JLONG je,tickclear
dispatch:
 cmp phase,0
 je mainfirst
 cmp phase,1
 JLONG je,displaylist
 cmp phase,2
 JLONG je,sourcefirst
 cmp phase,3
 JLONG je,oemlist
 cmp phase,4
 JLONG je,mainsecond
 cmp phase,5
 JLONG je,configpage
 cmp phase,6
 JLONG je,latersource
 jmp near ptr tickclear
observer:
 mov ax,0b800h
 mov es,ax
 mov si,offset main_msg
 call findtext
 JLONG jnc,tickclear
 call snapshot
 mov armed,0
 jmp near ptr tickclear
mainfirst:
 mov si,offset main_msg
 call findtext
 JLONG jnc,tickclear
 mov ax,4800h
 mov cx,6
 call repeatkey
 mov ax,1c0dh
 call addkey
 mov phase,1
 jmp near ptr changed
displaylist:
 mov si,offset list_msg
 call findtext
 JLONG jnc,tickclear
 mov ax,5000h
 mov cx,40
 call repeatkey
 mov ax,1c0dh
 call addkey
 mov phase,2
 jmp near ptr changed
sourcefirst:
 mov si,offset source_msg
 call findtext
 JLONG jnc,tickclear
 call pathkeys
 mov phase,3
 jmp near ptr changed
oemlist:
 mov si,offset oem_msg
 call findtext
 JLONG jnc,tickclear
 mov ax,4800h
 mov cx,6
 call repeatkey
 xor cx,cx
 mov cl,row
 mov ax,5000h
 call repeatkey
 mov ax,1c0dh
 call addkey
 mov phase,4
 jmp near ptr changed
mainsecond:
 mov si,offset main_msg
 call findtext
 JLONG jnc,tickclear
 mov ax,5000h
 mov cx,6
 call repeatkey
 mov ax,1c0dh
 call addkey
 mov phase,5
 jmp near ptr changed
configpage:
 mov si,offset config_msg
 call findtext
 JLONG jnc,tickclear
 mov ax,5000h
 mov cx,2
 call repeatkey
 mov ax,1c0dh
 call addkey
 mov phase,6
 jmp near ptr changed
latersource:
 mov si,offset anysource_msg
 call findtext
 jc laterfound
 mov prompt_latch,0
 jmp near ptr tickclear
laterfound:
 cmp prompt_latch,0
 JLONG jne,tickclear
 mov prompt_latch,1
 call pathkeys
 jmp near ptr changed
changed:
 inc actions
 call snapshot
 mov cool,9
 jmp near ptr tickclear
inject:
 ; Only write the normal 1Eh..3Ch BIOS ring, and only when empty.
 mov di,es:[1ch]
 cmp di,es:[1ah]
 JLONG jne,tickclear
 cmp di,1eh
 JLONG jb,tickclear
 cmp di,3ch
 JLONG ja,tickclear
 test di,1
 JLONG jnz,tickclear
 mov ax,queue[bx]
 mov es:[di],ax
 add di,2
 cmp di,3eh
 jb tailok
 mov di,1eh
tailok:
 mov es:[1ch],di
 add qpos,2
 mov cool,1
 jmp near ptr tickclear
expire:
 mov phase,99
 call snapshot
 mov armed,0
tickclear:
 mov busy,0
tickdone:
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
 jmp dword ptr cs:old1c
tick endp

findtext proc near
 ; DS:SI zero-terminated ASCII; ES mode-3 framebuffer. Carry = found.
 push ax
 push bx
 push cx
 push dx
 push di
 push si
 mov di,pageoff
scan:
 mov bx,si
 mov dx,di
compare:
 mov al,[bx]
 or al,al
 jz found
 cmp dx,pageend
 jae missed
 push di
 mov di,dx
 cmp al,es:[di]
 pop di
 jne missed
 inc bx
 add dx,2
 jmp short compare
missed:
 add di,2
 cmp di,pageend
 jb scan
 clc
 jmp short finddone
found:
 mov foundoff,di
 stc
finddone:
 pop si
 pop di
 pop dx
 pop cx
 pop bx
 pop ax
 ret
findtext endp
copycheck proc near
 ; Return AX=0 absent, 1 same copy prompt, 2 newly queued copy path.
 ; Require all three observed strings; compare a bounded 32-character footer.
 ; VRAM is read-only. No DOS/BIOS calls and no change to Setup phase.
 push bx
 push cx
 push dx
 push si
 push di
 mov si,offset anysource_msg
 call findtext
 jnc copyabsent
 mov si,offset media_msg
 call findtext
 jnc copyabsent
 mov si,offset copy_msg
 call findtext
 jnc copyabsent
 mov di,foundoff
 xor bx,bx
 mov cx,32
copyread:
 xor ax,ax
 cmp di,pageend
 jae copypadded
 mov al,es:[di]
 add di,2
copypadded:
 mov copy_next[bx],al
 inc bx
 loop copyread
 cmp copy_latch,0
 je copynew
 xor bx,bx
 mov cx,32
copycompare:
 mov al,copy_next[bx]
 cmp al,copy_token[bx]
 jne copynew
 inc bx
 loop copycompare
 mov ax,1
 jmp short copydone
copynew:
 xor bx,bx
 mov cx,32
copyremember:
 mov al,copy_next[bx]
 mov copy_token[bx],al
 inc bx
 loop copyremember
 mov copy_latch,1
 call pathkeys
 mov ax,2
 jmp short copydone
copyabsent:
 mov copy_latch,0
 xor ax,ax
copydone:
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 ret
copycheck endp

addkey proc near
 push bx
 mov bx,qlen
 cmp bx,128
 jae noadd
 mov queue[bx],ax
 add qlen,2
noadd:
 pop bx
 ret
addkey endp
repeatkey proc near
 jcxz repeated
againkey:
 call addkey
 loop againkey
repeated:
 ret
repeatkey endp
pathkeys proc near
 mov ax,4700h
 call addkey
 mov ax,5300h
 mov cx,16
 call repeatkey
 ; Direct BIOS ASCII, independent of host keyboard layout/scancode timing.
 mov ax,0043h
 call addkey
 mov ax,003ah
 call addkey
 mov ax,005ch
 call addkey
 mov ax,0057h
 call addkey
 mov ax,0049h
 call addkey
 mov ax,004eh
 call addkey
 mov ax,0058h
 call addkey
 mov ax,0054h
 call addkey
 mov ax,1c0dh
 call addkey
 ret
pathkeys endp
snapshot proc near
 push ax
 push bx
 push cx
 push dx
 push si
 push di
 push ds
 push es
 mov bx,tracecount
 cmp bx,32
 jae shot
 mov cl,3
 shl bx,cl
 xor ax,ax
 mov al,phase
 mov trace[bx],al
 mov al,row
 mov trace[bx+1],al
 mov ax,age
 mov word ptr trace[bx+2],ax
 mov ax,qlen
 mov word ptr trace[bx+4],ax
 mov ax,actions
 mov word ptr trace[bx+6],ax
 inc tracecount
shot:
 mov ax,0b800h
 mov ds,ax
 push cs
 pop es
 mov si,cs:pageoff
 mov di,offset screen
 mov cx,2000
 rep movsw
 pop es
 pop ds
 pop di
 pop si
 pop dx
 pop cx
 pop bx
 pop ax
 ret
snapshot endp
resident_end label byte

install:
 push cs
 pop ds
 cmp byte ptr ds:[80h],2
 JLONG jb,badargs
 cmp byte ptr ds:[82h],'/'
 je dump
 mov al,ds:[82h]
 sub al,'0'
 cmp al,6
 JLONG ja,badargs
 mov row,al
 cmp al,6
 jne active_install
 mov observe,1
active_install:
 mov ax,351ch
 int 21h
 mov word ptr old1c,bx
 mov word ptr old1c+2,es
 mov dx,offset tick
 mov ax,251ch
 int 21h
 ; Free only this test helper's inherited DOS environment before staying resident.
 mov ax,ds:[2ch]
 or ax,ax
 jz stay
 mov es,ax
 mov ah,49h
 int 21h
 mov word ptr ds:[2ch],0
stay:
 mov dx,offset resident_end
 add dx,15
 mov cl,4
 shr dx,cl
 mov ax,3100h
 int 21h
badargs:
 mov ax,4c02h
 int 21h
dump:
 cmp byte ptr ds:[83h],'D'
 JLONG jne,badargs
 mov ax,351ch
 int 21h
 cmp word ptr es:[103h],4b53h
 JLONG jne,badargs
 cmp word ptr es:[105h],3159h
 JLONG jne,badargs
 mov bp,es
 mov al,es:phase
 mov cs:result,al
 mov byte ptr es:armed,0
 mov dx,word ptr es:old1c
 mov ax,word ptr es:old1c+2
 push ds
 mov ds,ax
 mov ax,251ch
 int 21h
 pop ds
 push ds
 mov ds,bp
 mov dx,offset trace_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JLONG jc,dumpfailed
 mov bx,ax
 mov dx,offset row
 mov cx,8
 mov ah,40h
 int 21h
 JLONG jc,dumpclosefail
 cmp ax,8
 JLONG jne,dumpclosefail
 mov dx,offset trace
 mov cx,256
 mov ah,40h
 int 21h
 JLONG jc,dumpclosefail
 cmp ax,256
 JLONG jne,dumpclosefail
 mov ah,3eh
 int 21h
 mov dx,offset screen_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JLONG jc,dumpfailed
 mov bx,ax
 mov dx,offset screen
 mov cx,4000
 mov ah,40h
 int 21h
 JLONG jc,dumpclosefail
 cmp ax,4000
 JLONG jne,dumpclosefail
 mov ah,3eh
 int 21h
 mov dx,offset view_name
 xor cx,cx
 mov ah,3ch
 int 21h
 JLONG jc,dumpfailed
 mov bx,ax
 mov dx,offset view
 mov cx,8
 mov ah,40h
 int 21h
 JLONG jc,dumpclosefail
 cmp ax,8
 JLONG jne,dumpclosefail
 mov ah,3eh
 int 21h
 pop ds
 mov es,bp
 mov ah,49h
 int 21h
 JLONG jc,badargs
 mov al,result
 cmp al,6
 jne notcomplete
 mov ax,4c00h
 int 21h
notcomplete:
 mov ax,4c01h
 int 21h
dumpclosefail:
 mov ah,3eh
 int 21h
dumpfailed:
 pop ds
 mov ax,4c02h
 int 21h
result db 0
code ends
end entry
