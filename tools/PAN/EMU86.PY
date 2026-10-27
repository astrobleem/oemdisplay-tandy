"""Bounded 86Box acceptance: preallocated native UI commands and real scanout."""
from pathlib import Path
import sys,shutil,importlib.machinery,os,subprocess,time,base64,json,argparse
ROOT=Path(__file__).resolve().parents[2]
r=ROOT.parent
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('stage',nargs='?',default='PREPARE');ap.add_argument('--out',type=Path,default=r/'cp-native-install-01')
for name in ('deps','control','emulator','roms'):ap.add_argument('--'+name,type=Path)
ap.add_argument('--guest-log',help='Optional guest helper log to collect with UI evidence')
ap.add_argument('--no-auto-captures',action='store_true',help='Keep state/return evidence without per-command PNG captures')
ap.add_argument('--seconds',type=int,default=600,help='Owned native session bound (30..1800 seconds)')
args=ap.parse_args()
if not 30<=args.seconds<=1800:ap.error('--seconds must be 30..1800')
out=args.out.resolve();c=out/'CROOT';image=out/'DISK.IMG'
import struct
with image.open('rb') as disk:header=disk.read(512)
parts=[struct.unpack_from('<I',header,454+i*16)[0] for i in range(4) if header[450+i*16]]
assert len(parts)==1 and parts[0]>0 and header[-2:]==b'\x55\xaa'
partition=parts[0]*512
m=importlib.machinery.SourceFileLoader('lease',str(ROOT/'src/softpan/WINRUN.PY')).load_module()
runner=m.Runner(out/(args.stage+'-LEASE.JSON'))

