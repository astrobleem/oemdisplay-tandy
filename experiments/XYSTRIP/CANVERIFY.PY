"""Independently verify normal same-name install and Paintbrush framebuffer."""
from pathlib import Path
import hashlib
import json
import re
import struct
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration'
RUN = OUT / (sys.argv[1] if len(sys.argv) > 1 else 'canonical-install-01')
sys.path.insert(0, r'C:\Users\chad\Documents\Codex\2026-10-14\task-16\deps-local')
from pyfatfs.PyFatFS import PyFatFS


def ident(b):
    return dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def pixel(s, x, y):
    i = y * 320 + x // 8
    return sum(w for p, w in enumerate((4, 2, 1, 8)) if s[i + p * 80] & (128 >> (x & 7)))


def verify(helper=False):
    r = json.loads((RUN / 'RESULT.JSON').read_bytes())
    assert not r.get('error'), r.get('error')
    assert r['complete'] and r['dos_return'] and r['owned_stopped']
    assert r['lease_acquired'] and r['lease_released']
    before = json.loads((RUN / 'PREPARE.JSON').read_bytes())
    if not helper:
        assert r['refresh_answered'] == 'Y'
        assert r['retained_old_before_refresh'] == before['installed_before']['HPXY.DRV']
    assert 'Version  3.20' in r['logs']['DOSVER.TXT']
    if not helper:
        assert 'DISPLAY RETURNED' in r['logs']['INSTALL.LOG']
        assert 'Replace only SYSTEM' in r['refresh_prompt'] and '[y/N]' in r['refresh_prompt']
    assert all(s in r['metrics'] for s in ('END FAILURES=0', 'CHECK REPAINT_PENDING=1',
        'CHECK REPAINT_COMPLETE=1', 'PAINTBRUSH - PANAPP.BMP'))
    with zipfile.ZipFile(OUT / 'CANONICAL.ZIP') as z:
        assert z.testzip() is None
        entries = {n: z.read(n) for n in z.namelist()}
    with PyFatFS(str(RUN / 'DISK.IMG'), offset=8704, read_only=True) as fs:
        preserved = {n: ident(fs.readbytes('WINDOWS/SYSTEM/' + n)) == pin
                     for n, pin in before['installed_before'].items() if n != 'HPXY.DRV'}
        assert all(preserved.values())
        assert fs.readbytes('WINDOWS/SYSTEM/HPXY.DRV') == entries['WINXT/HPXY.DRV']
        assert all(fs.readbytes('PANSTEP/' + n) == b for n, b in entries.items())
        assert all(ident(fs.readbytes('ALT/WINXT/' + n)) == p for n, p in before['old_source'].items())
        ini = fs.readbytes('WINDOWS/SYSTEM.INI')
        assert b'display.drv=HPXY.DRV' in ini and b'shell=progman.exe' in ini.lower()
        (RUN / 'SYSTEM-AFTER.INI').write_bytes(ini)
        fixture = Path(r'C:\Users\chad\Documents\Codex\2026-10-24\task-3\native\COMMON-OEM2\DISK.IMG')
        with PyFatFS(str(fixture), offset=8704, read_only=True) as baseline:
            for n in ['CONFIG.SYS', 'WINDOWS/PROGMAN.EXE', 'WINDOWS/PBRUSH.EXE', 'WINDOWS/PBRUSH.DLL']:
                assert fs.readbytes(n) == baseline.readbytes(n), n
    frames = []
    for line in r['metrics'].splitlines():
        if not line.startswith('FRAME '):
            continue
        d = {k: int(v) for k, v in re.findall(r'(\w+)=(-?\d+)', line)}
        s = (RUN / ('A%03d.BIN' % d['id'])).read_bytes()
        v = (RUN / ('B%03d.BIN' % d['id'])).read_bytes()
        assert len(s) == 81920 and len(v) == 32768
        for y in range(200):
            for x in range(0, 320, 2):
                expected = 16 * pixel(s, d['x'] + x, d['y'] + y) + pixel(s, d['x'] + x + 1, d['y'] + y)
                address = (y & 3) * 8192 + ((y // 4 * 160 + d['head'] * 2 + x // 2) & 8191)
                assert v[address] == expected, (d, x, y, address)
        frames.append(dict(frame=d, compared_bytes=32000, result='PASS'))
    assert len(frames) == (8 if helper else 4)
    if helper:
        expected = [(102, 8, 0, 800), (110, 8, 4, 640), (101, 0, 4, 800), (109, 0, 0, 640)]
        actual = [tuple(map(int, m)) for m in re.findall(
            r'HELPER command=(\d+) x=(\d+) y=(\d+) bytes=(\d+) reason=0', r['metrics'])]
        assert actual == expected
        assert all('CHECK ' + k + '=1' in r['metrics'] for k in
                   ('HELPER_SOURCE', 'HELPER_DEFAULT_SOFT', 'HELPER_CLOSED'))
    with (RUN / 'DISK.IMG').open('rb') as f:
        f.seek(8704)
        b = f.read(512)
        bps, rs = struct.unpack_from('<HH', b, 11)[0], struct.unpack_from('<H', b, 14)[0]
        nf, spf = b[16], struct.unpack_from('<H', b, 22)[0]
        fats = []
        for i in range(nf):
            f.seek(8704 + (rs + i * spf) * bps)
            fats.append(f.read(spf * bps))
        assert all(b == fats[0] for b in fats)
    move = re.search(r'MOVE from=0,0 to=16,8 total_ms=(\d+) bytes=2816 reason=0', r['metrics'])
    assert move
    q = dict(complete=True, owned_stopped=True, lease_released=True,
        archive=ident((OUT / 'CANONICAL.ZIP').read_bytes()),
        installed_driver=ident(entries['WINXT/HPXY.DRV']), normal_dos_return=True,
        paintbrush_repaint_and_pan=True, same_basename_replaced_after_explicit_Y=not helper,
        installed_helper_steps_verified=helper,
        source_folder_exact=True, original_source_preserved=True,
        unrelated_modules_preserved=preserved, fat_copies_match=True,
        application_frames=frames, guest_dos='IBM PC DOS 3.20',
        movement=dict(path='Absolute Escape (0,0)->(16,8), mode1 staged2816',
            total_ms=int(move[1]), blackout_ms=None, timer_resolution_ms=55,
            excludes='Logging, helper cadence and forced repaint after pan'),
        scope=('Installed canonical DISPWIN, Paintbrush and actual XYCTL 8/4 menu commands' if helper else
               'Actual native DISPLAY/Other/same-name refresh/DISPWIN and Paintbrush'),
        physical_hardware=False, seconds=r['seconds'], lease_wait_seconds=r.get('lease_wait_seconds', 0))
    if not helper:
        q['native_setup_return'] = r['raw_setup_return']
    (RUN / 'VERIFIED.JSN').write_bytes((json.dumps(q, indent=2) + '\r\n').encode('ascii'))
    print(json.dumps(q, indent=2))
    return q


if __name__ == '__main__':
    verify('--helper' in sys.argv)
