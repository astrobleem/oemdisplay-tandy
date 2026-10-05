from pathlib import Path
import subprocess,os,time,struct,argparse,shutil,runpy
ap=argparse.ArgumentParser()
ap.add_argument('--repo',type=Path,required=True,help='Existing licensed toolchain and DDK root')
ap.add_argument('--dosbox',type=Path,required=True,help='DOSBox-X executable')
a=ap.parse_args()
root=Path(__file__).resolve().parent;out=root/'work';repo=a.repo.resolve()
if out.exists() or (root/'base').exists():raise SystemExit('Use a fresh SOURCE directory; base/work already exist.')
for name in ('BIN/MASM.EXE','BIN/LINK4.EXE','DDK/286/KEYBOARD/TABS.ASM'):
 if not (repo/name).is_file():raise SystemExit('Missing prerequisite: '+name)
expected=__import__('json').loads((root/'BASESHA.JSON').read_text())
for name,digest in expected.items():
 f=repo/'DDK/286/KEYBOARD'/name
 if not f.is_file() or __import__('hashlib').sha256(f.read_bytes()).hexdigest()!=digest:raise SystemExit('Different DDK input: '+name)
shutil.copytree(repo/'DDK/286/KEYBOARD',root/'base')
shutil.copytree(root/'base',out)
runpy.run_path(str(root/'PATCH.PY'))
mods=['TRAP','INIT','TOASCII','XLAT','ENABLE','SETSPEED','TABS','OEMSCAN','GETNAME','WEP']
lines=['@echo off','set PATH=C:\\BIN','set INCLUDE=C:\\DDK\\286\\INC','set LIB=C:\\LIB','echo START > BUILD.LOG']
for m in mods:
 opts={'TRAP':' /DENHANCE','TABS':' /DENHANCE','TOASCII':' /DDEAD','OEMSCAN':' /DDEAD','XLAT':' /DEXTENDEDANSI'}.get(m,'')
 lines+=['C:\\BIN\\MASM /DROM=0 /I. /ITABLES /IC:\\DDK\\286\\INC'+opts+' '+m+','+('XLATUS' if m=='XLAT' else m)+','+m+'; >> BUILD.LOG','if errorlevel 1 goto fail']
lines+=['C:\\BIN\\LINK4 @KEYBOARD.LNK >> BUILD.LOG','if errorlevel 1 goto fail','echo PASS >> BUILD.LOG','goto done',':fail','echo FAIL >> BUILD.LOG',':done','exit']
(out/'BUILD.BAT').write_bytes(('\r\n'.join(lines)+'\r\n').encode()); (out/'KEYBOARD.DEF').write_bytes((out/'KBD.DEF').read_bytes())
cnf=f'''[sdl]\nfullscreen=false\noutput=surface\n[dosbox]\nmachine=tandy\nmemsize=16\n[cpu]\ncore=normal\ncputype=8086_prefetch\ncycles=fixed 200000\n[mixer]\nnosound=true\n[autoexec]\nmount c "{repo}"\nmount d "{out}"\nd:\nBUILD.BAT\n'''
(root/'build.conf').write_text(cnf)
env=os.environ.copy();env['SDL_VIDEODRIVER']='dummy'
p=subprocess.Popen([str(a.dosbox.resolve()),'-nopromptfolder','-conf',str(root/'build.conf')],env=env,stdout=(root/'host.log').open('wb'),stderr=subprocess.STDOUT)
try:p.wait(timeout=120)
except: p.kill();p.wait()
print((out/'BUILD.LOG').read_text(errors='replace'))
if 'PASS' in (out/'BUILD.LOG').read_text():
 b=bytearray((out/'KEYBOARD.EXE').read_bytes());n=struct.unpack_from('<I',b,60)[0];struct.pack_into('<H',b,n+62,0x300);(out/'TNDYK3.DRV').write_bytes(b)

assert 'PASS' in (out/'BUILD.LOG').read_text(), 'Build failed'
print('Driver:',out/'TNDYK3.DRV')
