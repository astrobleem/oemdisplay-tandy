from pathlib import Path
import tempfile,subprocess,json,os
os.environ.setdefault("ASAN_OPTIONS","detect_leaks=0")
P=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory() as tmp:
 q=Path(tmp);(q/'dos.h').write_text('unsigned _dos_open(char*,unsigned,unsigned*); unsigned _dos_read(unsigned,void*,unsigned,unsigned*); unsigned _dos_close(unsigned);\n')
 (q/'shim.c').write_text('#include <fcntl.h>\n#include <unistd.h>\nunsigned _dos_open(char*p,unsigned m,unsigned*h){int f=open(p,m);if(f<0)return 1;*h=f;return 0;}\nunsigned _dos_read(unsigned h,void*p,unsigned n,unsigned*r){int x=read(h,p,n);if(x<0)return 1;*r=x;return 0;}\nunsigned _dos_close(unsigned h){return close(h)<0;}\n')
 exe=q/'check';subprocess.run(['cc','-std=c89','-Wall','-Wextra','-pedantic','-fsanitize=address,undefined','-I'+str(q),'-x','c',str(P/'TSCHECK.C'),str(q/'shim.c'),'-o',str(exe)],check=True)
 cases=[]
 def test(a,b,expected,label):
  (q/'a').write_bytes(a);(q/'b').write_bytes(b);r=subprocess.run([str(exe),str(q/'a'),str(q/'b')],capture_output=True);assert r.returncode==expected,(label,r.returncode,r.stderr);cases.append(label)
 for size in [0,1,2,511,512,1023,1024,1025,4096,65535,65536,68451]:
  b=bytes((i*73+21)&255 for i in range(size));test(b,b,0,'equal-'+str(size));test(b,b+b'X',1,'longer-'+str(size))
  if size:
   test(b,b[:-1],1,'shorter-'+str(size))
   for pos in sorted(set([0,size//2,size-1])):
    c=bytearray(b);c[pos]^=0x55;test(b,c,1,'different-'+str(size)+'-'+str(pos))
 for args,expected in [([],3),([str(q/'a')],3),([str(q/'missing'),str(q/'a')],2),([str(q/'a'),str(q/'missing')],2),([str(q/'a'),str(q)],2)]:
  r=subprocess.run([str(exe)]+args,capture_output=True);assert r.returncode==expected;(cases.append('error-'+str(expected)))
 (P/'HOSTTEST.JSON').write_text(json.dumps({'passed':True,'cases':len(cases),'labels':cases,'sanitizers':'ASan/UBSan','limits':'POSIX shims validate comparison and errors, not DOS ABI'},indent=2)+'\n');print('PASS',len(cases),'comparison cases')
