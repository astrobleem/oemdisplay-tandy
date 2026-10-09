"""Pin reviewed own rebuilds into an unpublished isolated font candidate.

Does not alter the qualified baseline. Refuses warnings/missing completion.
Host-only: never required on the vintage computer.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from BUILD import textfile


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(args):
    candidate, build = args.candidate.resolve(), args.build.resolve()
    log = (build / 'BUILD.LOG').read_text('latin1')
    if 'SUCCESS' not in log or 'FAILED' in log or re.search(r'warning|error', log, re.I):
        raise ValueError('Native build incomplete or has diagnostics')
    runtime, flash = candidate / 'distributions/WINXT', candidate / 'tools/FLASHDISK'
    # Ground the review source overlay and the compiled inputs exactly.
    for name in ('PREPXT.C', 'XTPINS.H', 'PACKPINS.H', 'SZSTREAM.H'):
        if sha(flash / name) != sha(build / name):
            raise ValueError('Compile input differs from candidate: ' + name)
    if sha(candidate / 'src/tandysw/TINST.C') != sha(build / 'TINST.C'):
        raise ValueError('Installer compile input differs')
    for name in ('PREPXT.EXE', 'TINST.EXE'):
        data = (build / name).read_bytes()
        if data[:2] != b'MZ' or not 1000 < len(data) < 65536:
            raise ValueError('Invalid 8086 DOS executable: ' + name)
    shutil.copyfile(build / 'PREPXT.EXE', flash / 'PREPXT.EXE')
    shutil.copyfile(build / 'TINST.EXE', runtime / 'TINST.EXE')
    manifest = {name: digest for digest, name in (line.split() for line in
                (runtime / 'MANIFEST.SHA').read_text().splitlines())}
    for name in manifest:
        if name not in ('CGA.GR2', 'CGALOGO.LGO'):
            manifest[name] = sha(runtime / name)
    textfile(runtime / 'MANIFEST.SHA', ''.join(manifest[n] + '  ' + n + '\n' for n in sorted(manifest)))
    pins = (flash / 'XTPINS.H').read_text()
    rows = re.findall(r'\{"([A-Z0-9_.]+)","([a-f0-9]{64})",(\d+)UL,([01])\}', pins)
    if set(n for n, h, size, kind in rows) != set(manifest) | {'MANIFEST.SHA'}:
        raise ValueError('Candidate pin names drifted')
    updated = '/* Original font candidate; native rebuilt helper/installer pins. */\nstatic struct pin pins[]={\n'
    for name, digest, size, kind in rows:
        if kind == '0':
            path = runtime / name
            digest, size = sha(path), str(path.stat().st_size)
        updated += ' {"%s","%s",%sUL,%s},\n' % (name, digest, size, kind)
    updated += '};\n'
    # PREPXT embeds XTPINS.H. A TINST rebuild may change its pin. The helper
    # must then be recompiled against the new table, never patched in-place.
    if re.findall(r'\{"([A-Z0-9_.]+)","([a-f0-9]{64})",(\d+)UL,([01])\}', updated) != rows:
        textfile(flash / 'XTPINS.H', updated)
        textfile(candidate / 'RECOMPILE.TXT', 'TINST or manifest pin changed. Recompile PREPXT against updated XTPINS.H before final helper pinning.\n')
        print('RECOMPILE PREPXT: table changed; final HELPER.SHA withheld')
        return
    names = ('PREPXT.EXE', 'PREPXT.C', 'XTPINS.H', 'BUILD.BAT', 'SZSTREAM.H', 'PACKPINS.H', 'SZPACK.PY')
    textfile(flash / 'HELPER.SHA', ''.join(sha(flash / n) + '  ' + n + '\n' for n in sorted(names)))
    textfile(candidate / 'REBUILD.JSON', json.dumps({'kind': 'Unpublished own rebuilt font candidate',
        'native_package_qualified': False, 'publication_allowed': False,
        'helper_sha256': sha(flash / 'PREPXT.EXE'), 'installer_sha256': sha(runtime / 'TINST.EXE'),
        'runtime_manifest_sha256': sha(runtime / 'MANIFEST.SHA')}, indent=2) + '\n')
    print('PINNED: unpublished helper/installer candidate; native package gate remains')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--build', type=Path, required=True)
    main(p.parse_args())
