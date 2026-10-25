"""Exercise actual FIXXT CHECK/REPAIR against synthetic XRSYNC file fixtures.

Windows host checks complement the separate native DOS acceptance. Every GCC
compile on Windows uses the shared dependency-preflight launcher.
"""
from pathlib import Path
import os
import re
import subprocess
import sys
import tempfile
import zlib

HERE = Path(__file__).resolve().parent


def require(ok, message):
    if not ok:
        raise AssertionError(message)


def inventory(root):
    return {str(p.relative_to(root)): p.read_bytes()
            for p in root.rglob('*') if p.is_file()}


def crc_fixture(length, wanted):
    data = bytearray(length)
    start = zlib.crc32(data)
    basis = {}
    for bit in range(32):
        altered = bytearray(data)
        altered[-4+(bit//8)] ^= 1 << (bit%8)
        value, mask = zlib.crc32(altered)^start, 1 << bit
        while value:
            top = value.bit_length()-1
            if top in basis:
                value ^= basis[top][0]; mask ^= basis[top][1]
            else:
                basis[top] = value, mask
                break
    value, mask = wanted^start, 0
    while value:
        top = value.bit_length()-1
        value ^= basis[top][0]; mask ^= basis[top][1]
    data[-4:] = mask.to_bytes(4, 'little')
    require(zlib.crc32(data) == wanted, 'Synthetic CRC fixture failed')
    return bytes(data)


def main():
    if os.name != 'nt':
        raise SystemExit('TESTFIX requires Windows host file APIs; native DOS QA is separate')
    source = (HERE/'FIXXT.C').read_text()
    names = re.findall(r'"([^"]+)"', re.search(
        r'static const char \*names\[\]=\{([^}]+)\};', source).group(1))
    sound_header = (HERE/'SOUNDID.H').read_text()
    sound_bytes = int(re.search(r'#define SOUND_BYTES (\d+)U', sound_header).group(1))
    sound_crc = int(re.search(r'#define SOUND_CRC 0x([0-9a-f]+)UL', sound_header).group(1), 16)
    sizes = [sound_bytes if n == 'SOUND_BYTES' else int(n[:-2]) for n in re.search(
        r'static unsigned long sizes\[\]=\{([^}]+)\};', source).group(1).split(',')]
    targets = [int(n) for n in re.search(
        r'static int target\[\]=\{([^}]+)\};', source).group(1).split(',')]
    skip = {'C216N6.DRV', 'C23216.DRV', 'PANCMP2.DRV', 'HPXY.DRV',
            'XYCTL.EXE', 'XTPAN.EXE', 'XTS6SYS.FON', 'XTS6FIX.FON',
            'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON', 'CGA.GR2', 'SETUP.INF'}
    launcher = Path(r'C:\Users\chad\Documents\Codex\toolchains\gcc-ucrt64.py')
    with tempfile.TemporaryDirectory(prefix='fixxt-xrsync-') as temp:
        root = Path(temp)
        exe = root/'FIXXT-HOST.EXE'
        subprocess.run([sys.executable, str(launcher), '--', '-x', 'c',
            '-std=c89', '-DHOST_TEST', '-O0', str(HERE/'FIXXT.C'),
            '-o', str(exe)], check=True)
        win, home = root/'WIN', root/'WINXT'
        system, media = win/'SYSTEM', home/'FILES'
        system.mkdir(parents=True)
        media.mkdir(parents=True)
        for name, size, target in zip(names, sizes, targets):
            if name in skip:
                continue
            data = (name.encode('ascii')+b'\0')*size
            data = data[:size]
            if name == 'SOUND.DRV':
                data = crc_fixture(sound_bytes, sound_crc)
            (media/name).write_bytes(data)
            ((home if target == 2 else system if target else win)/name).write_bytes(data)
        ini = ('; preserve comments\r\n[boot]\r\n'
            'system.drv=SYSTEM.DRV\r\nsound.drv=SOUND.DRV\r\n'
            'shell=TSHELL.EXE\r\nkeyboard.drv=TNDYK3.DRV\r\n'
            'mouse.drv=WHEEL.DRV\r\n'
            'display.drv=XRSYNC.DRV ; keep selected display\r\n'
            'fonts.fon=CUSTOM.FON\r\nfixedfon.fon=CUSTOMFX.FON\r\n'
            'oemfonts.fon=CUSTOMOEM.FON\r\n286grabber=CUSTOM.GR2\r\n'
            '[boot.description]\r\n'
            'system.drv=Tandy 1000 EX/HX (WindowsXT)\r\n'
            'keyboard.typ=PC/XT - Type keyboard (84 keys)\r\n'
            'mouse.drv=Tandy serial wheel mouse (COM1/IRQ4)\r\n'
            'display.drv=Selected XRSYNC profile\r\n'
            '[keyboard]\r\ntype=1\r\n').encode('ascii')
        (system/'SYSTEM.DRV').write_bytes(crc_fixture(2784, 0x3ff05fec))
        (win/'SYSTEM.INI').write_bytes(ini)
        (win/'WIN.INI').write_bytes(b'[windows]\r\nrun=C:\\XR155\\XYCTL.EXE /KEEP OTHER.EXE\r\nBorderWidth=7\r\n')
        (win/'WIN.COM').write_bytes(b'original installed Windows bootstrap')
        for name in ('XRSYNC.DRV', 'CUSTOM.FON', 'CUSTOMFX.FON', 'CUSTOMOEM.FON', 'CUSTOM.GR2', 'SETUP.INF'):
            (system/name).write_bytes(b'currently installed independent display data: '+name.encode())
        (home/'XYCTL.EXE').write_bytes(b'current XRSYNC panning controller')
        (home/'PROFILE.TXT').write_bytes(b'HPXY.DRV\r\n')
        preserved = {p: p.read_bytes() for p in
            [win/'SYSTEM.INI', win/'WIN.INI', home/'XYCTL.EXE']+
            [system/name for name in ('XRSYNC.DRV', 'CUSTOM.FON', 'CUSTOMFX.FON', 'CUSTOMOEM.FON', 'CUSTOM.GR2', 'SETUP.INF')]}

        def run(verb, *options):
            result = subprocess.run([str(exe), verb, str(win), str(home), *options],
                capture_output=True, text=True, timeout=20)
            if result.returncode:
                print(result.stdout, end='')
            return result

        before = inventory(root)
        require(run('CHECK').returncode == 0, 'CHECK must prefer installed XRSYNC to stale HPXY profile')
        require(inventory(root) == before, 'CHECK changed files')
        (home/'TP.EXE').unlink()
        (system/'SOUND.DRV').unlink()
        require(run('REPAIR').returncode == 0, 'REPAIR must update shared clients with display sources absent')
        require((home/'TP.EXE').read_bytes() == (media/'TP.EXE').read_bytes(), 'Shared TP repair failed')
        require((system/'SOUND.DRV').read_bytes() == (media/'SOUND.DRV').read_bytes(), 'Canonical sound install failed')
        require((home/'PROFILE.TXT').read_bytes() == b'XRSYNC.DRV\r\n', 'Selected profile was downgraded')
        require(all(p.read_bytes() == data for p, data in preserved.items()), 'Display/font/grabber/panning state changed')
        require(run('CHECK').returncode == 0, 'CHECK failed after client repair')
        (home/'PROFILE.TXT').write_bytes(b'HPXY.DRV\r\n')
        require(run('REPAIR', '/XR1', '/FRESH').returncode == 0, 'Legacy install defaults overrode actual XRSYNC')
        require(all(p.read_bytes() == data for p, data in preserved.items()), 'Legacy install defaults changed display state')
        require((home/'PROFILE.TXT').read_bytes() == b'XRSYNC.DRV\r\n', 'Fresh default downgraded saved profile')
        # Current shell and wrapper can change only in their middle bytes.
        for name in ('XTCLEAN.COM', 'TSHELL.EXE'):
            stale = bytearray((win/name).read_bytes())
            stale[len(stale)//2] ^= 1
            (win/name).write_bytes(stale)
            before = inventory(root)
            require(run('CHECK').returncode == 2, 'Same-edge stale '+name+' was accepted')
            require(inventory(root) == before, 'Stale-client CHECK changed files')
            require(run('REPAIR').returncode == 0, name+' exact repair failed')
            require((win/name).read_bytes() == (media/name).read_bytes(), name+' full identity not restored')
        (win/'SYSTEM.INI').write_bytes(ini.replace(b'sound.drv=SOUND.DRV', b'sound.drv=TSOUND.DRV'))
        require(run('REPAIR').returncode == 0, 'Existing sound entry was not unified')
        require((win/'SYSTEM.INI').read_bytes() == ini, 'Sound key repair changed unrelated settings')
        for badpath in (media/'SOUND.DRV', system/'SYSTEM.DRV'):
            good = badpath.read_bytes()
            damaged = bytearray(good); damaged[100] ^= 1
            badpath.write_bytes(damaged)
            before = inventory(root)
            require(run('REPAIR').returncode == 2, 'Bad sound/system bytes were accepted')
            require(inventory(root) == before, 'Bad source/system refusal changed files')
            badpath.write_bytes(good)
        for badini in (ini.replace(b'system.drv=SYSTEM.DRV', b'system.drv=OTHER.DRV'),
                       ini.replace(b'sound.drv=SOUND.DRV\r\n', b''),
                       ini.replace(b'sound.drv=SOUND.DRV', b'sound.drv=SOUND.DRV\r\nsound.drv=SOUND.DRV')):
            (win/'SYSTEM.INI').write_bytes(badini)
            before = inventory(root)
            require(run('REPAIR').returncode == 2, 'Incompatible or duplicate/missing selection accepted')
            require(inventory(root) == before, 'Selection refusal changed files')
        (win/'SYSTEM.INI').write_bytes(ini)
        # SOUND requires full identity even when size/header/end match.
        badsound = bytearray((system/'SOUND.DRV').read_bytes())
        badsound[len(badsound)//2] ^= 1
        (system/'SOUND.DRV').write_bytes(badsound)
        require(run('CHECK').returncode == 2, 'Same-edge corrupt SOUND was accepted')
        require(run('REPAIR').returncode == 0, 'Canonical SOUND repair failed')
        require((system/'SOUND.DRV').read_bytes() == (media/'SOUND.DRV').read_bytes(), 'Canonical SOUND identity not restored')
        # Recover the finisher's own interrupted SYSTEM.INI rename only after
        # immutable SYSTEM/source pins pass; then validate the restored keys.
        (win/'SYSTEM.INI').rename(win/'SIMPLE.OLD')
        (win/'SIMPLE.NEW').write_bytes(ini)
        (win/'SIMPLE.JRN').write_bytes(b'TINYXT1 SYSTEM.INI 1\r\n')
        soundgood = (media/'SOUND.DRV').read_bytes()
        badsound = bytearray(soundgood); badsound[100] ^= 1
        (media/'SOUND.DRV').write_bytes(badsound)
        before = inventory(root)
        require(run('REPAIR').returncode == 2, 'Bad source allowed pending journal writes')
        require(inventory(root) == before, 'Bad-source preflight changed pending recovery')
        (media/'SOUND.DRV').write_bytes(soundgood)
        require(run('REPAIR').returncode == 0, 'Own torn INI rename did not recover')
        require((win/'SYSTEM.INI').read_bytes() == ini, 'Recovered INI changed settings')
        require(not any((win/n).exists() for n in ('SIMPLE.OLD','SIMPLE.NEW','SIMPLE.JRN')), 'Own recovery left temporary state')
        (system/'XRSYNC.DRV').unlink()
        before = inventory(root)
        result = run('REPAIR')
        require(result.returncode == 2 and 'Selected XRSYNC driver is missing' in result.stdout,
                'Missing installed XRSYNC was not refused')
        require(inventory(root) == before, 'Missing-driver refusal changed files')
    print('PASS: XRSYNC preservation; canonical SOUND install; sound/system preflight refusals; exact XTCLEAN repair; no-write failed starts')


if __name__ == '__main__':
    main()
