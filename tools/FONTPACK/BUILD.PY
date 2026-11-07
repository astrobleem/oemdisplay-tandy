"""Rebuild font-release native installers with explicitly supplied Open Watcom."""
from pathlib import Path
import argparse,hashlib,os,re,shutil,subprocess,zlib
HERE=Path(__file__).resolve().parent
CPSET_SHA='245e858eb2fe1153f57838aa8ef0499af75bbcc913484819379bdab57cca4f42'
def write(path,text):path.write_bytes(text.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def compile_one(source,out,watcom):
 out.mkdir()
 for p in source.iterdir():
  if p.suffix.upper() in ('.C','.H','.ASM'):shutil.copyfile(p,out/p.name)
 compiler=watcom/'binnt/wcl.exe';assert compiler.is_file(),'Native Windows Open Watcom required'
 env=dict(os.environ,WATCOM=str(watcom),INCLUDE=str(watcom/'h'));env['PATH']=str(compiler.parent)+os.pathsep+env.get('PATH','')
 def run(name,opts):subprocess.run([str(compiler),'-zq','-bt=dos','-0','-os',*opts,'-fe='+name+'.EXE',name+'.C'],cwd=out,env=env,check=True)
 run('CPSET',['-ml','-s','-k8192'])
 assert hashlib.sha256((out/'CPSET.EXE').read_bytes()).hexdigest()==CPSET_SHA,'Toolchain differs from unchanged accepted CPSET'
 run('FIXXT',['-ms','-k8192'])
 data=(out/'FIXXT.EXE').read_bytes()
 pins=(out/'SETPINS.H').read_text();pins,n=re.subn(r'\{"FIXXT.EXE","[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL\}',lambda m:'{"FIXXT.EXE","%s",%dUL,0,0x%08xUL}'%(hashlib.sha256(data).hexdigest(),len(data),zlib.crc32(data)),pins);assert n==1
 write(out/'SETPINS.H',pins)
 files=(out/'SETFILES.H').read_text();files,n=re.subn(r'(,"FIXXT.EXE",)\d+UL',lambda m:m[1]+str(len(data))+'UL',files);assert n==2
 write(out/'SETFILES.H',files)
 # Large-model far string pointers permit read-only literals in code segments.
 # Added font inventories otherwise exhaust the legacy 64 KB near data group.
 run('SETUP',['-ml','-zc'])
 # Separate native fault-injection binary is never part of the consumer packet.
 subprocess.run([str(compiler),'-zq','-bt=dos','-0','-os','-ms','-k8192','-dFONT_TEST','-fe=FXTEST.EXE','FIXXT.C'],cwd=out,env=env,check=True)
def build(source,out,watcom):
 assert not out.exists(),'Fresh output directory required';out.mkdir(parents=True)
 compile_one(source,out/'native',watcom);compile_one(source,out/'repeat',watcom)
 for name in ('CPSET.EXE','FIXXT.EXE','SETUP.EXE','FXTEST.EXE','SETPINS.H','SETFILES.H'):
  assert (out/'native'/name).read_bytes()==(out/'repeat'/name).read_bytes(),'Rebuild mismatch: '+name
 print('PASS: CPSET matches accepted baseline; FIXXT/SETUP exact independent native rebuild equality.')
if __name__=='__main__':
 a=argparse.ArgumentParser(description=__doc__);a.add_argument('--source',type=Path,default=HERE/'NATIVE');a.add_argument('--out',type=Path,required=True);a.add_argument('--watcom',type=Path,required=True);v=a.parse_args();build(v.source,v.out,v.watcom)
