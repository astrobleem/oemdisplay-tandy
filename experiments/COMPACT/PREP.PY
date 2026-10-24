"""Reversible OFFLINE installer for a disposable, already-working 160 clone.

Run on the modern host against an extracted private guest Windows directory.
Never run against host Windows or a live/mounted-by-emulator guest. No CF or
disk-image writes. Baseline display must match the selected pinned target.
"""
import argparse
import base64
import hashlib
import json
import os
import re
from pathlib import Path
import BUILD

# Original C16VIEW.C, /G0 /Gw /AS, pinned toolchain / LINK4 recipe.
VIEW_SHA256 = 'e4e92c79615a1607494168e3518be5bb082911955903d5ca771829ae81b888d1'


def sha(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def read(path):
    if linked(path):
        raise ValueError('linked file refused: ' + str(path))
    return path.read_bytes() if path.exists() else None


def linked(path):
    return path.is_symlink() or getattr(path, 'is_junction', lambda: False)()


def ini(data, section, key, value=None):
    """Preserve unrelated bytes. Reject duplicate sections/keys and bad input."""
    if b'\0' in data:
        raise ValueError('binary INI')
    lines = data.decode('latin1').splitlines(keepends=True)
    starts = [i for i, s in enumerate(lines) if s.strip().lower() == '[' + section.lower() + ']']
    if len(starts) > 1:
        raise ValueError('duplicate INI section: ' + section)
    if not starts:
        if value is None:
            return None
        lines.append(('' if not lines or lines[-1].endswith(('\r', '\n')) else '\r\n') +
                     '[' + section + ']\r\n')
        starts = [len(lines) - 1]
    start = starts[0] + 1
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith('[')), len(lines))
    matches = [i for i in range(start, end) if '=' in lines[i] and
               lines[i].split('=', 1)[0].strip().lower() == key.lower()]
    if len(matches) > 1:
        raise ValueError('duplicate INI key: ' + section + '/' + key)
    old = lines[matches[0]].split('=', 1)[1].strip() if matches else None
    if value is None:
        return old
    replacement = key + '=' + value + '\r\n'
    if matches:
        lines[matches[0]] = replacement
    else:
        if end and not lines[end - 1].endswith(('\r', '\n')):
            lines[end - 1] += '\r\n'
        lines.insert(end, replacement)
    return ''.join(lines).encode('latin1')


def safe(root, relative):
    parts = relative.split('/')
    if not parts or any(not re.fullmatch(r'[A-Za-z0-9_.-]+', p) or p in ('.', '..') for p in parts):
        raise ValueError('unsafe transaction path')
    path = root
    for part in parts:
        path = path / part
        if linked(path):
            raise ValueError('linked transaction path')
    if not path.resolve().is_relative_to(root):
        raise ValueError('transaction outside clone')
    return path


def atomic(path, data):
    temporary = path.with_name(path.name + '.C16TMP')
    created = False
    try:
        with temporary.open('xb') as f:
            created = True
            f.write(data)
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, path)
    finally:
        if created and temporary.exists():
            temporary.unlink()


def clone_root(windows):
    root = Path(windows).absolute()
    if linked(root) or any(linked(p) for p in root.parents):
        raise ValueError('linked clone root')
    root = root.resolve()
    host = os.environ.get('WINDIR')
    if host and (root == Path(host).resolve() or root.is_relative_to(Path(host).resolve())):
        raise ValueError('host Windows refused')
    if not root.is_dir():
        raise ValueError('missing extracted clone directory')
    return root


