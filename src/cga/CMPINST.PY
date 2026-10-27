#!/usr/bin/env python3
"""Exercise real accepted legacy inventories through the host C89 installer.

This is transaction evidence, never native Windows or consumer proof.
"""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,zipfile
import CMPPACK,PACKCGA as P
from INSTALLT import SYSTEM,WIN,snapshot,SHIM
from STAGECGA import write

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args()
 root=a.out.resolve();root.mkdir(parents=True,exist_ok=False);repo=a.repo.resolve()
 CMPPACK.prepare(repo,root/'prepared','0'*40)
 src=root/'src';shutil.copytree(root/'prepared/native-src',src);write(src/'HOSTTEST.H',SHIM)
 packet=root/'candidate';shutil.copytree(root/'prepared/packet',packet)
 launcher=Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'
 env=dict(os.environ,PATH=r'C:\msys64\ucrt64\bin'+os.pathsep+os.environ.get('PATH',''))
 def compile(folder,version=0):
  source=(src/'SETUP.C').read_text()
  if version:
   anchor='    if(argc!=3 && argc!=2){';assert source.count(anchor)==1
   source=source.replace(anchor,'    cga_select('+str(version)+');\n'+anchor)
  unit=folder/'HOST.C';write(unit,source);exe=folder/'SETUPHOST.EXE'
  p=subprocess.run([sys.executable,str(launcher),'--','-x','c','-std=c89','-Wall','-Wextra','-O2','-DHOST_TEST','-I',str(src),str(unit),'-o',str(exe)],capture_output=True,text=True)
  write(folder/'HOSTCC.LOG',p.stdout+p.stderr);assert p.returncode==0,p.stderr
  return exe
 new=compile(packet);tests=[]
 for version,zpath in ((1,repo/'docs/QUAL/CGACMP/BASE.ZIP'),(2,repo/'docs/QUAL/CGAPAN/BASE.ZIP')):
  old=root/('legacy'+str(version));old.mkdir()
  with zipfile.ZipFile(zpath) as z:z.extractall(old)
  exe=compile(old,version)
  for action in ('upgrade','undo','changed-refusal'):
   w=root/('w'+str(version)+action);(w/'SYSTEM').mkdir(parents=True)
   (w/'WIN.COM').write_bytes(b'host transaction fixture, not Windows');(w/'SYSTEM.INI').write_bytes(SYSTEM);(w/'WIN.INI').write_bytes(WIN)
   before=snapshot(w)
   def run(binary,mode,ok=0):
    argv=[str(binary),mode,str(w)] if mode=='UNDO' else [str(binary),str(w),mode]
    p=subprocess.run(argv,env=env,capture_output=True,text=True);write(root/('v'+str(version)+'-'+action+'-'+mode+'.LOG'),p.stdout+p.stderr)
    assert p.returncode==ok,(mode,p.returncode,p.stdout,p.stderr)
   run(exe,'320');assert (w/'CGACOPY.STA').exists()
   if action=='upgrade':
    run(new,'320C');assert b'display.drv=CGA32C.DRV' in (w/'SYSTEM.INI').read_bytes()
    run(new,'640C');run(new,'640');run(new,'UNDO');assert snapshot(w)==before
   elif action=='undo':run(new,'UNDO');assert snapshot(w)==before
   else:
    (w/'SYSTEM/CGA320.DRV').write_bytes(b'user-modified legacy driver');changed=snapshot(w)
    run(new,'320C',1);assert snapshot(w)==changed
   tests.append('accepted legacy'+str(version)+' '+action)
 result=dict(host='PASS',native='NOT_RUN',windows='NOT_TESTED',tests=tests,prepared_payload_files=len(P.COMPACT_FILES))
 write(root/'CMPINST.JSN',json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
if __name__=='__main__':main()
