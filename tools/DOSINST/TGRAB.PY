"""Bind the Tandy clipboard integration to bounded normal-install evidence."""
from pathlib import Path
import hashlib
import importlib.machinery
import io
import json
import zipfile

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
QUAL = ROOT / 'docs/QUAL/TGRAB'
CHANGED = {'SETUP.EXE', 'README.TXT', 'WINXT/FIXXT.EXE',
           'WINXT/OEMSETUP.INF', 'WINXT/DISPLAY.BAT', 'WINXT/DISPWIN.BAT',
           'WINXT/DISPLAY.TXT'}
ADDED = {'WINXT/TANDYGR.GR2', 'WINXT/TGCLIP.EXE'}
SOURCES = {
    'tools/DOSINST/' + name for name in (
        'FIXXT.C', 'TGINT.H', 'TGID.H', 'XRPREP.C', 'SETUP.C',
        'SETPINS.H', 'SETFILES.H', 'SETINPUT.H', 'MAKESET.PY',
        'TGALIAS.PY', 'TGUPSET.H', 'TGSETID.H', 'RCPUB.PY',
        'TGRAB.PY', 'INSTALL.TXT')}
SOURCES.update('tools/XROEM/' + name for name in (
    'DISPLAY.BAT', 'DISPWIN.BAT', 'OEMSETUP.INF', 'DISPLAY.TXT'))
SOURCES.update('src/tgrab/' + name for name in (
    'TGTANDY.ASM', 'TGSRSCR.ASM', 'TGBMP.ASM', 'TGCLIP.C',
    'BUILDTG.PY', 'BUILDAPP.PY'))


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def qualify(entries, archive):
    hp = importlib.machinery.SourceFileLoader(
        'preserved_hpxy_grabber', str(HERE / 'HPXY.PY')).load_module()
    require(entries['WINXT/HPXY.DRV'] == hp.runtime(), 'HPXY runtime changed')
    baseline = json.loads((ROOT / 'docs/QUAL/HPXY/PACKAGE.JSN').read_bytes())
    q = json.loads((QUAL / 'PACKAGE.JSN').read_bytes())
    require(q['status'] == 'PASS_CANONICAL_TGRAB_PACKAGE' and
            q['physical_hardware'] is False, 'Grabber native acceptance incomplete')
    require(q['baseline'] == identity((ROOT / 'docs/QUAL/HPXY/PACKAGE.JSN').read_bytes()),
            'Grabber baseline receipt changed')
    files = {n: identity(b) for n, b in sorted(entries.items())}
    require(q['archive'] == identity(archive) and q['files'] == files,
            'Grabber package differs from tested bytes')
    require(set(files) - set(baseline['files']) == ADDED and
            not set(baseline['files']) - set(files) and
            {n for n in baseline['files'] if files[n] != baseline['files'][n]} == CHANGED,
            'Unexpected grabber package changes')
    require(set(q['sources']) == SOURCES, 'Grabber source inventory incomplete')
    for name, pin in q['sources'].items():
        require(identity((ROOT/name).read_bytes()) == pin, 'Grabber source changed: '+name)
    require(set(q['evidence']) == {'docs/QUAL/TGRAB/INSTALL.ZIP'},
            'Grabber raw evidence inventory incomplete')
    for name, pin in q['evidence'].items():
        data = (ROOT/name).read_bytes()
        require(identity(data) == pin, 'Grabber evidence changed: '+name)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            require(z.testzip() is None and
                    len(z.namelist()) == len(set(z.namelist())) and
                    json.loads(z.read('RESULT.JSN')) == q['native'],
                    'Grabber raw native result differs')
    for name in ('fresh', 'update', 'drivers_only', 'clipboard'):
        case = q['native'][name]
        require(case['complete'] and case['owned_stopped'] and case['lease_released']
                and not case.get('error') and case['archive'] == q['archive'],
                'Grabber native case incomplete: '+name)
    require(all(q['checks'].values()) and set(q['checks']) == {
        'text_clipboard', 'graphics_clipboard_paintbrush', 'display_switch_retains_support',
        'normal_dos_return', 'fresh_update_preparation', 'full_finisher'},
        'Grabber integration checks incomplete')
    return q
