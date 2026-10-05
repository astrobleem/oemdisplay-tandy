#!/usr/bin/env python3
"""Exact-source host fault matrix. QA pin is local to qa/, not release source."""
import hashlib,json,os,pathlib,shutil,subprocess,tempfile
R=pathlib.Path(__file__).resolve().parent
Q=R/'qa';Q.mkdir(exist_ok=True)
for name in ['BUILD.BAT','BUILD.PY']:shutil.copyfile(R/name,Q/name)
D=((R.parent/'TNDYK3.DRV') if (R.parent/'TNDYK3.DRV').exists() else (R.parent/'work/TNDYK3.DRV')).read_bytes()
(Q/'K3SET.C').write_bytes((R/'K3SET.C').read_bytes())
(Q/'K3PIN.H').write_text('#define K3_PIN_READY 1\n#define K3_PIN_SIZE %dUL\n#define K3_PIN_SHA256 "%s"\n'%(len(D),hashlib.sha256(D).hexdigest()))
flags=['gcc','-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-DHOST_TEST']
if os.getenv('SANITIZE'): flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie','-g']
EXE=Q/'k3set-host';subprocess.run(flags+['-o',str(EXE),str(Q/'K3SET.C')],check=True)
BASE=b'; keep\r\n[boot]\r\n  Keyboard.drv = KEYBOARD.DRV  ; original\r\nshell=TSHELL.EXE\r\n[keyboard]\r\nx=1\r\n'
NEW=BASE.replace(b'KEYBOARD.DRV',b'TNDYK3.DRV');OLD=b'MZ original keyboard bytes\x00\xff'
count=0;checks={}
def fixture(data=BASE):
 p=pathlib.Path(tempfile.mkdtemp(prefix='k3test-'));(p/'SYSTEM').mkdir();(p/'SYSTEM.INI').write_bytes(data);(p/'SYSTEM/KEYBOARD.DRV').write_bytes(OLD);(p/'TNDYK3.DRV').write_bytes(D);return p
