from pathlib import Path
r=Path(__file__).resolve().parent; b=r/'base'; w=r/'work'
def edit(n,fn):
 s=(b/n).read_text();s=fn(s);(w/n).write_bytes(s.replace('\n','\r\n').encode())
data='''
; Tandy 1000 EX adaptation, 2026. Canonical scan is latched for each
; physical key until break, so releasing Shift first cannot stick a key.
public TandyLatch, TandyExtended
TandyLatch db 128 dup (0)
TandyExtended db 0
TandyMap label byte
'''
mp=list(range(128))
for a,v in {0x29:0xc8,0x2b:0xcb,0x4a:0xd0,0x4e:0xcd,0x53:0x4a,0x54:0x64,0x55:0x4e,0x56:0x53,0x57:0x9c,0x58:0xc7,0x59:0x57,0x5a:0x58}.items():mp[a]=v
for i in range(0,128,16):data+=' db '+','.join('0%02xh'%x for x in mp[i:i+16])+'\n'
routine='''
; Input raw AL; output canonical AL, preserving hardware break bit.
; Scan 60..63 are private character keys for Tandy's shifted keypad
; legends (backslash, vertical bar, tilde, grave). They are never IRQ
; commands and are decoded by ToAscii. No AT controller commands used.
TandyNormalize proc near
 assumes ds,DATA
 assumes es,RAMBIOS
 push bx
 push dx
 mov dl,al
 xor bh,bh
 mov bl,al
 and bl,7fh
 mov al,TandyLatch[bx]
 or al,al
 jnz tnLatched
 mov al,TandyMap[bx]
 test dl,80h
 jnz tnFinish
 cmp bl,46h
 jne tnNotHold
 test byte ptr es:[kb_flag],fCtrl
 jz tnSave
 mov al,64h
 jmp short tnSave
tnNotHold:
 cmp bl,53h
 jne tnNotDelete
 test byte ptr es:[kb_flag],fShift+fCtrl+fAlt
 jz tnSave
 mov al,53h
 jmp short tnSave
tnNotDelete:
 cmp bl,55h
 jne tnNotInsert
 test byte ptr es:[kb_flag],fShift
 jz tnSave
 mov al,52h
 jmp short tnSave
tnNotInsert:
 test byte ptr es:[kb_flag],fCtrl+fAlt
 jnz tnSave
 test byte ptr es:[kb_flag],fShift
 jz tnSave
 cmp bl,47h
 jne tnBar
 mov al,60h
 jmp short tnSave
tnBar:
 cmp bl,4bh
 jne tnTilde
 mov al,61h
 jmp short tnSave
tnTilde:
 cmp bl,48h
 jne tnGrave
 mov al,62h
 jmp short tnSave
tnGrave:
 cmp bl,50h
 jne tnSave
 mov al,63h
tnSave:
 mov TandyLatch[bx],al
tnLatched:
 test dl,80h
 jz tnFinish
 mov TandyLatch[bx],0
tnFinish:
 mov TandyExtended,0
 test al,80h
 jz tnNotExt
 mov TandyExtended,1
tnNotExt:
 and al,7fh
 and dl,80h
 or al,dl
 pop dx
 pop bx
 ret
TandyNormalize endp
'''
def trap(s):
 s=s.replace('sEnd DATA\n',data+'\nsEnd DATA\n',1)
 s=s.replace('public keybd_int\nkeybd_int',routine+'\npublic keybd_int\nkeybd_int',1)
 s=s.replace('\tin\tal,kb_data\t\t; get the scan code','\tin\tal,kb_data\t\t; get the scan code\n\tcall TandyNormalize',1)
 s=s.replace('\tmov\tfExtend, bh','\tor bh,TandyExtended\n\tmov\tfExtend, bh',1)
 s=s.replace('CheckNumPad:\n','CheckNumPad:\n\tcmp TandyExtended,0\n\tje tnNotDedicated\n\tjmp kbi4\ntnNotDedicated:\n',1)
 s=s.replace('\ttest\tbyte ptr es:[kb_flag],fCtrl\t; is it Ctrl?', '\tcmp al,46h\n\tjne tnNotPlainHold\n\tmov bx,ax\n\tmov al,VK_OEM_SCROLL\n\tjmp kbi4\ntnNotPlainHold:\n\ttest\tbyte ptr es:[kb_flag],fCtrl\t; is it Ctrl?',1)
 s=s.replace('kbi2:\txor\tbx,bx','kbi2:\n\tcmp al,64h\n\tjne tnNotBreak\n\tmov bx,ax\n\ttest ah,80h\n\tjz tnBreakSend\n\tcall CtlBrkCase\ntnBreakSend:\n\tmov al,VK_CANCEL\n\tjmp kbi4\ntnNotBreak:\n\txor\tbx,bx',1)
 return s
