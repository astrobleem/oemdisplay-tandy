"""Build Yamaha packets with historical validation and a qualified B800 overlay."""
import argparse
import hashlib
import importlib.machinery
import io
import json
from pathlib import Path
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MEDIA = importlib.machinery.SourceFileLoader('yam_media', str(ROOT / 'tools/XR1PACK/PREPARE.PY')).load_module()
PROFILES = {
    'pc1': ('PC1YAMA.DRV', 'EXPERIMENTAL Olivetti PC1 160x200x16', 'PC1.ZIP',
            'PC1-B000-CANDIDATE03.ZIP', '8c73d52d6811fff071dd252343c33702a1cfea0b2613ec8b20faf5a739da2a08', 54992),
    'b800': ('YAM160.DRV', 'EXPERIMENTAL Yamaha B800 EMULATOR ONLY', 'YAMAHA.ZIP',
             'YAMAHA-B800-CANDIDATE03.ZIP', 'a3d339a3f1e831bd8499fb2b0a28c683bf08f9fbeb0e96689dc3f6ef9a627c8a', 55008),
}
SUPPORT = {'CGA.GR2', 'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON', 'XTSTATIC.LGO', 'WXTSPL01.RLE'}
LICENSES = {'FONTLIC.TXT', 'LOGOLIC.TXT'}
STAMP = (1980, 1, 1, 0, 0, 0)
B800_PAYLOAD = HERE / 'PAYLOAD/YAM160.DRV'

def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}

