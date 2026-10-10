"""Fail-closed rc.6 publication checks. Host only; no private media or guest.
MIT, Copyright (c) 2026 Windows XT contributors.
"""
import argparse
import importlib.machinery
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile

HERE=Path(__file__).resolve().parent
loader=importlib.machinery.SourceFileLoader('rc6_publication',str(HERE/'PUBLISH.PY'))
spec=importlib.util.spec_from_loader(loader.name,loader)
pub=importlib.util.module_from_spec(spec);loader.exec_module(pub)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--release',type=Path,required=True);a=ap.parse_args()
    pub.verify(a.release)
    with tempfile.TemporaryDirectory(prefix='rc6-guard-test-') as td:
        base=Path(td);checks=0
        def refusal(change,reason):
            nonlocal checks
            folder=base/str(checks);shutil.copytree(a.release,folder);change(folder)
            try: pub.verify(folder)
            except (ValueError,pub.TESTPKG.package.PackageError): checks+=1
            else: raise AssertionError('Accepted invalid publication '+reason)
        def alter(folder,name):
            p=folder/name;b=bytearray(p.read_bytes());b[len(b)//2]^=1;p.write_bytes(b)
        refusal(lambda p:alter(p,'WINXT720.IMG'),'changed disk')
        refusal(lambda p:(p/'WIN.CNF').write_bytes(b'private'),'extra owned resource')
        refusal(lambda p:alter(p,'WINXT-RC6-SOURCE.zip'),'changed source')
        refusal(lambda p:alter(p,'QUALIFY.JSON'),'changed qualification')
        for field,value in [('publication_allowed',False),('refreshed_helper_executed_in_guest',True)]:
            def change(folder,field=field,value=value):
                p=folder/'RELEASE.JSON';r=json.loads(p.read_bytes());r[field]=value
                p.write_bytes(json.dumps(r).encode())
                (folder/'SHA256SUMS').write_bytes(''.join(pub.sha(pub.read(folder/n))+'  '+n+'\n'
                    for n in sorted(pub.ASSETS-{'SHA256SUMS'})).encode())
            refusal(change,field)
        try:pub.verify(a.release,'f'*40)
        except ValueError: checks+=1
        else:raise AssertionError('Accepted wrong publication commit')
        for name in ('WIN.CNF','../escape','a\\CGA.GR2','/absolute','tools/CL.EXE'):
            try:pub.safe_name(name)
            except ValueError:checks+=1
            else:raise AssertionError('Unsafe source member '+name)
    print('PASS rc.6 publication negatives:',checks)
if __name__=='__main__':main()