def run(p,cmd,crash=None,short=None,windows=False):
 e=os.environ.copy()
 if crash:e['K3_CRASH']=str(crash)
 if short:e['K3_SHORT']=str(short)
 if windows:e['K3_WINDOWS']='1'
 r=subprocess.run([str(EXE),cmd,str(p/'SYSTEM.INI')],cwd=p,env=e,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert b'AddressSanitizer' not in r.stderr and b'runtime error:' not in r.stderr,r.stderr
 return r
def ok(r):assert r.returncode==0,(r.returncode,r.stdout,r.stderr)
def check(x,why=''):
 global count
 assert x,why
 count+=1
def done(p):shutil.rmtree(p)
def state(p):return {str(f.relative_to(p)):f.read_bytes() for f in p.rglob('*') if f.is_file()}
p=fixture();before=state(p);ok(run(p,'CHECK'));check(state(p)==before);ok(run(p,'APPLY'));ok(run(p,'APPLY'));check((p/'SYSTEM.INI').read_bytes()==NEW);check((p/'K3ORIG.BAK').read_bytes()==OLD);check((p/'SYSTEM/KEYBOARD.DRV').read_bytes()==OLD)
changed=NEW.replace(b'x=1',b'x=2\r\nnew=later');(p/'SYSTEM.INI').write_bytes(changed);(p/'TNDYK3.DRV').unlink();ok(run(p,'RESTORE'));check((p/'SYSTEM.INI').read_bytes()==changed.replace(b'TNDYK3.DRV',b'KEYBOARD.DRV'));ok(run(p,'RESTORE'));check((p/'K3SEL.BAK').read_bytes()==BASE);done(p)
for cmd in ['APPLY','RESTORE']:
 for step in range(1,40):
  p=fixture()
  if cmd=='RESTORE':ok(run(p,'APPLY'));(p/'SYSTEM.INI').write_bytes(changed)
  r=run(p,cmd,crash=step)
  if r.returncode==0:done(p);break
  check(r.returncode==99,(cmd,step,r.stderr));ok(run(p,'RESTORE'))
  want=BASE if cmd=='APPLY' else changed.replace(b'TNDYK3.DRV',b'KEYBOARD.DRV')
  check((p/'SYSTEM.INI').read_bytes()==want,(cmd,step));ok(run(p,'APPLY'));ok(run(p,'RESTORE'));done(p)
 checks[cmd+'_mutation_checkpoints']=step-1
for initial in range(1,checks['APPLY_mutation_checkpoints']+1):
 for stop in range(1,30):
  p=fixture();check(run(p,'APPLY',crash=initial).returncode==99);r=run(p,'RESTORE',crash=stop)
  if r.returncode==0:done(p);break
  check(r.returncode==99,(initial,stop,r.stderr));ok(run(p,'RESTORE'));check((p/'SYSTEM.INI').read_bytes()==BASE);done(p)
# Every completed APPLY mutation can also be resumed by APPLY.
for step in range(1,checks['APPLY_mutation_checkpoints']+1):
 p=fixture();check(run(p,'APPLY',crash=step).returncode==99);ok(run(p,'APPLY'));check((p/'SYSTEM.INI').read_bytes()==NEW);ok(run(p,'RESTORE'));done(p)
for data in [b'',BASE+b'[boot]\r\nkeyboard.drv=x\r\n',BASE+b'[KEYBOARD]\r\nx=2\r\n',BASE.replace(b'shell=',b'keyboard.drv='),BASE.replace(b'KEYBOARD.DRV',b''),BASE+b'\0',BASE+b'x'*16001,BASE.replace(b'[boot]',b'[boot]junk'),BASE.replace(b'KEYBOARD.DRV',b'TNDYK3.DRV'),BASE.replace(b'KEYBOARD.DRV',b'X'),BASE.replace(b'KEYBOARD.DRV',b'..\\KEYBOARD.DRV'),BASE.replace(b'KEYBOARD.DRV',b'C:\\KEYBOARD.DRV')]:
 p=fixture(data);before=state(p);check(run(p,'APPLY').returncode!=0);check(state(p)==before);done(p)
for name in ['K3SEL.JRN','K3SEL.SAV','K3SEL.BAK','K3SEL.NEW','K3SEL.OLD','K3SEL.RST','K3ORIG.SAV','K3ORIG.BAK','SYSTEM/TNDYK3.DRV','SYSTEM/K3DRV.NEW']:
 p=fixture();(p/name).write_bytes(b'foreign');before=state(p);check(run(p,'APPLY').returncode!=0,name);check(state(p)==before,name);done(p)
for cmd in ['CHECK','APPLY','RESTORE']:
 p=fixture();before=state(p);check(run(p,cmd,windows=True).returncode!=0);check(state(p)==before);done(p)
for cmd in ['APPLY','RESTORE']:
 for step in range(1,checks[cmd+'_mutation_checkpoints']+2):
  p=fixture()
  if cmd=='RESTORE':ok(run(p,'APPLY'))
  before=(p/'SYSTEM.INI').read_bytes();r=run(p,cmd,short=step)
  if r.returncode:check((p/'SYSTEM.INI').read_bytes()==before,(cmd,step));check((p/'SYSTEM/KEYBOARD.DRV').read_bytes()==OLD)
  done(p)
for name in ['K3SEL.BAK','K3SEL.SAV','K3ORIG.BAK','K3ORIG.SAV','SYSTEM/TNDYK3.DRV','SYSTEM/KEYBOARD.DRV']:
 p=fixture();ok(run(p,'APPLY'));(p/name).write_bytes(b'changed');before=state(p);check(run(p,'RESTORE').returncode!=0,name);check(state(p)==before,name);done(p)
p=fixture();ok(run(p,'APPLY'));alien=NEW.replace(b'TNDYK3.DRV',b'OTHER.DRV');(p/'SYSTEM.INI').write_bytes(alien);before=state(p);check(run(p,'RESTORE').returncode!=0);check(state(p)==before);done(p)
p=fixture();(p/'KEYBOARD.DRV').write_bytes(OLD);before=state(p);check(run(p,'APPLY').returncode!=0);check(state(p)==before);done(p)
p=fixture();(p/'SYSTEM.INI').chmod(0o444);before=state(p);check(run(p,'APPLY').returncode!=0);check(state(p)==before);done(p)
for data in [BASE.replace(b'\r\n',b'\n'),BASE.replace(b'\r\n',b'\r'),BASE.rstrip(b'\r\n')]:
 p=fixture(data);ok(run(p,'APPLY'));ok(run(p,'RESTORE'));check((p/'SYSTEM.INI').read_bytes()==data);done(p)
# Same-length package mutation cannot pass the SHA-256 pin.
p=fixture();bad=bytearray(D);bad[-1]^=1;(p/'TNDYK3.DRV').write_bytes(bad);before=state(p);check(run(p,'APPLY').returncode!=0);check(state(p)==before);done(p)
# Unknown missing current and edits after an interrupted restoration are never guessed.
p=fixture();ok(run(p,'APPLY'));(p/'SYSTEM.INI').unlink();before=state(p);check(run(p,'RESTORE').returncode!=0);check(state(p)==before);done(p)
p=fixture();ok(run(p,'APPLY'));check(run(p,'RESTORE',crash=1).returncode==99);(p/'SYSTEM.INI').write_bytes(NEW+b'changed=after-restore-started\r\n');before=state(p);check(run(p,'RESTORE').returncode!=0);check(state(p)==before);done(p)
# Journal cleanup refusal retains the recovery proof.
p=fixture();ok(run(p,'APPLY'));(p/'K3SEL.JRN').chmod(0o444);check(run(p,'RESTORE').returncode!=0);check((p/'SYSTEM.INI').read_bytes()==BASE);check((p/'K3SEL.JRN').exists());(p/'K3SEL.JRN').chmod(0o644);ok(run(p,'RESTORE'));done(p)
# Maximum supported original-driver size and INI size, then one byte over.
p=fixture(BASE+b';'+b'x'*(14000-len(BASE)-1));(p/'SYSTEM/KEYBOARD.DRV').write_bytes(b'k'*14000);before=(p/'SYSTEM.INI').read_bytes();ok(run(p,'APPLY'));ok(run(p,'RESTORE'));check((p/'SYSTEM.INI').read_bytes()==before);check((p/'K3ORIG.BAK').read_bytes()==b'k'*14000);done(p)
p=fixture(BASE+b';'+b'x'*(14001-len(BASE)-1));before=state(p);check(run(p,'APPLY').returncode!=0);check(state(p)==before);done(p)
report={'passed':count,'checkpoints':checks,'sanitizers':bool(os.getenv('SANITIZE')),'driver_candidate_sha256':hashlib.sha256(D).hexdigest(),'source_sha256':hashlib.sha256((R/'K3SET.C').read_bytes()).hexdigest()}
print(json.dumps(report,indent=2));(R/('SANITIZER.JSON' if os.getenv('SANITIZE') else 'HOSTTEST.JSON')).write_text(json.dumps(report,indent=2)+'\n')
