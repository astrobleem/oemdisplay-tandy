"""Stage a private four-saver candidate from the current fixed-default packet.

Does not qualify, publish, or change historical accepted package identities.
Use matching current native sources, not the older HPDIB source snapshot.
"""
import argparse
import hashlib
from pathlib import Path
import re
import shutil
import zipfile
import zlib

BASE_SHA = '35266732e122068d03c44c98a610621d65c06c38c29b8ca3d1d0513a94d30fca'
RUNTIME = ('TSHELL.EXE', 'TSINPUT.DLL', 'CUBE.EXE', 'ORBITS.EXE')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def write(path, data):
    path.write_bytes(data.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def members(path):
    require(hashlib.sha256(path.read_bytes()).hexdigest() == BASE_SHA,
            'Different current fixed-default baseline')
    with zipfile.ZipFile(path) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), 'Duplicate ZIP member')
        return {n: archive.read(n) for n in archive.namelist()}


def pinrow(name, data):
    return '{"%s","%s",%dUL,0,0x%08xUL}' % (
        name, hashlib.sha256(data).hexdigest(), len(data), zlib.crc32(data))


def aliases(native, payload):
    pins = (native / 'SETPINS.H').read_text()
    files = (native / 'SETFILES.H').read_text()
    crcs = (native / 'SETINPUT.H').read_text()
    # These three parallel inventories must remain in exactly the same order.
    before = len(re.findall(r'^\{"', files, re.M))
    files = ''.join(line for line in files.splitlines(True) if '"MAZE.EXE"' not in line)
    pins = ''.join(line for line in pins.splitlines(True) if '"MAZE.EXE"' not in line)
    crcs = ''.join(line for line in crcs.splitlines(True) if 'MAZE.EXE' not in line)
    for name, data in payload.items():
        pattern = r'\{"' + re.escape(name) + r'","[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL\}'
        if re.search(pattern, pins):
            pins, count = re.subn(pattern, lambda m: pinrow(name, data), pins)
            require(count == 1, 'Duplicate pin: ' + name)
            files, count = re.subn(r'(,"' + re.escape(name) + r'",)\d+UL(,0\})',
                                  lambda m: m[1] + str(len(data)) + 'UL' + m[2], files)
            require(count == (1 if name == 'APPS.TXT' else 2), 'Missing parallel aliases: ' + name)
        else:
            require(name in ('CUBE.EXE', 'ORBITS.EXE'), 'Missing existing pin: ' + name)
            pins = pins.replace('};', pinrow(name, data) + ',\n};')
            for prefix in ('WINXT\\\\FILES\\\\', 'WINXT\\\\'):
                dest = prefix + name
                files = files.replace('};\n#define NFILES',
                                      '{"%s","%s",%dUL,0},\n};\n#define NFILES' % (dest, name, len(data)))
                crcs = crcs.replace('};', ' 0x00000000UL, /* ' + dest + ' */\n};')
    after = len(re.findall(r'^\{"', files, re.M))
    setup = (native / 'SETUP.C').read_text()
    for macro in ('FRESH_COUNT', 'UPDATE_COUNT'):
        setup, count = re.subn(r'(#define ' + macro + r' )(\d+)',
                              lambda m: m[1] + str(int(m[2]) + after - before), setup)
        require(count == 1, 'Missing preparation count: ' + macro)
    for name, data in [('SETPINS.H', pins), ('SETFILES.H', files), ('SETINPUT.H', crcs), ('SETUP.C', setup)]:
        write(native / name, data)


