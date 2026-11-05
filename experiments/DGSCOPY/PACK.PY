'''Make separate opt-in fixed-driver development packets, never current products.

Includes only the explicitly qualified driver, closed support and installation
instructions. No manifests, checksums or standalone test documents are emitted.
'''
from pathlib import Path
import argparse
import hashlib
import io
import zipfile

SUPPORT = {'CGA.GR2': '1fc24254a1b76c2030a0ae60e25a17d6df4730c2a99d293ca22886059d8be067',
 'FONTLIC.TXT': 'b7b5b82f34c6a21e5f680e983af2dc628b9bd913363a7ffc6087cd1486201c80',
 'LOGOLIC.TXT': 'b7b5b82f34c6a21e5f680e983af2dc628b9bd913363a7ffc6087cd1486201c80',
 'WXTSPL01.RLE': 'eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c',
 'XTCFIX.FON': '3c02c48996d3f8bc9d5a1825bfee966ca4da97ed3e8331472dc78cbe2a63a971',
 'XTCOEM.FON': '8fc600059c0246a1b43c1af47bef17a34df844b3ae21369ce53b9ecc8ccc3055',
 'XTCSYS.FON': 'c45b5d313109fe0b5fa6e665344accd5fa9de4a5ef35c0f416fe8ca1d83c1326',
 'XTEFIX.FON': '3c7ac7c82a987d75445f6e3c9e2a9afa650689a20cab573b8f661a37287b142c',
 'XTEOEM.FON': '8fc600059c0246a1b43c1af47bef17a34df844b3ae21369ce53b9ecc8ccc3055',
 'XTESYS.FON': '50af47922fb4df487ecfbfb77a744dbdc315f521365b8fd089a71b6c5c6c6946',
 'XTSTATIC.LGO': '995d71e3626de64c8fe21bc1f037e0dece0853d4f0d09082bf607b2d237b37ef'}
PROFILES = {
    'colorplus32016': ('CP3216', 'CP3216.DRV', 'ColorPlus 320x200x16 DEVELOPMENT',
                      'XTE', '133,96,72', '543fe058f9a150477009170ae583d50d3d321665ad1c832af45c8b0d14c1f962'),
    'yamaha160-b800': ('YMB800', 'YMB800.DRV', 'Yamaha B800 160x200x16 EMULATOR ONLY',
                       'XTC', '200,96,48', 'c309326e4213e85cd6347697f3a73e785b0c1644eedd3860af63f36affddf62c'),
}


def dos(text):
    return text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii')


def descriptor(profile):
    folder, driver, label, fonts, metrics, _ = PROFILES[profile]
    return dos(f'''[data]
Version = "3.0"
[disks]
a = C:\\{folder}, "{label}", OEMSETUP.INF
[display]
{driver[:-4]} = a:{driver}, "{label}", "{metrics}", a:CGA.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE
[sysfonts]
a:{fonts}SYS.FON, "XT Pixels System", "{metrics}"
[fixedfonts]
a:{fonts}FIX.FON, "XT Pixels Fixed", "{metrics}"
[oemfonts]
a:{fonts}OEM.FON, "XT Pixels Terminal", "{metrics}", 1
''')


def install(profile):
    folder, driver, *_ = PROFILES[profile]
    return dos(f'''ECHO OFF
IF NOT EXIST C:\\WINDOWS\\WIN.COM GOTO NOWIN
IF NOT EXIST C:\\{folder}\\CGA.GR2 GOTO NOPACK
IF NOT EXIST C:\\{folder}\\{driver} GOTO NOPACK
COPY /B C:\\{folder}\\CGA.GR2 C:\\WINDOWS\\SYSTEM\\CGA.GR2 > NUL
IF ERRORLEVEL 1 GOTO FAILED
COPY /B C:\\{folder}\\{driver} C:\\WINDOWS\\SYSTEM\\{driver} > NUL
IF ERRORLEVEL 1 GOTO FAILED
C:
CD \\WINDOWS
SETUP
GOTO END
:NOWIN
ECHO Windows 3.0 must already be installed in C:\\WINDOWS.
GOTO END
:NOPACK
ECHO Extract the complete development packet to C:\\{folder}.
GOTO END
:FAILED
ECHO File staging failed. Setup was not started.
:END
''')


