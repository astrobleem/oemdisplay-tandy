"""Build all 31 native modules and resources for either fixed profile.

Uses canonical 8086 staging on an explicit external DDK/C6 view. No retained
project object is copied into the build. Normal builds use the external repo
for both native toolchain mounts and require an explicit qualified driver.
An optional historical reference adds object/resource/linkage checks; retained
objects never become build inputs. Equality does not establish qualification.
"""
from pathlib import Path
import argparse
import fcntl
import os
import re
import runpy
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TOOLS = ROOT/'src/tandysw'
shared = runpy.run_path(str(HERE/'BUILD.PY'))
NAMES = {'colorplus32016': ('N32016', 'CPLS/N32016'),
         'yamaha160-b800': ('N16016', 'YAMAHA/N16016')}
BACKEND = 'BITBLT CBLT POLYLINE SCANLINE OUTPUT PIXEL SCANLR RLSTRBLT RLBLDSTR REALFIX REALPRO DITHERS COLORINF ENUM COLORS SETMODE CHKSTK CHARWDTH FB LODITHER BMC_ETI BMC_ITE BMC_MAIN SDIB88 RLE88'.split()


def check_resources(profile, built, legacy, qualified, pack):
    if legacy is None:
        if profile not in NAMES:
            raise RuntimeError('Unknown resource profile')
        def indexed(records, pad):
            result = {}
            for typ, ident, flags, payload in records:
                key = (typ, ident)
                if key in result:
                    raise RuntimeError('Duplicate resource record: '+str(key))
                result[key] = (flags, payload+bytes((-len(payload)) % 16) if pad else payload)
            return result
        fresh = indexed(pack['read_res'](built), True)
        expected = indexed(pack['inspect_ne'](qualified), False)
        if set(fresh) != set(expected):
            raise RuntimeError('Fresh resource inventory differs from selected driver')
        for key in fresh:
            if fresh[key] != expected[key]:
                raise RuntimeError('Fresh padded resource payload/flags differ from selected driver: '+str(key))
        return
    if profile == 'colorplus32016':
        if built != legacy:
            raise RuntimeError('Fresh ColorPlus resources differ from original reference resources')
        return
    if profile != 'yamaha160-b800':
        raise RuntimeError('Unknown resource profile')
    current = pack['read_res'](built)
    original = pack['read_res'](legacy)
    cursor_types = (1, 12)
    if ([record for record in current if record[0] not in cursor_types] !=
            [record for record in original if record[0] not in cursor_types]):
        raise RuntimeError('Yamaha noncursor resource records changed')

    def indexed(records):
        result = {}
        for typ, ident, flags, payload in records:
            key = (typ, ident)
            if key in result:
                raise RuntimeError('Duplicate resource record: '+str(key))
            result[key] = (flags, payload)
        return result

    fresh = indexed(current)
    prior = indexed(original)
    expected = indexed(pack['inspect_ne'](qualified))
    if set(fresh) != set(prior) or set(fresh) != set(expected):
        raise RuntimeError('Yamaha resource inventory differs from reference')
    for key, (flags, payload) in fresh.items():
        if key[0] in cursor_types:
            # PACKRES attaches NE resources at 16-byte granularity. Compare all
            # stored bytes, including zero padding, rather than trimming data.
            padded = payload+bytes((-len(payload)) % 16)
            if (flags, padded) != expected[key]:
                raise RuntimeError('Yamaha cursor payload/flags differ from selected driver: '+str(key))


