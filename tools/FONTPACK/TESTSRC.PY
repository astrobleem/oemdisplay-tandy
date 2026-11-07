"""Host-only font-release source/inventory checks; not Windows GUI qualification."""
from pathlib import Path
import ast,importlib.machinery,re,shutil,subprocess,tempfile,unittest,zlib
HERE=Path(__file__).resolve().parent
M=importlib.machinery.SourceFileLoader('font_release_stage',str(HERE/'PREPARE.PY')).load_module()
class FontRelease(unittest.TestCase):
 def test_exact_scope_and_font_notices(self):
  old=M.baseline();body=M.payload()
  self.assertEqual({n for n in old if old[n]!=body[n]},{'README.TXT','WINXT/DISPLAY.TXT','WINXT/XTCSYS.FON'})
  self.assertEqual(set(body)-set(old),{'WINXT/FONTS/'+n for n in (*M.FONTS,'README.TXT','LICENSE.TXT','FONTLIC.TXT')})
  for n in (*M.FONTS,'LICENSE.TXT','FONTLIC.TXT'):self.assertEqual(body['WINXT/FONTS/'+n],(M.ROOT/'tools/PROPFONT/BIN'/n).read_bytes())
  for n in ('XTCFIX.FON','XTCOEM.FON','XTESYS.FON','XTEFIX.FON','XTEOEM.FON'):self.assertEqual(body['WINXT/'+n],old['WINXT/'+n])
 def test_native_inventories_and_idempotent_binding(self):
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'stage';M.stage(out);native=out/'native';body=M.payload()
   before={p.name:p.read_bytes() for p in native.iterdir()};M.bind_headers(native,body)
   self.assertEqual(before,{p.name:p.read_bytes() for p in native.iterdir()})
   M.bind_headers(native,dict(reversed(list(body.items()))))
   self.assertEqual(before,{p.name:p.read_bytes() for p in native.iterdir()},'Binding depends on filesystem enumeration order')
   text=(native/'SETPINS.H').read_text();rows=re.findall(r'^\{"((?:[^"\\]|\\.)+)","([a-f0-9]{64})",(\d+)UL,0,0x([a-f0-9]+)UL\}',text,re.M)
   self.assertEqual(len(rows),len(body)-2)
   for name,sha,size,crc in rows:
    n=ast.literal_eval('"'+name+'"').replace('\\','/');b=body['WINXT/'+n]
    self.assertEqual((sha,int(size),int(crc,16)),(M.hashlib.sha256(b).hexdigest(),len(b),zlib.crc32(b)))
   files=(native/'SETFILES.H').read_text();rows=re.findall(r'^\{"((?:[^"\\]|\\.)+)","((?:[^"\\]|\\.)+)",(\d+)UL,(\d+)\}',files,re.M)
   crcs=re.findall(r'^\s*0x[a-f0-9]+UL,',(native/'SETINPUT.H').read_text(),re.M)
   self.assertEqual(len(rows),433);self.assertEqual(len(crcs),433)
   self.assertEqual(sum(not a.startswith('W30\\\\') for a,b,c,d in rows),140)
   optional=[row for row in rows if row[0].startswith('WINXT\\\\FONTS\\\\')]
   self.assertEqual(len(optional),12)
   for dest,name,size,kind in optional:
    d=ast.literal_eval('"'+dest+'"').replace('\\','/');n=ast.literal_eval('"'+name+'"').replace('\\','/')
    self.assertEqual(d,'WINXT/'+n);self.assertEqual(int(size),len(body[d]));self.assertEqual(kind,'0')
 def test_native_source_contracts(self):
  native=HERE/'NATIVE';s=(native/'FIXXT.C').read_text();p=(native/'XRPREP.C').read_text()
  self.assertIn('font=font_selected(names[i],mode);',s)
  self.assertLess(s.index('font=font_selected(names[i],mode);'),s.index('if((mode==KEEP_XRSYNC||(mode==KEEP_DISPLAY&&stricmp(names[i]'))
  self.assertIn('if(forced>=0){changeini("boot","fonts.fon"',s)
  self.assertNotIn('changeini("fonts"',s)
  self.assertIn('Different optional font file preserved.',p)
  self.assertIn('parents_check(to);',p)
  for message in ('Staged font readback failed','Committed font readback failed','Ambiguous committed font; original retained'):self.assertIn(message,s)
  ids=(native/'FONTID.H').read_text()
  old=M.baseline()['WINXT/XTCSYS.FON'];new=M.payload()['WINXT/XTCSYS.FON']
  self.assertIn('{"XTCSYS.FON",4592UL,0x%08xUL,0x%08xUL,0xbe8c12adUL}'%(zlib.crc32(new),zlib.crc32(old)),ids)
 def test_real_font_selector_c89(self):
  source=(HERE/'NATIVE/FIXXT.C').read_text();a=source.index('static int font_selected(');b=source.index('static void checkfont(',a)
  prefix=r'''
#include <stdio.h>
#include <string.h>
#include <strings.h>
#include <ctype.h>
#include <stdlib.h>
#define stricmp strcasecmp
#define KEEP_XRSYNC 4
#define FIXED_320 5
#define KEEP_DISPLAY 6
#include "FONTID.H"
static int forced=-1;
static const char *display="HPXY.DRV",*system_font="XTCSYS.FON",*fixed_font="XTCFIX.FON",*oem_font="XTCOEM.FON";
static int inivalue(const char *key,char *v){strcpy(v,!strcmp(key,"display.drv")?display:!strcmp(key,"fonts.fon")?system_font:!strcmp(key,"fixedfon.fon")?fixed_font:oem_font);return 1;}
static void trim(char *s){char *p=s;size_t n;while(*p==' '||*p=='\t')p++;if(p!=s)memmove(s,p,strlen(p)+1);n=strlen(s);while(n&&isspace((unsigned char)s[n-1]))s[--n]=0;}
static void expect(int actual,int wanted){if(actual!=wanted){fprintf(stderr,"selector got %d wanted %d\n",actual,wanted);exit(1);}}
'''
  main=r'''
int main(void){unsigned i;const char *modes[]={"TNDY6404.DRV","TNDY3204.DRV","TNDY160.DRV","TNDY6402.DRV"};
 expect(font_selected("XTCSYS.FON",3),1);expect(font_selected("XTESYS.FON",3),0);
 system_font="custom.fon";expect(font_selected("XTCSYS.FON",3),0);
 system_font="C:\\WINDOWS\\SYSTEM\\XTCSYS.FON";expect(font_selected("XTCSYS.FON",3),0);
 system_font=" xtcsys.fon ; comment";expect(font_selected("XTCSYS.FON",3),1);
 for(i=0;i<4;i++){display=modes[i];expect(font_selected("XTCSYS.FON",KEEP_DISPLAY),1);expect(font_selected("XTCFIX.FON",KEEP_DISPLAY),0);}
 display="CGA.DRV";expect(font_selected("XTCSYS.FON",KEEP_DISPLAY),0);
 expect(font_selected("XTCSYS.FON",KEEP_XRSYNC),0);
 system_font="XTESYS.FON";expect(font_selected("XTCSYS.FON",FIXED_320),0);expect(font_selected("XTESYS.FON",FIXED_320),1);
 forced=FIXED_320;expect(font_selected("XTESYS.FON",FIXED_320),1);expect(font_selected("XTEFIX.FON",FIXED_320),1);expect(font_selected("XTEOEM.FON",FIXED_320),1);
 expect(font_selected("XTCSYS.FON",FIXED_320),0);puts("PASS: actual C89 font selector");return 0;}
'''
  with tempfile.TemporaryDirectory() as tmp:
   tmp=Path(tmp);shutil.copyfile(HERE/'NATIVE/FONTID.H',tmp/'FONTID.H');(tmp/'selector.c').write_text(prefix+source[a:b]+main)
   subprocess.run(['cc','-std=c89','-Wall','-Wextra','-Werror',str(tmp/'selector.c'),'-o',str(tmp/'selector')],check=True)
   subprocess.run([str(tmp/'selector')],check=True)
if __name__=='__main__':unittest.main()
