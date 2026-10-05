from pathlib import Path
import json, argparse, subprocess, os
parser=argparse.ArgumentParser(description='Execute the actual staged Trial5 validation gate with 62 rejection/ABI cases under DOSBox-X; not a full renderer test.')
parser.add_argument('--build',type=Path,required=True,help='160x200x16 candidate build output')
parser.add_argument('--repo',type=Path,required=True,help='authorized MASM/LINK toolchain repository')
parser.add_argument('--dosbox',type=Path,required=True)
parser.add_argument('--out',type=Path,required=True)
a=parser.parse_args()
if a.out.exists():raise SystemExit('Choose fresh output directory')
root=a.out.resolve();src=(a.build/'renderer/EGA/TSOFT.ASM').read_text()
helper=src[src.index('or_require macro'):src.index('cProc TOutput,')]
gate=src[src.index('    pushf\n',src.index('cProc TOutput,')):src.index('    cCall Output,<',src.index('cProc TOutput,'))]
# Variables are private to this standalone semantic harness, no production edits.
base='''.8086
code segment para public 'CODE'
assume cs:code,ds:code,es:nothing,ss:stackseg
SCREEN_WIDTH equ 160
SCREEN_HEIGHT equ 200
SCREEN_W_BYTES equ 20
'''+helper+'''
start:
 mov ax,code
 mov ds,ax
 mov es,ax
'''
cases=[]
def add(name,edits='',expected=1,flags=0x202):cases.append((name,edits,expected,flags))
add('count3 two border intervals')
add('count2 unchanged',' mov count,2\n')
add('count64 upper bound',' mov count,64\n')
for c in [0,1,65,16384,65535]:add('count fallback '+str(c),' mov count,'+str(c)+'\n',0)
for y in [0,199]:add('edge Y '+str(y),' mov pts+2,'+str(y)+'\n')
for y in [200,65535]:add('bad Y '+str(y),' mov pts+2,'+str(y)+'\n',0)
for name,ed in [('zero left',' mov pts+4,0\n'),('right bound',' mov pts+10,160\n'),('overlap unchanged',' mov pts+8,6\n'),('reversed interval order unchanged',' mov pts+4,120\n mov pts+6,122\n')]:add(name,ed)
for name,ed in [('left negative',' mov pts+4,65535\n'),('right too large',' mov pts+10,161\n'),('empty second',' mov pts+10,110\n'),('inverted second',' mov pts+10,109\n')]:add(name,ed,0)
for r in range(1,17):add('ROP2 '+str(r),' mov modes,'+str(r)+'\n')
for r in [0,17,65535]:add('bad ROP2 '+str(r),' mov modes,'+str(r)+'\n',0)
add('opaque background',' mov modes+2,2\n')
add('bad background',' mov modes+2,3\n',0)
add('pattern brush fallback',' mov brdata+40,3\n',0)
add('null brush solid pen',' mov word ptr brush,0\n mov word ptr brush+2,0\n')
add('null brush invalid pen',' mov word ptr brush,0\n mov word ptr brush+2,0\n mov pendata+4,5\n',0)
for field,size in [('points',12),('mode',32),('brush',54)]:
 add(field+' null',' mov word ptr '+field+',0\n mov word ptr '+field+'+2,0\n',0 if field!='brush' else 1)
 add(field+' 64K wrap',' mov word ptr '+field+',65530\n',0)
 add(field+' 20bit wrap',' mov word ptr '+field+',65530\n mov word ptr '+field+'+2,65535\n',0)
 add(field+' shadow alias',' mov word ptr '+field+',offset shadow_bits\n mov ax,seg shadow_bits\n mov word ptr '+field+'+2,ax\n',0)
add('clip ignored scanline',' mov word ptr clip,65535\n mov word ptr clip+2,65535\n')
add('memory destination',' mov dirty,0\n',0)
add('marker80 fallback',' mov style,80\n',0)
add('thin line unchanged',' mov style,18\n mov count,2\n mov pts,5\n mov pts+2,5\n mov pts+4,20\n mov pts+6,20\n')
add('thin count3 fallback',' mov style,18\n',0)
add('DF CF OF flags preserved','',1,0xe97)
for idx,(name,ed,expected,flags) in enumerate(cases):
 base+=' mov caseid,'+str(idx)+'\n call setup\n'+ed+' mov ax,'+str(flags)+'\n push ax\n popf\n call exercise\n'
 base+=' cmp outrows,'+str(expected)+'\n jne failjump'+str(idx)+'\n jmp next'+str(idx)+'\nfailjump'+str(idx)+':\n jmp failed\nnext'+str(idx)+':\n'
