from pathlib import Path
import sys,shutil,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
sys.path[:0]=[r'C:\Users\chad\Documents\Codex\2026-10-27\task-6\deps-local']
from pyfatfs.PyFatFS import PyFatFS
native=len(sys.argv)>1
out=ROOT/(sys.argv[1] if native else 'fresh-oem-01');out.mkdir()
dos6=native
source=Path(r'C:\Users\chad\Documents\Codex\2026-10-24\task-2\native\RCDOS-FRESH-FINAL\DISK.IMG') if dos6 else Path(r'E:\DOSMCP\disks\tandy_hdd_dos_baseline.img')
offset=17408 if dos6 else 8704
assert shutil.disk_usage(ROOT).free>1024**3
shutil.copyfile(source,out/'DISK.IMG')
pins={}
with PyFatFS(str(out/'DISK.IMG'),offset=offset) as fs:
    for n in list(fs.listdir('/')):
        if n.upper() in ('IO.SYS','MSDOS.SYS','COMMAND.COM','DOS') if dos6 else n.upper() in ('IBMBIO.COM','IBMDOS.COM','COMMAND.COM'):continue
        if fs.isdir(n):fs.removetree(n)
        else:fs.remove(n)
    assert not fs.exists('WINDOWS')
    fs.makedir('W30SRC');fs.makedir('CGAPK');fs.makedir('CGAPK/CGA')
    for disk in sorted(Path(r'E:\gh\Microsoft Windows 3.0 (3.5-1.44MB)').glob('DISK*.IMG')):
        pins[disk.name]=hashlib.sha256(disk.read_bytes()).hexdigest()
        with PyFatFS(str(disk),read_only=True) as media:
            for n in media.listdir('/'):
                if media.isdir(n):raise ValueError(n)
                b=media.readbytes(n);target='W30SRC/'+n
                if fs.exists(target):assert fs.readbytes(target)==b
                else:fs.writebytes(target,b)
    with zipfile.ZipFile(ROOT/('fresh-packet-01/CGAFRESH.ZIP' if native else 'display/downloads/COMPACT/CGA.ZIP')) as z:
        for n in z.namelist():
            target='CGAPK/'+n
            parent=target.rsplit('/',1)[0]
            fs.makedirs(parent,recreate=True)
            fs.writebytes(target,z.read(n))
    fs.writebytes('CONFIG.SYS',b'FILES=30\r\nBUFFERS=20\r\n')
    fs.writebytes('AUTOEXEC.BAT',b'@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS\r\nVER >C:\\DOSVER.TXT\r\nCD \\W30SRC\r\nSETUP\r\nECHO RETURNED>C:\\RETURN.TXT\r\n')
    if native:
        fs.writebytes('AUTOEXEC.BAT',b'@ECHO OFF\r\nPATH C:\\;C:\\WINDOWS\r\nVER >C:\\DOSVER.TXT\r\nCD \\CGAPK\r\nFRESH /CHECK C:\\NOTHERE >C:\\BADMEDIA.LOG\r\nIF ERRORLEVEL 4 GOTO FAIL\r\nIF NOT ERRORLEVEL 3 GOTO FAIL\r\nCOPY FRESH640\\OEMSETUP.INF ORIGINAL.INF >NUL\r\nECHO BROKEN>FRESH640\\OEMSETUP.INF\r\nFRESH /CHECK C:\\W30SRC >C:\\BADKIT.LOG\r\nIF ERRORLEVEL 5 GOTO FAIL\r\nIF NOT ERRORLEVEL 4 GOTO FAIL\r\nCOPY ORIGINAL.INF FRESH640\\OEMSETUP.INF >NUL\r\nFRESH /CHECK C:\\W30SRC >C:\\INPUTOK.LOG\r\nIF ERRORLEVEL 1 GOTO FAIL\r\nECHO PASS>C:\\CHECK.DON\r\nFRESH C:\\W30SRC\r\nECHO RETURNED>C:\\RETURN.TXT\r\nGOTO END\r\n:FAIL\r\nECHO FAIL>C:\\CHECK.DON\r\n:END\r\n')
    fs.fs.flush_fat()
cfg='''[General]
confirm_exit = 0
confirm_reset = 0
confirm_save = 0
[Machine]
cpu_family = 8088
cpu_multi = 1
cpu_speed = 4772728
cpu_use_dynarec = 0
machine = ibmxt86
mem_size = 640
time_sync = disabled
[Video]
gfxcard = cga
[IBM CGA]
display_type = 0
composite_type = 1
rgb_type = 0
snow_enabled = 1
double_type = 1
[Input devices]
keyboard_type = keyboard_pc_xt
mouse_type = msserial
[Storage controllers]
hdc_1 = xtide
[Hard disks]
hdd_01_fn = DISK.IMG
hdd_01_ide_channel = 0:0
hdd_01_parameters = 17, 4, 615, 0, ide
hdd_01_speed = ramdisk
[PC/XT XTIDE #1]
bios = xt
[Floppy and CD-ROM drives]
fdd_01_type = 525_2dd
fdd_02_type = none
'''
if dos6:cfg=cfg.replace('17, 4, 615','34, 5, 969')
(out/'86box.cfg').write_text(cfg)
(out/'PREPARE.json').write_text(json.dumps(dict(original_media=pins,windows_absent_at_start=True,fat_offset=offset,disk_bytes=(out/'DISK.IMG').stat().st_size,source_disk_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),setup_inf_sha256=hashlib.sha256(Path(r'E:\gh\Microsoft Windows 3.0 (3.5-1.44MB)\SETUP.INF').read_bytes()).hexdigest()),indent=2))
print(out)
