"""Replay accepted fresh-CGA evidence with its original catalog source bytes."""
from pathlib import Path
import hashlib,importlib.machinery,io,json,tempfile,zipfile
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
NAMES={'tools/CURRENT/BUNDLE.PY','tools/CURRENT/CHECK.PY','tools/CURRENT/PRODUCTS.JSN'}

def identity(data):return dict(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
def verify(data):
    raw=(ROOT/'tools/CGAFRESH/ACCEPT.JSN').read_bytes();q=json.loads(raw)
    with zipfile.ZipFile(HERE/'CGASNAP.ZIP')as z:
        names=z.namelist()
        if set(names)!=NAMES or len(names)!=len(NAMES) or z.testzip()is not None:raise ValueError('Fresh catalog snapshot inventory differs')
        frozen={n:z.read(n)for n in names}
    files={'tools/CGAFRESH/ACCEPT.JSN':raw}
    def add(name,want):
        p=Path(name)
        if p.is_absolute()or '..'in p.parts or ':'in name or '\\'in name:raise ValueError('Unsafe frozen fresh path')
        body=frozen[name]if name in NAMES else(ROOT/p).read_bytes()
        if identity(body)!=want:raise ValueError('Changed original fresh proof: '+name)
        files[name]=body;return body
    for n,want in q['sources'].items():add(n,want)
    for row in list(q.values())+list(q['captures'].values()):
        if isinstance(row,dict)and'path'in row and'identity'in row:add(row['path'],row['identity'])
    full=json.loads(files[q['native_completion']['path']]);parent=Path(q['native_completion']['path']).parent
    for n,want in full['evidence'].items():add((parent/n).as_posix(),want)
    with zipfile.ZipFile(io.BytesIO(files[q['source_packet']['path']]))as z:
        base='downloads/COMPACT/CGA.ZIP';files[base]=z.read(base)
    with tempfile.TemporaryDirectory(prefix='fresh-original-proof-')as tmp:
        root=Path(tmp)
        for n,body in files.items():
            path=root/n;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(body)
        gate=importlib.machinery.SourceFileLoader('current_frozen_fresh_gate',str(root/'tools/CGAFRESH/VERIFY.PY')).load_module()
        return gate.verify(data)
