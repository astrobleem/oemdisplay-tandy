"""Reproduce the current wrapper resource and bounded updater digest binding."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WRAPPER = 'a59b3ee294d95f152b17ed20fe9d1e090c1d5ca966476c6433cc532a5b938376'
OLD = 'be8daca3153969921238b04307cdb4f75698086d12f74a024e4c198e95ce43ad'
NAMES = {'BIND.PY', 'BUILD.JSN', 'BASE.C', 'BASE.EXE', 'BUILD.PY',
         'WAVEXT.C', 'WAVEXT.EXE', 'XTCLEAN.ASM', 'XTCLEAN.COM'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def resources():
    record = json.loads((HERE / 'BUILD.JSN').read_bytes())
    wrapper = (HERE / 'XTCLEAN.COM').read_bytes()
    if len(wrapper) != 1071 or sha(wrapper) != WRAPPER:
        raise ValueError('Current wrapper differs')
    if sha((HERE / 'XTCLEAN.ASM').read_bytes()) != record['wrapper']['source_sha256']:
        raise ValueError('Current wrapper source differs')
    base = (HERE / 'BASE.EXE').read_bytes()
    source = (HERE / 'BASE.C').read_bytes()
    updater = record['updater']
    if (sha(base) != updater['base_sha256'] or
            sha(source) != updater['base_source_sha256'] or
            base.count(OLD.encode()) != 1 or source.count(OLD.encode()) != 1):
        raise ValueError('Original updater source/runtime differs')
    bound = base.replace(OLD.encode(), WRAPPER.encode())
    expected_source = source.replace(OLD.encode(), WRAPPER.encode())
    if (bound != (HERE / 'WAVEXT.EXE').read_bytes() or
            expected_source != (HERE / 'WAVEXT.C').read_bytes() or
            len(bound) != updater['bytes'] or sha(bound) != updater['sha256'] or
            sha(expected_source) != updater['source_sha256'] or
            base.index(OLD.encode()) != updater['digest_offset']):
        raise ValueError('Updater wrapper-digest binding differs')
    return {'XTCLEAN.COM': wrapper, 'WAVEXT.EXE': bound}, record


def source_payload():
    resources()
    if {p.name for p in HERE.iterdir() if p.is_file()} != NAMES:
        raise ValueError('Current launch source allowlist differs')
    return {'LAUNCH/' + n: (HERE / n).read_bytes() for n in sorted(NAMES)}
