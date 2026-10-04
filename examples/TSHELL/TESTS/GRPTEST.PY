#!/usr/bin/env python3
"""Exercise the exact portable GRPREAD.C with read-bound checks and mutations."""
import ctypes as C
import random
import struct
import subprocess
import unittest
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = tempfile.TemporaryDirectory(prefix='tshell-grp-')
SO = Path(BUILD.name) / 'GRPTEST.SO'
subprocess.run(['gcc', '-std=c89', '-pedantic', '-Wall', '-Wextra', '-Werror',
                '-fPIC', '-shared', '-x', 'c', str(ROOT / 'GRPREAD.C'),
                '-o', str(SO)], check=True)
LIB = C.CDLL(str(SO))
READ = C.CFUNCTYPE(C.c_int, C.c_void_p, C.c_ulong,
                   C.POINTER(C.c_ubyte), C.c_uint)
class Item(C.Structure):
    _fields_ = [('name', C.c_uint), ('command', C.c_uint),
                ('commandLength', C.c_uint)]
class Group(C.Structure):
    _fields_ = [('size', C.c_uint), ('dataStart', C.c_uint),
                ('count', C.c_uint), ('slots', C.c_uint),
                ('title', C.c_char * 64), ('item', Item * 50)]
LIB.PmReadGroup.argtypes = [READ, C.c_void_p, C.c_ulong, C.POINTER(Group)]
LIB.PmReadName.argtypes = [READ, C.c_void_p, C.POINTER(Group), C.c_uint,
                          C.c_char_p, C.c_uint]
LIB.PmReadCommand.argtypes = LIB.PmReadName.argtypes
LIB.PmCommandToken.argtypes = [C.c_char_p, C.c_char_p, C.c_uint]
LIB.PmTokenKind.argtypes = [C.c_char_p]

