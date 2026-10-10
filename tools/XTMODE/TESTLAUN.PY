"""Compile real TINST batch emitter and wave patcher with host I/O shims."""
from pathlib import Path
import json,subprocess,os,argparse,hashlib
HERE=Path(__file__).resolve().parent;REPO=HERE.parent.parent
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);ap.add_argument('--gcc',type=Path,required=True);a=ap.parse_args();out=a.out.resolve();out.mkdir(parents=True,exist_ok=False);env=os.environ.copy();env['PATH']=str(a.gcc.parent)+';'+env['PATH']
 t=(REPO/'src/tandysw/TINST.C').read_text('ascii');emit=t[t.index('static void makefiles(void)'):t.index('int main(')]
 wave=(REPO/'examples/WXTSPL/UPDATER/WAVEXT.C').read_text('ascii');patch=wave[wave.index('static void patch_mode('):wave.index('static void patch(',wave.index('static void patch_mode('))]
 prefix=r'''
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#define PTH 80
#define MAXBAT 8192
#define HELP src
#define P_WAIT 0
static char src[PTH],win[PTH],bak[PTH],buf[MAXBAT];
static struct {char src[PTH],rel[24];unsigned long size;} files[2];
static int count,deep_verify,computer_changed,used;
static FILE *handles[16];
static char original[2][MAXBAT],replacement[2][MAXBAT],home[PTH],oldhash[2][65],newhash[2][65];
static void hashtext(const char *s,char *h){(void)s;strcpy(h,"hash shim; patch text tested separately");}
static void fail(const char *m,const char *d){fprintf(stderr,"%s: %s\n",m,d?d:"");exit(2);}
static void join(char *p,const char *d,const char *n){if(strlen(d)+strlen(n)+2>PTH)fail("Path overflow",d);strcpy(p,d);strcat(p,"\\");strcat(p,n);}
static int newtext(const char *p){const char *n=strrchr(p,'\\');if(++used>=16)fail("handles",p);handles[used]=fopen(n?n+1:p,"wb");if(!handles[used])fail("open",p);return used;}
static void put(int h,const char *s){if(fputs(s,handles[h])<0)fail("write",s);}
static void closeout(int h){if(fclose(handles[h]))fail("close","");}
static int mockrename(const char *a,const char *b){(void)a;(void)b;return 0;}
static int spawnl(int wait,const char *p,...){(void)wait;(void)p;return 0;}
static int testsprintf(char *p,const char *fmt,...){int n;va_list args;va_start(args,fmt);n=vsnprintf(p,512,fmt,args);va_end(args);if(n<0||n>=512)fail("512-byte emitter buffer exceeded",fmt);return n;}
#define rename mockrename
#define sprintf testsprintf
'''
 # The emitter calls the native helpers through spawnl. The shim only emits
 # files; it does not execute those helpers, modify OS media, or launch guests.
 suffix=r'''
int main(int argc,char **argv){FILE *f;size_t n;if(argc<2)return 2;strcpy(src,argv[1]);strcpy(win,"C:\\WINDOWS");strcpy(bak,"C:\\WINXT\\BACKUP\\B001");makefiles();
 strcpy(home,src);f=fopen("WINXT.BAT","rb");if(!f)return 2;n=fread(buf,1,sizeof(buf)-1,f);fclose(f);buf[n]=0;strcpy(original[0],buf);patch_mode(0,1);f=fopen("WAVEWIN.BAT","wb");fputs(replacement[0],f);fclose(f);return 0;}
'''
 code=prefix+emit+'\n#undef sprintf\n'+patch.replace('fail(', 'wavefail(')+suffix
 code=code.replace('\nstatic void patch_mode(', '\nstatic void wavefail(const char *m){fail(m,"");}\nstatic void patch_mode(')
 (out/'EMITTER.C').write_bytes(code.replace('\n','\r\n').encode());exe=out/'EMITTER.EXE'
 r=subprocess.run([str(a.gcc),'-x','c','-std=c89','-pedantic','-Wall','-Wextra','-Werror','-o',str(exe),str(out/'EMITTER.C')],env=env,capture_output=True,text=True);(out/'BUILD.LOG').write_text(r.stdout+r.stderr);assert r.returncode==0,r.stderr
 reports=[]
 for name,source in [('NORMAL',r'C:\WINXT'),('LONG',r'C:\ABCDEFGH\ABCDEFGH\ABCDEFGH\ABCDEFGH\ABCDEFGH\ABCDEFGH')]:
  d=out/name;d.mkdir();r=subprocess.run([str(exe),source],cwd=d,env=env,capture_output=True,text=True);assert r.returncode==0,r.stderr
  bat=(d/'WINXT.BAT').read_text('ascii');wavebat=(d/'WAVEWIN.BAT').read_text('ascii');restore=(d/'RESTORE.BAT').read_text('ascii');mode=(d/'MODES.BAT').read_text('ascii')
  pos=[bat.index('SHELLSEL.EXE RECOVER'),bat.index('XTMODE.EXE RECOVER'),bat.index('XTMODE.EXE GUARD'),bat.index('\\RESERVE.COM\n'),bat.index('\\WIN.COM /R')];assert pos==sorted(pos),pos
  assert 'XTMODE.EXE ACCEPT' in bat and 'XTMODE.EXE FORGET' in restore
  assert 'XTMODE.EXE INSTALL' in mode and 'XTMODE.EXE MENU' in mode and 'XTMODE.EXE SET' in mode
  assert wavebat[:wavebat.index('IF NOT EXIST '+source+'\\WAVE.RDY')]==bat[:bat.index('C:\\WINDOWS\\WIN.COM /R')]
  assert source+'\\WAVEXT.EXE START' in wavebat and 'C:\\WINDOWS\\XTCLEAN.COM' in wavebat and ':XWPLAIN\nC:\\WINDOWS\\WIN.COM /R' in wavebat
  reports.append({'source_path':source,'generated_bytes':len(bat),'patched_bytes':len(wavebat),'real_emitter_and_wave_patcher':True,'recovery_before_reservation_before_launch':True,'accepted_wave_and_static_routes_preserved':True})
 start=(REPO/'distributions/WINXT/TSTART.BAT').read_text('ascii');assert start.index('XTMODE.EXE RECOVER')<start.index('XTMODE.EXE GUARD')<start.index('%TSRSV%\n')<start.index('SHELLSEL.EXE SELECT')<start.index('WIN.COM /R')
 report={'host_only':True,'qualified':False,'cases':reports,'TSTART_guard_order':True,'source_sha256':{str(p.relative_to(REPO)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (REPO/'src/tandysw/TINST.C',REPO/'distributions/WINXT/TSTART.BAT',REPO/'examples/WXTSPL/UPDATER/WAVEXT.C')}};(out/'RESULTS.JSN').write_bytes(json.dumps(report,indent=2).replace('\n','\r\n').encode());print(json.dumps(report,indent=2))
if __name__=='__main__':main()