def dos(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii')

def pins():
    return json.loads((HERE / 'SUPPORT.JSN').read_bytes())

def exact(data, expected, name):
    if identity(data) != expected:
        raise ValueError('Accepted bytes differ: ' + name)
    return data

def native_binding():
    verifier = importlib.machinery.SourceFileLoader(
        'yam_native_verify', str(ROOT / 'experiments/DGSCOPY/VERIFY.PY')).load_module()
    return verifier.verify_profile('yamaha160-b800')

def driver_pin(profile):
    if profile == 'pc1':
        return {'bytes': PROFILES[profile][5], 'sha256': PROFILES[profile][4]}
    pin = native_binding()['driver']
    if (set(pin) != {'bytes', 'sha256'} or type(pin['bytes']) is not int
            or not 0 < pin['bytes'] <= 1048576 or not isinstance(pin['sha256'], str)
            or len(pin['sha256']) != 64 or any(c not in '0123456789abcdef' for c in pin['sha256'])):
        raise ValueError('Invalid qualified B800 driver identity')
    return pin

def qualified_b800():
    pin = driver_pin('b800')
    if B800_PAYLOAD.stat().st_size > 1048576:
        raise ValueError('Qualified B800 overlay exceeds 1 MiB')
    return exact(B800_PAYLOAD.read_bytes(), pin, 'qualified B800 overlay')

def selector(profile):
    driver, label, *_ = PROFILES[profile]
    return dos(f'''[data]
Version = "3.0"
[disks]
a = C:\\YAMAHA, "{label}", OEMSETUP.INF
[display]
{driver[:-4]} = a:{driver}, "{label}", "200,96,48", a:CGA.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE
[sysfonts]
a:XTCSYS.FON, "XT Pixels CGA System", "200,96,48"
[fixedfonts]
a:XTCFIX.FON, "XT Pixels CGA Fixed", "200,96,48"
[oemfonts]
a:XTCOEM.FON, "XT Pixels CGA Terminal", "200,96,48", 1
''')

def archive(files):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(name, STAMP)
            info.create_system = 0
            info.external_attr = 0x20
            z.writestr(info, data)
    return stream.getvalue()

def read_archive(data, names):
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        if len(z.namelist()) != len(names) or set(z.namelist()) != names:
            raise ValueError('Unexpected or duplicate packet members')
        if any(i.file_size > 1048576 for i in z.infolist()) or z.testzip() is not None:
            raise ValueError('Oversized or corrupt packet member')
        return {n: z.read(n) for n in names}

def checksum(files):
    return dos(''.join(hashlib.sha256(data).hexdigest() + '  ' + name + '\n'
                       for name, data in sorted(files.items())))

def metadata(profile):
    return {'OEMSETUP.INF': selector(profile), 'README.TXT': (HERE / (profile.upper() + '.TXT')).read_bytes(),
            'NOTICE.TXT': (HERE / 'NOTICE.TXT').read_bytes()}

def historical_files(profile, accepted=None, grabber=None):
    # Preserve candidate03 archive membership, historical driver and support checks.
    driver, label, filename, oldname, digest, size = PROFILES[profile]
    source = Path(accepted) if accepted else ROOT / 'downloads/experimental/yamaha-candidate03' / oldname
    if source.stat().st_size > 1048576:
        raise ValueError('Accepted archive exceeds 1 MiB')
    old = read_archive(source.read_bytes(), {driver, 'OEMSETUP.INF', 'README.TXT', 'MANIFEST.JSN',
        'SHA256SUMS.TXT', 'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON', 'WXTSPL01.RLE'} | LICENSES)
    files = {driver: exact(old[driver], {'bytes': size, 'sha256': digest}, driver)}
    for name, pin in pins().items():
        if name == 'CGA.GR2':
            path = Path(grabber) if grabber else ROOT / "distributions/WINXT" / name
            if path.stat().st_size > 1048576:
                raise ValueError('Grabber input exceeds 1 MiB')
            data = MEDIA.expanded_file(path.read_bytes(), name)
        else:
            data = (ROOT / 'distributions/WINXT' / name).read_bytes()
        files[name] = exact(data, pin, name)
    files.update(metadata(profile))
    return files

def packet_bytes(profile, files):
    driver, label, *_ = PROFILES[profile]
    files = dict(files)
    record = {'schema': 1, 'profile': profile, 'driver': driver, 'selector': label,
              'files': {n: identity(b) for n, b in sorted(files.items())},
              'external_support_inputs': [], 'native_test': 'not asserted by host packaging'}
    files['MANIFEST.JSN'] = dos(json.dumps(record, indent=2, sort_keys=True) + '\n')
    files['SHA256.SUM'] = checksum(files)
    return archive(files)

def build(profile, output, accepted=None, grabber=None):
    out = Path(output)
    if out.exists():
        raise ValueError('Output must be new')
    driver, label, filename, *_ = PROFILES[profile]
    files = historical_files(profile, accepted, grabber)
    # The optimized input never substitutes for validation of the historical base.
    if profile == 'b800':
        files[driver] = qualified_b800()
    packed = packet_bytes(profile, files)
    verify(profile, packed)
    with zipfile.ZipFile(io.BytesIO(packed)) as z:
        files = {name: z.read(name) for name in z.namelist()}
    out.mkdir(parents=True)
    for name, data in files.items():
        (out / name).write_bytes(data)
    (out / filename).write_bytes(packed)
    return {'profile': profile, 'packet': filename, **identity(packed), 'external_support_inputs': []}

def verify(profile, data):
    driver, label, *_ = PROFILES[profile]
    names = SUPPORT | LICENSES | {driver, 'OEMSETUP.INF', 'README.TXT', 'NOTICE.TXT', 'MANIFEST.JSN', 'SHA256.SUM'}
    files = read_archive(data, names)
    if data != archive(files):
        raise ValueError('Noncanonical packet metadata')
    exact(files[driver], driver_pin(profile), driver)
    for name, pin in pins().items():
        exact(files[name], pin, name)
    for name, expected in metadata(profile).items():
        if files[name] != expected:
            raise ValueError('Current source differs: ' + name)
    record = json.loads(files['MANIFEST.JSN'])
    expected = {'schema': 1, 'profile': profile, 'driver': driver, 'selector': label,
                'files': {n: identity(b) for n, b in sorted(files.items()) if n not in {'MANIFEST.JSN', 'SHA256.SUM'}},
                'external_support_inputs': [], 'native_test': 'not asserted by host packaging'}
    if record != expected or files['SHA256.SUM'] != checksum({n: b for n, b in files.items() if n != 'SHA256.SUM'}):
        raise ValueError('Packet record or checksum differs')
    return record

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', choices=PROFILES, required=True)
    p.add_argument('--out', type=Path)
    p.add_argument('--accepted', type=Path)
    p.add_argument('--grabber', type=Path)
    p.add_argument('--verify', type=Path)
    a = p.parse_args()
    if a.verify:
        verify(a.profile, a.verify.read_bytes())
        print('PASS_HOST_PACKET ' + a.profile)
    elif a.out:
        print(json.dumps(build(a.profile, a.out, a.accepted, a.grabber), indent=2))
    else:
        p.error('use --out or --verify')
