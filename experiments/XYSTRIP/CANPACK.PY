"""Seal exact canonical normal-package native evidence after successful runs."""
from pathlib import Path
import hashlib
import json
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT.parent / 'tandy-pan-integration'
QUAL = ROOT / 'docs/QUAL/HPXY'
INSTALL = sys.argv[1] if len(sys.argv) > 1 else 'canonical-install-02'


def identity(b):
    return dict(bytes=len(b), sha256=hashlib.sha256(b).hexdigest())


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').replace('\n', '\r\n').encode('ascii')


def main():
    archive = (OUT / 'CANONICAL.ZIP').read_bytes()
    with zipfile.ZipFile(OUT / 'CANONICAL.ZIP') as z:
        assert z.testzip() is None
        entries = {n: z.read(n) for n in z.namelist()}
    native = {'drivers_only': json.loads((OUT / INSTALL / 'VERIFIED.JSN').read_bytes())}
    native['drivers_only']['helper_check'] = json.loads((OUT / 'canonical-helper-01/VERIFIED.JSN').read_bytes())
    for case in ('fresh', 'update'):
        row = json.loads((OUT / ('canonical-' + case) / 'RESULT.JSN').read_bytes())
        assert row['archive'] == identity(archive)
        for name, pin in row['tested_inputs'].items():
            assert pin == identity(entries[name])
        native[case] = row
    assert all(x['complete'] and x['owned_stopped'] and x['lease_released'] for x in native.values())
    assert native['drivers_only']['archive'] == identity(archive)
    with zipfile.ZipFile(QUAL / 'INSTALL.ZIP', 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr('RESULT.JSN', encoded(native))
        for case in ('fresh', 'update'):
            folder = OUT / ('canonical-' + case)
            for leaf in ('RESULT.JSN', 'PROCESS.JSON', 'RUN.BAT', 'RUN.CNF'):
                z.writestr(case + '/' + leaf, (folder / leaf).read_bytes())
            for leaf in ('PREP.LOG', 'FINISH.LOG', 'ACCEPT.OK'):
                p = folder / 'CROOT' / leaf
                if p.is_file():
                    z.writestr(case + '/' + leaf, p.read_bytes())
        folder = OUT / INSTALL
        for p in sorted(folder.iterdir()):
            if p.suffix == '.BIN' or p.name in ('NATIVE.PY', 'RESULT.JSON', 'VERIFIED.JSN',
                    'PREPARE.JSON', 'APPQA.LOG', 'SYSTEM-BEFORE.INI', 'SYSTEM-AFTER.INI',
                    'PAINTBRUSH.PNG', 'RETURNED.PNG', 'REFRESH.PNG'):
                z.writestr('drivers/' + p.name, p.read_bytes())
        for p in sorted((OUT / 'canonical-helper-01').iterdir()):
            if p.suffix == '.BIN' or p.name in ('NATIVE.PY', 'RESULT.JSON', 'VERIFIED.JSN',
                    'PREPARE.JSON', 'APPQA.LOG', 'PAINTBRUSH.PNG', 'RETURNED.PNG'):
                z.writestr('helper/' + p.name, p.read_bytes())
        z.writestr('C6/BUILD.LOG', (OUT / 'canonical-fix-build-05/BUILD.LOG').read_bytes())
        z.writestr('C6/PROCESS.JSON', (OUT / 'canonical-fix-build-05/PROCESS.JSON').read_bytes())
        for name in ('HOST-BASIC.JSN', 'HOST-BASIC.LOG'):
            z.writestr(name, (OUT / name).read_bytes())
    source_names = ('tools/DOSINST/FIXXT.C', 'tools/DOSINST/HPXYID.H',
        'tools/DOSINST/HPXY.PY', 'tools/DOSINST/PANUI.PY', 'tools/DOSINST/RCPUB.PY',
        'tools/DOSINST/SETPINS.H', 'tools/DOSINST/SETFILES.H', 'tools/DOSINST/SETINPUT.H',
        'tools/DOSINST/SETNAT.JSN', 'tools/DOSINST/RCNATIVE.JSN', 'tools/DOSINST/FIXBUILD.JSN',
        'tools/SOUNDOWN/FINBUILD.PY', 'tools/XROEM/DISPLAY.BAT', 'tools/XROEM/DISPLAY.TXT',
        'tools/DOSINST/TESTDISP.PY', 'tools/DOSINST/TESTHPXY.PY',
        'experiments/XYSTRIP/CANINST.PY', 'experiments/XYSTRIP/CANPREP.PY',
        'experiments/XYSTRIP/CANVERIFY.PY', 'experiments/XYSTRIP/APPQA.C',
        'experiments/XYSTRIP/CANHELP.PY', 'experiments/XYSTRIP/CANAPP.C')
    q = dict(schema=1, status='PASS_CANONICAL_HPXY_PACKAGE', physical_hardware=False,
        archive=identity(archive), files={n: identity(b) for n, b in sorted(entries.items())},
        driver=identity(entries['WINXT/HPXY.DRV']),
        inherited_package=identity((ROOT / 'docs/QUAL/WDESK/PACKAGE.JSN').read_bytes()),
        native=native, sources={n: identity((ROOT / n).read_bytes()) for n in source_names},
        evidence={'docs/QUAL/HPXY/INSTALL.ZIP': identity((QUAL / 'INSTALL.ZIP').read_bytes())},
        scope='Normal expanded package; native fresh/update preparation, full update finisher, PC DOS3.20 Other/same-name refresh/DISPWIN, Paintbrush repaint/pan. Prior full Windows fresh recipe retained with unchanged OS inputs.',
        remaining_gaps=['Physical EX scanout/blackout timing',
            'Native cancellation and alternate-display variants are covered by host transaction tests, not a separate guest campaign',
            'No deliberately exhausted-memory or natural retrace-timeout testing'])
    (QUAL / 'PACKAGE.JSN').write_bytes(encoded(q))
    print('Sealed canonical normal-package evidence:', identity(archive))


if __name__ == '__main__':
    main()
