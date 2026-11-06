"""Host checks for private fixed-default staging; not native qualification."""
from pathlib import Path
import argparse
import importlib.machinery
import os
import re
import shutil
import subprocess
import tempfile
import unittest
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
M = importlib.machinery.SourceFileLoader('fixed_default_stage_test',str(HERE/'STAGE.PY')).load_module()


class FixedDefault(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with zipfile.ZipFile(OPTIONS.baseline) as z:
            cls.baseline={n:z.read(n) for n in z.namelist()}
        cls.files=dict(cls.baseline)
        cls.files['WINXT/TANDY88.DRV']=OPTIONS.fixed.read_bytes()
        cls.files=M.payload(cls.files)
        cls.stock=OPTIONS.setup_input.read_bytes()
        cls.header=(OPTIONS.repo/'tools/DOSINST/SETFILES.H').read_text('ascii')
        cls.original=M.setup_bytes(cls.header,cls.stock)
        cls.header=M.adapt_operations(cls.header)
        cls.metadata=M.setup_bytes(cls.header,cls.stock)

    def test_default_and_opt_in_descriptors(self):
        for descriptor in (self.metadata.decode('latin1'),self.files['WINXT/OEMSETUP.INF'].decode('ascii')):
            self.assertIn('fixed = a:TANDY88.DRV',descriptor)
            self.assertIn('hpxy = a:HPXY.DRV',descriptor)
            machine=descriptor.split('"Tandy 1000 EX/HX (WindowsXT)"',1)[1].split('ebios',1)[0]
            self.assertIn('        fixed\r\n',machine)
            self.assertNotIn('        hpxy\r\n',machine)
            self.assertIn('"133,96,72"',descriptor)
            for font in ('XTESYS.FON','XTEFIX.FON','XTEOEM.FON'):
                self.assertIn('a:'+font,descriptor)

    def test_no_forced_setup_and_explicit_switches(self):
        batch=self.files['WINXT/SETUPXT.BAT'].decode('ascii')
        invocations=[s for s in batch.splitlines() if s.startswith('FIXXT INSTALL')]
        self.assertEqual(len(invocations),2)
        self.assertTrue(all('/XR1' not in s and '/320' not in s for s in invocations))
        self.assertIn('/FRESH',invocations[1])
        mode=self.files['WINXT/MODEXT.BAT'].decode('ascii')
        self.assertIn('IF "%1"=="/320" GOTO SELECT',mode)
        self.assertIn('IF "%1"=="/XR1" GOTO SELECT',mode)
        self.assertIn('FIXXT.EXE REPAIR C:\\WINDOWS C:\\WINXT %1',mode)

    def test_no_unrelated_runtime_change(self):
        allowed={'README.TXT','WINXT/SETUPXT.BAT','WINXT/MODEXT.BAT','WINXT/OEMSETUP.INF',
                 'WINXT/PROFILES.TXT','WINXT/START.TXT'}
        self.assertEqual({n for n,b in self.baseline.items() if self.files[n]!=b},allowed)
        self.assertEqual(self.files['WINXT/HPXY.DRV'],self.baseline['WINXT/HPXY.DRV'])
        self.assertEqual(set(self.files)-set(self.baseline),{'WINXT/TANDY88.DRV'})
        for n,b in self.files.items():
            if n.endswith(('.BAT','.INF','.TXT')):
                self.assertNotRegex(b,rb'(?<!\r)\n',n)

    def test_exact_stock_rejection(self):
        for bad in (self.stock[:-1],b'!'+self.stock[1:]):
            with self.assertRaises(ValueError):M.setup_bytes(self.header,bad)
        with self.assertRaises(ValueError):M.adapt_operations(self.header)

    def test_metadata_migrations_execute(self):
        if os.name=='nt' or not shutil.which('gcc'):
            self.skipTest('Linux host C compiler required for execution check')
        legacy=self.original.replace(b'a:TANDYGR.GR2',b'a:CGA.GR2')
        previous=[(self.original,zlib.crc32(self.original)),(legacy,zlib.crc32(legacy))]
        self.assertEqual([(len(b),crc) for b,crc in previous],[(49848,0x073140f6),(49840,0x0cf60179)])
        prefix='''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define SETUP_BYTES %dU
#define SETUP_OUTPUT_CRC 0x%08xUL
static unsigned char setup_bytes[SETUP_BYTES],setup_result[SETUP_BYTES];
static unsigned setup_used;
static unsigned long crc_add(unsigned long c,unsigned char *p,unsigned n){unsigned i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c>>1)^((c&1)?0xedb88320UL:0);}return c;}
static void stop(char *a,char *b){(void)a;(void)b;exit(7);}
''' % (len(self.metadata),zlib.crc32(self.metadata))
        suffix='int main(void){unsigned n=(unsigned)fread(setup_bytes,1,SETUP_BYTES,stdin);default_setup(n);return fwrite(setup_result,1,setup_used,stdout)!=setup_used;}\n'
        source=prefix+M.migration_header(previous,self.metadata)+suffix
        with tempfile.TemporaryDirectory(prefix='fixed-default-migrate-') as t:
            p=Path(t);(p/'test.c').write_text(source)
            subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            for original,_ in previous:
                result=subprocess.run([str(p/'test')],input=original,capture_output=True,check=True)
                self.assertEqual(result.stdout,self.metadata)

    def test_computer_metadata_validation_executes(self):
        if os.name=='nt' or not shutil.which('gcc'):
            self.skipTest('Linux host C compiler required for execution check')
        original=(OPTIONS.repo/'tools/UPAN/CPSET.C').read_text('ascii')
        adapted=M.computer_source(original,self.metadata)
        body=adapted[adapted.index('static U32 current_metadata_crc(void)'):adapted.index('static void join(')]
        prefix='''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
typedef uint32_t U32;
static unsigned char orig[60001];static unsigned on;
static void die(char *s){(void)s;exit(7);}
static unsigned locate(const char *s){char *p=strstr((char*)orig,s);if(!p||strstr(p+1,s))die("structure");return (unsigned)(p-(char*)orig);}
'''
        suffix='int main(void){on=(unsigned)fread(orig,1,60000,stdin);orig[on]=0;source();return 0;}\n'
        with tempfile.TemporaryDirectory(prefix='fixed-default-computer-') as t:
            p=Path(t);(p/'test.c').write_text(prefix+body+suffix)
            subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Wno-unused-variable',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            for data in (self.metadata,self.original,self.original.replace(b'a:TANDYGR.GR2',b'a:CGA.GR2')):
                self.assertEqual(subprocess.run([str(p/'test')],input=data,capture_output=True).returncode,0)
                damaged=bytearray(data);damaged[100]^=1
                self.assertEqual(subprocess.run([str(p/'test')],input=damaged,capture_output=True).returncode,7)

    def test_native_staging_inventory(self):
        staging=importlib.machinery.SourceFileLoader('fixed_default_native_test',str(OPTIONS.repo/'tools/PAN/PREPARE.PY')).load_module()
        with tempfile.TemporaryDirectory(prefix='fixed-default-native-test-') as t:
            native=Path(t)/'native';compile_native=staging.N.compile_native
            staging.N.compile_native=lambda *args,**kwargs:b''
            try:staging.stage(native,{n:self.files['WINXT/'+n] for n in M.APP},None)
            finally:staging.N.compile_native=compile_native
            M.write(native/'SETFILES.H',self.header)
            source=M.adapt_finisher((native/'FIXXT.C').read_text('ascii'),self.files,len(self.metadata))
            names=re.findall(r'"([A-Z0-9.]+)"',re.search(r'static const char \*names\[\]=\{(.*?)\};',source)[1])
            sizes=re.search(r'static unsigned long sizes\[\]=\{(.*?)\};',source)[1].split(',')
            targets=re.search(r'static int target\[\]=\{(.*?)\};',source)[1].split(',')
            self.assertEqual(len(names),48);self.assertEqual(len(sizes),48);self.assertEqual(len(targets),48)
            self.assertIn('!pinned_file(p,FIXED_BYTES,FIXED_CRC)',source)
            self.assertIn('#define FIXED_BYTES 58864UL',source)
            self.assertIn('mode==KEEP_DISPLAY&&stricmp(names[i],"SETUP.INF")',source)
            self.assertNotIn('return !stricmp(leaf,"XTPAN.EXE")||!stricmp(leaf,"XYCTL.EXE")',source)
            self.assertEqual(M.aliases(native,self.files,self.metadata),(407,118))
            recipe=(native/'SETFILES.H').read_text('ascii')
            rows=re.findall(r'\{"([^"\n]+)","([^"\n]+)",(\d+)UL,([0-4])\}',recipe)
            self.assertEqual(len(rows),len(set(n for n,_,_,_ in rows)))
            for name in ('TANDY88.DRV','XTESYS.FON','XTEFIX.FON','XTEOEM.FON'):
                self.assertTrue(any(n=='WINXT\\\\FILES\\\\'+name for n,_,_,_ in rows),name)
            pins=(native/'SETPINS.H').read_text('ascii')
            pinned={n:int(size) for n,size in re.findall(r'\{"([^"\n]+)","[0-9a-f]{64}",(\d+)UL,0,0x[0-9a-f]+UL\}',pins)}
            for _,source,size,kind in rows:
                if kind=='0':self.assertEqual(pinned[source],int(size),source)
            M.aliases_existing(native,'CPSET.EXE',b'compiled computer helper')
            M.aliases_existing(native,'FIXXT.EXE',b'compiled finisher')
            for name in ('SETPINS.H','SETFILES.H','SETINPUT.H','SETUP.C'):
                self.assertNotRegex((native/name).read_bytes(),rb'(?<!\r)\n',name)

    def test_live_selection_profile_executes(self):
        if os.name=='nt' or not shutil.which('gcc'):
            self.skipTest('Linux host C compiler required for execution check')
        source=(OPTIONS.repo/'tools/DOSINST/FIXXT.C').read_text('ascii')
        source=M.profile_source(source)
        function=source[source.index('static int profile(void)'):source.index('static void not_windows(void)')]
        prefix='''#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#define stricmp strcasecmp
#define PTH 200
#define KEEP_XRSYNC 4
#define FIXED_320 5
#define KEEP_DISPLAY 6
static char sys[100]="SYSTEM",*selected;static int forced=-1,exists=1;
static int inivalue(char *key,char *v){(void)key;strcpy(v,selected);return *v?1:0;}
static void trim(char *v){char *p=v,*e;while(isspace((unsigned char)*p))p++;memmove(v,p,strlen(p)+1);e=v+strlen(v);while(e>v&&isspace((unsigned char)e[-1]))*--e=0;}
static void path(char *v,char *s,char *n){sprintf(v,"%s/%s",s,n);}
static int kind(char *v){(void)v;return exists;}
static void stop(char *a,char *b){(void)a;(void)b;exit(7);}
'''
        suffix='int main(int argc,char **argv){selected=argv[1];if(argc>2)forced=atoi(argv[2]);if(argc>3)exists=atoi(argv[3]);printf("%d",profile());return 0;}\n'
        with tempfile.TemporaryDirectory(prefix='fixed-default-profile-') as t:
            p=Path(t);(p/'test.c').write_text(prefix+function+suffix)
            subprocess.run(['gcc','-std=c89','-Wall','-Wextra','-Werror',str(p/'test.c'),'-o',str(p/'test')],check=True,capture_output=True)
            cases=[(['TANDY88.DRV'],5),([' HPXY.DRV ; chosen by Setup'],3),(['CGA.DRV'],6),
                   (['FOREIGN.DRV'],6),(['C23216.DRV'],6),(['XRSYNC.DRV'],4),
                   (['HPXY.DRV','5'],5),(['TANDY88.DRV','3'],3),(['XRSYNC.DRV','5'],4)]
            for args,want in cases:
                result=subprocess.run([str(p/'test')]+args,capture_output=True,check=True)
                self.assertEqual(int(result.stdout),want,args)
            self.assertEqual(subprocess.run([str(p/'test'),'XRSYNC.DRV','5','0'],capture_output=True).returncode,7)
            for bad in ('','  ',' ; no selection'):
                self.assertEqual(subprocess.run([str(p/'test'),bad],capture_output=True).returncode,7)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=M.ROOT)
    for name in ('baseline','fixed','setup-input'):
        parser.add_argument('--'+name,type=Path,required=True)
    OPTIONS,remaining=parser.parse_known_args()
    unittest.main(argv=[__file__]+remaining)
