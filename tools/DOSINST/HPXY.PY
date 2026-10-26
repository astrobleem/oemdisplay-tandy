"""Exact current HPXY build and bounded normal-package acceptance bindings."""
from pathlib import Path
import hashlib
import io
import json
import re
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUAL = ROOT / 'docs/QUAL/HPXY'
CHANGED = {'SETUP.EXE', 'README.TXT', 'WINXT/HPXY.DRV',
           'WINXT/FIXXT.EXE', 'WINXT/DISPLAY.BAT', 'WINXT/DISPLAY.TXT'}


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def runtime():
    q = json.loads((HERE / 'HPXY.JSN').read_bytes())
    require(q['status'] == 'PASS_FOCUSED_WINDOWS_EMULATOR' and
            q['physical_hardware'] is False, 'HPXY runtime unqualified')
    for name, pin in q['sources'].items():
        require(identity((ROOT / name).read_bytes()) == pin,
                'HPXY source differs: ' + name)
    for name, pin in q['evidence'].items():
        require(identity((ROOT / name).read_bytes()) == pin,
                'HPXY evidence differs: ' + name)
    build = json.loads((QUAL / 'BUILD.JSN').read_bytes())
    require(build['build'] == 'PASS' and build['stage_bytes'] == 2816 and
            build['gross_NE_bytes'] == 126883 and
            build['delta_from_R3_gross_bytes'] <= build['ceiling_delta'],
            'HPXY project allocation budget differs')
    data = (HERE / 'BIN/HPXY.DRV').read_bytes()
    require(identity(data) == q['driver'] and
            hashlib.sha256(data).hexdigest() == build['sha256'],
            'HPXY runtime bytes differ')
    header = (HERE / 'HPXYID.H').read_text('ascii')
    require(re.search(r'#define HPXY_BYTES ' + str(len(data)) + r'UL', header)
            and re.search(r'#define HPXY_CRC 0x%08xUL' % zlib.crc32(data), header),
            'HPXY finisher identity differs')
    return data


def qualify(entries, archive, inherited, expanded):
    runtime()
    q = json.loads((QUAL / 'PACKAGE.JSN').read_bytes())
    require(q['status'] == 'PASS_CANONICAL_HPXY_PACKAGE' and
            q['physical_hardware'] is False, 'HPXY package incomplete')
    require(q['inherited_package'] == identity(
        (ROOT / 'docs/QUAL/WDESK/PACKAGE.JSN').read_bytes()) and
        inherited['status'] == 'PASS_NATIVE_PACKAGE' and
        inherited['physical_qualification'] is False,
        'Inherited package receipt differs')
    require(inherited['baseline_expanded'] == identity(
        (ROOT / 'docs/QUAL/DOSINST/EXPAND.JSN').read_bytes()) and
        expanded['status'] == 'PASS_EXPANDED_NATIVE' and
        expanded['physical_test'] is False, 'Expanded baseline differs')
    for receipt, prefix in ((expanded, 'docs/QUAL/DOSINST/'),
                            (inherited, '')):
        for name, pin in receipt['evidence'].items():
            require(identity((ROOT / (prefix + name)).read_bytes()) == pin,
                    'Inherited raw evidence differs: ' + name)
    for name, row in inherited['native'].items():
        require(row['complete'] and row['owned_stopped'] and
                row['lease_released'] and not row.get('error') and
                row['archive'] == inherited['archive'],
                'Inherited native case incomplete: ' + name)
    files = {n: identity(b) for n, b in sorted(entries.items())}
    require(q['archive'] == identity(archive) and q['files'] == files,
            'HPXY package differs from native input')
    require(set(files) == set(inherited['files']) and
            {n for n in files if files[n] != inherited['files'][n]} == CHANGED,
            'Unexpected canonical package changes')
    require(q['driver'] == identity(entries['WINXT/HPXY.DRV']) and
            entries['WINXT/HPXY.DRV'] == runtime(),
            'Different HPXY packaged')
    require(set(q['native']) == {'drivers_only', 'update', 'fresh'},
            'Canonical native cases incomplete')
    for name, row in q['native'].items():
        require(row['complete'] and row['owned_stopped'] and
                row['lease_released'] and not row.get('error') and
                row['archive'] == q['archive'],
                'Canonical native case incomplete: ' + name)
    require(q['native']['drivers_only']['installed_driver'] == q['driver'] and
            q['native']['drivers_only']['paintbrush_repaint_and_pan'] and
            q['native']['drivers_only']['normal_dos_return'],
            'Canonical installed Windows acceptance missing')
    helper = q['native']['drivers_only']['helper_check']
    require(helper['complete'] and not helper.get('error') and helper['owned_stopped'] and helper['lease_released']
            and helper['installed_helper_steps_verified'] and helper['normal_dos_return']
            and helper['archive'] == q['archive'] and helper['installed_driver'] == q['driver'],
            'Installed XYCTL step acceptance missing')
    for name, count in (('fresh', 370), ('update', 83)):
        require(q['native'][name]['tested_inputs'] ==
                {n: files[n] for n in ('SETUP.EXE', 'WINXT/FIXXT.EXE', 'WINXT/HPXY.DRV')},
                'Different canonical native inputs: ' + name)
        require(q['native'][name]['prepared_comparison'] ==
                {'count': count, 'different': []},
                'Canonical prepared bytes differ: ' + name)
    update = q['native']['update']
    require(update['full_finisher_complete'] and
            update['installed_driver'] == q['driver'] and
            update['installed_helper'] == files['WINXT/XYCTL.EXE'],
            'Canonical full finisher/install verification missing')
    for name, pin in q['sources'].items():
        require(identity((ROOT / name).read_bytes()) == pin,
                'Canonical source differs: ' + name)
    require(set(q['evidence']) == {'docs/QUAL/HPXY/INSTALL.ZIP'},
            'Canonical evidence inventory differs')
    for name, pin in q['evidence'].items():
        data = (ROOT / name).read_bytes()
        require(identity(data) == pin, 'Canonical evidence differs: ' + name)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(z.testzip() is None and
                    len(z.namelist()) == len(set(z.namelist())) and
                    json.loads(z.read('RESULT.JSN')) == q['native'],
                    'Canonical raw result differs')
    return q