edit('TRAP.ASM',trap)
def tabs(s):
 needle='\t; This is the end of the table for drivers handling Enhanced keyboards!'
 s=s.replace(needle,'''\tdb -1,-1,-1,-1,-1,-1,-1 ; 59..5f unused canonical scans
\tdb VK_OEM_5,VK_OEM_5,VK_OEM_3,VK_OEM_3 ; 60..63 Tandy glyphs
\tdb VK_CANCEL ; 64 dedicated Break
'''+needle)
 s=s.replace('\nKeyTypeFound:\n','\nKeyTypeFound:\n\tmov KeyType,1 ; EX hardware is XT-class, regardless of INI\n\tmov PCType,0ffh ; never attempt AT LEDs or typematic commands\n',1)
 s=s.replace('\tmov\tiqdNumFunc, bx','\tmov bx,12\n\tmov\tiqdNumFunc, bx',1)
 # US-only fixed internal tables: don't permit an unrelated DLL to overwrite.
 s=s.replace('LoadNewDll:\n','LoadNewDll:\n\tjmp CannotLoadDll\n',1)
 return s
edit('TABS.ASM',tabs)
def asc(s):
 needle='T1NotCtrlShift:\n'
 s=s.replace(needle,needle+'''\tcmp bl,60h
\tjb tnAsciiNormal
\tcmp bl,63h
\tja tnAsciiNormal
\ttest dh,6
\tjnz tnAsciiNormal
\tmov al,5ch
\tcmp bl,60h
\tje tnAsciiChar
\tmov al,7ch
\tcmp bl,61h
\tje tnAsciiChar
\tmov al,7eh
\tcmp bl,62h
\tje tnAsciiChar
\tmov al,60h
tnAsciiChar:
\tjmp ToAscGoodExit
tnAsciiNormal:
''',1)
 return s
edit('TOASCII.ASM',asc)
# Reset latch state before driver resumes hardware ownership.
def ena(s):
 s=s.replace('cBegin\tEnable\n','''cBegin Enable
\tpush ax
\tpush cx
\tpush di
\tpush es
\tpush ds
\tpop es
\txor ax,ax
\tmov di,offset TandyLatch
\tmov cx,128
\tcld
\trep stosb
\tpop es
\tpop di
\tpop cx
\tpop ax
''',1)
 s=s.replace('extrn\tKeyType:byte','extrn TandyLatch:byte\n\textrn\tKeyType:byte',1)
 return s
edit('ENABLE.ASM',ena)
# Follow-up integration corrections, all anchored against exact text.
def refine(n,fn):
 s=(w/n).read_text();s=fn(s);(w/n).write_bytes(s.replace('\n','\r\n').encode())
refine('TRAP.ASM',lambda s:s.replace('mov al,53h\n jmp short tnSave','mov al,0d3h\n jmp short tnSave').replace('mov al,52h\n jmp short tnSave','mov al,0d2h\n jmp short tnSave'))
def life(s):
 start=s.index('cBegin Enable\n')+len('cBegin Enable\n'); end=s.index('; Save away',start)
 clear=s[start:end];s=s[:start]+s[end:]
 return s.replace('ke_cont:\n','ke_cont:\n\tpushf\n\tcli\n'+clear+'\tpopf\n',1)
refine('ENABLE.ASM',life)
def tbl(s):
 s=s.replace('LoadOemAnsi:\n','LoadOemAnsi:\n\tjmp NewTableExit ; fixed US CP437 conversion tables\n',1)
 s=s.replace('\tja\tMapVkExit\t\t\t; exit with [AX] = 0 if too big','\tjae\tMapVkExit\t\t\t; reject one-past-end too')
 s=s.replace('DB\tVK_OEM_3    \t; 029h','DB\t-1          \t; 029h',1).replace('DB\tVK_OEM_5    \t; 02bh','DB\t-1          \t; 02bh',1)
 s=s.replace('DB\tVK_OEM_102\t; 056h', 'DB\t-1        \t; 056h',1)
 return s.replace('db VK_OEM_5,VK_OEM_5,VK_OEM_3,VK_OEM_3','db VK_OEM_5,VK_OEM_102,VK_OEM_3,VK_OEM_8')
