"""Host-only paired rc.5/candidate diagnostics. Never allocate/run an emulator.

Fresh private copies only; preserved STATIC-NATIVE inputs/results are read-only.
All runtime branches remain unqualified until independently evaluated.
"""
from pathlib import Path
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT.parent
OLD = WORK / 'STATIC-NATIVE'
OUT = WORK / 'STATIC-DIAG-1'
RUNTIME = ROOT / 'distributions/WINXT'
sys.path.insert(0, str(ROOT / 'tools/XTFONTS'))
from NATIVE import config


def tf(path, value):
    path.write_bytes(value.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(directory):
    return {str(p.relative_to(directory)).replace('\\', '/'): sha(p)
            for p in sorted(directory.rglob('*')) if p.is_file()}


def prepare():
    if OUT.exists():
        raise ValueError('Use a fresh output; diagnostic evidence must not be overwritten')
    OUT.mkdir()
    evidence = OUT / 'EVIDENCE'
    evidence.mkdir()
    preserved = {}
    for p in sorted(OLD.rglob('*')):
        if p.is_file() and (p.suffix.upper() in ('.LOG', '.JSON', '.CNF', '.BAT', '.AVI')
                            or p.name.endswith(('.OK', '.TAG', '.TXT'))):
            preserved[str(p.relative_to(OLD)).replace('\\', '/')] = sha(p)
    tf(evidence / 'PRESERVED.JSON', json.dumps(preserved, indent=2))
    for name in ('LEASE.JSON', 'NATIVE-CHECKPOINT.JSON', 'QUALIFY.JSON', 'A-BADCNF.HOST.LOG'):
        shutil.copyfile(OLD / name, evidence / name)
    shutil.copyfile(ROOT / 'tools/XTLOGO/MSEQ.PY', evidence / 'MSEQ-OLD.PY')
    baseline_source = subprocess.check_output(
        ['git', '-C', str(ROOT), 'show', 'HEAD:src/tandysw/TINST.C'])
    current_source = (ROOT / 'src/tandysw/TINST.C').read_bytes()
    assert baseline_source.replace(b'CGALOGO.LGO', b'XTSTATIC.LGO') == current_source
    delta = ''.join(difflib.unified_diff(baseline_source.decode('ascii').splitlines(True),
                    current_source.decode('ascii').splitlines(True), 'rc5/TINST.C', 'candidate/TINST.C'))
    tf(evidence / 'TINST-DIFF.TXT', delta)
    bad = OLD / 'BADCNF'
    before = json.loads((bad / 'BEFORE.JSON').read_bytes())
    restored = hashes(bad / 'GUEST/WINDOWS')
    changed = [n for n, h in before.items() if restored.get(n.replace('\\', '/')) != h]
    assert not changed
    restore = (bad / 'GUEST/WINXT/BACKUP/B001/RESTORE.BAT').read_text('ascii')
    copies = sum(line.startswith('COPY /B ') for line in restore.splitlines())
    copy_logs = (OLD / 'A-BADCNF.HOST.LOG').read_text('ascii').count('SHELL:Redirect output to NUL')
    assert copies == copy_logs == 36
    baseline = OUT / 'RC5'
    baseline.mkdir()
    archive = WORK / 'PUB-ANONYMOUS-RC5/WXTTOOLS.ZIP'
    with zipfile.ZipFile(archive) as z:
        for name in ('TINST.EXE', 'OEMSETUP.INF'):
            (baseline / name).write_bytes(z.read('WINXT/' + name))
        shared = {}
        for n in ('RESERVE.COM', 'XTCLEAN.COM', 'WAVEXT.EXE', 'SHELLSEL.EXE', 'CPSET.EXE',
                  'TR53216.DRV', 'TR56404.DRV', 'TXTMODE.DRV', 'WXTSPL01.RLE',
                  'XTCSYS.FON', 'XTCFIX.FON', 'XTCOEM.FON', 'XTESYS.FON', 'XTEFIX.FON',
                  'XTEOEM.FON', 'XTTSYS.FON'):
            same = z.read('WINXT/' + n) == (RUNTIME / n).read_bytes()
            assert same, n
            shared[n] = {'rc5_equal': same, 'sha256': sha(RUNTIME / n)}
    private = WORK / 'FONT-NATIVE6/CGA/GUEST/WINDOWS'
    old_lgo = (private / 'SYSTEM/CGALOGO.LGO').read_bytes()
    cnf = (private / 'SYSTEM/WIN.CNF').read_bytes()
    art = (RUNTIME / 'WXTSPL01.RLE').read_bytes()
    coms = {'RC5': cnf + old_lgo + art,
            'NEW': cnf + (RUNTIME / 'XTSTATIC.LGO').read_bytes() + art}
    jobs = []
    manifests = {}
    common = ('@ECHO OFF\nSET PATH=C:\\WINDOWS;C:\\WINDOWS\\SYSTEM;Z:\\\n'
              'SET TEMP=C:\\WINDOWS\\TEMP\nC:\n')

    def helper(guest, version):
        shutil.copyfile(baseline / 'TINST.EXE' if version == 'RC5' else RUNTIME / 'TINST.EXE',
                        guest / 'WINXT/TINST.EXE')

    def save_case(name, guest, batch, seconds, purpose, capture=False):
        case = guest.parent
        tf(guest / 'DOSCASE.BAT', batch)
        if capture:
            (case / 'CAPTURE').mkdir()
            tf(guest / 'START.BAT', '@ECHO OFF\nDX-CAPTURE /V COMMAND.COM /C C:\\DOSCASE.BAT\nEXIT\n')
        else:
            tf(guest / 'START.BAT', batch)
        cfg = config([('C', guest)], 'C:\nSTART.BAT\n', guest, True)
        if capture:
            cfg = cfg.replace('machine=tandy', 'machine=tandy\ncaptures=' + str(case / 'CAPTURE'))
        tf(case / 'RUN.CNF', cfg)
        manifests[name] = {'purpose': purpose, 'initial_files': hashes(guest),
                           'seconds': seconds, 'capture': capture}
        jobs.append({'config': str(case / 'RUN.CNF'), 'purpose': name, 'seconds': seconds})

    # Same failed post-refusal transaction/RESTORE text. Exact public rc.5 helper
    # is the control. Each trial deliberately makes two snapshotted files differ.
    for version in ('RC5', 'NEW'):
        for callstyle in ('CMD', 'ZCMD', 'CALL'):
            name = 'R' + ('5' if version == 'RC5' else 'N') + callstyle
            guest = OUT / name / 'GUEST'
            shutil.copytree(bad / 'GUEST', guest)
            helper(guest, version)
            for p in guest.glob('*'):
                if p.is_file() and p.name != 'AUTOEXEC.BAT' and p.suffix.upper() in ('.LOG', '.OK', '.TXT', '.BAT'):
                    p.unlink()
            tf(guest / 'WINDOWS/CONTROL.INI', 'DIAGNOSTIC_MUTATION_CONTROL\n')
            tf(guest / 'WINDOWS/WIN.INI', 'DIAGNOSTIC_MUTATION_WIN\n')
            s = common + 'CD \\WINDOWS\n'
            s += ('C:\\WINXT\\TINST.EXE /COMPARE C:\\WINXT\\BACKUP\\B001\\ROOT\\WIN.INI '
                  'C:\\WINDOWS\\WIN.INI\nIF ERRORLEVEL 1 ECHO EXPECTED>C:\\SEEDED.OK\n')
            if callstyle == 'CALL':
                s += 'C:\\WINXT\\TINST.EXE /ZERO\nCALL C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES\n'
            else:
                if callstyle == 'ZCMD':
                    s += 'C:\\WINXT\\TINST.EXE /ZERO\n'
                s += 'COMMAND.COM /C C:\\WINXT\\BACKUP\\B001\\RESTORE.BAT YES > C:\\ROLLBACK.LOG\n'
            s += ('IF ERRORLEVEL 2 GOTO STATUS2\nIF ERRORLEVEL 1 GOTO STATUS1\n'
                  'ECHO ZERO>C:\\STATUS.TXT\nGOTO CHECK\n:STATUS2\nECHO TWO_OR_MORE>C:\\STATUS.TXT\n'
                  'GOTO CHECK\n:STATUS1\nECHO ONE>C:\\STATUS.TXT\n:CHECK\n')
            for n in ('CONTROL.INI', 'WIN.INI'):
                s += ('C:\\WINXT\\TINST.EXE /COMPARE C:\\WINXT\\BACKUP\\B001\\ROOT\\' + n +
                      ' C:\\WINDOWS\\' + n + '\nIF ERRORLEVEL 1 GOTO FAIL\n')
            s += 'ECHO BYTES_RETURNED>C:\\RESTORED.OK\nGOTO END\n:FAIL\nECHO BAD>C:\\FAIL.TXT\n:END\nECHO RETURNED>C:\\DONE.OK\nEXIT\n'
            save_case(name, guest, s, 15, 'Paired rollback status, mutated-byte restoration, retained refusal guard')

    # Exact prior selected INIs, fonts, Windows/kernel, private wave and launcher.
    # Baseline/control WIN.COM differs only in the measured static LGO resource.
    for mode, short in (('TR53216', '32'), ('TR56404', '64')):
        for version in ('RC5', 'NEW'):
            name = 'G' + short + ('R5' if version == 'RC5' else 'NEW')
            guest = OUT / name / 'GUEST'
            shutil.copytree(OLD / mode / 'GUEST', guest)
            helper(guest, version)
            (guest / 'WINDOWS/WIN.COM').write_bytes(coms[version])
            for p in guest.glob('*'):
                if p.is_file() and p.name != 'AUTOEXEC.BAT' and p.suffix.upper() in ('.LOG', '.OK', '.TXT', '.BAT', '.BIN', '.INI', '.WAV'):
                    p.unlink()
            assert (guest / 'WINDOWS/XTTEST.COM').read_bytes() == (private / 'XTTEST.COM').read_bytes()
            s = common + 'C:\\WINXT\\RESERVE.COM\nCD \\WINDOWS\n'
            s += 'C:\\MEMSNAP > C:\\BEFORE.LOG\nCOMMAND.COM /C C:\\WINXT\\WINXT.BAT > C:\\LAUNCH.LOG\n'
            s += ('C:\\MEMSNAP > C:\\AFTER.LOG\nIF NOT EXIST C:\\FONT.LOG GOTO FAIL\n'
                  'COPY C:\\FONT.LOG C:\\COMPLETE.LOG >NUL\nECHO RETURNED>C:\\DONE.OK\nGOTO END\n'
                  ':FAIL\nECHO PROBE_MISSING>C:\\FAIL.TXT\n:END\nEXIT\n')
            save_case(name, guest, s, 50, 'Paired normal launcher; fixed 200000 cycles; no AUTOTYPE', True)

    # Correct OEM prompt position. Capture actual sixth-choice/font-source prompts.
    # This pass deliberately uses the known passing 200000 clock in both versions.
    for mode, short in (('TR56404', '64'), ('TXTMODE', 'TXT')):
        auto = next(l for l in (OLD / mode / 'GUEST/FIXUP.BAT').read_text('ascii').splitlines()
                    if l.startswith('AUTOTYPE '))
        auto = auto.replace('-w 2 -p 0.075', '-w 3 -p 0.15')
        for version in ('RC5', 'NEW'):
            name = 'S' + short + ('R5' if version == 'RC5' else 'NEW')
            guest = OUT / name / 'GUEST'
            shutil.copytree(OLD / mode / 'GUEST', guest)
            helper(guest, version)
            (guest / 'WINDOWS/WIN.COM').write_bytes(coms[version])
            if version == 'RC5':
                shutil.copyfile(baseline / 'OEMSETUP.INF', guest / 'WINXT/OEMSETUP.INF')
                (guest / 'WINXT/CGALOGO.LGO').write_bytes(old_lgo)
            for p in guest.glob('*'):
                if p.is_file() and p.name != 'AUTOEXEC.BAT' and p.suffix.upper() in ('.LOG', '.OK', '.TXT', '.BAT', '.BIN', '.INI', '.WAV', '.COM'):
                    if p.name not in ('MEMSNAP.COM', 'TEXT3.COM'):
                        p.unlink()
            s = common + auto + '\nCD \\WINDOWS\n'
            s += 'COMMAND.COM /C C:\\WINXT\\WINXT.BAT SETUP > C:\\SETUP.LOG\n'
            s += ('COPY SYSTEM.INI C:\\SELECTED.INI >NUL\nCOPY WIN.COM C:\\SELECTED.COM >NUL\n'
                  'COPY XTTEST.COM C:\\SELECTED.WAV >NUL\nECHO RETURNED>C:\\SETDONE.OK\n'
                  'C:\\MEMSNAP > C:\\AFTER.LOG\nEXIT\n')
            save_case(name, guest, s, 60, 'Paired Setup selection/teardown with video; no runtime patch', True)

    (OUT / 'QUEUE').mkdir()
    for index, job in enumerate(jobs):
        tf(OUT / 'QUEUE' / ('%02d-%s.JSON' % (index, job['purpose'])), json.dumps(job))
    inputs = json.loads((OLD / 'INPUTS.JSON').read_bytes())
    inputs['status'] = 'PREPARED ONLY; no allocated emulator slot'
    inputs['prior_evidence'] = str(evidence / 'PRESERVED.JSON')
    tf(OUT / 'INPUTS.JSON', json.dumps(inputs, indent=2))
    tf(OUT / 'STOP.LEASE', 'No allocation. Do not launch until an explicit slot is granted.\n')
    tf(OUT / 'CASES.JSON', json.dumps(manifests, indent=2))
    report = {
        'status': 'HOST DIAGNOSIS; native comparisons prepared, not run',
        'native_package_qualified': False, 'publication_allowed': False,
        'baseline': '0c400228eede1b0aedde8c91c3598636b1ea7e1c',
        'rc5_archive_sha256': sha(archive),
        'rollback': {'original_windows_files_exact': len(before), 'changed': changed,
                     'restore_copy_commands': copies, 'observed_copy_log_lines': copy_logs,
                     'partial_guard_retained_by_contract': True,
                     'ready_marker_is_helper_completeness_not_activation': True,
                     'nested_command_status_cause': 'Unproven; paired /C vs qualified CALL+/ZERO tests prepared'},
        'source': {'tinst_only_delta': 'Required file CGALOGO.LGO -> XTSTATIC.LGO',
                   'rollback_generator_and_zero_compare_paths_unchanged': True,
                   'shared_rc5_payloads': shared},
        'gui': {'passing_cold_cycles': 200000, 'failed_gui_cycles': 1000000,
                'cold_native_gui_and_dos_return_passed': True,
                'short_capture_limit_not_a_proven_hang': True,
                'zero_length_open_font_log_is_not_stage_evidence': True},
        'setup': {'two_host_exit_codes': '0xC0000005 after saved outputs/SETDONE.OK',
                  'cause': 'Unproven; baseline/candidate paired tests required',
                  'text_choice': 'Previous selected INI still TR53216; text chain test incomplete',
                  'text_chain_required': True, 'text_desktop_improvement_in_scope': False},
        'requested_slot_minutes': 12,
        'job_bounds_seconds': sum(j['seconds'] for j in jobs),
        'job_count': len(jobs),
        'jobs': jobs,
        'runtime_corrective_change': 'None justified by present evidence',
        'test_oracle_correction': 'Retain READY.TAG after successful committed rollback; WAVE.RDY must be inactive',
        'preserved_evidence_manifest': str(evidence / 'PRESERVED.JSON')}
    tf(OUT / 'DIAGNOSIS.JSON', json.dumps(report, indent=2))
    print(json.dumps({k: report[k] for k in ('status', 'requested_slot_minutes', 'job_bounds_seconds', 'job_count')}, indent=2))


if __name__ == '__main__':
    prepare()
