"""Prepare only fresh private Setup/rollback and loader-failure fixtures."""
from pathlib import Path
import hashlib,json,shutil,sys,struct
ROOT=Path(__file__).resolve().parents[2];WORK=ROOT.parent;OUT=WORK/'STATIC-NATIVE'
sys.path.insert(0,str(ROOT/'tools/XTFONTS'))
from NATIVE import config
from PIL import Image
def tf(p,s):p.write_bytes(s.replace('\r\n','\n').replace('\n','\r\n').encode('ascii'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def files(p):return {str(f.relative_to(p)):sha(f) for f in p.rglob('*') if f.is_file()}
def queue(num,name,cfg,seconds=60):tf(OUT/'QUEUE'/('%02d-%s.JSON'%(num,name)),json.dumps({'config':str(cfg),'purpose':name,'seconds':seconds}))
def prepare():
 source=WORK/'FONT-NATIVE6/INSTALL/GUEST';old=source.joinpath('START.BAT').read_text('ascii')
 auto=next(l for l in old.splitlines() if l.startswith('AUTOTYPE '))
 needle='down down down down down down enter '+', '*25+'enter'
 assert needle in auto
 report={}
 for index,driver in enumerate(('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE')):
  case=OUT/driver;guest=case/'GUEST';guest.mkdir(parents=True)
  shutil.copytree(source/'WINDOWS',guest/'WINDOWS')
  (guest/'WINDOWS/SYSTEM/CGALOGO.LGO').unlink()
  (guest/'MEDIA').mkdir();(guest/'SOURCEOS/SYSTEM').mkdir(parents=True)
  shutil.copyfile(source/'WINDOWS/SYSTEM/CGA.GR2',guest/'MEDIA/CGA.GR2')
  for n in ('FONTPRB.EXE','FONENC.EXE') :shutil.copyfile(source/n,guest/n)
  for n in ('MEMSNAP.COM','TEXT3.COM') :shutil.copyfile(Path(r'C:\Users\chad\Documents\Codex\2026-10-08\task-2')/n,guest/n)
  tf(guest/'YES.TXT','Y\n');tf(guest/'CONFIG.SYS','FILES=30\nBUFFERS=20\n');tf(guest/'AUTOEXEC.BAT','@ECHO OFF\n')
  report[driver]={'windows':files(guest/'WINDOWS'),'boot':{n:sha(guest/n) for n in ('CONFIG.SYS','AUTOEXEC.BAT')}}
  selected=auto.replace(needle,'home '+('down '*index)+'enter '+', '*25+'enter')
  batch='@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nC:\n'
  batch+='D:\\PREPD A:\\WINXT C:\\SOURCEOS C:\\MEDIA < C:\\YES.TXT > C:\\PREP.LOG\nIF ERRORLEVEL 1 GOTO FAIL\n'
  batch+='CD \\WINXT\nD:\\TINSTD C:\\WINDOWS > C:\\INSTALL.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO OK>C:\\INST.OK\n'
  batch+=selected+'\nCD \\WINDOWS\nCOMMAND.COM /C C:\\WINXT\\WINXT.BAT SETUP > C:\\SETUP.LOG\n'
  batch+='COPY SYSTEM.INI C:\\SELECTED.INI >NUL\nCOPY WIN.COM C:\\SELECTED.COM >NUL\nCOPY XTTEST.COM C:\\SELECTED.WAV >NUL\nECHO OK>C:\\SETUP.OK\n'
  batch+='C:\\MEMSNAP > C:\\BEFORE.LOG\nCOMMAND.COM /C C:\\WINXT\\WINXT.BAT > C:\\WAVE.LOG\nIF NOT EXIST C:\\FONT.LOG GOTO FAIL\nCOPY C:\\FONT.LOG C:\\WAVEFONT.LOG >NUL\nC:\\MEMSNAP > C:\\WAVEMEM.LOG\n'
  batch+='DEL C:\\FONT.LOG\nWIN /R > C:\\STATIC.LOG\nIF NOT EXIST C:\\FONT.LOG GOTO FAIL\nC:\\MEMSNAP > C:\\STATICMEM.LOG\nECHO OK>C:\\GUI.OK\n'
  batch+='ECHO ROLLBACK_MUTATION>CONTROL.INI\nECHO ROLLBACK_MUTATION>WIN.INI\nCOMMAND.COM /C C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES > C:\\ROLLBACK.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO OK>C:\\ROLL.OK\nECHO OK>C:\\DONE.OK\nGOTO END\n:FAIL\nECHO SEQUENCE_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n'
  tf(guest/'START.BAT',batch)
  cfg=config([('C',guest),('D',OUT/'BUILD')],'',guest,True)
  cfg+='IMGMOUNT A "'+str(WORK/'STATIC-PACKAGE2/WINXT720.IMG')+'" -T FLOPPY\nC:\nSTART.BAT\n'
  tf(case/'RUN.CNF',cfg)
 tf(OUT/'SETUP-INPUTS.JSON',json.dumps(report,indent=2))
 print('Prepared six fresh Setup fixtures; no emulator launched')
def abiverify():
 sys.path.insert(0,str(ROOT/'tools/XTLOGO'));from TEST import decode,framebuffer
 expected=framebuffer(decode((ROOT/'distributions/WINXT/WXTSPL01.RLE').read_bytes()))
 report={}
 for n in ('GOOD','BADRLE','TRUNC'):
  data=(OUT/'ABI'/(n+'.BIN')).read_bytes();rows=[struct.unpack('<B11H',data[i:i+23]) for i in range(0,len(data),23)]
  assert len(rows)==6 and [r[0] for r in rows]==[10,30,40,70,80,90]
  assert rows[1][1]==48
  assert rows[1][7]&255==(6 if n=='GOOD' else 3)
  assert rows[-1][7]&255==3
  assert len({r[6] for r in rows})==1
  report[n]={'stages':[r[0] for r in rows],'sp':rows[0][6],'mode_show':rows[1][7]&255,'mode_hide':rows[-1][7]&255,'trace':rows}
 actual=(OUT/'ABI/GOOD.VRM').read_bytes()
 assert actual==expected
 im=Image.new('1',(640,200));im.putdata([int(bool(actual[(y//2)*80+(y%2)*8192+x//8]&(128>>(x%8)))) for y in range(200) for x in range(640)])
 im.save(OUT/'ABI/NATIVE640.PNG')
 tf(OUT/'ABI/QUALIFY.JSON',json.dumps({'kind':'Genuine DOSBox-X 8088 ABI/framebuffer capture; PNG is decoded native VRAM','exact_frame':True,'cases':report},indent=2))
 print('PASS native exact static framebuffer, relocation/repeated hide, bad RLE and truncation')
def split():
 for i,d in enumerate(('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE')):
  case=OUT/d;g=case/'GUEST';s=(g/'START.BAT').read_text('ascii');a=s.index('CD \\WINXT');b=s.index('AUTOTYPE ')
  tf(g/'PREP.BAT',s[:a]+'ECHO OK>C:\\PREP.OK\nGOTO END\n:FAIL\nECHO PREP_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n')
  tf(g/'INSTALL.BAT',s[:s.index('D:\\PREPD')]+s[a:b]+'GOTO END\n:FAIL\nECHO INSTALL_FAILED>C:\\FAIL.TXT\n:END\nEXIT\n')
  tf(g/'SETUP.BAT',s[:s.index('D:\\PREPD')]+s[b:])
  cfg=(case/'RUN.CNF').read_text('ascii')
  for name in ('PREP','INSTALL','SETUP'):tf(case/(name+'.CNF'),cfg.replace('START.BAT',name+'.BAT'))
  if i>0:
   # These jobs have not launched; leave the currently running first case untouched.
   tf(case/'RUN.CNF',cfg.replace('START.BAT','PREP.BAT'))
 print('Separated private preparation, installation and Setup; current first job untouched')
def failures():
 case=OUT/'FAILURES';g=case/'GUEST';g.mkdir(parents=True);(g/'WINDOWS/SYSTEM').mkdir(parents=True)
 fixture=WORK/'FONT-NATIVE6/CGA/GUEST/WINDOWS';sysdir=fixture/'SYSTEM'
 cnf=(sysdir/'WIN.CNF').read_bytes();art=(ROOT/'distributions/WINXT/WXTSPL01.RLE').read_bytes()
 (g/'WINDOWS/OLD.COM').write_bytes(cnf+(sysdir/'CGALOGO.LGO').read_bytes()+art)
 (g/'WINDOWS/NEW.COM').write_bytes(cnf+(ROOT/'distributions/WINXT/XTSTATIC.LGO').read_bytes()+art)
 (g/'WINDOWS/XTTEST.COM').write_bytes((fixture/'XTTEST.COM').read_bytes())
 for n in ('MEMSNAP.COM','TEXT3.COM','KRNZERO.EXE','KRNFAIL.EXE'):shutil.copyfile(Path(r'C:\Users\chad\Documents\Codex\2026-10-08\task-2')/n,g/n)
 shutil.copyfile(ROOT/'distributions/WINXT/RESERVE.COM',g/'RESERVE.COM')
 shutil.copyfile(ROOT/'examples/WXTSPL/WAVE/XTCLEAN.COM',g/'WINDOWS/XTCLEAN.COM')
 s='@ECHO OFF\nC:\nCD \\WINDOWS\nC:\\RESERVE > C:\\RESERVE.LOG\n'
 for stem,child,stub in (('OLDZERO','OLD','KRNZERO'),('NEWZERO','NEW','KRNZERO'),('OLDFAIL','OLD','KRNFAIL'),('NEWFAIL','NEW','KRNFAIL'),('WAVFAIL','XTCLEAN','KRNFAIL')):
  s+='C:\\TEXT3\nCOPY C:\\'+stub+'.EXE SYSTEM\\KERNEL.EXE >NUL\nC:\\MEMSNAP > C:\\'+stem+'.BEF\n'+child+' /R > C:\\'+stem+'.LOG\nIF ERRORLEVEL 1 ECHO NONZERO>C:\\'+stem+'.ERR\nC:\\MEMSNAP > C:\\'+stem+'.AFT\n'
 s+='C:\\TEXT3\nDEL SYSTEM\\KERNEL.EXE\nNEW /R > C:\\MISSING.LOG\nC:\\MEMSNAP > C:\\MISSING.AFT\nC:\\TEXT3\nECHO OK>C:\\DONE.OK\nEXIT\n'
 tf(g/'START.BAT',s);tf(case/'RUN.CNF',config([('C',g)],'C:\nSTART.BAT\n',g,True));queue(10,'FAILURES',case/'RUN.CNF',35)
 print('Prepared baseline/new zero/nonzero kernel and missing-kernel native comparison')
def clean():
 report=json.loads((OUT/'SETUP-INPUTS.JSON').read_bytes())
 original=json.loads((WORK/'FONT-NATIVE6/ROUND-INPUTS.JSON').read_bytes())['install_original_windows_sha256']
 for d in report:
  g=OUT/d/'GUEST';w=g/'WINDOWS';p=w/'SYSTEM/SETUP.INF';expected=original['SYSTEM\\SETUP.INF']
  if sha(p)!=expected:
   bak=w/'SYSTEM/CPINFO.BAK';assert sha(bak)==expected,'Original Setup INF unavailable';shutil.copyfile(bak,p)
  for n in ('CPINFO.SAV','CPINFO.BAK','CPINFO.NEW','CPINFO.OLD','CPINFO.RST','CPINFO.CUR'):
   p=w/'SYSTEM'/n
   if p.exists():p.unlink()
  report[d]['windows']=files(w)
  p=g/'FAIL.TXT'
  if p.exists():p.unlink()
 tf(OUT/'SETUP-INPUTS.JSON',json.dumps(report,indent=2))
 for i,d in enumerate(report):queue(11+i*2,d+'-INSTALL',OUT/d/'INSTALL.CNF',45);queue(12+i*2,d+'-SETUP',OUT/d/'SETUP.CNF',60)
 print('Removed prior fixture-only Computer journal copies, verified original Setup INF, recorded clean baseline, queued install/Setup')
def pristine():
 report=json.loads((OUT/'SETUP-INPUTS.JSON').read_bytes())
 original=json.loads((WORK/'FONT-NATIVE6/ROUND-INPUTS.JSON').read_bytes())['install_original_windows_sha256']
 for d in report:
  w=OUT/d/'GUEST/WINDOWS';assert w.resolve().is_relative_to(OUT.resolve())
  wanted={n.replace('\\','/'):h for n,h in original.items() if n!='SYSTEM\\CGALOGO.LGO'}
  for n,h in wanted.items():assert sha(w/n)==h,'Baseline mismatch '+d+' '+n
  for p in list(w.rglob('*')):
   if p.is_file() and str(p.relative_to(w)).replace('\\','/') not in wanted:p.unlink()
  report[d]['windows']=files(w)
 tf(OUT/'SETUP-INPUTS.JSON',json.dumps(report,indent=2))
 print('Private copies reduced to verified 112 original Windows files; CGALOGO absent, old first-party wave/add-on artifacts removed')
def refusals():
 for i,kind in enumerate(('MISSLGO','SHORTLGO','BADGR2','VERIFYLGO','VERIFYART')):
  c=OUT/'REFUSALS'/kind;g=c/'GUEST';g.mkdir(parents=True);shutil.copytree(OUT/'FLAT',g/'SRC');(g/'OS/SYSTEM').mkdir(parents=True)
  if kind=='MISSLGO':(g/'SRC/XTSTATIC.LGO').unlink()
  elif kind=='SHORTLGO':(g/'SRC/XTSTATIC.LGO').write_bytes(b'LOGO')
  elif kind=='BADGR2':
   p=g/'SRC/CGA.GR2';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
  else:
   p=g/'SRC'/('XTSTATIC.LGO' if kind=='VERIFYLGO' else 'WXTSPL01.RLE');b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
  tf(g/'YES.TXT','Y\n');s='@ECHO OFF\nC:\nD:\\PREPD C:\\SRC C:\\OS'+(' /VERIFY' if kind.startswith('VERIFY') else '')+' < C:\\YES.TXT > C:\\REFUSE.LOG\nIF ERRORLEVEL 1 ECHO REFUSED>C:\\REFUSE.OK\nIF EXIST C:\\WINXT\\INSTALL.BAT ECHO BAD_COMMIT>C:\\BAD.TXT\nECHO OK>C:\\DONE.OK\nEXIT\n';tf(g/'START.BAT',s)
  cfg=config([('C',g),('D',OUT/'BUILD')],'C:\nSTART.BAT\n',g,True)
  if kind.startswith('VERIFY'):cfg=cfg.replace('cycles=fixed 200000','cycles=fixed 20000000')
  tf(c/'RUN.CNF',cfg);queue(23+i,kind,c/'RUN.CNF',60 if kind.startswith('VERIFY') else 20)
 print('Queued native absent/truncated LGO, bad grabber and explicit VERIFY corruption refusals; VERIFY uses faster virtual clock, same 8086 CPU')
def splitgui():
 for i,d in enumerate(('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE')):
  c=OUT/d;g=c/'GUEST';s=(g/'SETUP.BAT').read_text('ascii');at=s.index('C:\\MEMSNAP > C:\\BEFORE.LOG')
  gui=s[:s.index('AUTOTYPE ')]+ 'C:\\WINXT\\RESERVE.COM\nCD \\WINDOWS\n'+s[at:]
  tf(g/'GUI.BAT',gui);tf(c/'GUI.CNF',(c/'SETUP.CNF').read_text('ascii').replace('SETUP.BAT','GUI.BAT'))
  if i>0:tf(g/'SETUP.BAT',s[:at]+'ECHO OK>C:\\SETDONE.OK\nEXIT\n')
  queue(28+i,d+'-GUI',c/'GUI.CNF',60)
 print('Separated Setup from startup/static/rollback for remaining cases; current first Setup left intact')
def cold():
 c=OUT/'TR53216';g=c/'GUEST'
 tf(g/'COLD.BAT','@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\nSET TEMP=C:\\WINDOWS\\TEMP\nC:\nC:\\WINXT\\RESERVE.COM\nCD \\WINDOWS\nWIN /R > C:\\COLD.LOG\nC:\\MEMSNAP > C:\\COLDMEM.LOG\nECHO OK>C:\\COLD.OK\nEXIT\n')
 tf(c/'COLD.CNF',(c/'SETUP.CNF').read_text('ascii').replace('SETUP.BAT','COLD.BAT'));queue(12,'A-COLD',c/'COLD.CNF',45)
def capture():
 c=OUT/'TR53216';g=c/'GUEST';caps=c/'CAPTURE';caps.mkdir(exist_ok=True)
 tf(g/'CAP.BAT','@ECHO OFF\nDX-CAPTURE /V COMMAND.COM /C C:\\COLD.BAT\nEXIT\n')
 cfg=(c/'COLD.CNF').read_text('ascii').replace('machine=tandy','machine=tandy\ncaptures='+str(caps)).replace('COLD.BAT','CAP.BAT')
 tf(c/'CAP.CNF',cfg);queue(13,'A-CAPTURE',c/'CAP.CNF',25)
def compactgui():
 for d in ('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE'):
  p=OUT/d/'GUEST/GUI.BAT';s=p.read_text('ascii');a=s.index('DEL C:\\FONT.LOG');b=s.index('ECHO OK>C:\\GUI.OK')
  # The first profile has a separate passing cold static run. Other accepted
  # profiles' normal launcher deliberately selects the static fallback.
  s=s[:a]+'C:\\MEMSNAP > C:\\STATICMEM.LOG\n'+s[b:]
  tf(p,s)
 print('One cold GUI per remaining profile; first profile static already independently passed, normal Color wave still tested')
def fixsetup():
 original=next(l for l in (WORK/'FONT-NATIVE6/INSTALL/GUEST/START.BAT').read_text('ascii').splitlines() if l.startswith('AUTOTYPE '))
 needle='period period backslash w i n x t enter '+', '*10+'enter'
 assert needle in original
 for i,d in enumerate(('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE')):
  c=OUT/d;g=c/'GUEST';s=(g/'SETUP.BAT').read_text('ascii')
  auto=original.replace(needle,'period period backslash w i n x t enter '+', '*10+'home '+('down '*i)+'enter')
  auto=auto.replace('-w 3 -p 0.15','-w 2 -p 0.075')
  a=s.index('AUTOTYPE ');b=s.index('\n',a);s=s[:a]+auto+s[b:];at=s.index('C:\\MEMSNAP > C:\\BEFORE.LOG') if 'C:\\MEMSNAP > C:\\BEFORE.LOG' in s else s.index('ECHO OK>C:\\SETDONE.OK')
  s=s[:at]+'ECHO OK>C:\\SETDONE.OK\nEXIT\n';tf(g/'FIXUP.BAT',s)
  cfg=(c/'SETUP.CNF').read_text('ascii').replace('SETUP.BAT','FIXUP.BAT').replace('cycles=fixed 200000','cycles=fixed 1000000')
  tf(c/'FIXUP.CNF',cfg);queue(23,'A-FIX-'+d,c/'FIXUP.CNF',35)
  cfg=(c/'GUI.CNF').read_text('ascii').replace('cycles=fixed 200000','cycles=fixed 1000000');tf(c/'GUI.CNF',cfg)
 print('Corrected OEM choice at first menu after source path; queued actual Setup switches, no INI mode edits. Faster virtual clock and shorter key delays only in tests.')
def verify():
 from NATIVEQA import metrics
 from INSPECT import resources,fontinfo,dword
 inputs=json.loads((OUT/'SETUP-INPUTS.JSON').read_bytes());runtime=ROOT/'distributions/WINXT'
 cnf=(WORK/'FONT-NATIVE6/CGA/GUEST/WINDOWS/SYSTEM/WIN.CNF').read_bytes()
 expected=cnf+(runtime/'XTSTATIC.LGO').read_bytes()+(runtime/'WXTSPL01.RLE').read_bytes()
 wave=(WORK/'FONT-NATIVE6/CGA/GUEST/WINDOWS/XTTEST.COM').read_bytes()
 report={'native_package_qualified':False,'publication_allowed':False,'cases':{},'failures':[]}
 modes={'TR53216':(9,320,'XTE'),'TR56404':(10,640,'XTC'),'TR51616':(8,160,'XTC'),'TR53204':(4,320,'XTC'),'TR56402':(6,640,'XTC'),'TXTMODE':(3,640,'XTC')}
 for d,(bios,width,family) in modes.items():
  g=OUT/d/'GUEST';errors=[];entry={}
  try:
   ini=(g/'SELECTED.INI').read_text('latin1');assert 'display.drv='+d+'.DRV' in ini,'Wrong Setup-selected profile'
   assert (g/'SELECTED.COM').read_bytes()==expected,'Setup static COM mismatch';assert (g/'SELECTED.WAV').read_bytes()==wave,'Slow-wave private loader changed'
   for n in ('INST.OK','SETUP.OK','GUI.OK','ROLL.OK','DONE.OK'):assert (g/n).exists(),'Missing '+n
   assert not (g/'FAIL.TXT').exists(),'Fixture failure marker'
   prep=(g/'PREP.LOG').read_text('latin1');install=(g/'INSTALL.LOG').read_text('latin1')
   assert 'SHA blocks=0' in prep and 'output readback=0 bytes' in prep and 'compared=0' in install,'Default deep work'
   assert [p.name for p in (g/'MEDIA').iterdir()]==['CGA.GR2'],'Unexpected support media'
   log=(g/'FONT.LOG').read_text('latin1');assert 'DONE=1' in log,'GDI probe incomplete'
   found=metrics(log)
   for stock,suffix in ((13,'SYS'),(16,'FIX'),(10,'OEM')):
    name='XTTSYS.FON' if d=='TXTMODE' and suffix=='SYS' else family+suffix+'.FON'
    b=(runtime/name).read_bytes();_,rr=resources(b);off=next(off for kind,rid,flags,off,size in rr if kind==0x8008);contract=fontinfo(b[off:off+dword(b,off+2)])
    for key,field in {'HEIGHT':'height','ASCENT':'ascent','INTERNAL':'internal','EXTERNAL':'external','AVERAGE':'avg_width','MAXIMUM':'max_width','FIRST':'first','LAST':'last','CHARSET':'charset'}.items():assert found[stock][key]==contract[field],'Metric '+key
   changed=[n for n,h in inputs[d]['windows'].items() if not (g/'WINDOWS'/n).is_file() or sha(g/'WINDOWS'/n)!=h];assert not changed,'Rollback originals '+str(changed)
   assert all(sha(g/n)==h for n,h in inputs[d]['boot'].items()),'Rollback boot mismatch'
   # READY is helper completeness; RESTORE retains helpers and this marker.
   # WAVE/optional shell activation must be disabled by their restorers.
   assert (g/'WINXT/READY.TAG').exists(),'Committed helper readiness lost'
   assert not (g/'WINXT/WAVE.RDY').exists() and (g/'WINXT/WAVE.OFF').exists(),'Wave activation survived rollback'
   assert not (g/'WINXT/SHREADY.TAG').exists(),'Shell activation survived rollback'
   mem=(g/'STATICMEM.LOG').read_text('ascii').splitlines()[-1].split();assert int(mem[0],16)==624 and int(mem[1],16)&255==3,'DOS mode/memory cleanup'
   fields=dict(l.split('=',1) for l in log.splitlines() if '=' in l)
   entry={'setup_selected':d,'static_com_exact':True,'slow_wave_com_unchanged':True,'stock_metrics_preserved':True,'zero_default_sha':True,'rollback_original_files':len(inputs[d]['windows']),'boot_exact':True,'dos_mode':3,'dialog_overflow':int(fields.get('DIALOG_SCREEN_OVERFLOW','-1'))}
   if bios!=3:
    palette=[(0,0,0),(0,0,170),(0,170,0),(0,170,170),(170,0,0),(170,0,170),(170,85,0),(170,170,170),(85,85,85),(85,85,255),(85,255,85),(85,255,255),(255,85,85),(255,85,255),(255,255,85),(255,255,255)]
    ids=[0,12,10,15] if bios==10 else [0,3,5,15] if bios==4 else [0,15]
    for snap in ('NORMAL','DIALOG'):
     raw=(g/(snap+'.BIN')).read_bytes();pixels=[]
     for y in range(200):
      for x in range(width):
       if bios==10:
        a=y%4*8192+y//4*160+x//8*2;color=(raw[a]>>(7-x%8)&1)|((raw[a+1]>>(7-x%8)&1)<<1)
       else:
        bits=1 if bios==6 else 2 if bios==4 else 4;banks=4 if bios==9 else 2;row=160 if bios==9 else 80;a=y%banks*8192+y//banks*row+x//(8//bits);color=raw[a]>>((8//bits-1-x%(8//bits))*bits)&((1<<bits)-1)
       pixels.append(palette[color if bios in (8,9) else ids[color]])
     im=Image.new('RGB',(width,200));im.putdata(pixels);im.save(OUT/d/(snap+'.PNG'))
  except Exception as e:errors.append(str(e))
  report['cases'][d]={**entry,'errors':errors}
  report['failures'] += [d+': '+e for e in errors]
 for name in ('MISSLGO','SHORTLGO','BADGR2','VERIFYLGO','VERIFYART'):
  g=OUT/'REFUSALS'/name/'GUEST'
  if not (g/'DONE.OK').exists() or not (g/'REFUSE.OK').exists() or (g/'REFUSE.OK').stat().st_size==0 or ((g/'BAD.TXT').exists() and (g/'BAD.TXT').stat().st_size):report['failures'].append(name+': native refusal incomplete')
 report['all_recorded_cases_passed']=not report['failures'];tf(OUT/'QUALIFY.JSON',json.dumps(report,indent=2));print(json.dumps(report,indent=2))
def badcnf():
 c=OUT/'BADCNF';g=c/'GUEST';g.mkdir(parents=True);shutil.copytree(OUT/'FLAT',g/'WINXT');shutil.copytree(WORK/'FONT-NATIVE6/INSTALL/GUEST/WINDOWS',g/'WINDOWS')
 original=json.loads((WORK/'FONT-NATIVE6/ROUND-INPUTS.JSON').read_bytes())['install_original_windows_sha256'];wanted={n.replace('\\','/'):h for n,h in original.items() if n!='SYSTEM\\CGALOGO.LGO'}
 w=g/'WINDOWS'
 for p in list(w.rglob('*')):
  if p.is_file() and str(p.relative_to(w)).replace('\\','/') not in wanted:p.unlink()
 p=w/'SYSTEM/WIN.CNF';b=bytearray(p.read_bytes());b[0]^=1;p.write_bytes(b)
 tf(g/'CONFIG.SYS','FILES=30\nBUFFERS=20\n');tf(g/'AUTOEXEC.BAT','@ECHO OFF\n');tf(c/'BEFORE.JSON',json.dumps(files(w),indent=2))
 s='@ECHO OFF\nC:\nCD \\WINXT\nD:\\TINSTD C:\\WINDOWS > C:\\REJECT.LOG\nIF ERRORLEVEL 1 GOTO REFUSED\nECHO BAD>C:\\BAD.TXT\nGOTO END\n:REFUSED\nECHO OK>C:\\REFUSE.OK\nCOMMAND.COM /C C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES > C:\\ROLLBACK.LOG\nIF ERRORLEVEL 1 GOTO FAIL\nECHO OK>C:\\DONE.OK\nGOTO END\n:FAIL\nECHO BAD>C:\\FAIL.TXT\n:END\nEXIT\n';tf(g/'START.BAT',s)
 tf(c/'RUN.CNF',config([('C',g),('D',OUT/'BUILD')],'C:\nSTART.BAT\n',g,True));queue(27,'A-BADCNF',c/'RUN.CNF',25)
def recovery():
 c=OUT/'RECOVERY';c.mkdir(exist_ok=True);s=''
 for d in ('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE'):
  g=OUT/d/'GUEST';s+='Z:\nMOUNT C "'+str(g)+'"\nC:\nCD \\WINDOWS\nECHO RECOVERY_TEST>CONTROL.INI\nECHO RECOVERY_TEST>WIN.INI\nCOMMAND.COM /C C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES > C:\\RECOVERY.LOG\nECHO RETURNED>C:\\RECOVER.OK\nZ:\nMOUNT -U C\n'
 s+='EXIT\n';tf(c/'RUN.CNF',config([],s,c,True));queue(28,'A-RECOVERY',c/'RUN.CNF',20)
 # Preserve submitted jobs but disable unstarted GUI runs: their Windows
 # resources will intentionally be rolled back by this recovery job.
 for p in (OUT/'QUEUE').glob('*-GUI.JSON'):
  j=json.loads(p.read_bytes())
  if j['purpose']=='TR53216-GUI':continue
  j['config']=str(c/'SKIP.CNF');j['seconds']=3;tf(p,json.dumps(j))
 tf(c/'SKIP.CNF',config([],'EXIT\n',c,True))
 print('Queued native recovery of all six private installations; remaining GUI jobs intentionally skipped after recovery')
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='abi':abiverify()
 elif sys.argv[1]=='queue':
  for i,d in enumerate(('TR53216','TR56404','TR51616','TR53204','TR56402','TXTMODE')):queue(4+i,d,OUT/d/'RUN.CNF')
 elif sys.argv[1]=='split':split()
 elif sys.argv[1]=='failures':failures()
 elif sys.argv[1]=='clean':clean()
 elif sys.argv[1]=='pristine':pristine()
 elif sys.argv[1]=='refusals':refusals()
 elif sys.argv[1]=='splitgui':splitgui()
 elif sys.argv[1]=='cold':cold()
 elif sys.argv[1]=='capture':capture()
 elif sys.argv[1]=='compactgui':compactgui()
 elif sys.argv[1]=='fixsetup':fixsetup()
 elif sys.argv[1]=='verify':verify()
 elif sys.argv[1]=='badcnf':badcnf()
 elif sys.argv[1]=='recovery':recovery()
