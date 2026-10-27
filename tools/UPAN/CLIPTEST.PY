"""Check actual staged FIXXT clipboard idempotence with unified owner startup."""
from pathlib import Path
import argparse,os,subprocess,sys,tempfile,json
ap=argparse.ArgumentParser();ap.add_argument('--native',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();a.out.mkdir(exist_ok=False)
with tempfile.TemporaryDirectory(prefix='clip-order-') as tmp:
 root=Path(tmp);win=root/'W';win.mkdir();src=a.out/'CLIPTEST.C';exe=a.out/'CLIPTEST.EXE'
 code='#define main original_main\n#include "'+(a.native/'FIXXT.C').resolve().as_posix()+'"\n#undef main\nint main(int argc,char **argv){if(argc!=3)return 2;strcpy(win,argv[2]);strupr(win);checking=!strcmp(argv[1],"CHECK");clipini(3);return 0;}\n';src.write_text(code)
 r=subprocess.run([sys.executable,str(Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'),'--','-x','c','-std=c89','-DHOST_TEST',str(src),'-o',str(exe)],capture_output=True,text=True);(a.out/'BUILD.LOG').write_text(r.stdout+r.stderr);assert not r.returncode,r.stderr
 canonical=str(win).upper()+'\\TGCLIP.EXE'
 def run(mode):return subprocess.run([str(exe.resolve()),mode,str(win)],capture_output=True,text=True)
 def put(value):
  data=('[windows]\r\nload='+value+'\r\nrun=kept.exe\r\n[custom]\r\nanswer=42\r\n').encode();(win/'WIN.INI').write_bytes(data);return data
 checks=[]
 for load in ['clock.exe '+canonical+' XYCTL.EXE','clock.exe XYCTL.EXE '+canonical,'clock.exe '+canonical.lower()+' XYCTL.EXE']:
  before=put(load);r=run('CHECK');assert not r.returncode and (win/'WIN.INI').read_bytes()==before,r.stdout+r.stderr
 checks.append('one correct TGCLIP token accepted before or after pan owner without rewriting load order; DOS case-insensitivity preserved')
 for load in ['clock.exe '+canonical+' XYCTL.EXE '+canonical,'clock.exe C:\\OTHER\\TGCLIP.EXE XYCTL.EXE','clock.exe XYCTL.EXE']:
  before=put(load);r=run('CHECK');assert r.returncode and (win/'WIN.INI').read_bytes()==before,r.stdout+r.stderr
  r=run('REPAIR');assert not r.returncode,r.stdout+r.stderr
  after=(win/'WIN.INI').read_bytes();assert after.count(b'TGCLIP.EXE')==1 and canonical.encode() in after and b'XYCTL.EXE' in after and b'answer=42' in after and b'run=kept.exe' in after
  r=run('CHECK');assert not r.returncode,r.stdout+r.stderr
 checks.append('duplicate, wrong-path and missing tokens still refused by CHECK and repaired once without changing unrelated programs/INI sections')
 result=dict(outcome='PASS_HOST_CLIPBOARD_ORDER',checks=checks);(a.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
