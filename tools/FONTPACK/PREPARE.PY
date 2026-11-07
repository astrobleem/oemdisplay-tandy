"""Build the font integration candidate without repinning historical SAVPACK."""
from pathlib import Path
import argparse,hashlib,re,shutil,zipfile,zlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
BASE_SHA='fa5b55806d35d0aca9cb6c3a67b608866a169843769d4e7b54628317214376aa'
FONTS=('T1P8.FON','T1P12.FON','T2P8.FON','T2P12.FON','TKP8.FON','TKP12.FON','CG1HELV.FON','CG2HELV.FON','CG6HELV.FON')
CHANGED={'README.TXT','WINXT/DISPLAY.TXT','WINXT/XTCSYS.FON','WINXT/FIXXT.EXE','SETUP.EXE'}

def require(ok,message):
 if not ok:raise ValueError(message)
def write(path,text):path.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def cstr(value):return '"'+value.replace('\\','\\\\')+'"'
def pinrow(name,data):return '{%s,"%s",%dUL,0,0x%08xUL},'%(cstr(name),hashlib.sha256(data).hexdigest(),len(data),zlib.crc32(data))
def baseline():
 path=ROOT/'tools/SAVPACK/BIN/WINXT.ZIP'
 require(hashlib.sha256(path.read_bytes()).hexdigest()==BASE_SHA,'Historical SAVPACK differs')
 with zipfile.ZipFile(path) as z:return {n:z.read(n) for n in z.namelist()}
def payload():
 body=baseline()
 body['WINXT/XTCSYS.FON']=(ROOT/'tools/XTFONTS/COMPAT/XTCSYS.FON').read_bytes()
 require(hashlib.sha256(body['WINXT/XTCSYS.FON']).hexdigest()=='56aab79d1fc587ed0d2fecb6f5dc6416aa8dbb9a1eed994775a4d633c316af90','Different corrected XTCSYS')
 for name in (*FONTS,'LICENSE.TXT','FONTLIC.TXT'):
  body['WINXT/FONTS/'+name]=(ROOT/'tools/PROPFONT/BIN'/name).read_bytes()
 guide=(ROOT/'tools/PROPFONT/README.TXT').read_text()
 note='''WINDOWS XT PACK: OPTIONAL APPLICATION FONTS

Full SETUP copies this folder to C:\\WINXT\\FONTS. In Windows, open
Control Panel > Fonts > Add and browse to C:\\WINXT\\FONTS. Drivers-only
users can browse to the FONTS folder inside this packet's WINXT folder.
Select only the optional fonts you want. Setup does not register any of
them or change your existing WIN.INI font registrations.

CAUTION: CG1HELV, CG2HELV and CG6HELV all use the existing Helv family.
These sizes can change which Helv font existing applications choose.
Add them only if you want that change. The six Tandy files use XT Tandy I, XT Tandy II and XT Tandy 2K.
These are application fonts, not replacements for System/Fixed/Terminal.
Keep the two unchanged license notices with the files.

'''
 body['WINXT/FONTS/README.TXT']=(note+guide).replace('\n','\r\n').encode('ascii')
 note='''
OPTIONAL APPLICATION FONTS
Full Setup copies nine optional font files and their notices to
C:\\WINXT\\FONTS. Open Control Panel > Fonts > Add to select the fonts you
want. See FONTS\\README.TXT first: the three compact CG* files use Helv
and can change which Helv font existing applications choose. Setup
itself preserves all installed application font registrations.

The compatible narrow XTCSYS font keeps M/W at nine pixels and preserves
Windows dialog spacing. Updates replace only the
recognized original/earlier narrow XTCSYS when already selected for HPXY or a supported fixed
XTC-font display. Unknown/custom font bytes or shadow files are refused,
not overwritten. Unrelated font choices and display selections survive.
Fresh 320x200 16-color Setup continues to use the unchanged XTE fonts.
'''
 body['README.TXT']+=note.replace('\n','\r\n').encode('ascii')
 body['WINXT/DISPLAY.TXT']+=('''
OPTIONAL FONTS: Control Panel > Fonts > Add can use the FONTS subfolder
of this driver source. Full Setup also copies it to C:\\WINXT\\FONTS.
Read FONTS\\README.TXT before adding Helv. Display installation keeps the
selected System/Fixed/Terminal font family; application fonts are optional.
''').replace('\n','\r\n').encode('ascii')
 return body

