"""Stage an isolated mode-03 presenter over the canonical 640x200 mono profile."""
from pathlib import Path
def read(p): return p.read_bytes().replace(b'\r\n',b'\n').decode('latin1')
def write(p,s): p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))

def port(renderer,resources,repo):
 p=renderer/'EGA/TSOFT.ASM';s=read(p)
 s=s.replace('incDevice=1','incDevice=1\nincFont=1\nincDrawMode=1')
 s=s.replace('sBegin Data\npublic enabled_flag', '''createSeg _TXCACHE,TextCache,word,public,DATA
sBegin TextCache
tx_cache db 16000 dup (255)
sEnd TextCache

sBegin Data
tx_first dw 1
tx_keeptext dw 0
tx_overlay dw 2000 dup (0)
tx_tile db 8 dup (0)
tx_font db 1024 dup (0)
tx_heads db 256 dup (255)
tx_links db 128 dup (255)
tx_source dw 0
tx_cachepos dw 0
tx_screen dw 0
tx_col dw 0
tx_row dw 0
tx_best dw 0
tx_score dw 0
tx_char db 0
tx_attr db 0
tx_inverse db 0
tx_pop db '''+'\n db '.join(','.join(str(i.bit_count()) for i in range(j,j+32)) for j in range(0,256,32))+'''
tx_shapes db 32,0,0,0,0,0,0,0,0
 db 219,255,255,255,255,255,255,255,255
 db 223,255,255,255,255,0,0,0,0
 db 220,0,0,0,0,255,255,255,255
 db 221,240,240,240,240,240,240,240,240
 db 222,15,15,15,15,15,15,15,15
 db 196,0,0,0,255,0,0,0,0
 db 179,24,24,24,24,24,24,24,24
 db 197,24,24,24,255,24,24,24,24
public enabled_flag''')
 a=s.index('public FlushShadow\n');b=s.index('\n; Translate a screen argument',a)
 s=s[:a]+read(repo/'src/tandysw/TEXTPRES.ASM')+s[b:]
 # The staged mono profile sets mode 06 and a graphics palette. Replace all.
 a=s.index('    mov ax,0006h\n');b=s.index('    mov ax,seg shadow_bits',a)
 s=s[:a]+'''    mov ax,0003h
    int 10h
    ; Hide BIOS hardware cursor; Windows cursor is an exact cell overlay.
    mov ah,1
    mov cx,2000h
    int 10h
    call TxInit
'''+s[b:]
 # Preserve the GDI bitmap and mirror printable text into hardware cells.
 for label in ('TStrBlt','TExtTextOut'):
  needle='    call FlushShadow\n'+label+'_done:'
  s=s.replace(needle,'    mov tx_keeptext,1\n    call FlushShadow\n    push ax\n    push dx\n    cCall TxString,<x,y,clip,string,count,font,mode>\n    pop dx\n    pop ax\n    mov tx_keeptext,0\n'+label+'_done:')
 s=s.replace('cProc TStrBlt,',read(repo/'src/tandysw/TXTEXT.ASM')+'\ncProc TStrBlt,')
 # Init helper resides in Code, called FAR from init.
 write(p,s)
 p=renderer/'EGA/TCURSOR.ASM';s=read(p)
 a=s.index('; AX = Y');b=s.index('; Caller owns tc_busy',a)
 s=s[:a]+''' ; Cell cursor overlay. Only one saved B800 word; canonical pixels untouched.
tc_erase proc near
    cmp tc_drawn,0
    je txce_done
    mov tc_drawn,0
    cmp enabled_flag,0
    je txce_done
    mov ax,0b800h
    mov es,ax
    mov di,tc_row_offset
    mov ax,word ptr tc_saved
    mov es:[di],ax
txce_done:
    ret
tc_erase endp

tc_draw proc near
    cmp enabled_flag,0
    je txcd_done
    cmp tc_have,0
    je txcd_done
    ; Use the pointer hotspot, not the upper-left of an arbitrary cursor bitmap.
    mov ax,tc_y
    cmp ax,200
    jae txcd_done
    shr ax,1
    shr ax,1
    shr ax,1
    mov bx,160
    mul bx
    mov di,ax
    mov ax,tc_x
    cmp ax,640
    jae txcd_done
    shr ax,1
    shr ax,1
    shr ax,1
    shl ax,1
    add di,ax
    mov tc_row_offset,di
    mov ax,0b800h
    mov es,ax
    mov ax,es:[di]
    mov word ptr tc_saved,ax
    xor ah,77h
    mov es:[di],ax
    mov tc_drawn,1
txcd_done:
    ret
tc_draw endp

'''+s[b:]
 write(p,s)
 return {'hardware':'BIOS 03h, B800:0000..0F9F 80x25 cells','canonical':'640x200 four-plane 64000-byte monochrome shadow','cache_bytes':16000,'matcher':'exact ROM ASCII hash chains, nine CP437 geometric fallbacks','cursor':'single saved cell overlay','status':'experimental, no readability promise'}
