"""Check actual CPSET current-metadata migration and retained refusal guards."""
from pathlib import Path
import argparse,hashlib,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[2]
def inventory(p):return {q.relative_to(p).as_posix():q.read_bytes() for q in p.rglob('*') if q.is_file()}
ap=argparse.ArgumentParser();
for n in ('current','legacy','keyboard','out'):ap.add_argument('--'+n,type=Path,required=True)
a=ap.parse_args();a.out.mkdir(exist_ok=False);exe=a.out/'CPTEST.EXE';source=ROOT/'tools/UPAN/CPSET.C'
r=subprocess.run([sys.executable,str(Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'),'--','-x','c','-std=c89','-DHOST_TEST','-DHOST_WINDOWS',str(source),'-o',str(exe)],capture_output=True,text=True);(a.out/'BUILD.LOG').write_text(r.stdout+r.stderr);assert not r.returncode,r.stderr
with tempfile.TemporaryDirectory(prefix='cp-guard-') as tmp:
 w=Path(tmp)/'W';system=w/'SYSTEM';system.mkdir(parents=True);shutil.copyfile(a.keyboard,system/'TNDYK3.DRV')
 systemini=b'[boot]\r\nsystem.drv=system.drv\r\nsound.drv=sound.drv\r\ncomm.drv=comm.drv\r\nkeyboard.drv=TNDYK3.DRV\r\n[boot.description]\r\nsystem.drv=Tandy 1000 EX/HX (WindowsXT)\r\n'
 (w/'SYSTEM.INI').write_bytes(systemini);meta=system/'SETUP.INF';marker=system/'CPREADY.OK';arg=w.as_posix();checks=[]
 def mark(size):return ('CPLEAN1\r\n'+arg+'/SYSTEM/SETUP.INF\r\n'+str(size)+'\r\n').encode()
 def run(mode,extra=None):return subprocess.run([str(exe.resolve()),mode,arg],capture_output=True,text=True,env=dict(os.environ,**(extra or {})))
 old=a.legacy.read_bytes();current=a.current.read_bytes();assert len(old)==49840 and len(current)==49848
 for data,size in [(old,49840),(current,49848)]:
  meta.write_bytes(data);marker.write_bytes(mark(49840));before=meta.read_bytes();r=run('APPLY');assert not r.returncode,r.stdout+r.stderr
  assert meta.read_bytes()==before and (w/'SYSTEM.INI').read_bytes()==systemini and marker.read_bytes()==mark(size)
  r=run('READY');assert not r.returncode,r.stderr
  before=inventory(w);r=run('APPLY');assert not r.returncode and inventory(w)==before,r.stderr
 checks.append('legacy49840 and exact current49848 Apply/Ready; owned old marker migration; metadata and active selections unchanged; repeated Apply no-op')
 meta.write_bytes(current);marker.write_bytes(b'FOREIGN\r\n');before=inventory(w);r=run('APPLY');assert r.returncode and inventory(w)==before,r.stdout+r.stderr
 checks.append('foreign marker refusal preserves all installed bytes')
 for data in [bytes([current[0]^1])+current[1:],current+b'X']:
  meta.write_bytes(data);marker.write_bytes(mark(49840));before=inventory(w);r=run('APPLY');assert r.returncode and inventory(w)==before,r.stdout+r.stderr
 checks.append('changed current metadata and unsupported length refused before writing')
 meta.write_bytes(current);marker.write_bytes(mark(49840));before=inventory(w);r=run('APPLY',{'CP_WINDOWS':'1'});assert r.returncode and inventory(w)==before
 checks.append('Windows-running refusal retained')
 result=dict(outcome='PASS_HOST_CPSET_GUARDS',source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),checks=checks)
 (a.out/'RESULT.JSN').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
