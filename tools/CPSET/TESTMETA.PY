"""Two metadata layouts and transaction guards; no emulator/OS installation.

Compiler executables are explicit arguments. Actual Windows inputs remain in
private local fixtures; no Windows metadata or keyboard bytes are published.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zlib


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--parser',type=Path,required=True)
    p.add_argument('--program',type=Path)
    p.add_argument('--original',type=Path)
    p.add_argument('--five-disk',type=Path)
    p.add_argument('--keyboard',type=Path)
    p.add_argument('--report',type=Path)
    a=p.parse_args()
    parser=str(a.parser.resolve());checks=[]
    def run(cmd,ok=True,env=None):
        r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=env)
        assert (r.returncode==0)==ok,(cmd,r.returncode,r.stdout.decode(errors='replace'))
        return r.stdout.decode(errors='replace').strip()
    def check(label,cmd,ok=True,env=None):
        value=run(cmd,ok,env);checks.append(label);return value
    with tempfile.TemporaryDirectory(prefix='cpset-inputs-') as tmp:
        root=Path(tmp);sample=root/'META.INF'
        vectors=[b'',b'123456789',bytes(range(256)),b'\0'*4096,b'x'*4096]
        for i,b in enumerate(vectors):
            sample.write_bytes(b)
            got=check('CRC vector '+str(i),[parser,'crc',str(sample)])
            assert got=='%08x'%zlib.crc32(b),got
        def layout(size,count):
            text='[setup]\r\n[disks]\r\n'+''.join('%d=. ,"Disk",disk%d\r\n'%(i,i) for i in range(1,count+1))
            text+='[keyboard.drivers]\r\nkbd=1:keyboard.drv\r\n[io.device]\r\n;'
            b=text.encode('ascii');return b+b'x'*(size-len(b))
        for size,count in [(49046,4),(49095,5)]:
            good=layout(size,count);sample.write_bytes(good)
            check('structured '+str(count)+'-disk layout',[parser,'layout',str(sample)])
            cases={
                'duplicate section':good.replace(b'[io.device]',b'[setup]    '),
                'missing disk section':good.replace(b'[disks]',b';disks;'),
                'missing section':good.replace(b'[setup]',b';setup;'),
                'comment-only section':good.replace(b'[setup]',b';setup]'),
                'duplicate disk':good.replace(b'2=. ',b'1=. '),
                'missing disk':good.replace(b'2=. ',b';=. '),
                'foreign disk':good.replace(b'2=. ',b'9=. '),
                'malformed section':good.replace(b'[setup]',b'[setup '),
                'section suffix':good.replace(b'[setup]\r\n',b'[setup]XX'),
                'wrong section order':good.replace(b'[setup]',b'[disks]').replace(b'[disks]\r\n1=',b'[setup]\r\n1='),
            }
            for label,bad in cases.items():
                sample.write_bytes(bad);check(str(count)+' '+label,[parser,'layout',str(sample)],False)
            sample.write_bytes(good)
            check('unrelated same-size content refused '+str(count),[parser,'source',str(sample)],False)
        actual=[]
        for name,path,size,crc,digest in [
            ('original',a.original,49046,0x92333a90,'4f4b65bdc0ce2d4a23859494f8936376296e857872a554b0037ceb068f2202f2'),
            ('five-disk',a.five_disk,49095,0xa8246e14,'aa4a92022c88750d9dee4a8c4b003de295d44f82f70f2d5430023f1984e6d84c')]:
            if path is None:continue
            b=path.read_bytes();assert len(b)==size and zlib.crc32(b)==crc and hashlib.sha256(b).hexdigest()==digest
            for mode in ['source','verify']:check(name+' '+mode,[parser,mode,str(path.resolve())])
            actual.append({'name':name,'bytes':len(b),'sha256':digest})
            if not a.program or not a.keyboard:continue
            win=root/name;system=win/'SYSTEM';system.mkdir(parents=True)
            metadata=system/'SETUP.INF';metadata.write_bytes(b)
            (system/'KEYBOARD.DRV').write_bytes(a.keyboard.read_bytes())
            ini=b'[boot]\r\nsystem.drv=system.drv\r\nsound.drv=sound.drv\r\ncomm.drv=comm.drv\r\nkeyboard.drv=keyboard.drv\r\n[boot.description]\r\nsystem.drv=MS-DOS or PC-DOS System\r\n'
            (win/'SYSTEM.INI').write_bytes(ini)
            command=[str(a.program.resolve())]
            for action in ['CHECK','APPLY','CHECK','RESTORE']:
                check(name+' '+action,command+[action,str(win)])
                assert (win/'SYSTEM.INI').read_bytes()==ini
            assert metadata.read_bytes()==b
            check(name+' APPLY again',command+['APPLY',str(win)])
            journal=(system/'CPINFO.SAV').read_bytes()
            assert int.from_bytes(journal[138:142],'little')==zlib.crc32(b)
            patched=metadata.read_bytes();metadata.write_bytes(patched+b'; unrelated edit\r\n')
            check(name+' preserve unrelated edit',command+['RESTORE',str(win)],False)
            assert metadata.read_bytes()==patched+b'; unrelated edit\r\n'
            metadata.write_bytes(patched)
            check(name+' restore exact input',command+['RESTORE',str(win)])
            assert metadata.read_bytes()==b
            for i in range(1,4):
                env=os.environ.copy();env['CP_ALLOCFAIL']=str(i)
                check(name+' allocation refusal '+str(i),command+['CHECK',str(win)],False,env)
                assert metadata.read_bytes()==b
        report={'status':'PASS','checks':checks,'actual_private_inputs':actual,'windows_bytes_published':False}
        if a.report:a.report.write_text(json.dumps(report,indent=2),encoding='utf-8')
        print('CPSET metadata: %d checks passed; %d concrete inputs'%(len(checks),len(actual)))


if __name__=='__main__':main()
