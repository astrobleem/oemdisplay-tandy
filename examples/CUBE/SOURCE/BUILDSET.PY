"""Build the pinned, native DOS Cube installer with external Open Watcom."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,zlib
HERE=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('watcom','cube','shell','idle','old-shell','old-idle','out'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
    shutil.copyfile(HERE/'CUBESET.C',out/'CUBESET.C')
    crc=HERE.parents[2]/'tools/DOSINST/CRCFAST.H';shutil.copyfile(crc,out/'CRCFAST.H')
    lines=[];pins={}
    for name,path in [('CUBE',a.cube),('SHELL',a.shell),('IDLE',a.idle),('OLD',a.old_shell),('OLDIDLE',a.old_idle)]:
        data=path.read_bytes();pins[name]=dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),crc32=zlib.crc32(data))
        lines.extend([f'#define {name}_SIZE {len(data)}UL',f'#define {name}_CRC 0x{zlib.crc32(data):08x}UL'])
    (out/'CUBEPINS.H').write_bytes(('\r\n'.join(lines)+'\r\n').encode('ascii'))
    home=a.watcom.resolve();env=dict(os.environ,WATCOM=str(home),INCLUDE=str(home/'h'))
    env['PATH']=str(home/'binnt')+os.pathsep+env.get('PATH','')
    cmd=[str(home/'binnt/wcl.exe'),'-zq','-bt=dos','-0','-ms','-os','-k4096','-fe=CUBESET.EXE','CUBESET.C']
    r=subprocess.run(cmd,cwd=out,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (out/'BUILD.LOG').write_bytes(r.stdout)
    if r.returncode:raise RuntimeError(r.stdout.decode(errors='replace'))
    exe=(out/'CUBESET.EXE').read_bytes()
    result=dict(target='DOS 3.3+, 8086/8088',flags=cmd[1:],pins=pins,runtime=dict(bytes=len(exe),sha256=hashlib.sha256(exe).hexdigest()))
    (out/'BUILD.JSON').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
