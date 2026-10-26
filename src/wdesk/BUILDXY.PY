"""Build the existing Watcom XY helper plus the explicit placement dependency.

Developer compile/link evidence only. No emulator, installer or pin changes.
"""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess
here=Path(__file__).resolve().parent;repo=here.parents[1]
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--out',type=Path,required=True)
p.add_argument('--placement',type=Path,default=here/'PLACE')
a=p.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
for folder,names in [(repo/'experiments/XYOVERVIEW',['XYCTL.C','XYCTL.LNK']),
                     (repo/'src/panui',['PANSET.C','PANSET.H','PANDLG.C','PANDLG.H']),
                     (here,['WDCORE.C','WDCORE.H','WDWIN.C','WDWIN.H']),
                     (a.placement,['WTPLACE.C','WTPLACE.H'])]:
    for n in names:shutil.copyfile(folder/n,out/n)
env=dict(os.environ,WATCOM=r'C:\WATCOM');commands=[]
for n in ['XYCTL.C','PANSET.C','PANDLG.C','WDCORE.C','WDWIN.C','WTPLACE.C']:
    cmd=[r'C:\WATCOM\BINNT\WCC.EXE','-zW','-0','-ms',
         r'-IC:\WATCOM\H',r'-IC:\WATCOM\H\WIN','-I'+str(out),n]
    result=subprocess.run(cmd,cwd=out,env=env,capture_output=True,timeout=30)
    (out/(n+'.LOG')).write_bytes(result.stdout+result.stderr)
    text=(result.stdout+result.stderr).decode('ascii',errors='replace')
    assert result.returncode==0 and 'Error!' not in text and 'Warning!' not in text,(n,text)
    commands.append(cmd)
cmd=[r'C:\WATCOM\BINNT\WLINK.EXE','@XYCTL.LNK']
result=subprocess.run(cmd,cwd=out,env=env,capture_output=True,timeout=30)
(out/'LINK.LOG').write_bytes(result.stdout+result.stderr)
assert result.returncode==0,(result.stdout,result.stderr)
b=(out/'XYCTL.EXE').read_bytes();assert b[:2]==b'MZ' and b[int.from_bytes(b[60:64],'little'):][:2]==b'NE'
record={'status':'BUILT_NOT_NATIVE_QUALIFIED','binary':{'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()},
        'commands':commands+[cmd],'source':{f.name:{'bytes':len(f.read_bytes()),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()}
             for f in out.iterdir() if f.suffix.upper() in ['.C','.H','.LNK']}}
(out/'BUILD.JSON').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps({'status':record['status'],'binary':record['binary']},indent=2))
