#!/usr/bin/env python3
"""Private own-media developer QA. Never publish the generated output directory.
The DOS end user does not need Python. This harness embeds no Windows bytes.
"""
from pathlib import Path
import argparse, concurrent.futures, hashlib, json, os, shutil, struct, subprocess, time, runpy
H=ROOT=OWN=OWNWIN=DOSBOX=STAGE=BASE=ENV=None
KINDS=['szdd','expanded','private','mixed','missing','corrupt','ambiguous','trunchdr','flags','literal','reference','oversize','overrun','trailing','runtime','manifest','lowspace','cancel','existingfile','existingdir','dos2','powerloss']
PROFILE="""[sdl]
output=surface
[dosbox]
machine=tandy
memsize=0
memsizekb=640
allow more than 640kb base memory=false
[cpu]
core=normal
cputype=8086_prefetch
cycles={cycles}
fpu=false
[dos]
ver=3.30
xms=false
ems=false
umb=false
"""
SUP=['CGA.GR2','CGALOGO.LGO','CGAFIX.FON','CGAOEM.FON','CGASYS.FON','EGAFIX.FON','EGAOEM.FON','EGASYS.FON']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def snapshot(d): return {str(p.relative_to(d)):digest(p) for p in sorted(d.rglob('*')) if p.is_file()}
def expanded(n):return STAGE['expanded_file']((OWN/n).read_bytes(),n)
def base(name,fullwin=False,private=False):
 t=H/'TESTS'/name;t.mkdir(parents=True);a=t/'A';c=t/'C';a.mkdir();c.mkdir();runtime=a/'WINXT';runtime.mkdir()
 for line in (ROOT/'MANIFEST.SHA').read_text().splitlines():
  _,n=line.split()
  if n not in SUP and n!='TXTSYS.FON':shutil.copy2(ROOT/n,runtime/n)
 shutil.copy2(ROOT/'MANIFEST.SHA',runtime/'MANIFEST.SHA')
 if fullwin:shutil.copytree(OWNWIN,c/'WINDOWS')
 else:
  (c/'WINDOWS'/'SYSTEM').mkdir(parents=True)
  for n in ['SYSTEM.INI','WIN.INI','WIN.COM']:shutil.copy2(OWNWIN/n,c/'WINDOWS'/n)
 (c/'MEDIA').mkdir()
 for n in SUP:shutil.copy2(OWN/n,c/'MEDIA'/n)
 (c/'CONFIG.SYS').write_bytes(b'FILES=30\r\nBUFFERS=20\r\n');(c/'AUTOEXEC.BAT').write_bytes(b'@ECHO OFF\r\n')
 return t,a,c,runtime

