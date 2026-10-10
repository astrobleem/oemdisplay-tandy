"""Generate numeric/resource identity contracts from original first-party files."""
from pathlib import Path
import argparse,json,hashlib,struct,zlib,sys
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
import importlib.machinery,importlib.util
loader=importlib.machinery.SourceFileLoader('INSPECT',str(HERE.parent/'XTFONTS/INSPECT.PY'));spec=importlib.util.spec_from_loader(loader.name,loader);INSPECT=importlib.util.module_from_spec(spec);loader.exec_module(INSPECT)
NAMES=('TR53216.DRV','TR56404.DRV','TR51616.DRV','TR53204.DRV','TR56402.DRV','TXTMODE.DRV','XTESYS.FON','XTEFIX.FON','XTEOEM.FON','XTCSYS.FON','XTCFIX.FON','XTCOEM.FON','XTTSYS.FON','XTSTATIC.LGO','WXTSPL01.RLE')
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--runtime',type=Path,default=HERE.parent/'WINXT' if (HERE.parent/'WINXT').is_dir() else REPO/'distributions/WINXT');ap.add_argument('--out',type=Path,default=HERE);a=ap.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 files=[]
 for name in NAMES:
  b=(a.runtime/name).read_bytes();v={'name':name,'size':len(b),'crc32':zlib.crc32(b)&0xffffffff,'ne':0,'font_offset':0,'height':0,'ascent':0,'charset':0,'module':'','face':'','width_sum':0,'sha256':hashlib.sha256(b).hexdigest()}
  if name.endswith(('.DRV','.FON')):
   v['ne']=struct.unpack_from('<I',b,60)[0];v['module'],resources=INSPECT.resources(b)
  if name.endswith('.FON'):
   r=next(r for r in resources if r[0]==0x8008);fo=r[3];f=INSPECT.fontinfo(b[fo:fo+r[4]])
   v.update(font_offset=fo,height=f['height'],ascent=f['ascent'],charset=f['charset'],face=f['face'])
   a1=a2=0
   for w in f['widths']:
    for c in struct.pack('<H',w):a1=(a1+c)%255;a2=(a2+a1)%255
   v['width_sum']=(a2<<8)|a1
  files.append(v)
 h='/* Generated original payload contracts; no glyph bitmap data. */\nstatic const Payload payloads[] = {\n'
 for v in files:h+=' {"%s",%dUL,0x%08xUL,%dU,%dU,%dU,%dU,%dU,"%s","%s",%dU},\n'%(v['name'],v['size'],v['crc32'],v['ne'],v['font_offset'],v['height'],v['ascent'],v['charset'],v['module'],v['face'],v['width_sum'])
 h+='};\n#define NPAY ((unsigned)(sizeof(payloads)/sizeof(payloads[0])))\n'
 (a.out/'XTPINS.H').write_bytes(h.replace('\n','\r\n').encode());(a.out/'PAYLOADS.JSN').write_bytes(json.dumps(files,indent=2).replace('\n','\r\n').encode());print('Generated',len(files),'original resource contracts')
if __name__=='__main__':main()
