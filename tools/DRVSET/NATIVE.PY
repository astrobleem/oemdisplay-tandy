"""Read the exact carrier/native-install evidence; never run an installer."""
import hashlib
import importlib.machinery
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
        len(record.get('checks',{}))!=7 or not all(v is True for v in record['checks'].values())):
        return pending,None
    names={'NATIVE.JSN','NATIVE.PY','P15.PNG','TARGET.JSN','TARGET.LOG','TARGET.PY','TARGET.BAT','TARGET.CNF'}
    if set(record.get('evidence',{}))!=names:raise ValueError('Native carrier evidence list differs')
    for name,pin in record['evidence'].items():
        if identity((HERE/'QA'/name).read_bytes())!=pin:
            raise ValueError('Native carrier evidence differs: '+name)
    actual={n:identity(b) for n,b in files.items()}
    if record.get('outputs',{}).get(product)==outputs and record.get('runtime',{}).get(product)==actual:
        return 'PASS: '+record['scope'],{'path':'tools/DRVSET/NATIVE.JSN',**identity(path.read_bytes())}
    # A later PC1512 driver has separate native run/carrier evidence. Never
    # rewrite the original Setup receipt or inherit its pass for new bytes.
    root=HERE.parents[1]
    qual=root/'tools/P15PACK/QUALIFY.JSN'
    if product!='PC1512' or not qual.is_file():return pending,None
    update=json.loads(qual.read_bytes())
    if update.get('outputs')!=outputs or update.get('runtime')!=actual:return pending,None
    if update.get('original_installer_receipt')!=identity(path.read_bytes()):
        raise ValueError('Original PC1512 installer receipt differs')
    original=record['runtime']['PC1512']
    if set(actual)!=set(original) or any(actual[n]!=original[n] for n in actual if n!='PC1512.DRV'):
        raise ValueError('PC1512 driver update changed installer/support inputs')
    verifier=importlib.machinery.SourceFileLoader('p15_native_update',str(root/'src/pc1512/P15VERIFY.PY')).load_module()
    checked,_=verifier.verify()
    if checked!=update:raise ValueError('PC1512 qualification record changed during verification')
    return ('PASS: native PC1512 Output/frame/return-state qualification and new carrier extraction; '
            'original OEM Setup, installer and support bytes preserved'),{
                'path':'tools/P15PACK/QUALIFY.JSN',**identity(qual.read_bytes())}