def prepare(repo, out, profile):
    view = out/'VIEW'
    view.mkdir()
    for name in ['BIN', 'DDK', 'LIB', 'INCLUDE']:
        (view/name).symlink_to(repo/name, target_is_directory=True)
    (view/'src').symlink_to(ROOT/'src', target_is_directory=True)
    base = runpy.run_path(str(TOOLS/'build.py'))
    renderer, resources = base['prepare'](view, out)
    for name, args in [('PORT8086.PY', (renderer, view)),
                       ('PORTDIB.PY', (renderer, view)),
                       ('MODEPROF.PY', (renderer, resources, view, '320x200x16')),
                       ('REPCOPY88.PY', (renderer, '320x200x16')),
                       ('BYTECOL.PY', (renderer, '320x200x16')),
                       ('CURKEEP.PY', (renderer, '320x200x16')),
                       ('OUTROWS.PY', (renderer, '320x200x16')),
                       ('WIDESCAN.PY', (renderer, '320x200x16'))]:
        module = runpy.run_path(str(TOOLS/name))
        module['port'](*args, **({'combined': True} if name == 'CURKEEP.PY' else {}))
    # The shared raster backend is identical for both fixed adapters; the exact
    # profile wrappers below own hardware, geometry, cursor and shadow binding.
    folder = HERE/NAMES[profile][0]
    for name in ['TSOFT.ASM', 'TCURSOR.ASM']:
        shutil.copyfile(folder/name, renderer/'EGA'/name)
    code = out/'CODE'
    code.mkdir()
    for name in ['GENDRAW.C', 'GENDECO.C']:
        shutil.copyfile(folder/name, code/name)
    shutil.copyfile(HERE/'DGFAR.ASM', code/'DGFAR.ASM')
    for name in ['GENDRAW.H', 'GENDECO.H', 'GENTRY.H', 'GENFAR.H', 'GENSPAN.H']:
        shutil.copyfile(HERE/name, code/name)
    pen = out/'PEN16'
    pen.mkdir()
    for name in ['ROBJECT.ASM', 'DISPLAY.INC']:
        shutil.copyfile(HERE/'PEN16'/name, pen/name)
    objects = out/'OBJECTS'
    objects.mkdir()
    for name in ['TSOFT.LNK', 'TSOFT.DEF']:
        shutil.copyfile(folder/name, objects/name)
    if profile == 'yamaha160-b800':
        runpy.run_path(str(HERE/'YAMCUR.PY'))['stage'](resources)
    resources.rename(out/'RES')
    return renderer, out/'RES', code, objects, base


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--profile', choices=NAMES, required=True)
    p.add_argument('--repo', type=Path, required=True)
    p.add_argument('--reference', type=Path, help='Optional read-only historical object/resource/linkage closure')
    p.add_argument('--qualified-driver', type=Path,
                   help='Required without --reference: read-only published driver for all-resource and exact final-byte comparison. With --reference, defaults to MATCHED candidate. Does not establish qualification.')
    p.add_argument('--dosbox', type=Path, required=True)
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--lease', type=Path, required=True)
    a = p.parse_args()
    repo, out = a.repo.resolve(), a.out.resolve()
    reference = a.reference.resolve() if a.reference is not None else None
    if out == HERE or HERE in out.parents:
        p.error('Use a fresh output outside source')
    if reference is None and a.qualified_driver is None:
        p.error('--qualified-driver is required without --reference')
    target = reference/'MATCHED'/NAMES[a.profile][1]/'CAND' if reference is not None else None
    toolchain = reference/'TOOLCHAIN' if reference is not None else repo
    qualified = (a.qualified_driver if a.qualified_driver is not None else target/'TSOFT.DRV').resolve()
    for name in ('BIN', 'DDK', 'LIB', 'INCLUDE'):
        if not (repo/name).is_dir():
            p.error('Missing external repo directory: '+str(repo/name))
    for root, names in ((toolchain, ('BIN/MASM.EXE', 'BIN/LINK4.EXE', 'LIB/LIBW.LIB', 'LIB/SDLLCEW.LIB')),
                        (repo, ('BIN/CL.EXE', 'BIN/C1.EXE', 'BIN/C2.EXE', 'BIN/C3.EXE',
                                'BIN/MASM.EXE', 'BIN/LINK.EXE', 'DDK/TOOLS/EXE2BIN.EXE'))):
        for name in names:
            if not (root/name).is_file():
                p.error('Missing external tool input: '+str(root/name))
    if qualified == out or out in qualified.parents:
        p.error('The read-only driver reference must be outside the fresh output')
    try:
        qualified_bytes = qualified.read_bytes()
    except OSError as error:
        p.error('Cannot read driver reference: '+str(error))
    out.mkdir(parents=True, exist_ok=False)
    renderer, resources, code, objects, base = prepare(repo, out, a.profile)
    commands = ['@echo off', 'PATH E:\\BIN;C:\\BIN',
                'SET INCLUDE=D:\\renderer\\INC;C:\\DDK\\286\\INC;D:\\renderer;D:\\renderer\\EGA',
                'CD \\renderer\\EGA', 'ECHO Fresh source modules > D:\\MODULES.LOG']
    for name in BACKEND+['TSOFT', 'TCURSOR']:
        source = name if name in ['TSOFT', 'TCURSOR'] else '..\\'+('DITHER' if name == 'LODITHER' else name)
        extra = ' -DLORES' if name == 'LODITHER' else ''
        commands += ['C:\\BIN\\MASM -LA -I. -I.. -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T'+extra+' '+source+'.ASM,D:\\OBJECTS\\'+name+'.OBJ,D:\\OBJECTS\\'+name+'.LST; >> D:\\MODULES.LOG', 'IF ERRORLEVEL1 GOTO FAIL']
    commands += ['CD \\PEN16', 'C:\\BIN\\MASM -LA -I. -ID:\\renderer -DMASMFLAGS=04001h -D?QUIET -ML -W2 -T ROBJECT.ASM,D:\\OBJECTS\\ROBJECT.OBJ,D:\\OBJECTS\\ROBJECT.LST; >> D:\\MODULES.LOG', 'IF ERRORLEVEL1 GOTO FAIL',
                 'CD \\CODE', 'C:\\BIN\\MASM -LA -ML DGFAR.ASM,D:\\OBJECTS\\DGFAR.OBJ,D:\\OBJECTS\\DGFAR.LST; >> D:\\MODULES.LOG', 'IF ERRORLEVEL1 GOTO FAIL', 'SET INCLUDE=D:\\CODE;E:\\INCLUDE',
                 'E:\\BIN\\CL /nologo /c /G0 /Gw /AS /Aw /Gs /W3 /Od /Fa GENDRAW.C GENDECO.C > D:\\C6.LOG',
                 'IF ERRORLEVEL1 GOTO FAIL', 'ECHO MODULES_OK > D:\\MREADY.TXT', 'GOTO END', ':FAIL', 'ECHO MODULES_FAILED > D:\\MREADY.TXT', ':END']
    with a.lease.open('r+') as lease:
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        if not lease.read().strip():
            raise RuntimeError('Existing coordinator lease marker is empty; do not recreate it')
        try:
            shared['native'](out, toolchain, repo, a.dosbox.resolve(), '\n'.join(commands).replace('ERRORLEVEL1', 'ERRORLEVEL 1'), 'MODULES')
            if (out/'MREADY.TXT').read_text().strip() != 'MODULES_OK':
                raise RuntimeError('Fresh source compilation failed; inspect retained MODULES.LOG/C6.LOG')
            for name, target_name in [('GENDRAW', 'DGSCDRW'), ('GENDECO', 'DGSCDEC')]:
                result = shared['fix']((code/(name+'.OBJ')).read_bytes())
                if target is not None:
                    expected = {x.name.upper(): x for x in target.iterdir()}[target_name+'.OBJ'].read_bytes()
                    if result != expected:
                        raise RuntimeError('Fresh native C object differs from qualified input: '+target_name)
                (objects/(target_name+'.OBJ')).write_bytes(result)
            listings = list(objects.glob('*.LST'))
            if len(listings) != 29 or len(list(objects.glob('*.OBJ'))) != 31:
                raise RuntimeError('Expected 29 assembly listings and 31 freshly built objects')
            for path in listings:
                if not re.search(r'(?im)^\s*0\s+Severe\s+Errors', path.read_text(errors='replace')):
                    raise RuntimeError('Unconfirmed assembler result: '+path.name)
            isa = runpy.run_path(str(TOOLS/'AUDIT88.PY'))['audit'](listings)
            rep = runpy.run_path(str(TOOLS/'REPCOPY88.PY'))['audit_listings'](listings)
            print('8086 listing gates passed: '+str(isa['emitted_instruction_rows_checked'])+' rows; no unsupported opcodes or multi-prefix REP', flush=True)
            body = ['@echo off', 'SET LIB=C:\\LIB', 'CD \\OBJECTS',
                    'C:\\BIN\\LINK4 @TSOFT.LNK > LINK.LOG', 'IF ERRORLEVEL1 GOTO FAIL',
                    'CD \\RES', 'ECHO Source resources > RES.LOG']
            for name in ['CONFIG', 'FONTS', 'COLORTAB']:
                body += ['E:\\BIN\\MASM /T '+name+','+name+','+name+'; >> RES.LOG', 'IF ERRORLEVEL1 GOTO FAIL',
                         'E:\\BIN\\LINK '+name+','+name+'; >> RES.LOG', 'IF ERRORLEVEL1 GOTO FAIL',
                         'E:\\DDK\\TOOLS\\EXE2BIN.EXE '+name+'.EXE '+name+'.BIN >> RES.LOG', 'IF ERRORLEVEL1 GOTO FAIL']
            body += ['ECHO LINK_OK > D:\\LREADY.TXT', 'GOTO END', ':FAIL', 'ECHO LINK_FAILED > D:\\LREADY.TXT', ':END']
            shared['native'](out, toolchain, repo, a.dosbox.resolve(), '\n'.join(body).replace('ERRORLEVEL1', 'ERRORLEVEL 1'), 'LINKRES')
            if (out/'LREADY.TXT').read_text().strip() != 'LINK_OK':
                raise RuntimeError('Fresh link/resource build failed; inspect retained logs')
        finally:
            fcntl.flock(lease, fcntl.LOCK_UN)
            print('Shared lease released', flush=True)
    old = os.environ.get('TANDY_REPO')
    os.environ['TANDY_REPO'] = str(out/'VIEW')
    try:
        pack = runpy.run_path(str(resources/'PACKRES.PY'))
        resource_bytes = pack['write_res'](pack['resource_records']())
    finally:
        if old is None:
            os.environ.pop('TANDY_REPO', None)
        else:
            os.environ['TANDY_REPO'] = old
    legacy_resources = ((reference/'MATCHED'/NAMES[a.profile][1].split('/')[0]/'TANDY.RES').read_bytes()
                        if reference is not None else None)
    check_resources(a.profile, resource_bytes, legacy_resources, qualified_bytes, pack)
    (out/'TANDY.RES').write_bytes(resource_bytes)
    result, _ = pack['attach_ne']((objects/'TSOFT.DRV').read_bytes(), pack['read_res'](resource_bytes))
    (out/'TSOFT.DRV').write_bytes(result)
    if reference is not None:
        subprocess.run([sys.executable, str(reference/'MATCHED/BMCFIX/audit_linked_driver.py'),
                        '--base', str(out/'TSOFT.DRV'), '--control', str(qualified),
                        '--map', str(objects/'TSOFT.MAP'), '--output', os.devnull, '--require-ready'], check=True)
    if qualified.read_bytes() != qualified_bytes:
        raise RuntimeError('Read-only driver reference changed during the build')
    if result != qualified_bytes:
        raise RuntimeError('Complete source build differs from selected driver reference; no promotion')
    print(a.profile+': all 31 native modules and resources rebuilt from source; selected driver reference reproduced byte-for-byte')


if __name__ == '__main__':
    main()