def instructions(profile):
    folder, driver, label, *_ = PROFILES[profile]
    limits = ('Fixed 320x200x16 only. No ColorPlus panning driver is included.'
              if profile == 'colorplus32016' else
              'B800 Yamaha V6355D fixture only. Not the Olivetti PC1/B000 profile.\n'
              'Physical scanout remains unqualified.')
    fixture = 'Plantronics ColorPlus' if profile == 'colorplus32016' else 'Yamaha V6355D B800'
    return dos(f'''{label}

Separate experimental development packet. Existing accepted packets are unchanged.
Requires DOS and an installed Windows 3.0 real-mode system in C:\\WINDOWS.
No operating system media, ROMs, emulator or compiler is included.
{limits}

1. Exit Windows to DOS. Extract the complete packet to C:\\ so that its
   files are in C:\\{folder}. Keep all supplied files together.
2. Run C:\\{folder}\\INSTALL. It stages the supplied grabber and driver,
   checks copy failures, and opens Windows Setup.
3. In Setup select Display, then Other, and enter C:\\{folder}.
   Select "{label}" and accept the new display settings.
   If offered CONFIG.SYS changes, choose "Setup can make NO changes for you."
4. After Setup returns to DOS, run C:\\{folder}\\START. This uses WIN /R.

To roll back, exit Windows and use DOS Windows Setup to select the previous
accepted display packet. Do not install this packet over CPPAN or YAMAHA.

Qualification: Windows 3.0 real-mode Setup selection and WIN /R startup passed
on the matched IBM XT 8088, 4.77 MHz, 640 KB {fixture} emulator fixture.
The installed driver and selected support bytes matched exactly, and all three
native RLE frames matched the qualified baseline. Baseline/candidate ellipse
accuracy frames also matched. Physical hardware remains unqualified. This is a
development packet, not an accepted release or a complete OS installation kit.
''')


def notice():
    return dos('''FIXED DISPLAY DEVELOPMENT PACKETS - COMPONENT NOTICES

These development drivers adapt Microsoft Windows DDK renderer code/resources.
Existing Microsoft Corporation notices remain applicable. This packet does not
grant a new or blanket license for third-party renderer or resource inputs.
The included CGA.GR2 was supplied by the repository owner; its existing
component notices remain applicable.

The XT Pixels fonts and XTSTATIC.LGO/WXTSPL01.RLE startup assets are original
first-party work under the included FONTLIC.TXT and LOGOLIC.TXT notices.

DOS and Windows are supplied by the user. No operating-system installation
media, ROM, compiler, SDK, emulator or unrelated prepared guest is included.
''')


def members(profile, driver, support):
    folder, name, _, font, _, digest = PROFILES[profile]
    data = Path(driver).read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('Driver differs from the matched qualified candidate')
    files = {name: data}
    names = ['CGA.GR2', 'XTSTATIC.LGO', 'WXTSPL01.RLE', 'FONTLIC.TXT', 'LOGOLIC.TXT']
    names += [font+suffix+'.FON' for suffix in ['SYS', 'FIX', 'OEM']]
    for item in names:
        content = (Path(support)/item).read_bytes()
        if hashlib.sha256(content).hexdigest() != SUPPORT[item]:
            raise ValueError('Support differs from accepted bytes: '+item)
        files[item] = content
    files.update({'OEMSETUP.INF': descriptor(profile), 'INSTALL.BAT': install(profile),
                  'START.BAT': dos('ECHO OFF\nC:\nCD \\WINDOWS\nWIN /R\n'),
                  'README.TXT': instructions(profile), 'NOTICE.TXT': notice()})
    return files


def archive(profile, files):
    stream = io.BytesIO()
    folder = PROFILES[profile][0]
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(files.items()):
            info = zipfile.ZipInfo(folder+'/'+name, (1980, 1, 1, 0, 0, 0))
            info.create_system = 0
            info.external_attr = 0x20
            z.writestr(info, data)
    return stream.getvalue()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', choices=PROFILES, required=True)
    p.add_argument('--driver', type=Path, required=True)
    p.add_argument('--support', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    a = p.parse_args()
    files = members(a.profile, a.driver, a.support)
    packed = archive(a.profile, files)
    with zipfile.ZipFile(io.BytesIO(packed)) as z:
        assert len(z.namelist()) == len(files) and z.testzip() is None
        assert all(z.read(PROFILES[a.profile][0]+'/'+n) == b for n,b in files.items())
    a.out.mkdir(parents=True, exist_ok=False)
    folder = a.out/PROFILES[a.profile][0]
    folder.mkdir()
    for name, data in files.items():
        (folder/name).write_bytes(data)
    filename = PROFILES[a.profile][0]+'.ZIP'
    (a.out/filename).write_bytes(packed)
    print(a.profile+': development packet '+str(a.out/filename)+'; matched emulator Setup/startup qualified, development only')


if __name__ == '__main__':
    main()
