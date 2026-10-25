"""Read the exact carrier/native-install evidence; never run an installer."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def identity(data):return {'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}


def status(product,outputs,files):
    path=HERE/'NATIVE.JSN'
    pending='PENDING: no completed native receipt for these exact packet bytes'
    if not path.is_file():return pending,None
    record=json.loads(path.read_bytes())
    if (record.get('complete') is not True or
        record.get('outputs',{}).get(product)!=outputs or
        record.get('runtime',{}).get(product)!={n:identity(b) for n,b in files.items()} or
        len(record.get('checks',{}))!=6 or not all(v is True for v in record['checks'].values())):
        return pending,None
    names={'NATIVE.JSN','NATIVE.PY','P15.PNG'}
    if set(record.get('evidence',{}))!=names:raise ValueError('Native carrier evidence list differs')
    for name,pin in record['evidence'].items():
        if identity((HERE/'QA'/name).read_bytes())!=pin:
            raise ValueError('Native carrier evidence differs: '+name)
    return 'PASS: '+record['scope'],{'path':'tools/DRVSET/NATIVE.JSN',**identity(path.read_bytes())}
