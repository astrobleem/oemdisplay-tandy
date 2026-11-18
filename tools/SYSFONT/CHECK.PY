"""Verify candidate bitmap bounds, unchanged metrics and approved PR219 ink."""
import importlib.machinery as M
from pathlib import Path
import struct
import tempfile
B=M.SourceFileLoader('sysfont_builder',str(Path(__file__).with_name('BUILD.PY'))).load_module()

def check():
    for name in ('CG1SYS.FON','CG2SYS.FON','XTCSYS.FON','XTESYS.FON'):
        before=B.source(name);after=B.improve(name,before)
        a,base=B.strike(before);b,newbase=B.strike(after)
        assert base==newbase and len(before)==len(after)
        assert B.I.resources(before)==B.I.resources(after)
        h=B.I.fontinfo(a)
        end=118+4*(h['last']-h['first']+2)
        assert a[:end]==b[:end], 'Header/advance/offset changed'
        allowed=set()
        for code in range(h['first'],h['last']+1):
            w,off=struct.unpack_from('<HH',a,118+4*(code-h['first']))
            if 33<=code<=126:
                allowed.update(range(base+off,base+off+((w+7)//8)*h['height']))
            else:assert B.bitmap(a,code)==B.bitmap(b,code)
        changed={i for i,(x,y) in enumerate(zip(before,after)) if x!=y}
        assert changed and changed<=allowed
        for c in 'MWIJCES' if name=='XTCSYS.FON' else '':
            assert B.bitmap(a,ord(c))==B.bitmap(b,ord(c))
        # Counter and outline distinctions matter at the compact sizes.
        if h['height'] in (5,6):
            assert B.bitmap(b,ord('0'))!=B.bitmap(b,ord('O'))
            assert B.bitmap(b,ord('0'))!=B.bitmap(b,ord('8'))
            assert B.bitmap(b,ord('8'))!=B.bitmap(b,ord('B'))
        # Windows 3.0's dialog-unit helper samples a..y, A..Z and one
        # unwritten byte. Preserve the result for every possible tail.
        sample='abcdefghijklmnopqrstuvwxyABCDEFGHIJKLMNOPQRSTUVWXYZ'
        widths=lambda raw:[len(B.bitmap(raw,c)[0]) for c in range(32,256)]
        assert widths(a)==widths(b)
        units={ (sum(len(B.bitmap(b,ord(c))[0]) for c in sample)+w)//52 for w in widths(b)}
        print('PASS',name,'height',h['height'],'all 224 widths exact; dialog units',sorted(units),'changed bytes',len(changed))
    with tempfile.TemporaryDirectory() as d:
        out=Path(d)/'fonts';B.build(out)
        assert sorted(p.name for p in out.iterdir())==['CG1SYS.FON','CG2SYS.FON','XTCSYS.FON','XTESYS.FON']
        try:B.build(out)
        except FileExistsError:pass
        else:raise AssertionError('Output overwrite accepted')

if __name__=='__main__':check()
