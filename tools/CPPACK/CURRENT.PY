"""Overlay the current qualified fixed driver on the unchanged accepted PAN kit."""
from pathlib import Path
import importlib.machinery
import json

ROOT = Path(__file__).resolve().parents[2]


def load(name, path):
    return importlib.machinery.SourceFileLoader(name, str(ROOT / path)).load_module()


def install_guide(original):
    old = b'Existing fixed-driver and grabber bytes remain intact.'
    if original.count(old) != 1:
        raise ValueError('Accepted ColorPlus guide changed; review before deriving current guide')
    text = original.replace(old, b'Existing panning-driver and grabber bytes remain intact.')
    marker = b'Keep the whole packet and its notices.'
    if text.count(marker) != 1:
        raise ValueError('ColorPlus guide insertion point changed')
    note = (b'The fixed 320x200 driver includes the qualified ellipse/COPY optimization.\r\n'
            b'One narrow-drawing test measured 110 ms over 20,000 calls (about 0.14%)\r\n'
            b'slower than the prior fixed driver. Panning helpers are unchanged.\r\n')
    return text.replace(marker, note + marker)


def qualified():
    fixed = load('current_copy_qualification', 'experiments/DGSCOPY/VERIFY.PY')
    proof = fixed.verify_profile('colorplus32016')
    q = json.loads((ROOT / 'tools/CPPACK/QUALIFY.JSN').read_bytes())['optimized']
    prior = load('current_copy_panning', 'tools/PAN/PUBLISH.PY')
    acceptance, packets = prior.products()
    base = packets['CPPAN.ZIP']
    if prior.identity(base) != q['colorplus_panning_base']:
        raise ValueError('Accepted current panning kit differs')
    before = prior.C.members(base)
    files = dict(before)
    driver = fixed.exact(q['profiles']['colorplus32016']['driver'])
    if prior.identity(driver) != proof['driver'] or 'PCP3216.DRV' not in before:
        raise ValueError('Current fixed driver differs from executed qualification')
    files['PCP3216.DRV'] = driver
    files['INSTALL.TXT'] = install_guide(before['INSTALL.TXT'])
    if (set(files) != set(before) or
            any(files[n] != before[n] for n in files if n not in {'PCP3216.DRV', 'INSTALL.TXT'})):
        raise ValueError('Fixed update changed panning, installer or support')
    data = prior.C.archive(files)
    return {'CPPAN.ZIP': data, 'INSTALL.TXT': files['INSTALL.TXT']}, proof


def outputs():
    return qualified()[0]


def verify(data):
    expected, proof = qualified()
    if data != expected['CPPAN.ZIP']:
        raise ValueError('Current ColorPlus packet differs from qualified driver/guide overlay')
    return proof
