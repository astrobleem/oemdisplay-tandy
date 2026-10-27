"""Two-axis software framebuffer: 640x400 through 320x200, 8086 only.

Reuse split-band GDI and rectangle conversion; never program a pan start address.
The PCjr physical video page and ColorPlus plane format remain adapter-specific.
"""
from pathlib import Path
import importlib.machinery
ROOT=Path(__file__).resolve().parents[2]
def load(n,p):return importlib.machinery.SourceFileLoader(n,str(ROOT/p)).load_module()
def one(s,a,b):
 if s.count(a)!=1:raise ValueError('PANXY anchor differs: '+a[:65]+' count='+str(s.count(a)))
 return s.replace(a,b)
def patch_staged(ega,adapter='pcjr'):
 ega=Path(ega);renderer=ega.parent
 original_cursor=(ega/'TCURSOR.ASM').read_bytes().decode('latin1')
 load('panxy_existing_split','experiments/XYPAN/XYPATCH.PY').patch(renderer)
 p=ega/'TSOFT.ASM';s=p.read_text(encoding='latin1')
 s=one(s,'SCREEN_HEIGHT equ 256','SCREEN_HEIGHT equ 400')
 s=one(s,'shadow_tail db 17920 dup (0)','shadow_tail db 64000 dup (0)')
 for typ in (0,1):s=one(s,f'BITMAP <{typ},640,256,80,4,1,0,20480',f'BITMAP <{typ},640,400,80,4,1,0,32000')
 s=one(s,'480,230,640,256','480,360,640,400')
 s=one(s,'    mov cx,8960','    mov cx,32000')
 s=one(s,'    mov word ptr es:[di+10],256','    mov word ptr es:[di+10],400')
 # Keep only the canonical software rectangle converter. Stage/CRTC code is absent.
 a=s.index('; Task-time rectangle conversion.');b=s.index('; Translate a screen argument',a)
 copy=(ROOT/'experiments/XYPAN/XYCOPY.ASM').read_text()
 copy=copy[:copy.index('; Commit the same already-clipped rectangle')]
 copy=one(copy,'    mov bx,256','    mov bx,400')
 code=(ROOT/'src/panxy/PRESENT.ASM').read_text()
 s=s[:a]+copy+'\n'+code+'\n'+s[b:]
 # A software backend has no hardware stats/readback export.
 p.write_bytes(s.replace('\n','\r\n').encode('latin1'))
 p=renderer/'SDIB88.ASM';s=p.read_text(encoding='latin1');s=one(s,'    cmp bx,256\n    jle sd_clip_bottom\n    mov bx,256\n','    cmp bx,400\n    jle sd_clip_bottom\n    mov bx,400\n');p.write_bytes(s.replace('\n','\r\n').encode('latin1'))
 p=ega/'TSOFT.DEF';s=p.read_text();s=s.replace(' XYRows @108\n','').replace(' HpStats @106\n','');s=s.replace('HPXY 640x256 logical / 320x200 viewport PRIVATE','Panning 640x400 desktop / 320x200 software view');p.write_bytes(s.replace('\n','\r\n').encode())
 p=ega/'TCURSOR.ASM';tc=p.read_bytes().decode('latin1')
 if adapter=='pcjr':
  jr=load('panxy_pcjr','src/pcjr/JRPATCH.PY');p=ega/'TSOFT.ASM';s=p.read_bytes().decode('latin1')
  s=jr.patch_v1(s,s.count('    mov ax,0b800h\r\n    mov es,ax\r\n'));p.write_bytes(s.encode('latin1'));tc=jr.patch_tc(tc)
 elif adapter=='colorplus':
  pcp=load('panxy_colorplus','src/pcp/PCPPATCH.PY');p=ega/'TSOFT.ASM';s=p.read_bytes().decode('latin1').replace('\r\n','\n')
  macros=pcp.CONVERT_MACROS.replace('pp_half 0,40','pp_half 0,80').replace('pp_half 80,120','pp_half 160,240')
  s=one(s,'; Task-time rectangle conversion.',macros.replace('\r\n','\n')+pcp.spread_table_text().replace('\r\n','\n')+'; Task-time rectangle conversion.')
  a=s.index('xyc_group:');b=s.index('    cmp word ptr ss:[bp-18],0',a)
  s=s[:a]+'xyc_group:\n    pp_byte\n'+s[b:]
  s=one(s,'    and di,3\n','    and di,1\n')
  s=one(s,'    shr ax,1\n    shr ax,1\n    mov cx,160','    shr ax,1\n    mov cx,80')
  s=one(s,'    shl ax,1\n    shl ax,1\n    add di,ax','    shl ax,1\n    add di,ax')
  s=one(s,pcp.ENABLE_OLD.replace('\r\n','\n'),pcp.ENABLE_NEW.replace('\r\n','\n'))
  s=one(s,pcp.DISABLE_OLD.replace('\r\n','\n'),pcp.DISABLE_NEW.replace('\r\n','\n'))
  p.write_bytes(s.replace('\n','\r\n').encode('latin1'))
  tc=pcp.patch_tcursor(original_cursor).replace('\r\n','\n')
  tc=one(tc,'    externB enabled_flag\n','    externB enabled_flag\n    externW hp_left\n    externW hp_top\n')
  tc=one(tc,'    sub ax,tc_hot_x\n','    sub ax,tc_hot_x\n    sub ax,hp_left\n')
  tc=one(tc,'    sub ax,tc_hot_y\n','    sub ax,tc_hot_y\n    sub ax,hp_top\n')
  a=tc.index('cursor_begin_retain proc far');b=tc.index('cursor_begin_retain endp',a)
  tc=tc[:a]+'cursor_begin_retain proc far\n    pushf\n    mov word ptr ss:[si],0\n    popf\n    retf\n'+tc[b:]
  tc=tc.replace('\n','\r\n')
 else:raise ValueError('Unsupported adapter')
 (ega/'TCURSOR.ASM').write_bytes(tc.encode('latin1'))
 return {p.name:p.read_bytes().decode('latin1') for p in (ega/'TSOFT.ASM',ega/'TCURSOR.ASM',renderer/'SDIB88.ASM',ega/'TSOFT.DEF')}
