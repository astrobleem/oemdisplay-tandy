"""Viewport-based graphics UI resources for ordinary OEM developer staging.

No renderer, mode, palette, guard or fixed-font bytes change.
Historical accepted inputs remain immutable. No records are generated.
"""
from pathlib import Path
import importlib.machinery as M,re,struct,zipfile
ROOT=Path(__file__).resolve().parents[2]
N=M.SourceFileLoader('viewport_ne',str(ROOT/'src/cga/CMPRSC.PY')).load_module()
# Physical viewport; panning desktops deliberately do not enter this table.
VIEWPORTS={
 'TANDY88.DRV':320,'TNDY6404.DRV':640,'TNDY3204.DRV':320,
 'TNDY160.DRV':160,'TNDY6402.DRV':640,'HPXY.DRV':320,
 'JRPAN.DRV':320,'TNDYJR.DRV':320,'CPPAN.DRV':320,'PCP3216.DRV':320,
 'PC1512.DRV':640,'TNDYV2.DRV':640,'PC1YAMA.DRV':160,'YAM160.DRV':160,
 'CGA640.DRV':640,'CGA32C.DRV':320}
# Already-compact or explicitly labelled legacy opt-ins.
RETAINED={'CGA100.DRV','CGAPAN.DRV','CGA64C.DRV','CGA320.DRV'}

def donor(width):
 packet='tools/FONTPACK/BIN/WINXT.ZIP' if width==640 else 'downloads/FRESH/CGA.ZIP'
 name='WINXT/HPXY.DRV' if width==640 else 'CGA/CGA100.DRV'
 with zipfile.ZipFile(ROOT/packet) as z:return N.resources(z.read(name))[2]

def profile(width):
 if width==640:return 'XTCSYS.FON','200,96,48',8,7
 if width==320:return 'UI6SYS.FON','200,48,48',6,4
 return 'CG1SYS.FON','200,48,40',5,3

def driver(original,width):
 old={(r['type'],r['id']):r for r in N.resources(original)[2]}
 small=[dict(r) for r in donor(width)]
 # CONFIG's first six words are UI sizes. Preserve the target's own aspect,
 # monochrome/color configuration and complete system-color table afterward.
 cfg=next(r for r in small if (r['type'],r['id'])==(0xf006,0x8001))
 cfg['data']=cfg['data'][:12]+old[0xf006,0x8001]['data'][12:]
 desc=next(r for r in small if (r['type'],r['id'])==(0xf006,0x8003))
 b=bytearray(old[0xf006,0x8003]['data']);pos=b.index(b'Helv')-18
 _,_,height,avg=profile(width);struct.pack_into('<HH',b,pos,height,avg)
 # Only the default variable application face descriptor follows UI height;
 # Terminal/Courier requests retain the target's original fixed-cell defaults.
 desc['data']=bytes(b)
 out,_=N.transplant(original,small)
 actual={(r['type'],r['id']):r['data'] for r in N.resources(out)[2]}
 assert actual[0xf006,0x8001][12:]==old[0xf006,0x8001]['data'][12:]
 assert actual[0xf006,0x8002]==old[0xf006,0x8002]['data'] # hardware palette
 assert actual[0xf006,0x8003][:pos]==old[0xf006,0x8003]['data'][:pos]
 return out

def apply(body):
 body=dict(body);text=body['OEMSETUP.INF'].decode('ascii');lines=text.splitlines()
 section='';newfonts={};display=[];output=[];converted=set()
 for line in lines:
  if line.strip().startswith('['):section=line.strip().lower()
  if section=='[display]' and not line.lstrip().startswith(';'):
   m=re.search(r':([A-Z0-9_]+\.DRV)',line,re.I)
   if m and m[1].upper() not in VIEWPORTS and m[1].upper() not in RETAINED:
    raise ValueError('Unmapped graphics UI profile: '+m[1])
   if m and m[1].upper() in VIEWPORTS:
    name=m[1].upper();width=VIEWPORTS[name];font,key,_,_=profile(width)
    if name not in body:raise ValueError('Missing selected graphics driver: '+name)
    if name not in converted:
     # HPXY already has compact chrome; retain its accepted identity for
     # FIXXT DISPLAY's existing guarded source/installation contract.
     if name!='HPXY.DRV':body[name]=driver(body[name],width)
     converted.add(name)
    fields=re.findall(r'"([^"]*)"',line)
    oldkey=next((s for s in fields if re.fullmatch(r'\d+,\d+,\d+',s)),None)
    if oldkey is None:raise ValueError('Missing display font group: '+name)
    line=line.replace('"'+oldkey+'"','"'+key+'"')
    newfonts[key]=font
    display.append((oldkey,key))
  # Preserve every unrelated descriptor/choice, including explicit CGA320L.
  output.append(line)
 if not display:return body
 # Windows 3.0 dialog templates also depend on the selected Fixed face.
 # Use the existing compact 4x6 companions for low viewports, retaining
 # their exact bytes and deliberate monospace. Wide profiles keep 8x8.
 for key,font in newfonts.items():
  if font=='XTCSYS.FON':continue
  for sect,companion in (('[fixedfonts]','CG1FIX.FON'),('[oemfonts]','CG1OEM.FON')):
   start=next(i for i,v in enumerate(output) if v.strip().lower()==sect)+1
   end=next((i for i in range(start,len(output)) if output[i].strip().startswith('[')),len(output))
   keep=[v for v in output[start:end] if '"'+key+'"' not in v]
   row='a:'+companion+',"Compact 4x6 '+('Fixed' if sect=='[fixedfonts]' else 'Terminal')+'","'+key+'"'+(',1' if sect=='[oemfonts]' else '')
   output[start:end]=keep+[row]
   with zipfile.ZipFile(ROOT/'downloads/FRESH/CGA.ZIP') as z:body[companion]=z.read('CGA/'+companion)
 start=next(i for i,s in enumerate(output) if s.strip().lower()=='[sysfonts]')+1
 end=next((i for i in range(start,len(output)) if output[i].strip().startswith('[')),len(output))
 existing=[s for s in output[start:end] if not any('"'+key+'"' in s for key in newfonts)]
 output[start:end]=existing+['a:'+font+',"Viewport proportional System","'+key+'"' for key,font in sorted(newfonts.items())]
 for font in newfonts.values():
  if font=='UI6SYS.FON':
   U=M.SourceFileLoader('viewport_ui6',str(ROOT/'tools/RESUI/UI6.PY')).load_module();body[font]=U.build()
  else:body[font]=(ROOT/'tools/SYSFONT/BIN'/font).read_bytes()
 body['OEMSETUP.INF']=('\r\n'.join(output)+'\r\n').encode('ascii')
 return body