def bind_headers(native,body):
 pins='static struct pin pins[]={\n'+'\n'.join(pinrow(n[6:].replace('/','\\'),b) for n,b in sorted(body.items()) if n.startswith('WINXT/'))+'\n};\n'
 write(native/'SETPINS.H',pins)
 # Begin with the historical recipe so repeated staging/binding cannot add duplicates.
 files=(ROOT/'tools/SAVPACK/NATIVE/SETFILES.H').read_text()
 crcs=(ROOT/'tools/SAVPACK/NATIVE/SETINPUT.H').read_text()
 ordered=[n for n in body if not n.startswith('WINXT/FONTS/')]
 ordered+=['WINXT/FONTS/'+n for n in (*FONTS,'LICENSE.TXT','FONTLIC.TXT','README.TXT')]
 for n in ordered:
  b=body[n]
  if not n.startswith('WINXT/'):continue
  leaf=n[6:]
  if '/' not in leaf:
   files=re.sub(r'(,"'+re.escape(leaf)+r'",)\d+UL(,0\})',lambda m:m[1]+str(len(b))+'UL'+m[2],files)
  else:
   dest='WINXT\\'+leaf.replace('/','\\');source=leaf.replace('/','\\')
   row='{%s,%s,%dUL,0},\n'%(cstr(dest),cstr(source),len(b))
   files=files.replace('};\n#define NFILES',row+'};\n#define NFILES')
   crcs=crcs.replace('};',' 0x00000000UL, /* '+dest+' */\n};')
 write(native/'SETFILES.H',files);write(native/'SETINPUT.H',crcs)
 setup=(native/'SETUP.C').read_text()
 extra=sum(n.startswith('WINXT/FONTS/') for n in body)
 for mode,count in [('FRESH',421),('UPDATE',128)]:setup=re.sub(r'(#define '+mode+r'_COUNT )\d+',lambda m:m[1]+str(count+extra),setup)
 write(native/'SETUP.C',setup)

def stage(out):
 require(not out.exists(),'Fresh output directory required')
 body=payload();shutil.copytree(HERE/'NATIVE',out/'native')
 bind_headers(out/'native',body)
 for n,b in body.items():
  p=out/'expanded'/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
 print('Staged font candidate. Compile FIXXT, bind, then compile SETUP. No acceptance/publication.')

def bind(out):
 b=(out/'native/FIXXT.EXE').read_bytes();require(b[:2]==b'MZ','Native FIXXT missing')
 (out/'expanded/WINXT/FIXXT.EXE').write_bytes(b)
 body={p.relative_to(out/'expanded').as_posix():p.read_bytes() for p in (out/'expanded').rglob('*') if p.is_file()}
 bind_headers(out/'native',body)
 print('Bound FIXXT. Build SETUP from these exact headers.')

def pack(out):
 root=out/'expanded';(root/'SETUP.EXE').write_bytes((out/'native/SETUP.EXE').read_bytes())
 require(not (out/'WINXT.ZIP').exists(),'Output archive exists')
 with zipfile.ZipFile(out/'WINXT.ZIP','w',compression=zipfile.ZIP_STORED) as z:
  for p in sorted(root.rglob('*')):
   if p.is_file():
    zi=zipfile.ZipInfo(p.relative_to(root).as_posix(),(1980,1,1,0,0,0));zi.create_system=0;zi.external_attr=32;z.writestr(zi,p.read_bytes())
 print(out/'WINXT.ZIP')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('phase',choices=('stage','bind','pack'));a.add_argument('--out',type=Path,required=True);v=a.parse_args();globals()[v.phase](v.out)
