"""Prepare a review-only font integration overlay from a qualified baseline.

Does not create an installable disk, replace accepted binaries, or publish.
The revised PREPXT must be compiled and tested after native font acceptance.
"""
import argparse
import ast
import difflib
import hashlib
import json
import re
from pathlib import Path
from BUILD import textfile
from TEST import validate_fon

HERE = Path(__file__).resolve().parent
FONTS = ('CGASYS.FON', 'CGAFIX.FON', 'CGAOEM.FON', 'EGASYS.FON',
         'EGAFIX.FON', 'EGAOEM.FON', 'TXTSYS.FON')
OWNED = ('CGA.GR2', 'CGALOGO.LGO')


def sha(b):
    return hashlib.sha256(b).hexdigest()


def replace(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Baseline changed: expected one occurrence: ' + old[:80])
    return text.replace(old, new)


def remove_function(text, name):
    # Supported C89 functions have braces on their own lines; refuse drift.
    pattern = r'static [^\n]+\b' + name + r'\([^\n]*\)\n\{.*?\n\}\n'
    updated, count = re.subn(pattern, '', text, flags=re.S)
    if count != 1:
        raise ValueError('Cannot isolate baseline function: ' + name)
    return updated


def main(args):
    baseline, qualified = args.baseline.resolve(), args.qualified.resolve()
    fonts, out = args.fonts.resolve(), args.out.resolve()
    if out.exists():
        raise ValueError('Output exists; choose a fresh review directory')
    runtime = baseline / 'distributions/WINXT'
    flash = baseline / 'tools/FLASHDISK'
    qualified_build = json.loads((qualified / 'BUILD.JSON').read_text())
    manifest_raw = (runtime / 'MANIFEST.SHA').read_bytes()
    if sha(manifest_raw) != qualified_build['runtime_manifest_sha256']:
        raise ValueError('Baseline runtime is not the specified qualified package')
    if sha((flash / 'PREPXT.EXE').read_bytes()) != qualified_build['helper_sha256']:
        raise ValueError('Baseline PREPXT differs from qualified package')
    # Verify source/binary coupling using its existing exact helper manifest.
    for line in (flash / 'HELPER.SHA').read_text().splitlines():
        digest, name = line.split()
        if sha((flash / name).read_bytes()) != digest:
            raise ValueError('Baseline helper source/binary mismatch: ' + name)
    manifest = {n: h for h, n in (l.split() for l in manifest_raw.decode().splitlines())}
    info = {}
    for name, digest in manifest.items():
        if name not in OWNED + FONTS:
            b = (runtime / name).read_bytes()
            if sha(b) != digest:
                raise ValueError('Baseline public payload changed: ' + name)
            info[name] = {'sha256': digest, 'size': len(b), 'kind': 0}
    contracts = json.loads((HERE / 'CONTRACT.JSON').read_text())
    for item in contracts:
        validate_fon((fonts / item['filename']).read_bytes(), item)
    overlay = {}
    for name in FONTS:
        b = (fonts / name).read_bytes()
        overlay['distributions/WINXT/' + name] = b
        info[name] = {'sha256': sha(b), 'size': len(b), 'kind': 0}
    for name in OWNED:
        # Numeric pins only; no private support bytes are read/copied here.
        sizes = {'CGA.GR2': 2104, 'CGALOGO.LGO': 880}
        info[name] = {'sha256': manifest[name], 'size': sizes[name], 'kind': 1}
    overlay['distributions/WINXT/FONTLIC.TXT'] = (HERE / 'LICENSE').read_bytes()
    note = ('XT PIXELS - ORIGINAL WINDOWS XT BITMAP FONTS\n'
            'Development candidate: native Windows 3.0 qualification pending.\n'
            'Seven first-party FONs replace the six private fonts and derived\n'
            'TXTSYS. MIT license: FONTLIC.TXT. Sources: tools/XTFONTS.\n'
            'Original ASCII, Latin-1, early Windows ANSI and CP437 drawings.\n'
            'Reserved ANSI 7F,80,81,8D,8E,8F,90,9D,9E use visible fallback.\n'
            'No emoji. OEM 00/FF remain outside the font and default to space.\n'
            'System/fixed metrics and all character advances are preserved.\n'
            'No Python is needed on the vintage computer. CGA.GR2 and\n'
            'CGALOGO.LGO, Windows and other non-font dependencies remain.\n')
    overlay['distributions/WINXT/FONTINFO.TXT'] = note.replace('\n', '\r\n').encode('ascii')
    for name in ('FONTLIC.TXT', 'FONTINFO.TXT'):
        b = overlay['distributions/WINXT/' + name]
        info[name] = {'sha256': sha(b), 'size': len(b), 'kind': 0}
    # Remove the old private-font redistribution paragraph; retain other text.
    readme = (runtime / 'README.TXT').read_text('ascii')
    readme = replace(readme,
        'This complete package contains your licensed Microsoft fonts, grabber and\n'
        'logo loader, plus privately derived TXTSYS.FON. Do not mirror or redistribute\n'
        'those support files publicly. Public source staging requires your own media.\n',
        'XT Pixels fonts are original MIT-licensed files; see FONTLIC.TXT and\n'
        'FONTINFO.TXT. Windows fonts and locally derived TXTSYS are no longer\n'
        'source-media dependencies. CGA.GR2 and CGALOGO.LGO still require your\n'
        'own matching Windows media and must not be redistributed publicly.\n')
    overlay['distributions/WINXT/README.TXT'] = readme.replace('\n', '\r\n').encode('ascii')
    b = overlay['distributions/WINXT/README.TXT']
    info['README.TXT'] = {'sha256': sha(b), 'size': len(b), 'kind': 0}
    newmanifest = ''.join(info[n]['sha256'] + '  ' + n + '\r\n' for n in sorted(info)).encode('ascii')
    overlay['distributions/WINXT/MANIFEST.SHA'] = newmanifest
    info['MANIFEST.SHA'] = {'sha256': sha(newmanifest), 'size': len(newmanifest), 'kind': 0}
    pins = ('/* Review-only XT Pixels integration; zero SHA default retained. */\n'
            'static struct pin pins[]={\n')
    pins += ''.join(' {"%s","%s",%dUL,%d},\n' % (n, p['sha256'], p['size'], p['kind'])
                    for n, p in sorted(info.items())) + '};\n'
    overlay['tools/FLASHDISK/XTPINS.H'] = pins.replace('\n', '\r\n').encode('ascii')
    prep = (flash / 'PREPXT.C').read_text('ascii')
    prep = replace(prep, '/* kind: 0 public runtime, 1 user-owned support, 2 locally derived font. */',
                   '/* kind: 0 public runtime (including XT Pixels), 1 owned non-font support. */')
    prep = replace(prep, 'work[MAXFONT], derived[MAXFONT], ring[4096]', 'work[MAXFONT], ring[4096]')
    # These helpers were used only by the mandatory private-font transplant.
    for name in ('font_layout', 'derive_font'):
        prep = remove_function(prep, name)
    prep = replace(prep, 'static unsigned wordat(const unsigned char *b,unsigned p)\n'
                   '{ return (unsigned)b[p]|((unsigned)b[p+1]<<8); }\n'
                   'static U32 longat(const unsigned char *b,unsigned p)\n'
                   '{ return (U32)wordat(b,p)|((U32)wordat(b,p+2)<<16); }\n', '')
    prep = replace(prep, ' if(strstr(name,".FON")){font_layout(b,n,!strcmp(name,"CGASYS.FON")?1:!strcmp(name,"CGAFIX.FON")?2:0,name);return;}\n', '')
    prep = replace(prep, ' else if(pins[k].kind==2){hashmem(derived,(unsigned)pins[k].size,pins[k].hex,pins[k].name);createout(to);putbytes(derived,(unsigned)pins[k].size,to);closeout(to);}\n', '')
    prep = replace(prep, 'pins[k].kind==1?work:derived', 'work')
    prep = replace(prep, ' derive_font();\n', '')
    prep = replace(prep, 'Checking source sizes and required Windows font versions before output.',
                   'Checking runtime sizes and owned non-font support before output.')
    if 'derived' in prep or 'font_layout' in prep or 'derive_font' in prep:
        raise ValueError('Private font path remains')
    # Assert the existing no-SHA default is carried forward into this overlay.
    if 'all SHA verification OFF.' not in prep or 'if(deep_verify)' not in prep:
        raise ValueError('Qualified zero-SHA default missing')
    overlay['tools/FLASHDISK/PREPXT.C'] = prep.replace('\n', '\r\n').encode('ascii')
    stage = (runtime / 'STAGE.PY').read_text('ascii')
    stage = re.sub(r'^SUPPORT_HASHES = .*$', 'SUPPORT_HASHES = ' + repr({n: manifest[n] for n in OWNED}), stage, flags=re.M)
    stage = re.sub(r'^DERIVED_HASH=.*\n', '', stage, flags=re.M)
    stage = re.sub(r'\ndef resources\(data\):.*?\ndef verify_default_splash', '\ndef digest(b):return hashlib.sha256(b).hexdigest()\n\ndef verify_default_splash', stage, flags=re.S)
    stage = replace(stage, " data['TXTSYS.FON']=textfont(data)\n", '')
    stage = stage.replace('eight original Windows 3.0 support files', 'two original non-font Windows 3.0 support files')
    stage = stage.replace('Fixed-cell font\nresource transplant follows experiments/TEXTMODE/FIXFONT.PY; no font bytes\nare embedded or redistributed here.', 'XT Pixels fonts are public first-party payloads; only the non-font grabber\nand logo loader require owned media. No Python is needed on the DOS target.')
    overlay['distributions/WINXT/STAGE.PY'] = stage.replace('\n', '\r\n').encode('ascii')
    make = (flash / 'MAKEIMG.PY').read_text('ascii')
    additions = ', '.join(repr(n) for n in FONTS + ('FONTLIC.TXT', 'FONTINFO.TXT'))
    make = replace(make, "PUBLIC_NAMES = (", 'PUBLIC_NAMES = (' + additions + ', ')
    make = replace(make, "WINDOWS_NAMES = ('CGA.GR2', 'CGALOGO.LGO', 'CGAFIX.FON', 'CGAOEM.FON',\n    'CGASYS.FON', 'EGAFIX.FON', 'EGAOEM.FON', 'EGASYS.FON', 'TXTSYS.FON')",
                   "WINDOWS_NAMES = ('CGA.GR2', 'CGALOGO.LGO')")
    make = replace(make, "expected_kind = '2' if name == 'TXTSYS.FON' else ('1' if name in WINDOWS_NAMES else '0')",
                   "expected_kind = '1' if name in WINDOWS_NAMES else '0'")
    make = replace(make, 'if len(rows) != 3 or', 'if len(rows) != 11 or')
    make = make.replace('derives\n   the text font locally, expands three pinned packed drivers',
                        'expands\n   seven original fonts, three pinned packed drivers and the shell')
    overlay['tools/FLASHDISK/MAKEIMG.PY'] = make.replace('\n', '\r\n').encode('ascii')
    # Use the qualified deterministic compressor unchanged for font transport.
    # Its implementation is original repository code, not a font artwork source.
    import importlib.machinery
    packer = importlib.machinery.SourceFileLoader('xt_font_packer', str(flash / 'SZPACK.PY')).load_module()
    unpacker = importlib.machinery.SourceFileLoader('xt_font_unpacker', str(runtime / 'STAGE.PY')).load_module()
    packedrows = re.findall(r'\{"([A-Z0-9_.]+)","([A-Z0-9_.]+)","([a-f0-9]{64})",(\d+)UL\}',
                           (flash / 'PACKPINS.H').read_text())
    packed = {}
    for name in FONTS:
        raw = (fonts / name).read_bytes()
        b = packer.pack(raw)
        if unpacker.expanded_file(b, name) != raw:
            raise ValueError('Packed font round-trip failed: ' + name)
        packed[name] = {'stored_name': name[:-1] + '_', 'raw_bytes': len(raw),
                        'packed_bytes': len(b), 'sha256': sha(b)}
        packedrows.append((name, name[:-1] + '_', sha(b), str(len(b))))
    # Existing original streaming codec also packs the unchanged shell.
    # Its expanded accepted pin stays exact; this restores 720 KB headroom.
    shellraw = (runtime / 'TSHELL.EXE').read_bytes()
    shellpacked = packer.pack(shellraw)
    if unpacker.expanded_file(shellpacked, 'TSHELL.EXE') != shellraw:
        raise ValueError('Packed shell round-trip failed')
    packedrows.append(('TSHELL.EXE', 'TSHELL.EX_', sha(shellpacked), str(len(shellpacked))))
    packpins = ('/* Review-only transport pins; fonts need native acceptance. */\n'
                'static struct packed_pin packed_pins[]={\n')
    packpins += ''.join('{"%s","%s","%s",%sUL},\n' % row for row in packedrows)
    packpins += '};\n#define NPACKED (sizeof(packed_pins)/sizeof(packed_pins[0]))\n'
    overlay['tools/FLASHDISK/PACKPINS.H'] = packpins.replace('\n', '\r\n').encode('ascii')
    szpack = (flash / 'SZPACK.PY').read_text()
    szpack = re.sub(r'^PACKED_NAMES = .*$', 'PACKED_NAMES = ' + repr({n: s for n, s, h, z in packedrows}), szpack, flags=re.M)
    overlay['tools/FLASHDISK/SZPACK.PY'] = szpack.replace('\n', '\r\n').encode('ascii')
    for relative, b in overlay.items():
        if relative.endswith('.PY'):
            ast.parse(b.decode('ascii'))
    out.mkdir(parents=True)
    for relative, b in overlay.items():
        target = out / 'OVERLAY' / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b)
        original = baseline / relative
        if original.is_file() and relative.endswith(('.C', '.H', '.PY', '.TXT', '.SHA')):
            patch = ''.join(difflib.unified_diff(original.read_text('ascii').splitlines(True),
                b.decode('ascii').replace('\r\n', '\n').splitlines(True),
                fromfile='a/' + relative, tofile='b/' + relative))
            target = out / 'DIFF' / (relative + '.PATCH')
            target.parent.mkdir(parents=True, exist_ok=True)
            textfile(target, patch)
    cluster = qualified_build['fat_verification']['cluster_bytes']
    allocated = lambda n: (n + cluster - 1) // cluster * cluster
    rawcost = sum(allocated(p['raw_bytes']) for p in packed.values())
    packcost = sum(allocated(p['packed_bytes']) for p in packed.values())
    extras = sum(allocated(info[n]['size']) for n in ('FONTLIC.TXT', 'FONTINFO.TXT'))
    shellsaving = allocated(len(shellraw)) - allocated(len(shellpacked))
    report = {'kind': 'REVIEW ONLY; no rebuilt helper or installable image',
              'native_qualified': False, 'baseline_manifest_sha256': sha(manifest_raw),
              'baseline_helper_sha256': qualified_build['helper_sha256'],
              'first_party_fonts': list(FONTS), 'remaining_owned_support': list(OWNED),
              'zero_sha_default_preserved_in_source': True,
              'packed_fonts': packed,
              'unchanged_shell_transport': {'raw_bytes': len(shellraw),
                  'packed_bytes': len(shellpacked), 'expanded_sha256': sha(shellraw),
                  'packed_sha256': sha(shellpacked)},
              'fat_estimate': {
                  'cluster_bytes': cluster, 'baseline_free_bytes': qualified_build['fat_verification']['free_bytes'],
                  'raw_fonts_allocated': rawcost, 'packed_fonts_allocated': packcost,
                  'license_and_info_allocated': extras,
                  'additional_shell_packing_saves': shellsaving,
                  'remaining_before_changed_helper_and_metadata': qualified_build['fat_verification']['free_bytes'] - packcost - extras + shellsaving},
              'overlay_sha256': {r: sha(b) for r, b in overlay.items()},
              'next_gates': ['Native font loader/pixel/metrics/menu/dialog tests',
                            'Rebuild PREPXT with approved 8086 compiler; update HELPER.SHA',
                            'Update package readme/tests for first-party fonts and eleven transports',
                            'Setup/install/rollback and default-zero-SHA tests',
                            'Actual FAT12 image build and capacity verification']}
    textfile(out / 'REVIEW.JSON', json.dumps(report, indent=2) + '\n')
    textfile(out / 'README.TXT', 'REVIEW ONLY - DO NOT INSTALL\n\n'
             'Native Windows 3.0 loading is not qualified. No PREPXT.EXE,\n'
             'HELPER.SHA, IMG, ZIP installer or installable candidate is emitted.\n'
             'OVERLAY shows the proposed source/pin/font changes on the exact\n'
             'qualified zero-SHA baseline. Apply only in a fresh isolated source\n'
             'workspace after native font qualification; read REVIEW.JSON gates.\n')
    print(json.dumps(report['fat_estimate'], indent=2))
    print('REVIEW ONLY:', out)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for option in ('baseline', 'qualified', 'fonts', 'out'):
        parser.add_argument('--' + option, type=Path, required=True)
    main(parser.parse_args())
