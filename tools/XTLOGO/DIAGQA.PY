"""Validate prepared paired inputs or evaluate completed bounded diagnostics.

Host-only: never launches an emulator, acquires a lease, or edits guest inputs.
"""
from pathlib import Path
import argparse
import hashlib
import json

WORK = Path(__file__).resolve().parents[3]
OUT = WORK / 'STATIC-DIAG-1'
OLD = WORK / 'STATIC-NATIVE'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tf(p, s):
    p.write_bytes(s.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def files(p):
    return {str(f.relative_to(p)).replace('\\', '/'): sha(f)
            for f in sorted(p.rglob('*')) if f.is_file()}


def check(prepared):
    cases = json.loads((OUT / 'CASES.JSON').read_bytes())
    evidence = json.loads((OUT / 'EVIDENCE/PRESERVED.JSON').read_bytes())
    for n, h in evidence.items():
        assert sha(OLD / n) == h, 'Preserved evidence changed: ' + n
    if prepared:
        for name, case in cases.items():
            assert files(OUT / name / 'GUEST') == case['initial_files'], 'Input changed: ' + name
            cfg = (OUT / name / 'RUN.CNF').read_text('ascii')
            for requirement in ('cputype=8086_prefetch', 'cycles=fixed 200000',
                                'memsizekb=640', 'xms=false', 'ems=false', 'umb=false'):
                assert requirement in cfg, requirement
            assert case['seconds'] <= 60
        for left, right in (('G32R5', 'G32NEW'), ('G64R5', 'G64NEW'),
                            ('S64R5', 'S64NEW'), ('STXTR5', 'STXTNEW')):
            a, b = cases[left]['initial_files'], cases[right]['initial_files']
            difference = [n for n in sorted(set(a) | set(b)) if a.get(n) != b.get(n)]
            wanted = ['WINDOWS/WIN.COM', 'WINXT/TINST.EXE']
            if left.startswith('S'):
                wanted += ['WINXT/CGALOGO.LGO', 'WINXT/OEMSETUP.INF']
            assert difference == sorted(wanted), (left, difference)
        assert (OUT / 'STOP.LEASE').exists(), 'Missing allocation guard'
        report = {'prepared_inputs_valid': True, 'native_run': False,
                  'cases': len(cases), 'preserved_evidence_files': len(evidence),
                  'pair_differences_only_expected_runtime_inputs': True}
        tf(OUT / 'PREPQA.JSON', json.dumps(report, indent=2))
        print(json.dumps(report, indent=2))
        return
    lease = json.loads((OUT / 'LEASE.JSON').read_bytes())
    runs = {r['purpose']: r for r in lease['jobs']}
    results = {}
    old_before = json.loads((OLD / 'BADCNF/BEFORE.JSON').read_bytes())
    expected_com = (WORK / 'FONT-NATIVE6/CGA/GUEST/WINDOWS/SYSTEM/WIN.CNF').read_bytes()
    expected_art = (WORK / 'static-logo/distributions/WINXT/WXTSPL01.RLE').read_bytes()
    wave = (WORK / 'FONT-NATIVE6/CGA/GUEST/WINDOWS/XTTEST.COM').read_bytes()
    for name, case in cases.items():
        guest = OUT / name / 'GUEST'
        errors = []
        extra = {}
        run = runs.get(name)
        if not run:
            extra['emulator_outcome']='not run'
            errors.append('Native job not run')
        elif run.get('exit_code') is None:
            extra['emulator_outcome']='Harness timeout; lease runner terminated its process'
            errors.append('Native job exceeded its individual time bound')
        elif run['exit_code']==3221225477:
            extra['emulator_outcome']='Host access violation 0xC0000005'
            errors.append('Emulator teardown/access violation')
        else:
            extra['emulator_outcome']='Normal host exit' if run['exit_code']==0 else 'Nonzero host exit '+str(run['exit_code'])
            if run['exit_code']!=0:errors.append(extra['emulator_outcome'])
        if name.startswith('R'):
            current = files(guest / 'WINDOWS')
            changed = [n for n, h in old_before.items() if current.get(n.replace('\\', '/')) != h]
            if changed:
                errors.append('Original Windows byte mismatch: ' + str(changed))
            extra.update({'outer_shell_status': (guest / 'STATUS.TXT').read_text('ascii').strip()
                     if (guest / 'STATUS.TXT').exists() else 'missing',
                     'original_windows_exact': not changed,
                     'partial_guard_retained': (guest / 'WINXT/PARTIAL.TAG').exists(),
                     'ready_absent': not (guest / 'WINXT/READY.TAG').exists()})
            for n in ('SEEDED.OK', 'RESTORED.OK', 'DONE.OK'):
                if not (guest / n).exists() or not (guest / n).stat().st_size:
                    errors.append('Missing nonempty ' + n)
            if not extra['partial_guard_retained'] or not extra['ready_absent']:
                errors.append('Refusal guard contract violated')
        elif name.startswith('G'):
            done = (guest / 'COMPLETE.LOG').read_text('ascii') if (guest / 'COMPLETE.LOG').exists() else ''
            if 'DONE=1' not in done:
                errors.append('Win16 probe did not finish')
            if not (guest / 'DONE.OK').exists() or not (guest / 'DONE.OK').stat().st_size:
                errors.append('No post-Windows DOS return marker')
            extra['complete_log_bytes'] = len(done)
        else:
            driver = 'TXTMODE' if name.startswith('STXT') else 'TR56404'
            ini = (guest / 'SELECTED.INI').read_text('ascii') if (guest / 'SELECTED.INI').exists() else ''
            if 'display.drv=' + driver + '.DRV' not in ini:
                errors.append('Expected Setup-selected ' + driver + ' missing')
            lgo = (WORK / 'FONT-NATIVE6/CGA/GUEST/WINDOWS/SYSTEM/CGALOGO.LGO').read_bytes() if name.endswith('R5') else (WORK / 'static-logo/distributions/WINXT/XTSTATIC.LGO').read_bytes()
            if not (guest / 'SELECTED.COM').exists():errors.append('Setup-built static COM evidence missing')
            elif (guest / 'SELECTED.COM').read_bytes() != expected_com + lgo + expected_art:errors.append('Setup-built static COM mismatch')
            if not (guest / 'SELECTED.WAV').exists():errors.append('Selected private slow-wave evidence missing')
            elif (guest / 'SELECTED.WAV').read_bytes() != wave:errors.append('Private slow wave changed')
            if not (guest / 'SETDONE.OK').exists() or not (guest / 'SETDONE.OK').stat().st_size:
                errors.append('Setup did not return')
        if (guest / 'FAIL.TXT').exists() and (guest / 'FAIL.TXT').stat().st_size:
            errors.append('Native case failure marker')
        if not name.startswith('R'):
            try:
                last = (guest / 'AFTER.LOG').read_text('ascii').splitlines()[-1].split()
                extra['dos_kb'] = int(last[0], 16)
                extra['dos_mode'] = int(last[1], 16) & 255
                if extra['dos_kb'] != 624 or extra['dos_mode'] != 3:
                    errors.append('DOS video/reservation cleanup failed')
            except (OSError, ValueError, IndexError):
                errors.append('Missing post-return mode/memory evidence')
        results[name] = {'errors': errors, **extra}
    report = {'status': 'TARGETED DIAGNOSTICS; not full package qualification',
              'native_package_qualified': False, 'publication_allowed': False,
              'cases': results, 'all_targeted_cases_passed': not any(c['errors'] for c in results.values()),
              'lease_released': lease.get('active') == 'released',
              'conflicts_after': lease.get('conflicts_after')}
    tf(OUT / 'RESULTS.JSON', json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepared', action='store_true')
    check(p.parse_args().prepared)
