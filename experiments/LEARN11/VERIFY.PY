"""Offline read-only host prototype packet verification; no publication."""
from pathlib import Path
import ast,hashlib,json,zipfile
ROOT=Path(__file__).resolve().parent
sha=lambda data:hashlib.sha256(data).hexdigest()
meta=json.loads((ROOT/'PACKAGE.JSN').read_text())
assert sha((ROOT/'LEARN11.ZIP').read_bytes())==meta['zip_sha256']
with zipfile.ZipFile(ROOT/'LEARN11.ZIP') as z:
    assert z.testzip() is None
    expected={'LEARN11/SHA256.TXT'}
    for line in z.read('LEARN11/SHA256.TXT').decode().splitlines():
        digest,path=line.split('  ',1)
        assert not Path(path).is_absolute() and '..' not in Path(path).parts
        name='LEARN11/'+path;expected.add(name);assert sha(z.read(name))==digest
    assert set(z.namelist())==expected and len(expected)==meta['files']
    assert not any(Path(name).suffix.upper() in {'.EXE','.DLL','.DRV','.FON','.OBJ','.LIB','.COM'} for name in expected)
    for name in expected:
        if name.endswith('.PY'):ast.parse(z.read(name).decode('utf-8'),filename=name)
    pins=json.loads(z.read('LEARN11/BASE/PINS.JSN'))
    assert pins['tandi10_zip_sha256']==meta['tandi10_zip_sha256']=='15fb6d3575ceccf1b36e85b0327d32d489a6509fd5a1ea0750b0d519e3f887df'
    for name,digest in pins['files'].items():assert sha(z.read('LEARN11/BASE/'+name))==digest
    results=json.loads(z.read('LEARN11/EVIDENCE/CHECK11.JSN'))
    assert results['checks_passed']==meta['checks_passed']==68
    assert results['baseline']['claude_two_wrong']['failures']==31
    assert results['audit08']['claude_two_wrong']['failures']==36
    models=results['fixed_reference']
    assert [models[k]['claude_two_wrong']['failures'] for k in ['baseline','truthful_learning','consistent_false_reports','repeated_claude_noisy_reports','conflicts']]==[28,36,33,34,28]
    assert results['format']['max_file_bytes']==meta['max_overlay_bytes']==7228
    for name in ['README.TXT','POLICY.TXT','UI.TXT','UI.HTM','UI.PNG','UI.SVG']:
        assert z.read('LEARN11/'+name)==(ROOT/name).read_bytes()
    assert meta['evaluated_games']==7168 and meta['training_games']==126
    assert not meta['native_integration'] and not meta['publication_performed'] and not meta['personal_learned_data_accessed']
print('PASS exact LEARN11 host packet, 68 checks, 7,168 evaluated games, 126 training games, pinned engine/data, disclosed regressions, offline UI and payload exclusions')
