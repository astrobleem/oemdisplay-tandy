"""Console-only audit of current shipping OEM choices, System advances and chrome."""
from pathlib import Path
import zipfile,struct,importlib.machinery as M,re
ROOT=Path(__file__).resolve().parents[2]
P=M.SourceFileLoader('ui_packets',str(ROOT/'tools/SYSFONT/PACK.PY')).load_module()
I=M.SourceFileLoader('ui_inspect',str(ROOT/'tools/XTFONTS/INSPECT.PY')).load_module()
N=M.SourceFileLoader('ui_resources',str(ROOT/'src/cga/CMPRSC.PY')).load_module()
def font(data):
 r=next(x for x in I.resources(data)[1] if x[0]==0x8008);b=data[r[3]:r[3]+r[4]];first,last=b[95:97]
 widths={c:struct.unpack_from('<H',b,118+4*(c-first))[0] for c in range(first,last+1)}
 return 'h=%s avg=%s i=%s W=%s ascii-advances=%s'%(I.word(b,88),I.word(b,91),widths.get(105),widths.get(87),sorted(set(widths.get(c) for c in range(32,127) if c in widths)))
def chrome(data):
 try:rows=N.resources(data)[2]
 except ValueError as e:return str(e)
 cfg=next((r['data'] for r in rows if r['type']==0xf006 and r['id']==0x8001),None)
 dims={}
 for r in rows:
  if r['type']==0x8002:
   b=r['data'];hdr=struct.unpack_from('<I',b)[0]
   if hdr==12:w,h=struct.unpack_from('<HH',b,4)
   elif hdr>=40:w,h=struct.unpack_from('<ii',b,4)
   else:continue
   dims[r['id']&32767]=(w,h)
 return 'cfg='+str(struct.unpack_from('<10H',cfg) if cfg else None)+' bitmaps='+str(dims)
def audit():
 packets=[(folder,source) for _,folder,source in P.PACKETS]+[('TEXT80','downloads/experimental/TEXT80/TEXT80.ZIP')]
 for label,path in packets:
  with zipfile.ZipFile(ROOT/path) as z:
   files={n.upper():z.read(n) for n in z.namelist()}
  print('\nPACKET',label,path)
  displays=set()
  for n,b in files.items():
   if n.endswith('OEMSETUP.INF'):
    section=''
    for line in b.decode('latin1').splitlines():
     line=line.strip()
     if line.startswith('['):section=line.lower()
     elif section=='[display]' and not line.startswith(';'):
      match=re.search(r':([A-Z0-9_]+\.DRV)',line,re.I)
      if match:displays.add(match[1].upper())
  if label=='TEXT80':displays.update(['TEXT80.DRV','T80CMP.DRV','T80PAN.DRV','T80VGA.DRV'])
  for n,b in files.items():
   if n.endswith('OEMSETUP.INF'):
    print('OEM',n);sect=''
    for line in b.decode('latin1').splitlines():
     line=line.strip()
     if line.startswith('['):sect=line.lower()
     elif line and not line.startswith(';') and sect in ('[display]','[sysfonts]'):print(sect,line)
   if n.endswith('SYS.FON'):
    print('SYSTEM',n,font(b))
   if n.endswith('.DRV') and Path(n).name in displays:
    print('DRIVER',n,chrome(b))
if __name__=='__main__':audit()
