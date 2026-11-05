import argparse
import runpy,io,zipfile,re
from pathlib import Path
HERE = Path(__file__).resolve().parent
args = argparse.ArgumentParser(description='Check separate development packet closure and selectors.')
args.add_argument('--support', type=Path, required=True)
args.add_argument('--colorplus', type=Path, required=True)
args.add_argument('--yamaha', type=Path, required=True)
a = args.parse_args()
p = runpy.run_path(str(HERE/'PACK.PY'))
for profile,driver_path in [('colorplus32016',a.colorplus),('yamaha160-b800',a.yamaha)]:
 files=p['members'](profile,driver_path,a.support)
 data=p['archive'](profile,files);assert p['archive'](profile,files)==data
 folder,driver,label,font,metrics,_=p['PROFILES'][profile]
 assert len(files)==14
 assert b'qualification is pending' not in files['README.TXT']
 assert b'Physical hardware remains unqualified' in files['README.TXT']
 for name in files:assert re.fullmatch(r'[A-Z0-9_]{1,8}\.[A-Z0-9_]{1,3}',name),name
 assert len(re.findall(rb'(?m)^\w+ = a:.*\.DRV,',files['OEMSETUP.INF']))==1
 for name in [driver,'CGA.GR2','XTSTATIC.LGO','WXTSPL01.RLE',font+'SYS.FON',font+'FIX.FON',font+'OEM.FON']:
  assert name.encode() in files['OEMSETUP.INF']
 assert metrics.encode() in files['OEMSETUP.INF']
 assert not files['INSTALL.BAT'].startswith(b'@')
 assert b'CALL ' not in files['INSTALL.BAT']+files['START.BAT']
 assert b'CPPAN' not in files['INSTALL.BAT'] and b'RESERVE' not in files['INSTALL.BAT']
 assert b'CD \\WINDOWS\r\nWIN /R' in files['START.BAT']
 assert not any(n.upper().endswith(('.JSN','.JSON','.SHA','.SUM')) for n in files)
 with zipfile.ZipFile(io.BytesIO(data)) as z:
  assert set(z.namelist())=={folder+'/'+n for n in files}
  assert z.testzip() is None
  assert all(z.read(folder+'/'+n)==b for n,b in files.items())
 print(profile, 'PASS_HOST_PACKET', len(data), 'bytes',len(files),'members')
