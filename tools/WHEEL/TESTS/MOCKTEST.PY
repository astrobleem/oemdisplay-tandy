"""Host-only safety checks. Hardware calls are mocked; no real port access."""
from pathlib import Path
import os, subprocess, tempfile
root = Path(__file__).resolve().parent
source = (root.parent/'SOURCE'/'WHEEL.C').read_text()
source = source.replace('#include <dos.h>\n#include <bios.h>\n#include <conio.h>', '#include "MOCK.H"')
source = source.replace('#define MK_FP(s,o) ((void far *)(((unsigned long)(s)<<16)|(unsigned)(o)))', '#define MK_FP(s,o) mock_fp(s,o)')
source = source.replace('int main(int argc,char **argv)', 'int guest_main(int argc,char **argv)')
source += '''
int main(int argc,char **argv) { int r; char *args[]={"WHEEL","/RAW1"};
 if(argc!=2)return 9;scenario=argv[1];*(unsigned *)biosarea=0x3f8;
 if(!strcmp(scenario,"missing"))*(unsigned *)biosarea=0;
 if(!strcmp(scenario,"active"))ier=1;
 if(!strcmp(scenario,"dlab"))lcr=0x83;
 r=guest_main(2,args);
 if(!strcmp(scenario,"capture")||!strcmp(scenario,"escape")){
  if(r||writes!=11||lcr!=3||mcr||ier||dll!=12||dlh||clockticks>370)return 10;
 }else if(writes)return 11;
 printf("MOCK PASS %s (writes=%u, ticks=%u)\\n",scenario,writes,clockticks);return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp);p.joinpath('WHEELM.C').write_text(source)
    p.joinpath('MOCK.H').write_bytes(root.joinpath('MOCK.H').read_bytes())
    subprocess.run(['gcc','-x','c','-std=c89','-Wall','-Wextra','-Wno-unused-variable','-Wno-misleading-indentation','-fsanitize=address,undefined','-g',str(p/'WHEELM.C'),'-o',str(p/'test')],check=True)
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0')
    for scenario in ('resident','missing','active','cancel','changed','txbusy','dlab','escape','capture'):
        r=subprocess.run([str(p/'test'),scenario],env=env,text=True,capture_output=True)
        if r.returncode:raise RuntimeError(scenario+': '+r.stdout+'\n'+r.stderr)
        print(r.stdout.strip().splitlines()[-1])
