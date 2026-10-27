"""Host API checks of the actual staged FIXXT PANINIT transaction."""
from pathlib import Path
import argparse,json,os,shutil,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[2]
def inventory(p):return {q.relative_to(p).as_posix():q.read_bytes() for q in p.rglob('*') if q.is_file()}
def main():
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--native',type=Path,required=True);ap.add_argument('--helpers',type=Path,required=True);a=ap.parse_args()
 launcher=Path.home()/'Documents/Codex/toolchains/gcc-ucrt64.py'
 with tempfile.TemporaryDirectory(prefix='unified-pan-install-') as tmp:
  root=Path(tmp);source=root/'SOURCE';source.mkdir();win=root/'WINDOWS';system=win/'SYSTEM';system.mkdir(parents=True)
  exe=source/'PANINST.EXE'
  cmd=[sys.executable,str(launcher),'--','-x','c','-std=c89','-DHOST_TEST','-O0',str((a.native/'FIXXT.C').resolve()),'-o',str(exe)]
  p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stdout+p.stderr
  for n in ('XTPAN.EXE','XYCTL.EXE','PANCFG.EXE','PANKEY.DLL'):shutil.copyfile(a.helpers/n,source/n)
  (win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=HPXY.DRV ; selected\r\nshell=KEEP.EXE\r\n')
  original=b'; preserve\r\n[windows]\r\nload=clock.exe,C:\\OLD\\XTPAN.EXE\r\nrun=C:\\OLD\\XYCTL.EXE,kept.exe\r\n[custom]\r\nanswer=42\r\n'
  (win/'WIN.INI').write_bytes(original);(system/'HPXY.DRV').write_bytes(b'preserve driver')
  def run(extra=None):
   return subprocess.run([str(exe),'PANINIT',str(win)],cwd=root,capture_output=True,text=True,env=dict(os.environ,**(extra or {})))
  # A bad late source prevents every copy and INI change.
  key=(source/'PANKEY.DLL').read_bytes();(source/'PANKEY.DLL').write_bytes(b'bad')
  before=inventory(win);r=run();assert r.returncode and inventory(win)==before,r.stdout
  (source/'PANKEY.DLL').write_bytes(key);r=run();assert r.returncode==0,r.stdout+r.stderr
  for n in ('XTPAN.EXE','XYCTL.EXE','PANCFG.EXE'):assert (win/n).read_bytes()==(source/n).read_bytes()
  assert (system/'PANKEY.DLL').read_bytes()==key and (system/'HPXY.DRV').read_bytes()==b'preserve driver'
  ini=(win/'WIN.INI').read_bytes();assert b'load=clock.exe '+str(win).upper().encode()+b'\\XYCTL.EXE\r\n' in ini,ini
  assert b'run=kept.exe\r\n' in ini and b'answer=42' in ini
  assert b'[UnifiedPan]\r\nDisplay=HPXY.DRV' in ini
  # Later OFF is a persisted choice: startup initialization does not re-add it.
  ini=ini.replace(str(win).upper().encode()+b'\\XYCTL.EXE',b'')
  (win/'WIN.INI').write_bytes(ini);before=inventory(win);r=run();assert r.returncode==0 and inventory(win)==before,r.stdout
  # A deliberate driver change picks the matching owner, without two tokens.
  (win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=JRPAN.DRV\r\n')
  r=run();assert r.returncode==0,r.stdout
  ini=(win/'WIN.INI').read_bytes();assert b'\\XTPAN.EXE' in ini and b'\\XYCTL.EXE' not in ini
  # Fixed displays offer the window alternative through Settings, without
  # pretending a framebuffer engine exists or starting one automatically.
  (win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=C23216.DRV\r\n')
  r=run();assert r.returncode==0,r.stdout
  ini=(win/'WIN.INI').read_bytes();assert b'\\XTPAN.EXE' not in ini and b'\\XYCTL.EXE' not in ini
  # A foreign packet's selected display must retain its own startup path.
  (win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=CGAPAN.DRV\r\n')
  before=inventory(win);r=run();assert r.returncode==0 and inventory(win)==before,r.stdout
  # A valid old line must not overflow the editor after appending an owner.
  (win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=HPXY.DRV\r\n')
  longini=b'[windows]\r\nload='+b'a'*270+b'.exe\r\nrun=kept.exe\r\n'
  (win/'WIN.INI').write_bytes(longini);r=run()
  assert r.returncode and 'Panning startup line too long' in r.stdout+r.stderr and (win/'WIN.INI').read_bytes()==longini,r.stdout+r.stderr
  # Duplicate owned sections are refused by the same checked INI editor.
  (win/'SYSTEM.INI').write_bytes(b'[boot]\r\ndisplay.drv=HPXY.DRV\r\n')
  (win/'WIN.INI').write_bytes(ini+b'\r\n[UnifiedPan]\r\nDisplay=OTHER\r\n')
  r=run();assert r.returncode and b'Display=OTHER' in (win/'WIN.INI').read_bytes(),r.stdout
  print(json.dumps(dict(outcome='PASS_HOST_API_CHECKS',checks=['all source pins checked before copying','actual installed helper destinations','unrelated driver and INI preservation','one active startup owner','OFF persists across initialization','driver selection updates owner','fixed capability opt-in','duplicate owned section refusal'])))
if __name__=='__main__':main()
