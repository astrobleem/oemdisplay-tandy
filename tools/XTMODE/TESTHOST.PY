"""Exact C89 host build and isolated transaction/failure checks. No emulator."""
from pathlib import Path
import os,subprocess,tempfile,shutil,json,hashlib,struct,argparse
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
BASE=b'; keep bytes\r\n[boot.description]\r\n display.drv = Previous display ; comment\r\n[boot]\r\n shell = PROGMAN.EXE\r\nkeyboard.drv=KEYBOARD.DRV\r\nmouse.drv=MOUSE.DRV\r\n  fonts.fon = STOCKSYS.FON ; untouched spacing\r\n286grabber=CGA.GR2\r\ndisplay.drv=STOCK.DRV\r\noemfonts.fon=STOCKOEM.FON\r\nfixedfon.fon=STOCKFIX.FON\r\n[keyboard]\r\nlayout=US\r\n[mouse]\r\nspeed=7\r\n'

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--private-windows',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gcc',type=Path,required=True);a=ap.parse_args()
 out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);exe=out/'XTMHOST.EXE';env=os.environ.copy();env['PATH']=str(a.gcc.parent)+';'+env['PATH']
 build=subprocess.run([str(a.gcc),'-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-DHOST_TEST','-o',str(exe),str(HERE/'XTMODE.C')],env=env,capture_output=True,text=True)
 (out/'BUILD.LOG').write_bytes((build.stdout+build.stderr).encode());assert build.returncode==0,build.stderr
 root=Path(tempfile.mkdtemp(prefix='xm-fault-'));counter=0;checks=0;groups=[];failures=[]
 def fixture(data=BASE):
  nonlocal counter
  counter+=1;p=root/('%04d'%counter);p.mkdir();(p/'SYSTEM').mkdir();(p/'SYSTEM.INI').write_bytes(data)
  for f in json.loads((HERE/'PAYLOADS.JSN').read_bytes()):shutil.copyfile(REPO/'distributions/WINXT'/f['name'],p/'SYSTEM'/f['name'])
  shutil.copyfile(a.private_windows/'SYSTEM/CGA.GR2',p/'SYSTEM/CGA.GR2');shutil.copyfile(a.private_windows/'WIN.COM',p/'WIN.COM');return p
 def run(p,command,*args,crash=None,short=None,rename=None,windows=False):
  e=env.copy()
  for name,value in [('XM_CRASH',crash),('XM_SHORT',short),('XM_RENAME',rename),('XM_WINDOWS',1 if windows else None)]:
   if value is not None:e[name]=str(value)
  r=subprocess.run([str(exe),command,str(p/'SYSTEM.INI'),*args],env=e,capture_output=True,text=True)
  return r
 def require(v,detail):
  nonlocal checks
  checks+=1
  if not v:raise AssertionError(detail)
 def ok(r):require(r.returncode==0,(r.returncode,r.stdout,r.stderr))
 def gone(p):return not any(p.glob('XTMODE.*'))
 def safe_recover(p):
  ok(run(p,'RECOVER'));data=(p/'SYSTEM.INI').read_bytes()
  if data!=BASE:ok(run(p,'CHECK'));ok(run(p,'UNDO'))
  require((p/'SYSTEM.INI').read_bytes()==BASE,('restore',p));require(gone(p),('sidecars',p))
 try:
  p=fixture();ok(run(p,'SET','32016'));selected=(p/'SYSTEM.INI').read_bytes();before={q.name:q.read_bytes() for q in p.glob('XTMODE.*')};ok(run(p,'SET','32016'))
  require((p/'SYSTEM.INI').read_bytes()==selected,'Repeated SET changed INI');require(before=={q.name:q.read_bytes() for q in p.glob('XTMODE.*')},'Repeated SET changed journal')
  later=selected.replace(b'KEYBOARD.DRV',b'TANDYKBD.DRV').replace(b'MOUSE.DRV',b'NOMOUSE.DRV').replace(b'layout=US',b'layout=UK').replace(b'speed=7',b'speed=9')+b'[custom]\r\nnew=retained\r\n'
  (p/'SYSTEM.INI').write_bytes(later);ok(run(p,'SET','6404'));ok(run(p,'UNDO'));require((p/'SYSTEM.INI').read_bytes()==later,'UNDO did not restore previous tuple with all unrelated edits')
  ok(run(p,'UNDO'));require((p/'SYSTEM.INI').read_bytes()==later,'Second UNDO should be no-op without journal');groups.append('Repeated SET/no-op, one-level UNDO, later keyboard/mouse/layout/custom bytes retained')
  p=fixture();ok(run(p,'SET','32016'));(p/'SYSTEM.INI').write_bytes(later);ok(run(p,'UNDO'))
  require((p/'SYSTEM.INI').read_bytes()==BASE.replace(b'KEYBOARD.DRV',b'TANDYKBD.DRV').replace(b'MOUSE.DRV',b'NOMOUSE.DRV').replace(b'layout=US',b'layout=UK').replace(b'speed=7',b'speed=9')+b'[custom]\r\nnew=retained\r\n','UNDO arbitrary unrelated edits');groups.append('UNDO restores original controlled tuple and retains later unrelated edits')
  setpoints=0
  for step in range(1,20):
   p=fixture();r=run(p,'SET','6404',crash=step)
   if r.returncode==0:break
   require(r.returncode==99,('set',step,r.stderr));setpoints+=1;safe_recover(p)
  undo_points=0
  for step in range(1,30):
   p=fixture();ok(run(p,'SET','32016'));r=run(p,'UNDO',crash=step)
   if r.returncode==0:break
   require(r.returncode==99,('undo',step,r.stderr));undo_points+=1;safe_recover(p)
  nested=0
  for initial in range(1,setpoints+1):
   for stop in range(1,25):
    p=fixture();require(run(p,'SET','32016',crash=initial).returncode==99,('initial',initial));r=run(p,'RECOVER',crash=stop)
    if r.returncode==0:break
    require(r.returncode==99,('nested',initial,stop,r.stderr));nested+=1;safe_recover(p)
  groups.append({'set_completed_mutation_points':setpoints,'undo_completed_mutation_points':undo_points,'nested_recovery_crashes':nested})
  short_cases=0
  for cmd in ('SET','UNDO'):
   for step in range(1,8):
    p=fixture()
    if cmd=='UNDO':ok(run(p,'SET','32016'))
    before=(p/'SYSTEM.INI').read_bytes();r=run(p,cmd,*(['6404'] if cmd=='SET' else []),short=step)
    if r.returncode:
     short_cases+=1;require((p/'SYSTEM.INI').read_bytes()==before,('short-write preserved current',cmd,step));require(any(p.glob('XTMODE.*')),('short-write retains evidence',cmd,step))
  groups.append({'short_write_refusals':short_cases,'policy':'Partial unknown journal/temp retained, original/current INI unchanged; startup must refuse'})
  for cmd in ('SET','UNDO'):
   for point in (1,2):
    p=fixture()
    if cmd=='UNDO':ok(run(p,'SET','32016'))
    require(run(p,cmd,*(['6404'] if cmd=='SET' else []),rename=point).returncode!=0,('rename refusal',cmd,point));safe_recover(p)
  groups.append('Both rename operations refused during SET and UNDO; subsequent recovery passed')
  for command,args in [('SET',('6404',)),('UNDO',()),('RECOVER',()),('CHECK',()),('VERIFY',()),('GUARD',()),('FORGET',()),('ACCEPT',()),('MENU',()),('INSTALL',(str(REPO/'distributions/WINXT'),))]:
   p=fixture();ok(run(p,'SET','32016'));before={str(q.relative_to(p)):q.read_bytes() for q in p.rglob('*') if q.is_file()};r=run(p,command,*args,windows=True)
   require(r.returncode!=0,('Windows refusal',command));require(before=={str(q.relative_to(p)):q.read_bytes() for q in p.rglob('*') if q.is_file()},('Windows mutation',command))
  groups.append('Host-injected active-Windows refusal for every mutating and guarded command; native INT2F probes remain pending')
  for name in ('TR56404.DRV','XTCSYS.FON','XTCFIX.FON','XTCOEM.FON','XTSTATIC.LGO','WXTSPL01.RLE','CGA.GR2'):
   for damage in ('missing','truncated','signature'):
    p=fixture();f=p/'SYSTEM'/name;b=f.read_bytes()
    if damage=='missing':f.unlink()
    elif damage=='truncated':f.write_bytes(b[:-1])
    else:f.write_bytes(b'??'+b[2:])
    r=run(p,'SET','6404');require(r.returncode!=0,('resource refusal',name,damage));require((p/'SYSTEM.INI').read_bytes()==BASE,('resource changed INI',name,damage));require(gone(p),('resource produced journal',name,damage))
  for damage in ('missing','length','lgo','rle'):
   p=fixture();f=p/'WIN.COM';b=bytearray(f.read_bytes())
   if damage=='missing':f.unlink()
   elif damage=='length':f.write_bytes(b[:-1])
   else:b[3456 if damage=='lgo' else 3817]^=1;f.write_bytes(b)
   require(run(p,'SET','32016').returncode!=0,('WIN.COM refusal',damage));require((p/'SYSTEM.INI').read_bytes()==BASE,'WIN.COM changed INI')
  p=fixture();f=p/'SYSTEM/XTCSYS.FON';b=bytearray(f.read_bytes());fo=next(v['font_offset'] for v in json.loads((HERE/'PAYLOADS.JSN').read_bytes()) if v['name']=='XTCSYS.FON');b[fo+88]=9;f.write_bytes(b);require(run(p,'SET','6404').returncode!=0,'Wrong font metrics accepted')
  for at,value in ((118,0xffff),(120,0xffff),(95,255),(97,255)):
   p=fixture();f=p/'SYSTEM/XTCSYS.FON';b=bytearray(f.read_bytes());fo=1328
   if at in (118,120):struct.pack_into('<H',b,fo+at,value)
   else:b[fo+at]=value
   f.write_bytes(b);require(run(p,'SET','6404').returncode!=0,('FNT boundary',at))
  groups.append('Missing/truncated/wrong signatures, common loader components, FNT metrics/coverage/width/offset refusals before INI mutation')
  p=fixture();shutil.copyfile(p/'SYSTEM/XTCFIX.FON',p/'SYSTEM/XTTSYS.FON');require(run(p,'SET','TEXT','/TEXT').returncode!=0,'Same-size wrong font accepted');require(gone(p),'Wrong font mutated journal');groups.append('Same-size wrong font face/module refused')
  for value,expected in [('C:\\WINDOWS\\SYSTEM.INI',0),('D:\\TOOLS_1\\SYSTEM.INI',0),('C:\\LONGERDIR\\SYSTEM.INI',1),('C:\\WIN DOWS\\SYSTEM.INI',1),('C:\\..\\SYSTEM.INI',1),('C:\\WINDOWS\\BAD..INI',1),('C:WINDOWS\\SYSTEM.INI',1)]:
   r=subprocess.run([str(exe),'PATHCHECK',value],env=env,capture_output=True,text=True);require((r.returncode==0)==(expected==0),('8.3 validation',value))
  groups.append('Exact native DOS path validator accepts/refuses host-supplied 8.3 cases')
  malformed=[b'',BASE+b'\0',BASE+b'[BOOT]\r\nx=1\r\n',BASE.replace(b'[boot]',b'[boot]junk'),BASE.replace(b'fonts.fon = STOCKSYS.FON',b'fonts.fon = '),BASE.replace(b'keyboard.drv',b'display.drv'),BASE+b'x'*16001]
  for data in malformed:
   p=fixture(data);r=run(p,'SET','32016');require(r.returncode!=0,('INI rejection',data[:30]));require((p/'SYSTEM.INI').read_bytes()==data,'Malformed INI changed')
  for name in ('XTMODE.JRN','XTMODE.NEW','XTMODE.OLD','XTMODE.RST'):
   p=fixture();(p/name).write_bytes(b'foreign');require(run(p,'SET','32016').returncode!=0,('collision',name));require((p/name).read_bytes()==b'foreign','Foreign file changed')
  p=fixture();ok(run(p,'SET','32016'));j=p/'XTMODE.JRN';b=bytearray(j.read_bytes());b[-1]^=1;j.write_bytes(b);current=(p/'SYSTEM.INI').read_bytes();require(run(p,'RECOVER').returncode!=0,'Corrupt journal accepted');require((p/'SYSTEM.INI').read_bytes()==current,'Corrupt journal changed INI')
  p=fixture();ok(run(p,'SET','32016'));foreign=(p/'SYSTEM.INI').read_bytes().replace(b'TR53216.DRV',b'FOREIGN.DRV');(p/'SYSTEM.INI').write_bytes(foreign);require(run(p,'UNDO').returncode!=0,'Foreign tuple accepted');require((p/'SYSTEM.INI').read_bytes()==foreign,'Foreign tuple overwritten')
  p=fixture();r=run(p,'SET','TEXT');require(r.returncode!=0,'Text authorization ignored');require(gone(p),'Unapproved text produced journal');ok(run(p,'SET','TEXT','/TEXT'));ok(run(p,'UNDO'));groups.append('Malformed INI, sidecar collision, corrupt journal, foreign tuple and explicit text refusal checks')
  spaced=BASE.replace(b'display.drv=STOCK.DRV',b'DISPLAY.DRV = STOCK.DRV ; prior display comment');p=fixture(spaced);ok(run(p,'SET','32016'));require(b'display.drv=TR53216.DRV\r\n' in (p/'SYSTEM.INI').read_bytes(),'Canonical driver form for existing wave eligibility');ok(run(p,'UNDO'));require((p/'SYSTEM.INI').read_bytes()==spaced,'UNDO did not restore prior complete display line');groups.append('Controlled display line canonicalized for existing wave parser; UNDO restores prior line bytes')
 except Exception as e:
  failures.append(str(e));raise
 finally:
  report={'host_only':True,'qualified':False,'fixture_root':str(root),'checks':checks,'groups':groups,'failures':failures,'source_sha256':hashlib.sha256((HERE/'XTMODE.C').read_bytes()).hexdigest(),'compiler':str(a.gcc),'compiler_sha256':hashlib.sha256(a.gcc.read_bytes()).hexdigest(),'native_tests':False}
  (out/'RESULTS.JSN').write_bytes(json.dumps(report,indent=2).replace('\n','\r\n').encode());print(json.dumps({'checks':checks,'groups':groups,'failures':failures},indent=2))
if __name__=='__main__':main()