def stage(base, native, runtime, out):
    body = members(base)
    require(not out.exists(), 'Fresh output required')
    # Verify that the native source staging is for this actual released packet.
    pins = (native / 'SETPINS.H').read_text()
    for name in ('FIXXT.EXE', 'TSHELL.EXE', 'TSINPUT.DLL'):
        require(pinrow(name, body['WINXT/' + name]) in pins, 'Native source does not match current packet: ' + name)
    out.mkdir(parents=True)
    staged = out / 'native'
    staged.mkdir()
    for source in native.iterdir():
        if source.suffix.upper() in ('.C', '.H', '.ASM'):
            shutil.copyfile(source, staged / source.name)
    payload = {name: (runtime / name).read_bytes() for name in RUNTIME}
    for name, data in payload.items():
        require(data[:2] == b'MZ', 'Not a native executable: ' + name)
    ini = body['WINXT/TSHELL.INI'].decode('ascii')
    require('IdleSeconds=300' in ini, 'Unexpected idle preference')
    ini = ini.replace('MazeProgram=C:\\WINXT\\MAZE.EXE',
                      'CubeProgram=C:\\WINXT\\CUBE.EXE\r\nOvalsProgram=C:\\WINXT\\ORBITS.EXE')
    ini = ini.replace('Name2=Maze', 'Name2=Cube').replace('Command2=C:\\WINXT\\MAZE.EXE',
                      'Command2=C:\\WINXT\\CUBE.EXE /S')
    ini = ini.replace('Count=9', 'Count=10')
    ini += 'Name10=Ovals\r\nCommand10=C:\\WINXT\\ORBITS.EXE /S\r\n'
    payload['TSHELL.INI'] = ini.encode('ascii')
    payload['APPS.TXT'] = body['WINXT/APPS.TXT'].replace(
        b'Maze, Starfield, Matrix, Pinball and About',
        b'Cube, Starfield, Matrix, Ovals, Pinball and About')
    text = (staged / 'FIXXT.C').read_text()
    patterns = (r'(static const char \*names\[\]=\{)(.*?)(\};)',
                r'(static unsigned long sizes\[\]=\{)(.*?)(\};)',
                r'(static int target\[\]=\{)(.*?)(\};)')
    matches = [re.search(pattern, text) for pattern in patterns]
    require(all(matches), 'Finisher copy inventory missing')
    names = re.findall(r'"([A-Z0-9.]+)"', matches[0][2])
    sizes, targets = [m[2].split(',') for m in matches[1:]]
    require(len(names) == len(sizes) == len(targets), 'Finisher arrays disagree')
    require('MAZE.EXE' in names and 'CUBE.EXE' not in names and 'ORBITS.EXE' not in names, 'Unexpected saver baseline')
    i = names.index('MAZE.EXE')
    names[i] = 'CUBE.EXE'
    sizes[i] = str(len(payload['CUBE.EXE'])) + 'UL'
    names.append('ORBITS.EXE'); sizes.append(str(len(payload['ORBITS.EXE'])) + 'UL'); targets.append('2')
    for name in ('TSHELL.EXE', 'TSINPUT.DLL', 'TSHELL.INI'):
        sizes[names.index(name)] = str(len(payload[name])) + 'UL'
    values = (','.join('"' + name + '"' for name in names), ','.join(sizes), ','.join(targets))
    for pattern, value in zip(patterns, values):
        text = re.sub(pattern, lambda m: m[1] + value + m[3], text)
    text, count = re.subn(r'#define COUNT \d+', '#define COUNT ' + str(len(names)), text)
    require(count == 1, 'Finisher COUNT missing')
    write(staged / 'FIXXT.C', text)
    aliases(staged, payload)
    for name, data in payload.items():
        body['WINXT/' + name] = data
    del body['WINXT/MAZE.EXE']
    expanded = out / 'expanded'
    for name, data in body.items():
        dest = expanded / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    print('Staged candidate. Compile native/FIXXT.C; run bind, compile native/SETUP.C, then pack. Native qualification remains required.')


def bind(out):
    native = out / 'native'
    payload = {'FIXXT.EXE': (native / 'FIXXT.EXE').read_bytes()}
    # Include edited consumer text in Setup integrity checks too.
    for name in ('TSHELL.INI', 'APPS.TXT'):
        payload[name] = (out / 'expanded/WINXT' / name).read_bytes()
    # FIXXT checks TSHELL.INI length independently.
    text = (native / 'FIXXT.C').read_text()
    names = re.findall(r'"([A-Z0-9.]+)"', re.search(r'static const char \*names\[\]=\{(.*?)\};', text)[1])
    sizes = re.search(r'static unsigned long sizes\[\]=\{(.*?)\};', text)[1].split(',')
    require(sizes[names.index('TSHELL.INI')] == str(len(payload['TSHELL.INI'])) + 'UL',
            'Update FIXXT TSHELL.INI size and rebuild FIXXT before bind')
    aliases(native, payload)
    (out / 'expanded/WINXT/FIXXT.EXE').write_bytes(payload['FIXXT.EXE'])
    print('Setup pins bound. Compile native/SETUP.C next.')


def pack(out):
    native = out / 'native'
    root = out / 'expanded'
    (root / 'SETUP.EXE').write_bytes((native / 'SETUP.EXE').read_bytes())
    pins = (native / 'SETPINS.H').read_text()
    names = re.findall(r'^\{"([^"]+)","[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL\}', pins, re.M)
    require(names and len(names) == len(set(names)) and
            len(names) == len(re.findall(r'^\{"', pins, re.M)),
            'Missing, malformed or duplicate candidate pins')
    # Check every supplied component, including CPSET and optional display modes.
    for name in names:
        require(pinrow(name, (root / 'WINXT' / name).read_bytes()) in pins, 'Candidate pin differs: ' + name)
    require(not (root / 'WINXT/MAZE.EXE').exists(), 'Maze remains in packet')
    for name in ('TSHELL.INI', 'APPS.TXT'):
        require(b'MAZE' not in (root / 'WINXT' / name).read_bytes().upper(), 'Maze remains in ' + name)
    archive = out / 'WINXT.ZIP'
    require(not archive.exists(), 'Candidate archive already exists')
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_STORED) as zipped:
        for path in sorted(root.rglob('*')):
            if path.is_file():
                entry = zipfile.ZipInfo(path.relative_to(root).as_posix(), (1980, 1, 1, 0, 0, 0))
                entry.create_system = 0
                entry.external_attr = 32
                zipped.writestr(entry, path.read_bytes())
    print('Candidate packet ready for native FRESH, UPDATE and installed saver qualification: ' + str(archive))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('stage', 'bind', 'pack'))
    parser.add_argument('--out', required=True, type=Path)
    for name in ('base', 'native', 'runtime'):
        parser.add_argument('--' + name, type=Path, default=Path(__file__).resolve().parent / 'BASE' if name == 'native' else None)
    args = parser.parse_args()
    if args.phase == 'stage':
        require(all((args.base, args.native, args.runtime)), 'stage requires --base, --native, --runtime')
        stage(args.base, args.native, args.runtime, args.out)
    elif args.phase == 'bind':
        bind(args.out)
    else:
        pack(args.out)


if __name__ == '__main__':
    main()