def word(b, p): return struct.unpack_from('<H', b, p)[0]
def put(b, p, n): struct.pack_into('<H', b, p, n & 65535)
def checksum(b):
    put(b, 4, 0)
    put(b, 4, -sum(struct.unpack('<%dH' % (len(b)//2), b[:len(b)//2*2])))
    return b

def make(count=1, command=b'C:\\APPS\\APP.EXE /preview', name=b'App', title=b'Apps'):
    slots = max(16, ((count + 15)//16)*16)
    b = bytearray(34 + slots*2)
    b[:4] = b'PMCC'; put(b, 32, slots)
    put(b, 22, len(b)); b.extend(title + b'\0')
    for i in range(count):
        p = len(b); put(b, 34 + 2*i, p); b.extend(bytes(24))
        put(b, p+6, 12); put(b, p+8, 2); put(b, p+10, 2)
        for field, data in [(18, name), (20, command), (22, b'ICON.EXE')]:
            put(b, p+field, len(b)); b.extend(data + b'\0')
        put(b, p+12, len(b)); b.extend(struct.pack('<5H2B', 0, 0, 16, 1, 2, 1, 1))
        put(b, p+14, len(b)); b.extend(b'\xff\xff')
        put(b, p+16, len(b)); b.extend(b'\x00\x00')
    put(b, 6, len(b))
    return checksum(b)

class Source:
    def __init__(self, b):
        self.b = bytes(b); self.calls = []; self.invalid = []
        @READ
        def read(ctx, pos, out, n):
            self.calls.append((pos, n))
            if n > 256 or pos + n > len(self.b):
                self.invalid.append((pos, n)); return 0
            C.memmove(out, self.b[pos:pos+n], n)
            return 1
        self.read = read
    def parse(self, length=None):
        g = Group()
        status = LIB.PmReadGroup(self.read, None, len(self.b) if length is None else length, C.byref(g))
        return status, g

class Tests(unittest.TestCase):
    def parse(self, b):
        source = Source(b); status, group = source.parse()
        self.assertFalse(source.invalid)
        return status, group, source
    def test_counts(self):
        for count in [0, 1, 15, 16, 17, 18, 32, 49, 50]:
            status, g, s = self.parse(make(count))
            self.assertEqual(status, 0); self.assertEqual(g.count, count)
            self.assertEqual(g.title, b'Apps')
            self.assertLessEqual(max(n for p,n in s.calls), 256)
    def test_saved_command_exact(self):
        for cmd in [b'C:\\TANDYLAB\\CHIMES\\TEXIT.EXE /preview',
                    b'C:\\TANDYLAB\\EXPER\\CDLG\\CDSTART.EXE',
                    b'  C:\\APP\\X.EXE  /MiXeD\t"Two Words" ',
                    b'NOTEPAD.EXE']:
            st,g,s = self.parse(make(command=cmd)); self.assertEqual(st, 0)
            out = C.create_string_buffer(128)
            self.assertEqual(LIB.PmReadCommand(s.read,None,C.byref(g),0,out,128),0)
            self.assertEqual(out.value,cmd)
    def test_command_limit(self):
        for n in [1, 126, 127, 500]:
            st,g,s = self.parse(make(command=b'X'*n)); self.assertEqual(st,0)
            out=C.create_string_buffer(b'OLD',128)
            result=LIB.PmReadCommand(s.read,None,C.byref(g),0,out,128)
            self.assertEqual(result,0 if n<=126 else 7)
            self.assertEqual(out.value,b'X'*n if n<=126 else b'')
    def test_display_ellipsis(self):
        st,g,s=self.parse(make(name=b'A'*100,title=b'T'*100))
        self.assertEqual(st,0); self.assertEqual(g.title,b'T'*60+b'...')
        out=C.create_string_buffer(16)
        self.assertEqual(LIB.PmReadName(s.read,None,C.byref(g),0,out,16),0)
        self.assertEqual(out.value,b'A'*12+b'...')
    def test_checksum_signature_length(self):
        b=make(); b[0]=0; self.assertEqual(self.parse(b)[0],2)
        b=make(); b[50]^=1; self.assertEqual(self.parse(b)[0],3)
        b=make(); b+=b'\0'*6; checksum(b); self.assertEqual(self.parse(b)[0],4)
        self.assertEqual(self.parse(b'PMCC')[0],2)
        s=Source(b''); self.assertEqual(s.parse(65536)[0],2); self.assertFalse(s.calls)
    def test_bad_offsets(self):
        for pos,value in [(22,0),(22,65535),(34,65520),(34,20)]:
            b=make(); put(b,pos,value); checksum(b)
            self.assertNotEqual(self.parse(b)[0],0)
        for delta in [12,14,16,18,20,22]:
            b=make(); p=word(b,34); put(b,p+delta,65535); checksum(b)
            self.assertNotEqual(self.parse(b)[0],0)
    def test_bad_icon(self):
        b=make(); p=word(b,34); put(b,p+6,40); checksum(b)
        self.assertEqual(self.parse(b)[0],4)
        b=make(); p=word(b,34); q=word(b,p+12); put(b,q+4,0); checksum(b)
        self.assertEqual(self.parse(b)[0],2)
        b=make(); p=word(b,34); q=word(b,p+12)
        put(b,q+6,65535); put(b,q+8,65535); b[q+10]=255; checksum(b)
        self.assertEqual(self.parse(b)[0],2)
    def test_limits_and_holes(self):
        self.assertEqual(self.parse(make(51))[0],5)
        b=make(); put(b,32,65); checksum(b); self.assertEqual(self.parse(b)[0],5)
        b=make(3); put(b,36,0); checksum(b)
        st,g,s=self.parse(b); self.assertEqual(st,0); self.assertEqual(g.count,2)
    def test_unterminated_strings(self):
        b=make(); p=word(b,34); put(b,p+18,len(b)); b+=b'NONUL'; put(b,6,len(b));checksum(b)
        self.assertEqual(self.parse(b)[0],6)
        b=make(); p=word(b,34); put(b,p+20,len(b)); b+=b'NONUL'; put(b,6,len(b));checksum(b)
        self.assertEqual(self.parse(b)[0],6)
    def test_odd_checksum(self):
        b=make();
        if len(b)%2==0: b+=b'X'
        put(b,6,len(b));checksum(b)
        self.assertEqual(self.parse(b)[0],0)
        b[-1]^=42;self.assertEqual(self.parse(b)[0],0)
    def test_mutations_stay_bounded(self):
        rng=random.Random(8088); original=make(18)
        for i in range(1000):
            b=bytearray(original)
            for j in range(rng.randrange(1,6)): b[rng.randrange(len(b))]=rng.randrange(256)
            if i%2:checksum(b)
            self.parse(b)
    def test_executable_tokens(self):
        for command,expected,kind in [
            (b'C:\\A\\B.EXE /preview',b'C:\\A\\B.EXE',2),
            (b' NOTEPAD.EXE file.txt',b'NOTEPAD.EXE',1),
            (b'"C:\\A\\B.EXE" /preview',b'C:\\A\\B.EXE',2),
            (b'.\\APPS\\B.EXE',b'.\\APPS\\B.EXE',0),
            (b'C:B.EXE',b'C:B.EXE',0),
            (b'\\APPS\\B.EXE',b'\\APPS\\B.EXE',0)]:
            out=C.create_string_buffer(128)
            self.assertEqual(LIB.PmCommandToken(command,out,128),1)
            self.assertEqual(out.value,expected)
            self.assertEqual(LIB.PmTokenKind(out),kind)
        for command in [b'',b' ',b'"broken',b'"A.EXE"bad',b'A'*128]:
            out=C.create_string_buffer(128)
            self.assertEqual(LIB.PmCommandToken(command,out,128),0)

if __name__=='__main__': unittest.main(verbosity=2)
