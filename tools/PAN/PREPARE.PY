"""Prepare private single-application panning and canonical packets; no acceptance."""
from pathlib import Path
import argparse,hashlib,importlib.machinery,json,shutil,sys,zlib
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
N=importlib.machinery.SourceFileLoader('pan_native_transactions',str(ROOT/'tools/UPAN/NATIVE.PY')).load_module()
C=importlib.machinery.SourceFileLoader('pan_archive_recipes',str(ROOT/'tools/UPAN/COMPOSE.PY')).load_module()
APP=('XTPAN.EXE','XYCTL.EXE','PANCTL.EXE','CGACTL.EXE','PANCFG.EXE','PAN.EXE','PANKEY.DLL')
def identity(b):return dict(bytes=len(b),sha256=hashlib.sha256(b).hexdigest())
def emit(out,files):
 out.mkdir(parents=True,exist_ok=False)
 for n,b in files.items():
  p=out/n;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
def base(name):
 b=(HERE/'BASE'/name).read_bytes();assert identity(b)==json.loads((HERE/'BASE/PINS.JSN').read_bytes())[name];return C.members(b)
def stage(out,h,watcom):
 N.stage(out,h,support={'CPSET.EXE':(ROOT/'tools/UPAN/BIN/CPSET.EXE').read_bytes()})
 s=(out/'FIXXT.C').read_text();nn='"PAN.EXE","PANCTL.EXE","CGACTL.EXE"';sizes=','.join(str(len(h[n]))+'UL' for n in ('PAN.EXE','PANCTL.EXE','CGACTL.EXE'))
 import re
 for pattern,extra in [(r'(static const char \*names\[\]=\{)(.*?)(\};)',nn),(r'(static unsigned long sizes\[\]=\{)(.*?)(\};)',sizes),(r'(static int target\[\]=\{)(.*?)(\};)','0,0,0')]:
  s,count=re.subn(pattern,lambda m:m[1]+m[2]+','+extra+m[3],s);assert count==1
 s=s.replace('#define COUNT 41','#define COUNT 44')
 s=s.replace('if(!stricmp(n,"SYSTEM.INI")','if(!stricmp(n,"JRPAN.DRV")||!stricmp(n,"CPPAN.DRV")||!stricmp(n,"SYSTEM.INI")')
 N.write(out/'FIXXT.C',s)
 header='typedef struct {const char *name;unsigned long size,crc;int system;} PANFILE;\n#define PAN_COUNT 7\nstatic PANFILE pan_files[PAN_COUNT]={\n'
 for n in APP:header+=' {"%s",%dUL,0x%08xUL,%d},\n'%(n,len(h[n]),zlib.crc32(h[n]),n.endswith('.DLL'))
 N.write(out/'PANPINS.H',header+'};\n')
 s=(out/'PANINT.H').read_text().replace('sprintf(token,"%s\\\\%s",win,owner)','sprintf(token,"%s\\\\PAN.EXE",win)').replace('use PANCFG /SETTINGS','use PAN /SETTINGS')
 s=s.replace('!stricmp(leaf,\"TANDY88.DRV\")','!stricmp(leaf,\"TNDY160.DRV\")||!stricmp(leaf,\"TANDY88.DRV\")')
 # Retain an explicit OFF choice while migrating old owner tokens once.
 s=s.replace('char value[512],marker[512],','char value[512],marker[512],version[512],')
 s=s.replace('if(stricmp(marker,leaf)){','sectionvalue("UnifiedPan","Version",version);\n if(stricmp(marker,leaf)||strcmp(version,"2")){')
 s=s.replace('if(automatic){sprintf(token,','if(automatic && (stricmp(marker,leaf)||pan_present("load")||pan_present("run"))){sprintf(token,')
 s=s.replace('changeini("UnifiedPan","Display",leaf);','changeini("UnifiedPan","Display",leaf);changeini("UnifiedPan","Version","2");')
 a=s.index('static int pan_install(')
 helper="""static int pan_present(const char *key){
 char before[512],result[512],*p,*end;sectionvalue("windows",key,before);
 p=before;while(*p==' '||*p=='\\t'||*p==',')p++;
 end=p+strlen(p);while(end>p && (end[-1]==' '||end[-1]=='\\t'||end[-1]==','))*--end=0;
 if(!PanStartupEdit(p,0,result,sizeof(result)))stop("Malformed panning startup",key);
 return strcmp(p,result)!=0;
}
"""
 s=s[:a]+helper+s[a:]
 s=s.replace('if(!owner){puts(', '#ifdef PAN_UNIVERSAL\n automatic=1;if(!owner)owner=\"XTPAN.EXE\";\n#endif\n if(!owner){puts(')
 N.write(out/'PANINT.H',s)
 return N.compile_native(out,watcom)