def install(windows, packet, target, dialog_helper=None):
    root, packet = clone_root(windows), Path(packet).resolve()
    t = BUILD.TARGETS[target]
    statepath = root / 'C16STATE.JSN'
    if statepath.exists():
        raise ValueError('existing compact transaction; rollback first')
    system = read(safe(root, 'SYSTEM.INI'))
    win = read(safe(root, 'WIN.INI'))
    if system is None or win is None:
        raise ValueError('missing private Windows INIs')
    if (ini(system, 'boot', 'display.drv') or '').upper() != t['input']:
        raise ValueError('clone is not using the exact baseline target')
    dirs = [d for d in (root / 'SYSTEM', root) if (d / t['input']).is_file()]
    if len(dirs) != 1:
        raise ValueError('ambiguous/missing installed baseline driver')
    dest = dirs[0]
    baseline = read(safe(root, (dest / t['input']).relative_to(root).as_posix()))
    if sha(baseline) != t['sha256']:
        raise ValueError('installed baseline driver hash mismatch')
    record = json.loads((packet / 'BUILD.JSN').read_text())
    if record['target'] != target or record['baseline_sha256'] != t['sha256']:
        raise ValueError('wrong packet target')
    names = [t['output']] + list(BUILD.FONT.FACES)
    updates = {}
    if dialog_helper is not None:
        helper = Path(dialog_helper).read_bytes()
        if sha(helper) != VIEW_SHA256:
            raise ValueError('unrecognized optional C16VIEW helper')
        if read(safe(root, 'C16VIEW.EXE')) is not None:
            raise ValueError('pre-existing C16VIEW helper')
        load = (ini(win, 'windows', 'load') or '').strip()
        if 'C16VIEW' in load.upper():
            raise ValueError('pre-existing C16VIEW startup entry')
        updates['C16VIEW.EXE'] = helper
        win = ini(win, 'windows', 'load', (load + ' C16VIEW.EXE').strip())
    for name in names:
        data = (packet / name).read_bytes()
        if sha(data) != record['files'].get(name):
            raise ValueError('packet integrity mismatch: ' + name)
        updates[(dest / name).relative_to(root).as_posix()] = data
    for key, value in (('display.drv', t['output']), ('fonts.fon', 'C16SYS.FON'),
                       ('fixedfon.fon', 'C16FIX.FON'), ('oemfonts.fon', 'C16OEM.FON')):
        system = ini(system, 'boot', key, value)
    win = ini(win, 'windows', 'BorderWidth', '1')
    win = ini(win, 'windows', 'GridGranularity', '0')
    for key, value in (('XT Compact Helv (160)', 'C16HELV.FON'), ('XT Compact Courier (160)', 'C16COUR.FON')):
        if ini(win, 'fonts', key) is not None:
            raise ValueError('pre-existing compact font registration')
        win = ini(win, 'fonts', key, value)
    updates['SYSTEM.INI'], updates['WIN.INI'] = system, win
    # Saved pixel coordinates from a wider desktop can leave Program Manager
    # off-screen. Only its standard shell/profile is adjusted, in this already
    # pinned 160x200 transaction; custom shells and absent/unknown INIs stay.
    progman = read(safe(root, 'PROGMAN.INI'))
    shell = ini(read(safe(root, 'SYSTEM.INI')), 'boot', 'shell') or ''
    if progman is not None and shell.upper() == 'PROGMAN.EXE':
        placement = ini(progman, 'Settings', 'Window') or ''
        if re.fullmatch(r'-?\d+(?:\s+-?\d+){4}', placement):
            values = placement.split()
            values[-1] = '3'  # SW_SHOWMAXIMIZED; retain original normal rectangle
            updates['PROGMAN.INI'] = ini(progman, 'Settings', 'Window', ' '.join(values))
    entries = []
    for name, data in updates.items():
        before = read(safe(root, name))
        entries.append(dict(path=name, before=None if before is None else base64.b64encode(before).decode('ascii'),
                            before_sha256=sha(before), after_sha256=sha(data)))
    state = dict(schema=1, target=target, status='PREPARED', entries=entries)
    atomic(statepath, (json.dumps(state, indent=2) + '\n').encode('ascii'))
    # A durable journal exists before any Windows file changes. On interruption
    # rollback accepts either exact before or after bytes, including absent files.
    for name, data in updates.items():
        atomic(safe(root, name), data)
    state['status'] = 'INSTALLED'
    atomic(statepath, (json.dumps(state, indent=2) + '\n').encode('ascii'))
    return dict(target=target, status='INSTALLED OFFLINE; restart guest; runtime NOT_TESTED', files=len(entries))


def rollback(windows):
    root = clone_root(windows)
    statepath = root / 'C16STATE.JSN'
    state = json.loads(statepath.read_text())
    if state.get('schema') != 1 or state.get('status') not in ('PREPARED', 'INSTALLED'):
        raise ValueError('invalid/already-restored transaction')
    entries = state['entries']
    seen = set()
    for entry in entries:
        if entry['path'] in seen:
            raise ValueError('duplicate transaction path')
        seen.add(entry['path'])
        current = read(safe(root, entry['path']))
        before = None if entry['before'] is None else base64.b64decode(entry['before'], validate=True)
        if sha(before) != entry['before_sha256']:
            raise ValueError('corrupt saved before bytes')
        if sha(current) not in (entry['before_sha256'], entry['after_sha256']):
            raise ValueError('changed since installation; preserve and resolve first: ' + entry['path'])
    for entry in entries:
        path = safe(root, entry['path'])
        before = None if entry['before'] is None else base64.b64decode(entry['before'])
        if before is None:
            if path.exists():
                path.unlink()  # only this transaction's exact checked file
        else:
            atomic(path, before)
    state['status'] = 'ROLLED_BACK'
    atomic(statepath, (json.dumps(state, indent=2) + '\n').encode('ascii'))
    return dict(status='ROLLED_BACK', files=len(entries), journal='C16STATE.JSN retained')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('action', choices=('on', 'off'))
    p.add_argument('--windows', type=Path, required=True)
    p.add_argument('--offline-private-clone', action='store_true', required=True)
    p.add_argument('--packet', type=Path)
    p.add_argument('--target', choices=sorted(BUILD.TARGETS))
    p.add_argument('--dialog-helper', type=Path, help='optional exact locally built C16VIEW.EXE')
    a = p.parse_args()
    if a.action == 'on' and (not a.packet or not a.target):
        p.error('on requires --packet and --target')
    try:
        print(json.dumps(install(a.windows, a.packet, a.target, a.dialog_helper) if a.action == 'on' else rollback(a.windows)))
    except (ValueError, KeyError, OSError) as exc:
        p.error(str(exc))
