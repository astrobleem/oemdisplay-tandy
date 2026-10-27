#!/usr/bin/env python3
"""Prepare optional compact choices from the frozen current CGA packet.

Retain existing runtime bytes and defaults. Only two resource-derived drivers,
the visible OEM choices and the native installer are new. No emulator runs.
"""
import argparse,hashlib,json,zipfile
from pathlib import Path
import PACKCGA as P
import CMPRSC
from STAGECGA import write

def prepare(repo,out,commit):
    base=repo/'docs/QUAL/CGACMP'
    record=json.loads((base/'BASE.JSN').read_bytes());data=(base/'BASE.ZIP').read_bytes()
    if {k:P.identity(data)[k] for k in ('bytes','sha256')}!=record['packet']:
        raise ValueError('Frozen accepted CGA packet changed')
    with zipfile.ZipFile(base/'BASE.ZIP') as z:
        if z.testzip():raise ValueError('Corrupt accepted archive')
        original={n:z.read(n) for n in z.namelist()}
    if {n:{k:P.identity(b)[k] for k in ('bytes','sha256')} for n,b in original.items()}!=record['members']:
        raise ValueError('Accepted member inventory changed')
    files={n[4:]:b for n,b in original.items() if n.startswith('CGA/')};audits={}
    for mode,driver in (('320C','CGA320.DRV'),('640C','CGA640.DRV')):
        b,a=CMPRSC.compact(files[driver],files['CGA100.DRV'])
        files[P.COMPACT_DRIVERS[mode]]=b;audits[mode]=a
    files['OEMSETUP.INF']=(P.HERE/'OEMSETUP.INF').read_bytes()
    result=P.emit(repo,out,files,commit,compact_only=True)
    write(out/'COMPACT.JSN',json.dumps(dict(source_packet=record['packet'],profiles=audits,
          retained_runtime=[n for n,b in files.items() if n!='OEMSETUP.INF' and original.get('CGA/'+n)==b],
          windows='NOT_TESTED_NEW_INSTALLER',physical_hardware='UNQUALIFIED'),indent=2)+'\n')
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--repo',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    ap.add_argument('--source-commit',required=True);a=ap.parse_args()
    prepare(a.repo.resolve(),a.out.resolve(),a.source_commit)
    print('Optional compact profiles prepared; native installer and Windows qualification remain required.')
