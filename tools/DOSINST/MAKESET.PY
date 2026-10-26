"""Generate expanded input aliases and the portable OEM metadata output."""
from pathlib import Path
import hashlib
import importlib.machinery
import zlib
HERE = Path(__file__).resolve().parent

def generate():
    pins = (HERE / "XR1PINS.H").read_bytes()
    files = (HERE / "XRFILES.H").read_bytes()
    crcs = (HERE / "XRINPUT.H").read_bytes()
    ordinary = (HERE.parent / "XROEM/OEMSETUP.INF").read_bytes()
    assert pins.count(b'"OEMSETUP.INF"') == 1
    assert files.count(b'{"WINXT\\\\OEMSETUP.INF","OEMSETUP.INF",882UL,0}') == 1
    pins = pins.replace(b'"OEMSETUP.INF"', b'"HPXY.INF"')
    row = ('{"OEMSETUP.INF","%s",%dUL,0,0x%08xUL},\r\n' %
           (hashlib.sha256(ordinary).hexdigest(),len(ordinary),zlib.crc32(ordinary))).encode()
    assert pins.count(b'};') == 1
    pins = pins.replace(b'};',row+b'};')
    files = files.replace(b'{"WINXT\\\\OEMSETUP.INF","OEMSETUP.INF",882UL,0}',
                          b'{"WINXT\\\\HPXY.INF","HPXY.INF",882UL,0}')
    row = ('{"WINXT\\\\OEMSETUP.INF","OEMSETUP.INF",%dUL,0},\r\n' % len(ordinary)).encode()
    assert files.count(b'};\r\n#define NFILES') == 1
    files = files.replace(b'};\r\n#define NFILES',row+b'};\r\n#define NFILES')
    crcs = crcs.replace(b'/* WINXT\\\\OEMSETUP.INF */', b'/* WINXT\\\\HPXY.INF */')
    assert crcs.count(b'};') == 1
    crcs = crcs.replace(b'};',b'0x00000000UL, /* WINXT\\\\OEMSETUP.INF */\r\n};')
    panui = importlib.machinery.SourceFileLoader(
        "current_panui_aliases", str(HERE / "PANUI.PY")).load_module()
    pins, files = panui.aliases(pins, files)
    grab = importlib.machinery.SourceFileLoader(
        "current_grabber_aliases", str(HERE / "TGALIAS.PY")).load_module()
    pins, files, crcs = grab.aliases(pins, files, crcs)
    return {"SETPINS.H":pins,"SETFILES.H":files,"SETINPUT.H":crcs}

if __name__ == "__main__":
    for name,data in generate().items():
        (HERE/name).write_bytes(data)
