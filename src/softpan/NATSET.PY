from pathlib import Path
import argparse,importlib.machinery,os,shutil,subprocess,json,hashlib
repo=Path(__file__).resolve().parents[2]
root=repo.parent
p=argparse.ArgumentParser();p.add_argument('guest',type=Path);p.add_argument('packet');p.add_argument('--row',default='0');p.add_argument('--machine',default='pcjr');p.add_argument('--tag',default='');p.add_argument('--installer',action='store_true');a=p.parse_args()
c=a.guest.resolve();out=c.parent;name='SET'+a.packet+a.row+a.tag
b=out/name;b.mkdir(exist_ok=False)
s=(repo/'tools/XTLOGO/SKCTRL.ASM').read_text()
s=s.replace("oem_msg db 'Tandy EX/HX 320x200 16 colors',0", "oem_msg db 'EXPERIMENTAL',0" if a.row=='0' else ("oem_msg db 'ColorPlus 320x200 fixed',0" if a.packet=='CPPAN' else "oem_msg db 'IBM PCjr 320x200 fixed',0"))
old=""" mov ax,0057h
 call addkey
 mov ax,0049h
 call addkey
 mov ax,004eh
 call addkey
 mov ax,0058h
 call addkey
 mov ax,0054h
 call addkey"""
new='\n'.join(' mov ax,00%02xh\n call addkey'%ord(ch) for ch in a.packet)
assert old in s;s=s.replace(old,new)
for n,t in [('SKCTRL.ASM',s),('DRAIN.ASM',(repo/'tools/XTLOGO/DRAIN.ASM').read_text())]:(b/n).write_bytes(t.replace('\r\n','\n').replace('\n','\r\n').encode())
for n in ('SKCTRL','DRAIN'):
 for cmd in ([r'C:\WATCOM\binnt\wasm.exe','-0','-zcm=masm','-we','-fo='+n+'.OBJ',n+'.ASM'],[r'C:\WATCOM\binnt\wlink.exe','format','dos','com','option','quiet','file',n+'.OBJ','name',n+'.COM']):subprocess.run(cmd,cwd=b,check=True,capture_output=True)
 shutil.copyfile(b/(n+'.COM'),c/(n+'.COM'))
bat='@ECHO OFF\nSET PATH=C:\\WINDOWS;Z:\\\nCD \\WINDOWS\nC:\\SKCTRL '+a.row+'\nSETUP\nC:\\SKCTRL /D\nC:\\DRAIN\nCOPY SYSTEM.INI C:\\SELECTED.INI >NUL\nCOPY WIN.COM C:\\SELECTED.COM >NUL\nECHO RETURNED>C:\\SETRET.OK\nEXIT\n'
if a.installer:bat=bat.replace('\nSETUP\n','\nZ:\nCALL C:\\'+a.packet+'\\INSTALL.BAT\n')
(c/'SETNAT.BAT').write_bytes(bat.replace('\n','\r\n').encode())
if (c/'SETRET.OK').exists():(c/'SETRET.OK').unlink()
cfg='[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine='+a.machine+'\nmemsizekb=640\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\nfpu=false\n[dos]\nxms=false\nems=false\numb=false\n[mixer]\nnosound=true\n[autoexec]\n@echo off\nmount C "'+str(c)+'"\nC:\nSETNAT.BAT\n'
(b/'RUN.CNF').write_text(cfg)
m=importlib.machinery.SourceFileLoader('lease',str(repo/'src/softpan/WINRUN.PY')).load_module();r=m.Runner(b/'LEASE.JSON')
with r.lease():r.run([r'C:\DOSBox-X\dosbox-x.exe','-nopromptfolder','-conf',str(b/'RUN.CNF')],dict(os.environ,SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy'),b/'HOST.LOG',100)
print((c/'SELECTED.INI').read_text()[:700]);assert (c/'SETRET.OK').exists()
print('trace', (c/'KEYTRACE.BIN').read_bytes()[:8].hex())
for n in ('SELECTED.INI','SELECTED.COM','KEYTRACE.BIN','KEYSCR.BIN','KEYVIEW.BIN'):shutil.copyfile(c/n,b/n)
trace=(c/'KEYTRACE.BIN').read_bytes();assert trace[1]==6
meta={'native_setup_returned':True,'packet':a.packet,'row':int(a.row),'phase':trace[1],'actions':int.from_bytes(trace[4:6],'little'),'boot':(c/'SELECTED.INI').read_text(),'installed':{}}
for n in ('JRPAN.DRV','TNDYJR.DRV','CPPAN.DRV','PCP3216.DRV','JRGRAB.GR2','CGA.GR2','XTESYS.FON','XTEFIX.FON','XTEOEM.FON'):
 f=c/'WINDOWS/SYSTEM'/n
 if f.exists():meta['installed'][n]=hashlib.sha256(f.read_bytes()).hexdigest()
(b/'RESULT.JSON').write_text(json.dumps(meta,indent=2))
driver={'JRPAN':'JRPAN.DRV' if a.row=='0' else 'TNDYJR.DRV','PCJREXP':'TNDYJR.DRV','CPPAN':'CPPAN.DRV' if a.row=='0' else 'PCP3216.DRV'}[a.packet]
assert (c/'WINDOWS/SYSTEM'/driver).read_bytes()==(c/a.packet/driver).read_bytes(),'Setup retained different installed driver bytes'
