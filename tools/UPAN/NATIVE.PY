"""Stage the existing native installer with the unified helper inventory."""
from pathlib import Path
import hashlib,json,os,re,shutil,subprocess,zlib
ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).resolve().parent

def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def once(s,a,b):
 if s.count(a)!=1:raise ValueError('Native adaptation anchor changed: '+a[:80])
 return s.replace(a,b)
def pin(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def stage(out,helpers,small=False,support=None):
 out.mkdir(parents=True,exist_ok=False)
 for p in (ROOT/'tools/DOSINST').iterdir():
  if p.suffix in ('.C','.H','.ASM'):shutil.copyfile(p,out/p.name)
 s=(out/'FIXXT.C').read_text()
 names=re.search(r'static const char \*names\[\]=\{(.*?)\};',s).group(1)
 sizes=re.search(r'static unsigned long sizes\[\]=\{(.*?)\};',s).group(1)
 targets=re.search(r'static int target\[\]=\{(.*?)\};',s).group(1)
 nn=re.findall(r'"([A-Z0-9.]+)"',names);ss=sizes.split(',');tt=targets.split(',')
 for n in ('XTPAN.EXE','XYCTL.EXE'):
  ss[nn.index(n)]=str(len(helpers[n]))+'UL';tt[nn.index(n)]='0'
 if not small and support:
  ss[nn.index('CPSET.EXE')]=str(len(support['CPSET.EXE']))+'UL'
 for n in ('PANCFG.EXE','PANKEY.DLL'):
  nn.append(n);ss.append(str(len(helpers[n]))+'UL');tt.append('1' if n.endswith('.DLL') else '0')
 s=once(s,names,','.join('"'+n+'"' for n in nn))
 s=once(s,sizes,','.join(ss));s=once(s,targets,','.join(tt));s=once(s,'#define COUNT 39','#define COUNT 41')
 s=once(s,'||(!stricmp(names[i],"XTPAN.EXE")&&mode!=2)','||(!stricmp(names[i],"XTPAN.EXE")&&mode==3)')
 # Startup now belongs to PANINT, preserving the wheel's existing run entry.
 a=s.index(' if(mode==2||mode==3){startup_token(');b=s.index('\n',a)
 s=s[:a]+s[b:]
 s=once(s,'#include "TGINT.H"','#include "TGINT.H"\n#include "PANINT.H"')
 s=once(s,' setbuf(stdout,NULL);',' setbuf(stdout,NULL);\n if(argc==3&&!stricmp(argv[1],"PANINIT")){char *cut;if(!_fullpath(media,argv[0],PTH))stop("Cannot resolve packet executable","");cut=strrchr(media,\'\\\\\');if(!cut)stop("Cannot resolve packet directory","");if(cut==media+2)cut[1]=0;else *cut=0;return pan_install(argv[2],media);}')
 s=once(s,'panini(mode);clipini(mode);return 0;','panini(mode);clipini(mode);if(mode!=KEEP_XRSYNC)pan_install(win,media);return 0;')
 if not small:
  # Panning may follow TGCLIP in load=. Presence at the right path is enough;
  # keep the old repair path for missing, duplicate or foreign clipboard tokens.
  tg=(out/'TGINT.H').read_text()
  tg=once(tg,'unsigned i=0,k=0,w;int quoted,comma=0,h;','unsigned i=0,k=0,w,clips=0,canonical=0;int quoted,comma=0,h;')
  tg=once(tg,'sectionvalue("windows","load",load);','sectionvalue("windows","load",load);\n sprintf(token,"%s\\\\TGCLIP.EXE",win);')
  tg=once(tg,'memcpy(result+k,word,w);k+=w;\n  }\n  comma=0;','memcpy(result+k,word,w);k+=w;\n  }else{clips++;if(!stricmp(word,token))canonical++;}\n  comma=0;')
  tg=once(tg,' sprintf(token,"%s\\\\TGCLIP.EXE",win);\n if(k)', ' if(clips==1&&canonical==1){inifile="SYSTEM.INI";return;}\n sprintf(token,"%s\\\\TGCLIP.EXE",win);\n if(k)')
  write(out/'TGINT.H',tg)
 shutil.copyfile(HERE/'PANINT.H',out/'PANINT.H')
 for n in ('PANSTART.C','PANSTART.H'):shutil.copyfile(ROOT/'src/panui'/n,out/n)
 selected=('XTPAN.EXE','PANCFG.EXE','PANKEY.DLL') if small else ('XTPAN.EXE','XYCTL.EXE','PANCFG.EXE','PANKEY.DLL')
 header='typedef struct {const char *name;unsigned long size,crc;int system;} PANFILE;\n#define PAN_COUNT '+str(len(selected))+'\nstatic PANFILE pan_files[PAN_COUNT]={\n'
 for n in selected:header+=' {"%s",%dUL,0x%08xUL,%d},\n'%(n,len(helpers[n]),zlib.crc32(helpers[n]),n.endswith('.DLL'))
 write(out/'PANPINS.H',header+'};\n');write(out/'FIXXT.C',s)
 return selected

def compile_native(out,watcom,name='FIXXT',large=False):
 env=dict(os.environ,WATCOM=str(watcom),INCLUDE=str(watcom/'h'))
 # Compiler children find only this managed toolchain in this subprocess.
 env['PATH']=str(watcom/'binnt')+os.pathsep+env.get('PATH','')
 si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
 args=[str(watcom/'binnt/wcl.exe'),'-zq','-bt=dos','-0','-ml' if large else '-ms','-os']+(['-s','-k8192'] if name=='CPSET' else [] if large else ['-k8192'])+['-fe='+name+'.EXE',name+'.C']
 p=subprocess.run(args,cwd=out,env=env,capture_output=True,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW,timeout=120)
 (out/(name+'.LOG')).write_bytes(p.stdout+p.stderr)
 if p.returncode:raise ValueError('Native compile failed: '+str(out/(name+'.LOG')))
 return (out/(name+'.EXE')).read_bytes()

def aliases(out,helpers):
 added=0
 pins=(out/'SETPINS.H').read_text();files=(out/'SETFILES.H').read_text();crcs=(out/'SETINPUT.H').read_text()
 for n,b in helpers.items():
  row='{"%s","%s",%dUL,0,0x%08xUL}'%(n,hashlib.sha256(b).hexdigest(),len(b),zlib.crc32(b))
  pat=r'\{"'+re.escape(n)+r'","[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL\}'
  if re.search(pat,pins):
   pins,count=re.subn(pat,lambda _:row,pins)
   if count!=1:raise ValueError('Duplicate native pin '+n)
   files,count=re.subn(r'(,"'+re.escape(n)+r'",)\d+UL(,0\})',lambda m:m[1]+str(len(b))+'UL'+m[2],files)
   if count!=2:raise ValueError('Native alias missing '+n)
  else:
   added+=2
   pins=once(pins,'};',row+',\n};')
   for prefix in ('WINXT\\\\FILES\\\\','WINXT\\\\'):
    path=prefix+n
    files=once(files,'};\n#define NFILES','{"%s","%s",%dUL,0},\n};\n#define NFILES'%(path,n,len(b)))
    crcs=once(crcs,'};',' 0x00000000UL, /* '+path+' */\n};')
 write(out/'SETPINS.H',pins);write(out/'SETFILES.H',files);write(out/'SETINPUT.H',crcs)
 setup=(out/'SETUP.C').read_text().replace('FRESH_COUNT 375','FRESH_COUNT '+str(375+added)).replace('UPDATE_COUNT 87','UPDATE_COUNT '+str(87+added))
 write(out/'SETUP.C',setup)
