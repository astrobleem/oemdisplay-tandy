"""Private 640KB PCjr native viewport probe, guarded and bounded."""
from pathlib import Path
import argparse,importlib.machinery,os,shutil,json
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser()
for n in ('windows','probe','driver','guard','dosbox','lease','out'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();out=a.out.resolve();out.mkdir(exist_ok=False);c=out/'CROOT';w=c/'WINDOWS';shutil.copytree(a.windows,w)
h=importlib.machinery.SourceFileLoader('panxy_ini',str(ROOT/'src/softpan/RUNTEST.PY')).load_module()
def write(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('latin1'))
shutil.copyfile(a.driver,w/'SYSTEM/JRPAN.DRV');shutil.copyfile(a.probe,w/'PROBE.EXE');shutil.copyfile(a.guard,c/'JRGUARD.COM')
s=(w/'SYSTEM.INI').read_text(encoding='latin1')
for k,v in [('display.drv','JRPAN.DRV'),('shell','PROBE.EXE')]:s=h.ini(s,'boot',k,v)
write(w/'SYSTEM.INI',s)
s=(w/'WIN.INI').read_text(encoding='latin1')
for k in ('load','run'):s=h.ini(s,'windows',k,'')
write(w/'WIN.INI',s)
write(c/'TEST.BAT','@ECHO OFF\nSET PATH=C:\\WINDOWS;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nC:\\JRGUARD.COM > C:\\GUARD.TXT\nIF ERRORLEVEL 1 GOTO FAIL\nCD WINDOWS\nWIN /R > C:\\WINERR.TXT\nCD \\\nECHO RETURNED > C:\\RETURNED.TXT\nGOTO END\n:FAIL\nECHO GUARDFAILED > C:\\FAILED.TXT\n:END\nEXIT\n')
write(out/'RUN.CNF','[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=pcjr\nmemsizekb=640\nworking directory option=force\nworking directory default='+str(out)+'\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[midi]\nmididevice=none\n[autoexec]\n@ECHO OFF\nmount C "'+str(c)+'"\nC:\nTEST.BAT\n')
r=importlib.machinery.SourceFileLoader('panxy_native_runner',str(ROOT/'src/softpan/WINRUN.PY')).load_module().Runner(out/'LEASE.JSON',a.lease)
with r.lease():r.run([str(a.dosbox),'-nopromptfolder','-conf',str(out/'RUN.CNF')],dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),out/'HOST.LOG',180)
log=(c/'PANXY.LOG').read_text();assert (c/'RETURNED.TXT').exists() and 'COMPLETE=1' in log and 'FAILED=' not in log,log[-2000:]
print('Native probe completed and normal DOS return; pixel oracle still required')
