from pathlib import Path
import hashlib,json,zipfile
p=Path(__file__).resolve().parent;m=json.loads((p/'PACKAGE.JSN').read_bytes())
with zipfile.ZipFile(p/'LEARN12.ZIP') as z:
 assert hashlib.sha256((p/'LEARN12.ZIP').read_bytes()).hexdigest()==m['zip_sha256']
 assert z.testzip() is None
 expected={'LEARN12/SHA256.TXT'}
 for line in z.read('LEARN12/SHA256.TXT').decode().splitlines():
  digest,name=line.split('  ',1);assert '..' not in Path(name).parts and not Path(name).is_absolute()
  key='LEARN12/'+name;expected.add(key);assert hashlib.sha256(z.read(key)).hexdigest()==digest
 assert set(z.namelist())==expected and len(expected)==m['files']
 assert not any(Path(n).suffix.upper() in {'.EXE','.DLL','.DRV','.FON','.OBJ','.LIB','.COM'} for n in expected)
 assert not m['native_integration'] and not m['externally_verified_unknown_facts_claimed']
 assert m['all_repeats_deterministic'] and m['evaluated_games']==30720
print('PASS LEARN12 host study, exact source/results hashes and payload exclusions')
