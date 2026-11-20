"""Check private graphics OEM choices and resource-only invariants; console output."""
from pathlib import Path
import importlib.machinery as M,re,struct,sys,zipfile
ROOT=Path(__file__).resolve().parents[2]
G=M.SourceFileLoader('check_viewports',str(ROOT/'tools/RESUI/GRAPHICS.PY')).load_module()
P=M.SourceFileLoader('check_packets',str(ROOT/'tools/SYSFONT/PACK.PY')).load_module()
I=M.SourceFileLoader('check_strikes',str(ROOT/'tools/SYSFONT/BUILD.PY')).load_module()

def check(folder):
 count=0
 for archive,root,source in P.PACKETS:
  with zipfile.ZipFile(folder/archive) as z:body={Path(n).name:z.read(n) for n in z.namelist()}
  with zipfile.ZipFile(ROOT/source) as z:old={Path(n).name:z.read(n) for n in z.namelist() if not n.startswith('FRESH640/')}
  text=body['OEMSETUP.INF'].decode('ascii');section='';groups={};displays=[]
  for line in text.splitlines():
   if line.strip().startswith('['):section=line.strip().lower();continue
   if line.lstrip().startswith(';'):continue
   fields=re.findall(r'"([^"]*)"',line)
   key=next((v for v in fields if re.fullmatch(r'\d+,\d+,\d+',v)),None)
   if not key:continue
   if section=='[display]':
    name=re.search(r':([A-Z0-9_]+\.DRV)',line,re.I)[1].upper();displays.append((name,key))
   elif section in ('[sysfonts]','[fixedfonts]','[oemfonts]'):
    name=re.search(r':([A-Z0-9_]+\.FON)',line,re.I)[1].upper();groups[section,key]=name
  for name,key in displays:
   for sect in ('[sysfonts]','[fixedfonts]','[oemfonts]'):assert (sect,key) in groups,(archive,name,sect,key)
   sysfont=groups['[sysfonts]',key];raw,_=I.strike(body[sysfont]);first=raw[95]
   wi=struct.unpack_from('<H',raw,118+4*(105-first))[0];ww=struct.unpack_from('<H',raw,118+4*(87-first))[0];assert wi<ww,(name,wi,ww)
   for sect in ('[fixedfonts]','[oemfonts]'):
    f=groups[sect,key]
    if f in old:reference=old[f]
    else:
     with zipfile.ZipFile(ROOT/'downloads/FRESH/CGA.ZIP') as z:reference=z.read('CGA/'+f)
    assert body[f]==reference,('Fixed/Terminal bytes changed',archive,f)
   if name in G.VIEWPORTS:
    # Deterministic independent reconstruction invokes segment/fixup checks.
    assert body[name]==(old[name] if name=='HPXY.DRV' else G.driver(old[name],G.VIEWPORTS[name])),('Resource reconstruction',name)
    targetfont,_,height,avg=G.profile(G.VIEWPORTS[name]);assert sysfont==targetfont,(name,sysfont,targetfont)
    rows=G.N.resources(body[name])[2];cfg=next(r['data'] for r in rows if (r['type'],r['id'])==(0xf006,0x8001))
    print(archive,name,'view='+str(G.VIEWPORTS[name]),sysfont,'i/W='+str((wi,ww)),'thumbs='+str(struct.unpack_from('<HH',cfg)))
   count+=1
  for n in body:assert not n.upper().endswith(('.JSN','.JSON','.SHA','.SUM')),n
 print('PASS',count,'OEM display entries; all selected System widths variable; fixed/Terminal bytes retained; all transformed segments, fixups, palettes and target aspect preserved')
if __name__=='__main__':check(Path(sys.argv[1]))