refine('TABS.ASM',tbl)
# A different virtual key for each shifted glyph avoids ambiguous VkKeyScan.
def glyphvk(s):
 seq='\tmov ax,AnsiCode\n'
 for i,(ch,vk) in enumerate([(92,'VK_OEM_5'),(124,'VK_OEM_102'),(126,'VK_OEM_3'),(96,'VK_OEM_8')]):
  seq+=f'\tcmp al,{ch}\n\tjne tnVkNext{i}\n\tmov ax,0100h+{vk}\n\tjmp vkleave\ntnVkNext{i}:\n'
 return s.replace('cBegin\tVkKeyScan\n','cBegin\tVkKeyScan\n'+seq,1)
refine('TOASCII.ASM',glyphvk)
def oem(s):
 seq='\tmov al,OEMChar\n'
 for i,(ch,sc) in enumerate([(92,0x47),(124,0x4b),(126,0x48),(96,0x50)]):
  seq+=f'\tcmp al,{ch}\n\tjne tnOemNext{i}\n\tmov ax,{sc}\n\tmov dx,2\n\tjmp OemKeyExit\ntnOemNext{i}:\n'
 return s.replace('cBegin OemKeyScan\n','cBegin OemKeyScan\n'+seq,1)
edit('OEMSCAN.ASM',oem)
def names(s):
 seq='\tmov ax,lParamHi\n'
 for i,(sc,ch) in enumerate([(0x60,92),(0x61,124),(0x62,126),(0x63,96)]):
  seq+=f'\tcmp al,{sc}\n\tjne tnNameNext{i}\n\tmov al,{ch}\n\tjmp SaveSingleCharString\ntnNameNext{i}:\n'
 seq+='\tcmp al,64h\n\tjne tnNameNormal\n\tmov al,nPause\n\tjmp GetLocalString\ntnNameNormal:\n'
 return s.replace('nzstring:\n','nzstring:\n'+seq,1).replace('"Scroll Lock"','"Hold"').replace('"Pause"','"Break"')
edit('GETNAME.ASM',names)
def tab4(s):
 s=s.replace("VK_OEM_5    ,\t'\\',\t'|'", "VK_OEM_5    ,\t'\\',\t'\\'")
 s=s.replace("VK_OEM_102,\t'\\',\t'|'", "VK_OEM_102,\t'|',\t'|'")
 s=s.replace("VK_OEM_3    ,\t'`',\t'~'", "VK_OEM_3    ,\t'~',\t'~'")
 s=s.replace('VK_OEM_8    ,\t-1,\t-1', "VK_OEM_8    ,\t'`',\t'`'")
 return s
edit('TAB4.INC',tab4)
refine('TABS.ASM',lambda s:s.replace('\tmov\tselCS2DS, 0','\tmov\tselCS2DS, 0\n\tcld\n\tjmp KeyTypeFound ; fixed EX hardware, ignore incompatible INI types',1))
refine('GETNAME.ASM',lambda s:s.replace('\tjne zexit\t\t\t; exit if not found.','\tje tnNameFound\n\tjmp zexit\ntnNameFound:',1))
# Tandy has a dedicated Print key, not the XT keypad Multiply/Print key.
# Preserve the DDK screenshot callback convention (BX=1 screen, BX=0 Alt).
def prt(s):
 s=s.replace('\ttest\tbl,fCtrl\t\t; CTRL down? if so,\n\tjnz\tkbiNotPrint\t\t; This is no printscreen...!', '; Dedicated Tandy Print is valid without Shift and with Ctrl.',1)
 s=s.replace('\ttest\tbl,fShift+fAlt\t\t; is SHIFT or ALT down?\n\tjz\tkbiNotPrint', '; Dedicated Tandy Print needs no Shift modifier.',1)
 return s
refine('TRAP.ASM',prt)
refine('TABS.ASM',lambda s:s.replace('DB\tVK_MULTIPLY\t; 037h','DB\tVK_SNAPSHOT\t; 037h',1))
refine('GETNAME.ASM',lambda s:s.replace('"Num *"','"Print"',1))
