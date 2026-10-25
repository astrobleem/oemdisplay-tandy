"""Build the complete PC1512 OEM packet and its existing native SFX carrier."""
import argparse
import hashlib
import importlib.machinery
import io
import json
from pathlib import Path
import shutil
import struct
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DRIVER = '2f9f59e29a7e472e17a39fa54bd138cdb5b3f4d9562690791fddb3b5f4a76998'
SUPPORT = ('CGA.GR2', 'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON',
           'XTSTATIC.LGO', 'WXTSPL01.RLE', 'FONTLIC.TXT', 'LOGOLIC.TXT')
TEXT = ('OEMSETUP.INF', 'INSTALL.BAT', 'P15WIN.BAT', 'INSTALL.TXT')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def dos(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii')


def payload(accepted):
    if accepted:
        with zipfile.ZipFile(accepted) as z:
            if set(z.namelist()) != {'LICENSE.TXT', 'NOTICE.TXT', 'PC1512.DRV',
                    'PINS.JSN', 'README.TXT', 'SHA256.SUM'} or len(z.namelist()) != 6:
                raise ValueError('Accepted PC1512 archive membership differs')
            files = {n:z.read(n) for n in ['PC1512.DRV','LICENSE.TXT','NOTICE.TXT']}
    else:
        source=HERE/'PAYLOAD'
        if {p.name for p in source.iterdir() if p.is_file()} != {'PC1512.DRV','LICENSE.TXT','NOTICE.TXT'}:
            raise ValueError('Accepted PC1512 payload membership differs')
        files={n:(source/n).read_bytes() for n in ['PC1512.DRV','LICENSE.TXT','NOTICE.TXT']}
    driver=files['PC1512.DRV']
    if len(driver) != 58368 or sha(driver) != DRIVER:
        raise ValueError('Accepted PC1512 driver differs')
    pins = json.loads((ROOT / 'tools/YAMPACK/SUPPORT.JSN').read_bytes())
    for name in SUPPORT:
        if name == 'CGA.GR2':
            media = importlib.machinery.SourceFileLoader('p15_media',
                  str(ROOT / 'tools/XR1PACK/PREPARE.PY')).load_module()
            data = media.expanded_file((ROOT / 'distributions/WINXT' / name).read_bytes(), name)
        else:
            data = (ROOT / 'distributions/WINXT' / name).read_bytes()
        if name in pins and {'bytes':len(data), 'sha256':sha(data)} != pins[name]:
            raise ValueError('PC1512 support input differs: ' + name)
        files[name] = data
    files['OWATCOM.TXT']=(ROOT/'tools/XR1PACK/OWATCOM.TXT').read_bytes()
    files.update({n:(HERE / n).read_bytes() for n in TEXT})
    verify(files)
    return files


def verify(files):
    expected = set(SUPPORT) | set(TEXT) | {'PC1512.DRV', 'LICENSE.TXT', 'NOTICE.TXT', 'OWATCOM.TXT'}
    if set(files) != expected or sha(files['PC1512.DRV']) != DRIVER:
        raise ValueError('PC1512 packet differs')
    for n in TEXT:
        b = files[n]
        if b != (HERE / n).read_bytes() or b'\n' in b.replace(b'\r\n', b''):
            raise ValueError('PC1512 text/source or CRLF differs: ' + n)
    inf = files['OEMSETUP.INF'].decode('ascii')
    for n in ('PC1512.DRV', 'CGA.GR2', 'XTCSYS.FON', 'XTCFIX.FON',
              'XTCOEM.FON', 'XTSTATIC.LGO', 'WXTSPL01.RLE'):
        if 'a:' + n not in inf:
            raise ValueError('PC1512 selector omits support: ' + n)
    if '"200,96,48"' not in inf or 'RESERVE.COM' in inf:
        raise ValueError('PC1512 metrics/hardware contract differs')


def build(accepted, appset, watcom, out):
    files = payload(accepted)
    engine = Path(appset).resolve()
    if b'#ifndef APP_READY' not in (engine / 'APPSET.C').read_bytes():
        raise ValueError('Qualified APPSET completion hook is required')
    shared = importlib.machinery.SourceFileLoader('p15_sfx_pack',
                    str(engine / 'PACK.PY')).load_module()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    work = out / 'native'; work.mkdir()
    shutil.copyfile(engine / 'APPSET.C', work / 'APPSET.C')
    ready = 'PC1512 files are ready. From plain DOS run %s\\INSTALL.\n'
    lines = ['#define APP_TITLE "PC1512 display"', '#define SETUP_NAME "P15SET"',
             '#define DEFAULT_DIR '+json.dumps(r'C:\P15EXP'), '#define RUN_NAME "INSTALL.BAT"',
             '#define APP_FIXED_TARGET 1',
             '#define APP_COLLISION "Required C:\\\\P15EXP contains a different file. Extraction stopped."',
             '#define APP_READY(target) printf(' + json.dumps(ready) + ',target)',
             'static struct entry files[]={']
    lines += [' {"%s",%dUL,0x%08xUL,0},' % (n,len(d),zlib.crc32(d))
              for n,d in sorted(files.items())]
    lines += ['};']
    (work / 'FILES.H').write_bytes(dos('\n'.join(lines) + '\n'))
    shared.run(watcom.resolve(), work, ['-zq','-bt=dos','-0','-ml','-os',
                                      '-fe=P15SET.EXE','APPSET.C'])
    stub = (work / 'P15SET.EXE').read_bytes()
    last,pages = struct.unpack_from('<HH',stub,2)
    if pages*512-(512-last if last else 0) != len(stub):
        raise ValueError('Unexpected DOS carrier overlay')
    archive = shared.zip_bytes(files)
    (out / 'P15SET.EXE').write_bytes(stub + archive)
    (out / 'PC1512.ZIP').write_bytes(archive)
    (out / 'INSTALL.TXT').write_bytes(files['INSTALL.TXT'])
    record = {'target':'PC1512 built-in video, Windows 3.0 real mode',
              'driver_unchanged':False, 'support_complete':True,
              'native_install_test':'PENDING: requires coordinated slot',
              'files':{n:{'bytes':len(d),'sha256':sha(d)} for n,d in sorted(files.items())},
              'sfx_engine_sha256':sha((engine / 'APPSET.C').read_bytes()),
              'outputs':{n:{'bytes':(out/n).stat().st_size,'sha256':sha((out/n).read_bytes())}
                         for n in ['P15SET.EXE','PC1512.ZIP','INSTALL.TXT']}}
    native=importlib.machinery.SourceFileLoader('p15_native_receipt',
                    str(ROOT/'tools/DRVSET/NATIVE.PY')).load_module()
    record['native_install_test'],record['native_receipt']=native.status('PC1512',record['outputs'],files)
    (out / 'BUILD.JSN').write_bytes(dos(json.dumps(record,indent=2)+'\n'))
    print(json.dumps(record['outputs'],indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--accepted',type=Path,help='Optional accepted historical input; default is the local pinned driver')
    p.add_argument('--appset',type=Path,default=ROOT/'tools/APPSET')
    p.add_argument('--watcom',type=Path,required=True)
    p.add_argument('--out',type=Path,required=True)
    a=p.parse_args(); build(a.accepted,a.appset,a.watcom,a.out)