def prepare(build,jr,cp,out,watcom,commit):
 out.mkdir(parents=True,exist_ok=False);rec=json.loads((build/'BUILD.JSN').read_bytes());h={n:(build/n).read_bytes() for n in rec['binaries']}
 assert all(identity(h[n])==pin for n,pin in rec['binaries'].items());h['PAN.EXE']=h['PANCFG.EXE']
 native=out/'native';fix=stage(native,h,watcom)
 N.aliases(native,dict(h,**{'FIXXT.EXE':fix,'CPSET.EXE':(ROOT/'tools/UPAN/BIN/CPSET.EXE').read_bytes()}))
 setup=N.compile_native(native,watcom,'SETUP',True)
 body=base('WINXT.ZIP');body['SETUP.EXE']=setup;body['WINXT/FIXXT.EXE']=fix
 body['README.TXT']=body['README.TXT'].replace(b'PANCFG',b'PAN')
 for n,b in h.items():body['WINXT/'+n]=b
 emit(out/'WINXT',body)
 for kind,driver in [('JRPAN',jr),('CPPAN',cp)]:
  body=base(kind+'.ZIP');prefix='JRPAN/' if kind=='JRPAN' else ''
  for n,b in h.items():body[prefix+n]=b
  body[prefix+'PANINST.EXE']=fix;body[prefix+kind+'.DRV']=driver.read_bytes()
  body[prefix+'OEMSETUP.INF']=body[prefix+'OEMSETUP.INF'].replace(b'320x400',b'640x400').replace(b'software panning',b'Panning desktop')
  emit(out/kind,body)
 # Universal application uses existing installed drivers; upgrades exact old
 # vertical panning drivers without touching fixed/HPXY/CGA driver bytes.
 drivers={'JRPAN.DRV':jr.read_bytes(),'CPPAN.DRV':cp.read_bytes()}
 header='typedef struct {const char *name;unsigned long size,crc,oldsize,oldcrc;} PANDRIVER;\n#define DRV_COUNT 2\nstatic PANDRIVER pan_drivers[2]={\n'
 for kind,b in drivers.items():
  previous=base(kind.replace('.DRV','.ZIP'));old=previous[('JRPAN/' if kind.startswith('JR') else '')+kind]
  header+=' {"%s",%dUL,0x%08xUL,%dUL,0x%08xUL},\n'%(kind,len(b),zlib.crc32(b),len(old),zlib.crc32(old))
 N.write(native/'DRVPINS.H',header+'};\n');shutil.copyfile(HERE/'PANSETUP.C',native/'PANSETUP.C')
 universal_setup=N.compile_native(native,watcom,'PANSETUP')
 notices={}
 for kind in ('WINXT','JRPAN','CPPAN','CGA'):
  for name,body in base(kind+'.ZIP').items():
   leaf=name.rsplit('/',1)[-1]
   if leaf.endswith('.TXT') and ('LIC' in leaf or 'NOTICE' in leaf or leaf=='OWATCOM.TXT'):
    notices['NOTICES/'+kind+'/'+leaf]=body
 emit(out/'PAN',dict({'SETUP.EXE':universal_setup,'README.TXT':(HERE/'GUIDES/PAN.TXT').read_bytes()},**{'PAN/'+n:b for n,b in dict(h,**drivers,**notices).items()}))
 for kind in ('JRPAN','CPPAN'):
  prefix='JRPAN/' if kind=='JRPAN' else ''
  folder=out/kind/prefix;(folder/'PANINST.EXE').write_bytes(universal_setup)
  (folder/'INSTALL.TXT').write_bytes((HERE/'GUIDES'/(kind+'.TXT')).read_bytes())
  for script in ('INSTALL.BAT','JRSTART.BAT' if kind=='JRPAN' else 'CPWIN.BAT'):
   p=folder/script;data=p.read_bytes().replace(b'PANINST PANINIT ',b'PANINST ')
   if script=='INSTALL.BAT':
    at=data.index(b'COPY /B ');data=data[:at]+('C:\\'+kind+'\\PANINST C:\\WINDOWS\r\nIF ERRORLEVEL 1 GOTO FAILED\r\n').encode()+data[at:]
   p.write_bytes(data)
 # Expanded CGA source keeps all four accepted display drivers unchanged.
 body=base('CGA.ZIP');payload={n[4:]:b for n,b in body.items() if n.startswith('CGA/')}
 for n,b in h.items():payload[n]=b
 import CGASTAGE
 CGASTAGE.module({n[4:]:b for n,b in body.items() if n.startswith('CGA/')}).emit(ROOT,out/'cga-prepared',payload,commit)
 N.write(out/'PREPARE.JSN',json.dumps(dict(outcome='PREPARED_NOT_QUALIFIED',source_commit=commit,helpers={n:identity(b) for n,b in h.items()},drivers={n:identity(b) for n,b in drivers.items()}),indent=2)+'\n')
 print('Prepared',out)
if __name__=='__main__':
 p=argparse.ArgumentParser()
 for n in ('build','jr','cp','out','watcom'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--commit',required=True);a=p.parse_args();prepare(a.build,a.jr,a.cp,a.out,a.watcom,a.commit)
