"""Read-only source/runtime and recorded native closure for the app packets."""
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile
import importlib.util
from importlib.machinery import SourceFileLoader

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
loader=SourceFileLoader('app_packet_builder',str(HERE/'PACK.PY'))
spec=importlib.util.spec_from_loader(loader.name,loader)
pack=importlib.util.module_from_spec(spec);loader.exec_module(pack)
report=json.loads((HERE/'BUILD.JSN').read_bytes())
for name,pin in report['sources'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==pin,name
for setup,record in report['files'].items():
    exe=(HERE/'BIN'/(setup+'.EXE')).read_bytes()
    archive=(HERE/'BIN'/(setup+'.ZIP')).read_bytes()
    for data,key in [(exe,'exe'),(archive,'zip')]:
        assert len(data)==record[key]['bytes'] and pack.digest(data)==record[key]['sha256'],setup
    last,pages=struct.unpack_from('<HH',exe,2)
    size=pages*512-(512-last if last else 0)
    assert exe[size:]==archive,setup+' overlay'
    with zipfile.ZipFile(io.BytesIO(archive)) as z:
        assert z.testzip() is None
        assert set(z.namelist())==set(record['payload'])
        assert all(i.compress_type==0 for i in z.infolist())
        assert not any('/' in n or '\\' in n or n.endswith('.PY') for n in z.namelist())
        for name,pin in record['payload'].items():
            data=z.read(name)
            assert len(data)==pin['bytes'] and pack.digest(data)==pin['sha256'],name
        guide=z.read('INSTALL.TXT').decode('ascii')
        assert 'Run' in guide or 'run' in guide
        assert 'COPY ' not in guide and 'sound.drv=' not in guide and 'display.drv=' not in guide
        if setup=='MINESET':
            assert pack.imports(z.read('MINERUN.EXE'))==report['MINERUN_imports']
            for name,pin in pack.PINS.items():assert pack.digest(z.read(name))==pin
        else:assert pack.digest(z.read('COOKIE.EXE'))==pack.COOKIE_PIN
status,receipt=pack.native_receipt(report['files'])
assert status.startswith('PASS:'),status
assert report['native_windows_test']==status and report['native_receipt']==receipt
print('PASS: source/packet closure and exact native-qualified app bytes; '+status)