def prepare(name,kind):
 t,a,c,r=base(name,fullwin=(kind=='szdd'))
 cmd='H:\\PREPXT WINXT C:\\WINDOWS C:\\MEDIA'; answer='YES';space=''; dosver='';success=False;interrupt=False
 if kind=='szdd':success=True
 elif kind=='expanded':
  for n in SUP:(c/'MEDIA'/n).write_bytes(expanded(n))
  success=True
 elif kind=='private':
  for n in SUP:(r/n).write_bytes(expanded(n))
  cmd='H:\\PREPXT WINXT C:\\WINDOWS';success=True
 elif kind=='mixed':
  (c/'MEDIA2').mkdir()
  for i,n in enumerate(SUP):
   p=c/'MEDIA'/n;data=p.read_bytes();p.unlink();d=[c/'WINDOWS',c/'WINDOWS'/'SYSTEM',c/'MEDIA',c/'MEDIA2'][i%4]
   (d/(n[:-1]+'_' if i%2 else n)).write_bytes(data)
  cmd+=' C:\\MEDIA2';success=True
 elif kind=='missing':(c/'MEDIA'/'CGA.GR2').unlink()
 elif kind=='corrupt':
  b=bytearray(expanded('CGA.GR2'));b[-1]^=1;(c/'MEDIA'/'CGA.GR2').write_bytes(b)
 elif kind=='ambiguous':
  b=bytearray(expanded('CGA.GR2'));b[-1]^=1;(c/'MEDIA'/'CGA.GR_').write_bytes(b)
 elif kind=='trunchdr':(c/'MEDIA'/'CGA.GR2').write_bytes(b'SZDD\x88\xf0\x27\x33A\x00')
 elif kind in ('flags','literal','reference','oversize'):
  hdr=b'SZDD\x88\xf0\x27\x33A\x00'+struct.pack('<I',2104 if kind!='oversize' else 1000000)
  tail={'flags':b'','literal':b'\x01','reference':b'\x00\x00','oversize':b''}[kind]
  (c/'MEDIA'/'CGA.GR2').write_bytes(hdr+tail)
 elif kind=='overrun':
  b=b'SZDD\x88\xf0\x27\x33A\x00'+struct.pack('<I',2104)
  b+=(b'\xff'+b'x'*8)*262+b'\x7f'+b'x'*7+b'\x00\x00'
  (c/'MEDIA'/'CGA.GR2').write_bytes(b)
 elif kind=='trailing':
  p=c/'MEDIA'/'CGA.GR2';p.write_bytes(p.read_bytes()+b'\x00')
 elif kind=='runtime':
  p=r/'INSTALL.BAT';b=bytearray(p.read_bytes());b[-3]^=1;p.write_bytes(b)
 elif kind=='manifest':
  p=r/'MANIFEST.SHA';b=bytearray(p.read_bytes());b[0]=ord('f') if b[0]!=ord('f') else ord('e');p.write_bytes(b)
 elif kind=='lowspace':space=' -size 512,1,1440,50'
 elif kind=='cancel':answer='NO'
 elif kind=='existingfile':(c/'WINXT').write_bytes(b'USER DATA - DO NOT OVERWRITE\r\n')
 elif kind=='existingdir':(c/'WINXT').mkdir();(c/'WINXT'/'KEEP.TXT').write_bytes(b'USER DATA\r\n')
 elif kind=='dos2':dosver='ver set 2 0\n'
 elif kind=='powerloss':interrupt=True
 else:raise ValueError(kind)
 baseline={'runtime':snapshot(a),'windows':snapshot(c/'WINDOWS'),'media':snapshot(c/'MEDIA'),'config':digest(c/'CONFIG.SYS'),'autoexec':digest(c/'AUTOEXEC.BAT')}
 if (c/'MEDIA2').exists():baseline['media2']=snapshot(c/'MEDIA2')
 if (c/'WINXT').is_dir():baseline['existing']=snapshot(c/'WINXT')
 elif (c/'WINXT').is_file():baseline['existingfile']=digest(c/'WINXT')
 (t/'BEFORE.JSN').write_text(json.dumps(baseline,indent=2))
 batch='@ECHO OFF\r\nVER > C:\\VERSION.TXT\r\nA:\r\n'+cmd+' < H:\\'+answer+'.TXT > C:\\TEST.LOG\r\nIF ERRORLEVEL 1 GOTO BAD\r\nECHO RC=0>>C:\\TEST.LOG\r\nGOTO DONE\r\n:BAD\r\nECHO RC=1>>C:\\TEST.LOG\r\n:DONE\r\n'
 (t/'RUN.BAT').write_bytes(batch.encode())
 (t/'RUN.CNF').write_text(BASE+f'[autoexec]\nmount h {H}\nmount t {t}\nmount a {a} -t floppy\nmount c {c}{space}\n'+dosver+'call t:\\run.bat\nexit\n')
 return dict(name=name,kind=kind,t=t,c=c,success=success,interrupt=interrupt,baseline=baseline)

