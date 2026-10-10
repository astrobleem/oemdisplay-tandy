"""Host copy-transaction, launcher-guard and ownership fault tests."""
from pathlib import Path
import os,subprocess,shutil,tempfile,json,hashlib,argparse,math
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--private-windows',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--exe',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False)
 root=Path(tempfile.mkdtemp(prefix='xm-copy-'));source=root/'SOURCE';source.mkdir();payload=json.loads((HERE/'PAYLOADS.JSN').read_bytes())
 for v in payload:shutil.copyfile(REPO/'distributions/WINXT'/v['name'],source/v['name'])
 BASE=(a.private_windows/'SYSTEM.INI').read_bytes();counter=checks=0;groups=[];failures=[]
 env=os.environ.copy();env['PATH']=r'C:\msys64\ucrt64\bin;'+env['PATH']
 def fixture():
  nonlocal counter
  counter+=1;p=root/('%04d'%counter);p.mkdir();(p/'SYSTEM').mkdir();(p/'SYSTEM.INI').write_bytes(BASE);shutil.copyfile(a.private_windows/'SYSTEM/CGA.GR2',p/'SYSTEM/CGA.GR2');shutil.copyfile(a.private_windows/'WIN.COM',p/'WIN.COM');return p
 def run(p,cmd,*args,crash=None,short=None,rename=None):
  e=env.copy()
  for k,v in [('XM_CRASH',crash),('XM_SHORT',short),('XM_RENAME',rename)]:
   if v is not None:e[k]=str(v)
  return subprocess.run([str(a.exe.resolve()),cmd,str(p/'SYSTEM.INI'),*args],env=e,capture_output=True,text=True)
 def check(value,detail):
  nonlocal checks
  checks+=1
  if not value:raise AssertionError(detail)
 def ok(r):check(r.returncode==0,(r.returncode,r.stdout,r.stderr))
 def exact(p):
  check((p/'SYSTEM.INI').read_bytes()==BASE,'INSTALL changed original INI')
  for v in payload:check((p/'SYSTEM'/v['name']).read_bytes()==(source/v['name']).read_bytes(),('copy',v['name']))
  check(not(p/'XTFILES.JRN').exists() and not(p/'XTFILES.NEW').exists(),'pending copy after install')
 try:
  p=fixture();ok(run(p,'INSTALL',str(source)));exact(p);before={str(q.relative_to(p)):q.read_bytes() for q in p.rglob('*') if q.is_file()};ok(run(p,'INSTALL',str(source)));check(before=={str(q.relative_to(p)):q.read_bytes() for q in p.rglob('*') if q.is_file()},'Repeated INSTALL changed files')
  ok(run(p,'SET','6404'));ok(run(p,'GUARD'));ok(run(p,'ACCEPT'));check(not(p/'XTMODE.JRN').exists(),'ACCEPT retained history');ok(run(p,'FORGET'));check(not(p/'XTFILES.RDY').exists(),'FORGET retained active marker');groups.append('Install-all exact, repeated INSTALL/no-op, GUARD/ACCEPT/FORGET with active mode')
  points=0
  for stop in range(1,80):
   p=fixture();r=run(p,'INSTALL',str(source),crash=stop)
   if r.returncode==0:break
   check(r.returncode==99,('copy crash',stop,r.stderr));points+=1;check((p/'SYSTEM.INI').read_bytes()==BASE,('INI at crash',stop))
   if (p/'XTFILES.JRN').exists() or (p/'XTFILES.NEW').exists():check(run(p,'GUARD').returncode!=0,('pending copy startup escape',stop))
   ok(run(p,'INSTALL',str(source)));exact(p);ok(run(p,'GUARD'))
  groups.append({'install_completed_mutation_crashes':points})
  nested=0
  for first in (1,2,3):
   for second in range(1,8):
    p=fixture();check(run(p,'INSTALL',str(source),crash=first).returncode==99,'Initial copy crash');r=run(p,'INSTALL',str(source),crash=second)
    if r.returncode==0:break
    check(r.returncode==99,('nested copy',first,second,r.stderr));nested+=1;ok(run(p,'INSTALL',str(source)));exact(p)
  groups.append({'nested_copy_recovery_crashes':nested})
  writes=len(payload)+sum(math.ceil(v['size']/4096) for v in payload)+1
  for stop in (1,2,3,writes):
   p=fixture();r=run(p,'INSTALL',str(source),short=stop);check(r.returncode!=0,('short copy',stop));check((p/'SYSTEM.INI').read_bytes()==BASE,'Short copy changed INI');check(run(p,'GUARD').returncode!=0,('short-copy startup escape',stop))
   if stop in (2,3):ok(run(p,'INSTALL',str(source)));exact(p)
   else:check(run(p,'INSTALL',str(source)).returncode!=0,'Incomplete metadata should retain evidence')
  groups.append('Short copy bytes recover by verified source-prefix ownership; short metadata refuses and retains evidence')
  for stop in (1,5,15):
   p=fixture();check(run(p,'INSTALL',str(source),rename=stop).returncode!=0,('copy rename refusal',stop));ok(run(p,'INSTALL',str(source)));exact(p)
  groups.append('Resource rename refusal/retry at first, middle and final copied files')
  p=fixture();check(run(p,'INSTALL',str(source),crash=1).returncode==99,'Copy ownership crash');(p/'XTFILES.NEW').write_bytes(b'foreign');check(run(p,'INSTALL',str(source)).returncode!=0,'Foreign staging adopted');check((p/'XTFILES.NEW').read_bytes()==b'foreign','Foreign staging erased')
  p=fixture();(p/'SYSTEM/XTCFIX.FON').write_bytes((source/'XTTSYS.FON').read_bytes());check(run(p,'INSTALL',str(source)).returncode!=0,'Wrong existing destination replaced');check(not(p/'XTFILES.JRN').exists(),'Wrong destination started transaction')
  for name in ('WIN.COM','SYSTEM/CGA.GR2'):
   p=fixture();(p/name).unlink();check(run(p,'INSTALL',str(source)).returncode!=0,('Common missing',name));check(not(p/'XTFILES.JRN').exists(),'Missing common started copy');check(len(list((p/'SYSTEM').iterdir()))<=1,'Missing common copied assets')
  groups.append('Foreign partial staging, same-size wrong existing font, missing common resources refused without overwrite')
 except Exception as e:failures.append(str(e));raise
 finally:
  report={'host_only':True,'qualified':False,'checks':checks,'groups':groups,'failures':failures,'fixture_root':str(root),'source_sha256':hashlib.sha256((HERE/'XTMODE.C').read_bytes()).hexdigest(),'native_tests':False};(out/'RESULTS.JSN').write_bytes(json.dumps(report,indent=2).replace('\n','\r\n').encode());print(json.dumps({'checks':checks,'groups':groups,'failures':failures},indent=2))
if __name__=='__main__':main()
