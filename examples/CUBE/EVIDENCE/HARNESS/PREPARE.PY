from pathlib import Path
import sys,shutil,json,re,hashlib,subprocess,msvcrt
ROOT=Path(__file__).resolve().parent
BUILDS=dict(cube='build-cube-11',shell='build-shell-04',idle='build-idle-01',installer='build-set-06')
PAYLOAD={
 'CUBE.EXE':ROOT/BUILDS['cube']/'CUBE.EXE',
 'CUBECTL.EXE':ROOT/BUILDS['cube']/'CUBECTL.EXE',
 'CUBESHL.EXE':ROOT/BUILDS['shell']/'TSHELL.EXE',
 'TSINPUT.DLL':ROOT/BUILDS['idle']/'TSINPUT.DLL',
 'CUBESET.EXE':ROOT/BUILDS['installer']/'CUBESET.EXE'
}
if '--pre-focus'in sys.argv:
 PAYLOAD['CUBE.EXE']=ROOT/'build-cube-09/CUBE.EXE';PAYLOAD['CUBESET.EXE']=ROOT/'build-set-05/CUBESET.EXE'
sys.path.insert(0,r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\deps-local')
from pyfatfs.PyFatFS import PyFatFS
kind=sys.argv[1];out=ROOT/sys.argv[2];out.mkdir()
(out/'PREPARE.PY').write_bytes(Path(__file__).read_bytes())
ui='--ui' in sys.argv
reuse=next((s.split('=',1)[1]for s in sys.argv if s.startswith('--image=')),None)
base=Path(r'C:\Users\chad\Documents\Codex\2026-10-27\task-10\fresh-native-02') if kind.startswith('cga') or kind=='ega' else ROOT/'native-tandy-02'
lease=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock')
with lease.open('rb')as lock:
    lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_NBLCK,1)
    try:
        inv=subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue).Count'],text=True).strip()
        assert inv=='0'
        image=(ROOT/reuse).resolve()if reuse else out/'DISK.IMG';assert image.is_relative_to(ROOT)
        assert shutil.disk_usage(out).free>1024**3
        if not reuse:shutil.copyfile(base/'DISK.IMG',image)
        (out/'IMAGEREF.txt').write_text(str(image))
        with PyFatFS(str(image),offset=17408)as f:
            def put(path,data):
                # pyfatfs cannot safely grow some existing native DOS entries
                # via its truncating writer. Replace the directory entry first.
                if f.exists(path):f.remove(path)
                f.writebytes(path,data)
            f.makedirs('CUBE',recreate=True)
            for name,path in PAYLOAD.items():put('CUBE/'+name,path.read_bytes())
            for path in ('WINDOWS/TSHCUBE.BAK','WINDOWS/TICUBE.BAK','WINDOWS/CUBESH.NEW','WINDOWS/CUBEIN.NEW','WINDOWS/CUBE.INI','WINXT/CUBE.EXE','WINXT/CUBE.LOG','CUBEDONE.TXT','CUBEUI.LOG','INSTALL.LOG','UNDO.LOG','REINST.LOG','UNKNOWN.LOG','APPONLY.LOG','CUBE/AFTERSH.EXE'):
                if f.exists(path):f.remove(path)
            # Explicit private fixture: install the known current shell first.
            put('WINDOWS/TSHELL.EXE',(ROOT/'old-shell.exe').read_bytes())
            put('WINDOWS/TSINPUT.DLL',(ROOT/'display/examples/TSHELL/TSINPUT.DLL').read_bytes())
            put('WINDOWS/TSHELL.INI',b'[Sounds]\r\nStartup=NONE\r\nExitChime=0\r\n[Startup]\r\nLoadRun=0\r\n[ScreenSaver]\r\nEnabled=0\r\n')
            # WIN /R application tail selects the actual Cube /Q test process.
            ini=f.readtext('WINDOWS/SYSTEM.INI').replace('\r\n','\n').replace('\r','')
            def setting(key,value):
                global ini
                ini=re.sub(r'(?im)^'+re.escape(key)+r'=.*$',lambda m:key+'='+value,ini)
            if kind in ('cga100','cga320','cga640','cgapan'):
                driver={'cga100':'CGA100.DRV','cga320':'CGA320.DRV','cga640':'CGA640.DRV','cgapan':'CGAPAN.DRV'}[kind]
                names=[driver]+(['CG1SYS.FON','CG1FIX.FON','CG1OEM.FON'] if kind in ('cga100','cgapan') else ['XTCSYS.FON','XTCFIX.FON','XTCOEM.FON'])
                for n in names:put('WINDOWS/SYSTEM/'+n,f.readbytes('CGAPK/CGA/'+n))
                setting('display.drv',driver)
                for key,n in zip(('fonts.fon','fixedfon.fon','oemfonts.fon'),names[1:]):setting(key,n)
            elif kind in ('tandy160','tandy3204','tandy6404','tandy6402'):
                driver={'tandy160':'TNDY160.DRV','tandy3204':'TNDY3204.DRV','tandy6404':'TNDY6404.DRV','tandy6402':'TNDY6402.DRV'}[kind]
                put('WINDOWS/SYSTEM/'+driver,subprocess.check_output(['git','-C',str(ROOT/'display'),'show','HEAD:src/tandysw/bin/'+driver]))
                setting('display.drv',driver)
            elif kind in ('tandy','tandy320'):
                setting('display.drv','TR53216.DRV')
                for key,n in [('fonts.fon','XTESYS.FON'),('fixedfon.fon','XTEFIX.FON'),('oemfonts.fon','XTEOEM.FON')]:
                    put('WINDOWS/SYSTEM/'+n,subprocess.check_output(['git','-C',str(ROOT/'display'),'show','HEAD:distributions/WINXT/'+n]));setting(key,n)
            elif kind=='pan':
                put('WINDOWS/SYSTEM/HPXY.DRV',subprocess.check_output(['git','-C',str(ROOT/'display'),'show','HEAD:tools/HPDIB/BIN/HPXY.DRV']))
                setting('display.drv','HPXY.DRV')
            elif kind=='ega':
                for n in ('EGA.DRV','EGASYS.FON','EGAFIX.FON','EGAOEM.FON'):put('WINDOWS/SYSTEM/'+n,f.readbytes('W30SRC/'+n))
                for key,n in [('display.drv','EGA.DRV'),('fonts.fon','EGASYS.FON'),('fixedfon.fon','EGAFIX.FON'),('oemfonts.fon','EGAOEM.FON')]:setting(key,n)
            if kind in ('tandy160','tandy3204','tandy6404','tandy6402','pan'):
                for key,n in [('fonts.fon','XTCSYS.FON'),('fixedfon.fon','XTCFIX.FON'),('oemfonts.fon','XTCOEM.FON')]:
                    put('WINDOWS/SYSTEM/'+n,subprocess.check_output(['git','-C',str(ROOT/'display'),'show','HEAD:distributions/WINXT/'+n]));setting(key,n)
            setting('shell','TSHELL.EXE'if ui else'PROGMAN.EXE')
            put('WINDOWS/SYSTEM.INI',ini.replace('\n','\r\n').encode('ascii'))
            prefix=b'RESERVE 32\r\n' if not (kind.startswith('cga')or kind=='ega') else b''
            command=b'WIN /R C:\\CUBE\\CUBECTL.EXE' if ui else (b'WIN /R C:\\CUBE\\CUBECTL.EXE /P' if kind in ('pan','cgapan') else b'WIN /R C:\\CUBE\\CUBECTL.EXE /Q')
            guards=b''
            if '--install-guards'in sys.argv:
                guards=b'COPY /Y /B C:\\WINDOWS\\TSHELL.EXE C:\\CUBE\\OLDSHL.EXE >NUL\r\nECHO UNKNOWN>C:\\WINDOWS\\TSHELL.EXE\r\nCUBESET C:\\WINDOWS >C:\\UNKNOWN.LOG\r\nIF NOT ERRORLEVEL 1 GOTO FAIL\r\nCUBESET /APPONLY C:\\WINDOWS >C:\\APPONLY.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nCOPY /Y /B C:\\WINDOWS\\TSHELL.EXE C:\\CUBE\\AFTERSH.EXE >NUL\r\nCOPY /Y /B C:\\CUBE\\OLDSHL.EXE C:\\WINDOWS\\TSHELL.EXE >NUL\r\n'
            auto=b'@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS;C:\\DOS\r\nCD \\CUBE\r\n'+guards+b'CUBESET C:\\WINDOWS > C:\\INSTALL.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\n'+prefix+b'CD \\WINDOWS\r\n'+command+b'\r\nCD \\CUBE\r\nCUBESET /UNDO C:\\WINDOWS > C:\\UNDO.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nCUBESET C:\\WINDOWS > C:\\REINST.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nECHO RETURNED>C:\\CUBEDONE.TXT\r\nGOTO END\r\n:FAIL\r\nECHO FAILED>C:\\CUBEDONE.TXT\r\n:END\r\n'
            put('AUTOEXEC.BAT',auto);f.fs.flush_fat()
            environment={}
            for key in ('display.drv','fonts.fon','fixedfon.fon','oemfonts.fon'):
                name=re.search(r'(?im)^'+re.escape(key)+r'=(.*)$',ini)[1].strip()
                data=f.readbytes('WINDOWS/SYSTEM/'+name);environment[key]=dict(name=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
            environment['system_ini_sha256']=hashlib.sha256(f.readbytes('WINDOWS/SYSTEM.INI')).hexdigest()
        config=(base/'86box.cfg').read_text();config=re.sub(r'(?m)^hdd_01_fn\s*=.*$',lambda m:'hdd_01_fn = '+image.as_posix(),config)
        if kind=='ega':config=config.replace('gfxcard = cga','gfxcard = ega')
        (out/'86box.cfg').write_text(config)
        (out/'INPUT.CNF').write_bytes((out/'86box.cfg').read_bytes())
        (out/'PREPARE.json').write_text(json.dumps(dict(base=str(base),environment=environment,private_image=True,reused=bool(reuse),bytes=image.stat().st_size,scope=kind+('; UI and idle'if ui else '; kit, /Q, undo and reinstall'),install_guards='--install-guards'in sys.argv,negative_control='--pre-focus'in sys.argv,changes=['AUTOEXEC test entry','explicit known current TSHELL and TSINPUT baseline','kit files in CUBE folder','selected documented display fixture'],payload={n:hashlib.sha256(p.read_bytes()).hexdigest()for n,p in PAYLOAD.items()},originals={n:hashlib.sha256(p.read_bytes()).hexdigest()for n,p in [('TSHELL.EXE',ROOT/'old-shell.exe'),('TSINPUT.DLL',ROOT/'display/examples/TSHELL/TSINPUT.DLL')]}),indent=2))
    finally:lock.seek(0);msvcrt.locking(lock.fileno(),msvcrt.LK_UNLCK,1)
print(out)
