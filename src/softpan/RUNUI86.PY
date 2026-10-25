"""Reuse the owned 86Box fixture/control API; proxy preallocated guest input."""
from pathlib import Path
import sys,shutil,importlib.machinery,os,subprocess,time,base64,json,argparse
r=Path(__file__).resolve().parents[3]
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage',nargs='?',default='PREPARE');ap.add_argument('--prepare',action='store_true');ap.add_argument('--out',type=Path,default=r/'cp-native-install-01')
for name in ('deps','control','emulator','roms'):ap.add_argument('--'+name,type=Path)
args=ap.parse_args()
out=args.out.resolve();c=out/'CROOT';image=out/'DISK.IMG'
m=importlib.machinery.SourceFileLoader('lease',str(Path(__file__).resolve().parent/'WINRUN.PY')).load_module()
runner=m.Runner(out/((args.stage if not args.prepare else 'PREPARE')+'-LEASE.JSON'))

def owned_session():
    for name in ('deps','control','emulator','roms'):
     value=getattr(args,name)
     if value is None or not value.exists():raise ValueError('Supply existing --'+name)
    sys.path[:0]=[str(args.deps.resolve()),str(args.control.resolve())]
    from pyfatfs.PyFatFS import PyFatFS
    from src.gdbclient import GdbClient
    from src.headless_input import HeadlessCtl
    prepare=args.prepare
    if prepare:
     if image.exists():image.rename(out/'DISK-PRE-COPY.IMG')
     shutil.copyfile(r/'PCDOS320-BASE.IMG',image)
     with PyFatFS(str(image),offset=8704) as fs:
      def put(n,data):
       if fs.exists(n):fs.remove(n)
       fs.writebytes(n,data)
      for base in ('WINDOWS','CPPAN'):
       fs.makedirs(base,recreate=True)
       for p in (c/base).rglob('*'):
        n=p.relative_to(c).as_posix()
        if p.is_dir():fs.makedirs(n,recreate=True)
        else:put(n,p.read_bytes())
      put('UITASK.TXT',b'0 SNAP\r\n'+b' '*4088);put('SPTEST.INI',b'[test]\r\nvseg=47104\r\n')
      put('CONFIG.SYS',b'FILES=40\r\nBUFFERS=10\r\nLASTDRIVE=E\r\n')
      put('AUTOEXEC.BAT',b'ECHO OFF\r\nSET PATH=C:\\WINDOWS;C:\\DOS\r\nSET TEMP=C:\\WINDOWS\\TEMP\r\nC:\\CPPAN\\CPWIN\r\n')
     cfg=(r/'cp-dos320-template/86box.cfg').read_text(encoding='utf-8-sig');(out/'86box.cfg').write_text(cfg[cfg.index('[General]'):],encoding='ascii')
     print('Prepared installed ColorPlus boot image');return
    stage=args.stage;stop=out/'STOP.NOW'
    if stop.exists():stop.unlink()
    with PyFatFS(str(image),offset=8704) as fs:
     if fs.exists('RETURN1.TXT'):fs.remove('RETURN1.TXT')
     for n in ('UISTATE.TXT','UIVRAM.BIN'):
      if fs.exists(n):fs.remove(n)
     with fs.openbin('UITASK.TXT','r+') as f:f.write(b'0 SNAP\r\n'+b' '*4088)
    (c/'UITASK.TXT').write_bytes(b'0 SNAP\r\n'+b' '*4088)
    for n in ('UISTATE.TXT','UIVRAM.BIN'):
     if (c/n).exists():(c/n).unlink()
    with PyFatFS(str(image),offset=8704,read_only=True) as fs:
     entry=fs.fs.root_dir.get_entry('UITASK.TXT');clusters=list(fs.fs.get_cluster_chain(entry.get_cluster()));size=fs.fs.bytes_per_cluster
     offsets=[8704+fs.fs.get_data_cluster_address(n) for n in clusters];assert len(offsets)*size>=4096
    g=ctl=None
    with (out/(stage+'-HOST.LOG')).open('wb') as log:
     si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
     p=subprocess.Popen([str(args.emulator.resolve()),'-P',str(out),'-R',str(args.roms.resolve()),'-N'],cwd=out,env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
     child={'pid':p.pid,'bound_seconds':600};runner.state['children'].append(child);runner.save()
     try:
      started=time.monotonic();sent=None;captures=set();fresh=False
      while time.monotonic()-started<600:
       assert p.poll() is None
       if stop.exists():break
       if g is None:
        try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346)
        except OSError:
         if g:g.close()
         g=None;time.sleep(.2);continue
       reason=g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
       (out/'RUNTIME.JSON').write_text(json.dumps({'seconds':time.monotonic()-started,'reason':reason,'registers':g.read_all_registers(),'bios_ticks':int.from_bytes(g.read_memory(0x46c,4),'little'),'mode':g.read_memory(0x449,1)[0]}))
       b=(c/'UITASK.TXT').read_bytes()
       if b!=sent:
        assert len(b)==4096
        with image.open('r+b',buffering=0) as f:
         for i,off in enumerate(offsets):
          data=b[i*size:(i+1)*size]
          if data:f.seek(off);f.write(data)
        sent=b
       try:
        with PyFatFS(str(image),offset=8704,read_only=True) as fs:
         for n in ('UISTATE.TXT','UIVRAM.BIN','UIMEM.LOG'):
          if fs.exists(n):
           data=fs.readbytes(n)
           if n=='UISTATE.TXT' and not data.startswith(b'STATE '):continue
           if n=='UIVRAM.BIN' and len(data)!=32768:continue
           (c/n).write_bytes(data)
         fresh=(c/'UISTATE.TXT').exists() and (c/'UISTATE.TXT').read_bytes().startswith(b'STATE ')
         done=fresh and b' EXIT' in b and g.read_memory(0x449,1)==b'\x03'
        if fresh:
         state=(c/'UISTATE.TXT').read_text(errors='replace');seq=state.split(' ',3)[1]
         if seq not in captures and len(captures)<80:
          (out/(stage+'-'+seq.replace('=','')+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()));captures.add(seq)
        if done:
         g.run_while(lambda:None,settle_seconds=4,start_delay=.01)
         text=g.read_memory(0xb8000,4000)[::2].decode('cp437')
         if 'WINDOWS>' not in text and 'C>' not in text:continue
         (out/(stage+'-DOS.TXT')).write_text(text)
         (out/(stage+'-RETURN.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()));print('NORMAL_DOS_RETURN',stage,flush=True);break
       except (OSError,ValueError):pass
      else:raise TimeoutError('ColorPlus UI bound')
     finally:
      if ctl:ctl.close()
      if g:g.close()
      if p.poll() is None:p.kill();p.wait(timeout=10)
      child['stopped']=True;runner.save()

with runner.lease():
    owned_session()