def run(case):
 t=case['t'];c=case['c'];before=case['baseline'];start=time.time()
 with (t/'EMU.LOG').open('wb') as log:
  p=subprocess.Popen([DOSBOX,'-fastlaunch','-conf',str(t/'RUN.CNF')],env=ENV,stdout=log,stderr=subprocess.STDOUT)
  if case['interrupt']:
   # Interrupt only after the verified output stage has actually started.
   while p.poll() is None and not (c/'WINXT'/'TR51616.DRV').exists() and time.time()-start<600:time.sleep(.05)
   p.kill();p.wait(timeout=15)
  else:p.wait(timeout=900)
 text=(c/'TEST.LOG').read_text(errors='replace') if (c/'TEST.LOG').exists() else ''
 after={'runtime':snapshot(t/'A'),'windows':snapshot(c/'WINDOWS'),'media':snapshot(c/'MEDIA'),'config':digest(c/'CONFIG.SYS'),'autoexec':digest(c/'AUTOEXEC.BAT')}
 if (c/'MEDIA2').exists():after['media2']=snapshot(c/'MEDIA2')
 if 'existing' in before:after['existing']=snapshot(c/'WINXT')
 if 'existingfile' in before:after['existingfile']=digest(c/'WINXT')
 checks={'all_inputs_unchanged':before==after,'no_install_marker':not any((c/'WINXT'/n).exists() for n in ['READY.TAG','PARTIAL.TAG','SHREADY.TAG','WINXT.BAT'])}
 if case['success']:
  out=c/'WINXT';expected={line.split()[1]:line.split()[0] for line in (ROOT/'MANIFEST.SHA').read_text().splitlines()};expected['MANIFEST.SHA']=digest(ROOT/'MANIFEST.SHA')
  checks.update(success_exit='RC=0' in text,exact_complete_output=snapshot(out)==expected,total_bytes=sum(p.stat().st_size for p in out.iterdir())==651008)
 elif case['interrupt']:checks.update(partial_output=(c/'WINXT').exists(),installer_absent=not (c/'WINXT'/'INSTALL.BAT').exists())
 else:checks.update(refused='RC=1' in text,no_new_output=not (c/'WINXT').exists() or 'existing' in before or 'existingfile' in before)
 result={k:case[k] for k in ['name','kind']};result.update(seconds=round(time.time()-start,2),checks=checks,passed=all(checks.values()),log=text,version=(c/'VERSION.TXT').read_text(errors='replace'))
 (t/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(case['name'],case['kind'],result['passed'],result['seconds'],flush=True);return result

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--helper',type=Path,required=True,help='Built PREPXT.EXE')
 p.add_argument('--runtime',type=Path,required=True,help='Repository distributions/WINXT, including STAGE.PY')
 p.add_argument('--support-files',type=Path,required=True,help='Private original support files under their eight canonical filenames; SZDD or expanded')
 p.add_argument('--windows-dir',type=Path,required=True,help='Private installed Windows folder, copied before every test')
 p.add_argument('--dosbox',type=Path,required=True,help='DOSBox-X executable or wrapper')
 p.add_argument('--out',type=Path,required=True,help='Fresh PRIVATE output folder; will contain owned Windows copies')
 p.add_argument('--case',action='append',choices=KINDS,help='Run a selected case, repeatable; default is all 22')
 p.add_argument('--cycles',choices=['max','3000'],default='max')
 p.add_argument('--workers',type=int,choices=range(1,5),default=3)
 args=p.parse_args()
 H=args.out.resolve();ROOT=args.runtime.resolve();OWN=args.support_files.resolve();OWNWIN=args.windows_dir.resolve();DOSBOX=str(args.dosbox.resolve())
 for item in [args.helper,args.dosbox,ROOT/'STAGE.PY',ROOT/'MANIFEST.SHA']+[OWN/n for n in SUP]+[OWNWIN/n for n in ['SYSTEM.INI','WIN.INI','WIN.COM']]:
  if not item.is_file():p.error('Required file not found: '+str(item))
 if H.exists():p.error('Output exists; choose a fresh private --out directory')
 for source in [ROOT,OWN,OWNWIN]:
  try:H.relative_to(source)
  except ValueError:pass
  else:p.error('Output must be outside all input source directories')
 STAGE=runpy.run_path(str(ROOT/'STAGE.PY'))
 BASE=PROFILE.format(cycles=args.cycles);ENV={**os.environ,'SDL_VIDEODRIVER':'dummy','SDL_AUDIODRIVER':'dummy'}
 H.mkdir(parents=True);shutil.copy2(args.helper,H/'PREPXT.EXE');(H/'YES.TXT').write_bytes(b'Y\r\n');(H/'NO.TXT').write_bytes(b'N\r\n')
 kinds=args.case or KINDS
 cases=[prepare('F%02d'%(i+1),k) for i,k in enumerate(kinds)]
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:results=list(pool.map(run,cases))
 report={'executable_sha256':digest(H/'PREPXT.EXE'),'executable_bytes':(H/'PREPXT.EXE').stat().st_size,'profile':'8086_prefetch, normal core, 640KB, no EMS/XMS/UMB/FPU, internal DOS reporting 3.30 (not booted MS-DOS)','cycles':args.cycles,'results':results}
 (H/'QARESULT.JSN').write_text(json.dumps(report,indent=2));passed=all(r['passed'] for r in results);print('ALL PASSED',passed,flush=True)
 raise SystemExit(0 if passed else 1)
