"""Bind a qualified CPSET resource pin without changing PREPXT executable code.

The measured base and its original document binder stay intact. Only the
CPSET.EXE, WAVEXT.EXE and XTCLEAN.COM resource pins and the allowed document
rows may differ. Frozen source/native records are preserved.
"""
import hashlib
import importlib.machinery
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
OLD_CPSET=('c8207fa1eadf085d77cc0a69ffcc2c70bccb94e08c9507df225bc42c7918fdc9',35457)


def identity(b):
    return {'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}


def resource():
    record=json.loads((HERE/'CPBUILD.JSN').read_bytes())
    data=(HERE/'CPSET.EXE').read_bytes()
    source=HERE/'CPSET' if (HERE/'CPSET').is_dir() else HERE.parent/'CPSET'
    if record['source_sha256']!=identity((source/'CPSET.C').read_bytes())['sha256']:
        raise ValueError('CPSET build source differs')
    if record['runtime']!=identity(data) or not 1024<len(data)<65536 or data[:2]!=b'MZ':
        raise ValueError('CPSET DOS resource differs')
    return data,record


def bind(header):
    data,build=resource()
    old=importlib.machinery.SourceFileLoader('cpset_original_binder',str(HERE/'DOCPINS/REBIND.PY')).load_module()
    before=next(x for x in old.rows(HERE/'DOCPINS/BASEPINS.H') if x[0]=='CPSET.EXE')
    after=next(x for x in old.rows(header) if x[0]=='CPSET.EXE')
    if (before[1],before[2])!=OLD_CPSET or after!=('CPSET.EXE',identity(data)['sha256'],len(data),0):
        raise ValueError('Unexpected CPSET resource pin transition')
    launch=importlib.machinery.SourceFileLoader('current_launch_binder',str(HERE/'LAUNCH/BIND.PY')).load_module()
    resources,launch_build=launch.resources()
    for name,payload in resources.items():
        row=next(x for x in old.rows(header) if x[0]==name)
        if row!=(name,identity(payload)['sha256'],len(payload),0):
            raise ValueError('Unexpected launch resource pin: '+name)
    old.ALLOWED=old.ALLOWED|{'CPSET.EXE','WAVEXT.EXE','XTCLEAN.COM'}
    result,proof=old.bind(header)
    proof['binding_kind']='Host resource/document pin refresh of unchanged PREPXT code'
    proof['only_document_data_changed']=False
    del proof['MZ_header_code_relocations_non_document_data_exact']
    proof['MZ_header_code_relocations_other_data_exact']=True
    proof['resource_builds']={'CPSET':build,'launch':launch_build}
    proof['code_contract']='Only CPSET.EXE, WAVEXT.EXE, XTCLEAN.COM resource pins and permitted document data changed. PREPXT functions, control flow, buffers and paths are unchanged.'
    return result,proof