def owned_session():
    for name in ('deps','control','emulator','roms'):
     value=getattr(args,name)
     if value is None or not value.exists():raise ValueError('Supply existing --'+name)
    sys.path[:0]=[str(args.deps.resolve()),str(args.control.resolve())]
    from pyfatfs.PyFatFS import PyFatFS
    from pyfatfs._exceptions import PyFATException
    from src.gdbclient import GdbClient
    from src.headless_input import HeadlessCtl,type_string,SC_CTRL,SC_ALT
    stage=args.stage;stop=out/'STOP.NOW';keytimes=[]
    if stop.exists():stop.unlink()
    with PyFatFS(str(image),offset=partition) as fs:
     if fs.exists('RETURN1.TXT'):fs.remove('RETURN1.TXT')
     for n in ('UISTATE.TXT','UIVRAM.BIN'):
      if fs.exists(n):fs.remove(n)
     with fs.openbin('UITASK.TXT','r+') as f:f.write(b'0 SNAP\r\n'+b' '*4088)
    (c/'UITASK.TXT').write_bytes(b'0 SNAP\r\n'+b' '*4088)
    for n in ('UISTATE.TXT','UIVRAM.BIN'):
     if (c/n).exists():(c/n).unlink()
    with PyFatFS(str(image),offset=partition,read_only=True) as fs:
     entry=fs.fs.root_dir.get_entry('UITASK.TXT');clusters=list(fs.fs.get_cluster_chain(entry.get_cluster()));size=fs.fs.bytes_per_cluster
     offsets=[partition+fs.fs.get_data_cluster_address(n) for n in clusters];assert len(offsets)*size>=4096
    g=ctl=None
    with (out/(stage+'-HOST.LOG')).open('wb') as log:
     si=subprocess.STARTUPINFO();si.dwFlags|=subprocess.STARTF_USESHOWWINDOW;si.wShowWindow=0
     assert shutil.disk_usage(out).free>=512*1024*1024
     p=subprocess.Popen([str(args.emulator.resolve()),'-P',str(out),'-R',str(args.roms.resolve()),'-N'],cwd=out,env=dict(os.environ,QT_QPA_PLATFORM='offscreen'),stdout=log,stderr=subprocess.STDOUT,startupinfo=si,creationflags=subprocess.CREATE_NO_WINDOW)
     child={'pid':p.pid,'bound_seconds':args.seconds};runner.state['children'].append(child);runner.save()
     try:
      started=time.monotonic();sent=None;captures=set();fresh=False;keyserial=0;rom_ack=False;capture_serial=0
      while time.monotonic()-started<args.seconds:
       assert p.poll() is None
       assert (out/(stage+'-HOST.LOG')).stat().st_size<=16*1024*1024
       assert sum(png.stat().st_size for png in out.glob('*.PNG'))<=32*1024*1024
       if stop.exists():break
       if g is None:
        try:g=GdbClient(timeout=3);g.connect();ctl=HeadlessCtl('127.0.0.1',12346)
        except PermissionError:
         if g:g.close()
         raise
        except OSError:
         if g:g.close()
         g=None;time.sleep(.2);continue
       reason=g.run_while(lambda:None,settle_seconds=2,start_delay=.01)
       (out/'RUNTIME.JSON').write_text(json.dumps({'seconds':time.monotonic()-started,'reason':reason,'registers':g.read_all_registers(),'bios_ticks':int.from_bytes(g.read_memory(0x46c,4),'little'),'mode':g.read_memory(0x449,1)[0]}))
       if g.read_memory(0x449,1)==b'\x03':(out/'DOS-CURRENT.TXT').write_text(g.read_memory(0xb8000,4000)[::2].decode('cp437'),encoding='utf-8')
       if not rom_ack and time.monotonic()-started>40:
        textbytes=g.read_memory(0xb8000,4000)[::2]
        if b'RESUME' in textbytes and b'F1' in textbytes:
         g.run_while(lambda:type_string(ctl,'{F1}'),settle_seconds=2,start_delay=.05);rom_ack=True
         runner.state['rom_floppy_prompt_acknowledged']=True;runner.save()
       if (c/'KEYS.JSON').exists():
        request=json.loads((c/'KEYS.JSON').read_text())
        if request['id']>keyserial:
         before=int.from_bytes(g.read_memory(0x46c,4),'little')
         requested=request.get('scans',[request.get('scan')]);assert 1<=len(requested)<=12 and all(isinstance(n,int) and 0<n<128 for n in requested)
         def chord():
          for code in requested:
           scans=[SC_CTRL,SC_ALT,code]
           try:
            for scan in scans:ctl.key(True,scan);time.sleep(.08)
            time.sleep(.15)
           finally:
            for scan in reversed(scans):ctl.key(False,scan);time.sleep(.08)
         g.run_while(chord,settle_seconds=4,start_delay=.05)
         after=int.from_bytes(g.read_memory(0x46c,4),'little');keytimes.append(dict(id=request['id'],scans=requested,before=before,after=after));(out/'KEYTIMES.JSON').write_text(json.dumps(keytimes,indent=2))
         keyserial=request['id'];(c/'KEYACK.JSON').write_text(json.dumps({'id':keyserial}))
         (out/(stage+'-KEY'+str(keyserial)+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
       if (c/'CAPTURE.JSON').exists():
        request=json.loads((c/'CAPTURE.JSON').read_text())
        if request['id']>capture_serial:
         label=request['label'];assert label.isalnum() or all(ch.isalnum() or ch=='-' for ch in label)
         def capture_live():(out/(label+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
         g.run_while(capture_live,settle_seconds=.3,start_delay=.5);capture_serial=request['id']
       b=(c/'UITASK.TXT').read_bytes()
       if b!=sent:
        assert len(b)==4096
        with image.open('r+b',buffering=0) as f:
         for i,off in enumerate(offsets):
          data=b[i*size:(i+1)*size]
          if data:f.seek(off);f.write(data)
        sent=b
       try:
        with PyFatFS(str(image),offset=partition,read_only=True) as fs:
         for n in ['UISTATE.TXT','UIVRAM.BIN','UIMEM.LOG','INSTALL.LOG','GRAB.LOG','RETURN1.TXT','WINDOWS/WIN.INI','WINDOWS/SYSTEM.INI']+([args.guest_log] if args.guest_log else []):
          if fs.exists(n):
           data=fs.readbytes(n)
           if n=='UISTATE.TXT' and (not data.startswith(b'STATE ') or not data.endswith(b'UI_COMPLETE\r\n')):continue
           if n=='UIVRAM.BIN' and len(data)!=32768:continue
           (c/Path(n).name).write_bytes(data)
         fresh=(c/'UISTATE.TXT').exists() and (c/'UISTATE.TXT').read_bytes().startswith(b'STATE ')
         done=fresh and b' EXIT' in b and g.read_memory(0x449,1)==b'\x03'
        if fresh:
         state=(c/'UISTATE.TXT').read_text(errors='replace');seq=state.split(' ',3)[1]
         if not args.no_auto_captures and seq not in captures and len(captures)<80:
          (out/(stage+'-'+seq.replace('=','')+'.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()));captures.add(seq)
        if done:
         g.run_while(lambda:None,settle_seconds=4,start_delay=.01)
         text=g.read_memory(0xb8000,4000)[::2].decode('cp437')
         if 'WINDOWS>' not in text and 'C>' not in text and 'C:\\>' not in text:continue
         with PyFatFS(str(image),offset=partition,read_only=True) as fs:
          for name in ('RETURN1.TXT','WINDOWS/WIN.INI','WINDOWS/SYSTEM.INI'):
           if fs.exists(name):(c/Path(name).name).write_bytes(fs.readbytes(name))
         (out/(stage+'-DOS.TXT')).write_text(text,encoding='utf-8')
         (out/(stage+'-RETURN.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()));print('NORMAL_DOS_RETURN',stage,flush=True);break
       except PermissionError:raise
       except (OSError,ValueError,PyFATException):pass
      else:raise TimeoutError('ColorPlus UI bound')
     finally:
      if ctl and stop.exists():
       try:(out/(stage+'-STOP.PNG')).write_bytes(base64.b64decode(ctl.capture_frame_png_b64()))
       except OSError:pass
      if ctl:ctl.close()
      if g:g.close()
      if p.poll() is None:p.kill();p.wait(timeout=10)
      child['stopped']=True;runner.save()

with runner.lease():
    owned_session()