base+=''' mov dx,offset passed
 mov ah,9
 int 21h
 mov ax,4c00h
 int 21h
failed:
 cld
 mov dx,offset failure
 mov ah,9
 int 21h
 mov ax,4c01h
 int 21h
setup proc near
 cld
 mov ax,code
 mov ds,ax
 mov es,ax
 mov word ptr points,offset pts
 mov word ptr points+2,ax
 mov word ptr mode,offset modes
 mov word ptr mode+2,ax
 mov word ptr brush,offset brdata
 mov word ptr brush+2,ax
 mov word ptr pen,offset pendata
 mov word ptr pen+2,ax
 mov word ptr clip,0
 mov word ptr clip+2,0
 mov dirty,1
 mov outrows,0
 mov style,4
 mov count,3
 mov modes,13
 mov modes+2,1
 mov brdata+40,0
 mov pendata+4,0
 mov pts,0
 mov pts+2,50
 mov di,offset pts+4
 mov cx,64
initpts:
 mov ax,5
 stosw
 mov ax,7
 stosw
 loop initpts
 mov pts+8,110
 mov pts+10,112
 ret
setup endp
exercise proc near
 pushf
 pop expected_flags
 mov saved_sp,sp
 mov ax,1111h
 mov bx,2222h
 mov cx,3333h
 mov dx,4444h
 mov si,5555h
 mov di,6666h
 mov bp,7777h
'''+gate+'''
 pushf
 pop actual_flags
 cmp ax,1111h
 jne badregs
 cmp bx,2222h
 jne badregs
 cmp cx,3333h
 jne badregs
 cmp dx,4444h
 jne badregs
 cmp si,5555h
 jne badregs
 cmp di,6666h
 jne badregs
 cmp bp,7777h
 jne badregs
 mov ax,es
 mov bx,code
 cmp ax,bx
 jne badregs
 mov ax,ds
 cmp ax,bx
 jne badregs
 mov ax,actual_flags
 cmp ax,expected_flags
 jne badregs
 cmp sp,saved_sp
 jne badregs
 ret
badregs:
 jmp failed
exercise endp
passed db 'PASS GATE: '''+str(len(cases))+''' cases, flags, registers, segments and SP',13,10,'$'
failure db 'FAIL GATE',13,10,'$'
caseid dw 0
expected_flags dw 0
actual_flags dw 0
saved_sp dw 0
dirty dw 0
outrows dw 0
firstrow dw 0
lastrow dw 0
style dw 0
count dw 0
points dd 0
mode dd 0
brush dd 0
pen dd 0
clip dd 0
pts dw 130 dup(0)
modes dw 16 dup(0)
brdata dw 27 dup(0)
pendata dw 3 dup(0)
code ends
shadow segment para public 'SHADOW'
shadow_bits db 16000 dup(0)
shadow ends
stackseg segment para stack
 dw 1024 dup(?)
stackseg ends
end start
'''
p=root;p.mkdir(parents=True)
(p/'GATE.ASM').write_bytes(base.replace('\n','\r\n').encode())
(p/'CASES.JSON').write_text(json.dumps([x[0] for x in cases],indent=2))
(p/'BUILD.BAT').write_bytes(b'@ECHO OFF\r\nC:\\BIN\\MASM GATE.ASM,GATE.OBJ,GATE.LST; > BUILD.LOG\r\nC:\\BIN\\LINK4 GATE.OBJ,GATE.EXE,GATE.MAP; >> BUILD.LOG\r\nGATE.EXE > GATE.LOG\r\nEXIT\r\n')
(p/'RUN.CNF').write_text('[sdl]\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=0\nmemsizekb=640\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[dos]\nxms=false\nems=false\numb=false\n[autoexec]\nmount C "'+str(a.repo.resolve())+'"\nmount D "'+str(p)+'"\nD:\nBUILD.BAT\n')
env=os.environ.copy();env.update(SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy')
with (p/'HOST.LOG').open('w') as log:
 subprocess.run([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(p/'RUN.CNF')],env=env,stdout=log,stderr=subprocess.STDOUT,timeout=60,check=True)
log=(p/'BUILD.LOG').read_text();result=(p/'GATE.LOG').read_text()
if '0 Severe  Errors' not in log or 'PASS GATE: 62 cases' not in result:raise SystemExit('Gate test failed; inspect logs')
print(result.strip())
