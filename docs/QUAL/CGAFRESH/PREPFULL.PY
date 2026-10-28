from pathlib import Path
import sys,json,re,hashlib,subprocess,msvcrt,shutil
root=Path(__file__).resolve().parent
sys.path.insert(0,r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\deps-local')
from pyfatfs.PyFatFS import PyFatFS
out=root/'fresh-complete-01';out.mkdir()
image=root/'fresh-native-02/DISK.IMG'
lock=Path(r'C:\Users\chad\Documents\Codex\2026-10-06\tandy-emulator.lock')
assert shutil.disk_usage(root).free>1024**3
with lock.open('rb')as lease:
    lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_NBLCK,1)
    try:
        count=subprocess.check_output(['powershell.exe','-NoProfile','-Command','@(Get-Process -Name dosbox*,86Box,TRACEIO,FIXBOX,pcem,tandybox -ErrorAction SilentlyContinue).Count'],text=True).strip();assert count=='0'
        before=hashlib.sha256(image.read_bytes()).hexdigest()
        with PyFatFS(str(image),offset=17408)as f:
            assert b'shell=setup.exe' in f.readbytes('WINDOWS/SYSTEM.INI')
            (out/'AUTOEXEC.BEFORE').write_bytes(f.readbytes('AUTOEXEC.BAT'))
            f.writebytes('AUTOEXEC.BAT',b'@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS;C:\\DOS\r\nCD \\WINDOWS\r\nWIN /R\r\nECHO RETURNED>C:\\SETUPRET.TXT\r\n')
            f.writebytes('FIRST.BAT',b'@ECHO OFF\r\nCD \\WINDOWS\r\nWIN /R\r\nECHO RETURNED>C:\\FIRSTRUN.TXT\r\n')
            f.fs.flush_fat()
        cfg=(root/'fresh-native-02/86box.cfg').read_text();cfg=re.sub(r'(?m)^hdd_01_fn\s*=.*$',lambda m:'hdd_01_fn = '+image.as_posix(),cfg)
        (out/'86box.cfg').write_text(cfg)
        (out/'PREPARE.json').write_text(json.dumps(dict(reused_image=str(image),image_sha256_before_resume=before,new_disk_image=False,scope='Resume original graphical Setup shell, complete install, then normal WIN /R; no display/INI changes',changes=['AUTOEXEC only: WIN /R to resume existing original setup shell','FIRST.BAT only: ordinary WIN /R with DOS-return marker']),indent=2))
    finally:lease.seek(0);msvcrt.locking(lease.fileno(),msvcrt.LK_UNLCK,1)
runner=(root/'run_fresh.py').read_text().replace('bound=1200','bound=1800')
(root/'run_continue.py').write_text(runner)
print(out)
