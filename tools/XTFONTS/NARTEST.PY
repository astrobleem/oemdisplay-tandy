"""Check the XTCSYS M/W correction without writing reports or manifests."""
import argparse
import importlib.machinery
from pathlib import Path
import struct

HERE=Path(__file__).resolve().parent
N=importlib.machinery.SourceFileLoader('narrow_font',str(HERE/'NARROW.PY')).load_module()


def raw(data):
    offset=next(e[3] for e in N.I.resources(data)[1] if e[0]==0x8008)
    return data[offset:offset+N.I.dword(data,offset+2)],offset


def glyph(data,code):
    code=code if data[95]<=code<=data[96] else data[95]+data[97]
    width,offset=struct.unpack_from('<HH',data,118+(code-data[95])*4)
    return [[(data[offset+(x//8)*8+y]>>(7-x%8))&1 for x in range(width)] for y in range(8)]


def test(original,corrected):
    old=original.read_bytes();new=corrected.read_bytes()
    assert len(new)==len(old)==4592
    assert N.narrow(old)==new,'Correction is not reproducible'
    before,base=raw(old);after,newbase=raw(new)
    assert newbase==base and before[:118]==after[:118],'System metadata changed'
    allowed=set()
    for char in 'MW':
        at=118+(ord(char)-32)*4
        _,off=struct.unpack_from('<HH',before,at)
        allowed.update(range(base+at,base+at+2))
        allowed.update(range(base+off,base+off+16))
    actual={i for i,(a,b) in enumerate(zip(old,new)) if a!=b}
    assert actual and actual<=allowed,'Unrelated font byte changed'
    for code in range(256):
        a,b=glyph(before,code),glyph(after,code)
        if code not in (77,87):
            assert a==b,code
        else:
            assert len(b[0])==9
            assert all(row[0]==row[-1]==0 for row in b)
            assert [''.join('#' if p else '.' for p in row[1:8]) for row in b]==N.G[chr(code)]
    letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    assert sum(len(glyph(after,ord(c))[0]) for c in letters) == 414
    broken = bytearray(old)
    at = base+118+(ord('M')-32)*4
    _,offset = struct.unpack_from('<HH',broken,at)
    broken[base+offset] ^= 1
    try:
        N.narrow(bytes(broken))
    except ValueError:
        pass
    else:
        raise AssertionError('Edited M bitmap was accepted')
    for text in ['Windows XT','WM','MMMM WWWW','File Edit View Help','Cancel']:
        a=sum(len(glyph(before,ord(c))[0]) for c in text)
        b=sum(len(glyph(after,ord(c))[0]) for c in text)
        assert a-b==text.count('M')*3+text.count('W')*5
        print('%s: %d -> %d pixels' % (text,a,b))
    print('PASS: only M/W advance and bitmap bytes changed; all 254 other bytes render identically; all System metadata retained.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--original',type=Path,default=HERE.parents[1]/'distributions/WINXT/XTCSYS.FON')
    p.add_argument('--corrected',type=Path,required=True)
    a=p.parse_args();test(a.original,a.corrected)
