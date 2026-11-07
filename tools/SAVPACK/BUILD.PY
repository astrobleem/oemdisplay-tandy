"""Compile the final installer sources with an explicitly supplied Open Watcom.

Uses a fresh private output directory. Does not rebind, accept or publish bytes.
"""
from pathlib import Path
import argparse,os,shutil,subprocess
HERE=Path(__file__).resolve().parent
def build(source,out,watcom):
 assert not out.exists(),'Fresh output directory required'
 out.mkdir(parents=True)
 for p in source.iterdir():
  if p.suffix.upper() in ('.C','.H','.ASM'):shutil.copyfile(p,out/p.name)
 compiler=watcom/'binnt/wcl.exe'
 assert compiler.is_file(),'Supply the installed native Open Watcom root'
 env=dict(os.environ,WATCOM=str(watcom),INCLUDE=str(watcom/'h'))
 env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
 for name,opts in [('CPSET',['-ml','-s','-k8192']),('FIXXT',['-ms','-k8192']),('SETUP',['-ml'])]:
  subprocess.run([str(compiler),'-zq','-bt=dos','-0','-os',*opts,'-fe='+name+'.EXE',name+'.C'],cwd=out,env=env,check=True)
 print('Compiled final pinned sources; compare outputs with qualified package before use.')
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,default=HERE/'NATIVE');p.add_argument('--out',type=Path,required=True);p.add_argument('--watcom',type=Path,required=True);a=p.parse_args();build(a.source,a.out,a.watcom)
