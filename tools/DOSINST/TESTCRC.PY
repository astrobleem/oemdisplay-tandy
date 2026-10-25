"""Compare the native CRC header with zlib, using the mandatory Windows GCC launcher."""
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile
import zlib

HERE = Path(__file__).resolve().parent
SOURCE = r'''#include <stdio.h>
typedef unsigned long U32;
typedef char u32_must_be_four_bytes[sizeof(U32)==4?1:-1];
#include "CRCFAST.H"
int main(int argc,char **argv){
 FILE *f;unsigned char b[4096];unsigned n;U32 c=0xffffffffUL;
 if(argc!=2||(f=fopen(argv[1],"rb"))==NULL)return 2;
 while((n=(unsigned)fread(b,1,sizeof(b),f))!=0)c=fast_crc(c,b,n);
 if(ferror(f)||fclose(f))return 3;
 printf("%08lx\n",c^0xffffffffUL);return 0;
}
'''

def main():
    with tempfile.TemporaryDirectory(prefix='xr-crc-') as tmp:
        root = Path(tmp).resolve()
        assert root.is_relative_to(Path(tempfile.gettempdir()).resolve())
        source = root / 'crc.c'
        source.write_text(SOURCE, encoding='ascii')
        exe = root / ('crc.exe' if os.name == 'nt' else 'crc')
        if os.name == 'nt':
            wrapper = Path.home() / 'Documents/Codex/toolchains/gcc-ucrt64.py'
            command = [sys.executable, str(wrapper), '--']
        else:
            command = [os.environ.get('CC', 'cc')]
            # LP64 hosts need the same 32-bit width as DOS U32.
            source.write_text(SOURCE.replace('typedef unsigned long U32;', '#include <stdint.h>\ntypedef uint32_t U32;').replace('c^0xffffffffUL);', '(unsigned long)(c^0xffffffffUL));'), encoding='ascii')
        subprocess.run(command + ['-x', 'c', '-std=c89', '-Wall', '-Wextra', '-Werror', '-O2', '-I', str(HERE), '-o', str(exe), str(source)], check=True)
        env = os.environ.copy()
        if os.name == 'nt':
            env['PATH'] = r'C:\msys64\ucrt64\bin' + os.pathsep + env.get('PATH', '')
        randomizer = random.Random(0x8088)
        sizes = [0, 1, 2, 7, 8, 15, 16, 255, 256, 257, 4095, 4096, 4097, 32768, 65535]
        vectors = [b'123456789', bytes(range(256)) * 32]
        vectors += [bytes(randomizer.randrange(256) for _ in range(n)) for n in sizes]
        for body in vectors:
            path = root / 'input.bin'
            path.write_bytes(body)
            got = subprocess.check_output([str(exe), str(path)], env=env, text=True).strip()
            assert int(got, 16) == zlib.crc32(body), (len(body), got)
        print(json.dumps({'status': 'PASS', 'vectors': len(vectors), 'bytes': sum(map(len, vectors)), 'oracle': 'zlib.crc32', 'header': 'CRCFAST.H'}))

if __name__ == '__main__':
    main()
