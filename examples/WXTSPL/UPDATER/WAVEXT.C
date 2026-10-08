/* Original independent wave updater, C89 / DOS 3.3+ / 8086.
 * Never writes WIN.COM, drivers, fonts, INIs, OS or boot configuration.
 * No unlink: recognized rollback/stage files remain available for recovery.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#ifdef HOST_WIN
#include <windows.h>
#include <io.h>
#include <direct.h>
typedef unsigned long U32;
#elif defined(HOST_TEST)
#include <stdint.h>
#include <unistd.h>
#include <strings.h>
#define stricmp strcasecmp
#define strnicmp strncasecmp
#define S_IREAD S_IRUSR
#define S_IWRITE S_IWUSR
typedef uint32_t U32;
#else
#include <dos.h>
#include <io.h>
#include <direct.h>
typedef unsigned long U32;
#endif
#ifndef O_BINARY
#define O_BINARY 0
#endif
#ifdef HOST_TEST
#define PTH 512
#else
#define PTH 80
#endif
#if defined(HOST_TEST) && !defined(HOST_WIN)
#define SEP "/"
#else
#define SEP "\\"
#endif
#include "SHA256.H"
#define MAXBAT 8192
static const char logo_sha[]="8b2fc40b8c6cc3a231686f8c1337943450a1a976a5fc47dd02ed8859cbe72b2c";
static const char clean_sha[]="be8daca3153969921238b04307cdb4f75698086d12f74a024e4c198e95ce43ad";
static const char cnf_sha[]="371bd1935f84505d61873f1e08a17b858d667a5149d71995d4285c6f17782bdb";
static const char com_sha[]="d144918d757536b625b8ce04dc9b543ffd5592989d1d49855d4f832218e5fc5b";
static const char marker[]="Windows XT wave 01; qualified Color only; Mono/static\r\n";
static char win[PTH],home[PTH],txn[PTH],p[PTH],q[PTH],z[PTH];
static char original[2][MAXBAT],replacement[2][MAXBAT];
static char oldhash[2][65],newhash[2][65];
static char metadata[MAXBAT];
static const char *bat[2]={"WINXT.BAT","TSTART.BAT"};
static const char *saved[2]={"WINXT.BAK","TSTART.BAK"};
static const char *fresh[2]={"WINXT.NEW","TSTART.NEW"};
static const char *prior[2]={"WINXT.WVO","TSTART.WVO"};
static const char *next[2]={"WINXT.WVN","TSTART.WVN"};
static int have_shell;
static void fail(const char *s){printf("REFUSED/INCOMPLETE: %s\nPreserve WAVE01 and every sidecar. No Windows/Setup started.\n",s);exit(2);}
static void checkpoint(const char *s){
#ifdef HOST_TEST
 const char *v=getenv("WAVE_STOP");if(v&&!strcmp(v,s)){printf("TEST INTERRUPTION: %s\n",s);exit(99);}
#else
 s=s;
#endif
}
static void join(char *out,const char *a,const char *b){if(strlen(a)+strlen(b)+2>=PTH)fail("Path too long");sprintf(out,"%s%s%s",a,SEP,b);}
/* 0 absent; 1 regular; 2 directory; -1 inaccessible/link/device. */
static int kind(const char *s){struct stat st;
#ifdef HOST_WIN
 DWORD a=GetFileAttributesA(s);if(a==INVALID_FILE_ATTRIBUTES){if(GetLastError()==ERROR_FILE_NOT_FOUND||GetLastError()==ERROR_PATH_NOT_FOUND)return 0;return -1;}
 if(a&FILE_ATTRIBUTE_REPARSE_POINT)return -1;
#endif
#if defined(HOST_TEST) && !defined(HOST_WIN)
 if(lstat(s,&st))return errno==ENOENT?0:-1;
 if(S_ISLNK(st.st_mode))return -1;
 if(S_ISDIR(st.st_mode))return 2;return S_ISREG(st.st_mode)?1:-1;
#else
 if(stat(s,&st))return errno==ENOENT?0:-1;
 if(st.st_mode&S_IFDIR)return 2;return (st.st_mode&S_IFREG)?1:-1;
#endif
}
static int digest(const char *s,char *h,long *len){FILE *f;unsigned char b[512];unsigned n;SHA a;int k=kind(s);
 if(!k)return 0;if(k!=1)return -1;f=fopen(s,"rb");if(!f)return -1;init(&a);*len=0;
 while((n=(unsigned)fread(b,1,sizeof(b),f))!=0){*len+=n;if(*len>1048576L){fclose(f);return -1;}update(&a,b,n);}
 if(ferror(f)){fclose(f);return -1;}if(fclose(f))return -1;finish(&a,h);return 1;
}
static void hashtext(const char *s,char *h){SHA a;init(&a);update(&a,(const unsigned char *)s,(unsigned)strlen(s));finish(&a,h);}
static int exact(const char *s,const char *h,long expected){char got[65];long n;return digest(s,got,&n)==1&&!strcmp(h,got)&&(expected<0||n==expected);}
static const char *expected_cnf(void){
#ifdef HOST_TEST
 const char *v=getenv("WAVE_TEST_CNF");if(v)return v;
#endif
 return cnf_sha;
}
static const char *expected_com(void){
#ifdef HOST_TEST
 const char *v=getenv("WAVE_TEST_COM");if(v)return v;
#endif
 return com_sha;
}
static void write_new(const char *s,const unsigned char *b,unsigned n){int fd;unsigned off=0;int done;
 if(kind(s))fail("Output already exists");fd=open(s,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);if(fd<0)fail("Cannot exclusively create output");
 while(off<n){done=write(fd,b+off,n-off);if(done<=0){close(fd);fail("Output write/disk full");}off+=(unsigned)done;}if(close(fd))fail("Output close failed");
}
static void copy_new(const char *from,const char *to){FILE *f;int fd,n,w;unsigned char b[512];char h[65];long len;
 if(digest(from,h,&len)!=1||kind(to))fail("Copy preflight failed");f=fopen(from,"rb");if(!f)fail("Cannot reopen input");fd=open(to,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);if(fd<0){fclose(f);fail("Cannot exclusively create copy");}
 while((n=(int)fread(b,1,sizeof(b),f))!=0){w=write(fd,b,n);if(w!=n){close(fd);fclose(f);fail("Copy write/disk full");}}
 if(ferror(f)){fclose(f);close(fd);fail("Copy read failed");}if(fclose(f)||close(fd))fail("Copy close failed");if(!exact(to,h,len))fail("Copy readback failed");
}
static void move_new(const char *from,const char *to){if(kind(from)!=1||kind(to))fail("Rename conflict");if(rename(from,to))fail("Rename failed; recover recognized sidecars");}
static void textread(const char *s,char *out){FILE *f;size_t n;if(kind(s)!=1)fail("Starter/metadata is not a regular file");f=fopen(s,"rb");if(!f)fail("Cannot read starter");n=fread(out,1,MAXBAT-1,f);if(ferror(f)||fgetc(f)!=EOF||memchr(out,0,n)){fclose(f);fail("Starter too large/binary");}if(fclose(f))fail("Starter close failed");out[n]=0;}
static void patch(int i){char needle[PTH+32],snippet[1600],*at,*again;unsigned a,b;
 if(i)sprintf(needle,"%%TSDRV%%%%TSWIN%%\\WIN.COM /R\r\n");else sprintf(needle,"%s\\WIN.COM /R\r\n",win);
 at=strstr(original[i],needle);if(!at||(at!=original[i]&&at[-1]!='\n'))fail("Expected recognized original WIN /R command");again=strstr(at+strlen(needle),needle);if(again||strstr(original[i],":XWPLAIN")||strstr(original[i],":XWEND")||strstr(original[i],":XWFAIL"))fail("Ambiguous/custom starter");
 sprintf(snippet,"IF NOT EXIST %s\\WAVE.RDY GOTO XWPLAIN\r\n%s\\WAVEXT.EXE VERIFY %s %s\r\nIF ERRORLEVEL 2 GOTO XWFAIL\r\nIF ERRORLEVEL 1 GOTO XWPLAIN\r\n%s\\XTCLEAN.COM\r\nIF ERRORLEVEL 1 GOTO XWFAIL\r\nGOTO XWEND\r\n:XWFAIL\r\nECHO Wave safety check failed. Windows was not started.\r\nGOTO %s\r\n:XWPLAIN\r\n%s:XWEND\r\n",home,home,win,home,win,i?"WINFAIL":"DONE",needle);
 a=(unsigned)(at-original[i]);b=(unsigned)strlen(snippet);if(a+b+strlen(at+strlen(needle))>=MAXBAT)fail("Replacement starter too long");
 memcpy(replacement[i],original[i],a);strcpy(replacement[i]+a,snippet);strcat(replacement[i],at+strlen(needle));hashtext(original[i],oldhash[i]);hashtext(replacement[i],newhash[i]);
}
static void payload_check(void){FILE *f;int c,v;long count=0;unsigned n,i;unsigned char b[130];SHA a;char h[65];
 join(p,home,"XTWAVE.DAT");if(kind(p)!=1)fail("Missing compressed wave payload");f=fopen(p,"rb");if(!f)fail("Cannot read wave payload");init(&a);
 while((c=fgetc(f))!=EOF){if(c<128){n=(unsigned)c+1;if(fread(b,1,n,f)!=n){fclose(f);fail("Truncated literal");}}
 else{n=(unsigned)c-128+3;v=fgetc(f);if(v==EOF){fclose(f);fail("Truncated repeat");}for(i=0;i<n;i++)b[i]=(unsigned char)v;}
 count+=n;if(count>35971L){fclose(f);fail("Payload expansion exceeds qualified size");}update(&a,b,n);}
 if(ferror(f)||fclose(f))fail("Payload read failed");finish(&a,h);if(count!=35971L||strcmp(h,logo_sha))fail("Expanded module pin mismatch");
 join(p,home,"XTCLEAN.COM");if(!exact(p,clean_sha,1071))fail("Wrapper pin mismatch");join(p,win,"SYSTEM");join(q,p,"WIN.CNF");if(!exact(q,expected_cnf(),3456))fail("Unsupported owned WIN.CNF");
}
static void build_loader(const char *target){FILE *cnf,*art;int fd,c,v,w;unsigned char b[130];unsigned n,i;
 join(p,win,"SYSTEM");join(q,p,"WIN.CNF");join(p,home,"XTWAVE.DAT");cnf=fopen(q,"rb");art=fopen(p,"rb");if(!cnf||!art)fail("Cannot reopen qualified loader inputs");
 if(kind(target))fail("Loader stage exists");fd=open(target,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);if(fd<0)fail("Cannot create private loader stage");
 while((n=(unsigned)fread(b,1,sizeof(b),cnf))!=0)if(write(fd,b,n)!=(int)n)fail("Private loader write failed");if(ferror(cnf)||fclose(cnf))fail("Owned loader read failed");
 while((c=fgetc(art))!=EOF){if(c<128){n=(unsigned)c+1;if(fread(b,1,n,art)!=n)fail("Payload changed during staging");}else{n=(unsigned)c-128+3;v=fgetc(art);if(v==EOF)fail("Payload changed during staging");for(i=0;i<n;i++)b[i]=(unsigned char)v;}
 w=write(fd,b,n);if(w!=(int)n)fail("Private loader write failed");}
 if(ferror(art)||fclose(art)||close(fd))fail("Private loader close failed");if(!exact(target,expected_com(),39427))fail("Private loader readback/hash failed");
}
static void writable(const char *name){
#ifdef HOST_WIN
 DWORD a=GetFileAttributesA(name);if(a!=INVALID_FILE_ATTRIBUTES&&(a&FILE_ATTRIBUTE_READONLY))fail("Readonly starter/sidecar");
#elif !defined(HOST_TEST)
 unsigned a;if(!_dos_getfileattr(name,&a)&&(a&_A_RDONLY))fail("Readonly starter/sidecar");
#else
 struct stat st;if(!lstat(name,&st)&&!(st.st_mode&S_IWUSR))fail("Readonly starter/sidecar");
#endif
}
static void paths(const char *a,const char *b){unsigned n;const char *s;
 if(strlen(a)>180||strlen(b)>180||strlen(a)>PTH-20||strlen(b)>PTH-20||!strcmp(a,b))fail("Unsafe Windows/support paths");strcpy(win,a);strcpy(home,b);
#ifndef HOST_TEST
 for(n=0;n<2;n++){s=n?home:win;if(strlen(s)<4||!isalpha(s[0])||s[1]!=':'||s[2]!='\\')fail("Use absolute DOS 8.3 paths");for(s+=3;*s;s++)if(!isalnum(*s)&&*s!='\\'&&*s!='_'&&*s!='-'&&*s!='~'&&*s!='$'&&*s!='.')fail("Unsafe DOS path");}
 strupr(win);strupr(home);
#else
 n=0;s=win;n=n;s=s;
#endif
 if(kind(win)!=2||kind(home)!=2)fail("Windows/support directory missing");join(txn,home,"WAVE01");
}
static void space_check(void){
#ifdef HOST_TEST
 if(getenv("WAVE_NOSPACE"))fail("Insufficient free space (host fixture)");
#else
 struct diskfree_t d;unsigned long freebytes;if(_dos_getdiskfree(home[0]-'A'+1,&d))fail("Cannot inspect free space");freebytes=(unsigned long)d.avail_clusters*d.sectors_per_cluster*d.bytes_per_sector;if(freebytes<196608UL)fail("Need 192 KiB free for transaction and sidecars");
#endif
}
static void not_windows(void){
#ifdef HOST_TEST
 if(getenv("WAVE_RUNNING"))fail("Exit Windows/task switcher first");
#else
 union REGS r;r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al&&r.h.al!=0x80)fail("Exit Windows first");r.x.ax=0x4680;int86(0x2f,&r,&r);if(!r.x.ax)fail("Exit Windows/task switcher first");
#endif
}
static void create_txn(void){char *meta=metadata;int i;char h[65];
 payload_check();space_check();join(p,win,"XTTEST.COM");if(kind(p))fail("Existing private loader requires review");join(p,win,"XTCLEAN.COM");if(kind(p))fail("Existing wrapper requires review");
 join(p,home,"WAVE.RDY");if(kind(p))fail("Existing activation marker");join(p,home,"WAVE.OFF");if(kind(p))fail("Existing rollback marker");
 for(i=0;i<2;i++){join(p,home,prior[i]);join(q,home,next[i]);if(kind(p)||kind(q))fail("Existing starter sidecar");join(p,home,bat[i]);writable(p);if(!i||kind(p)){textread(p,original[i]);patch(i);if(i)have_shell=1;}}
#if defined(HOST_TEST) && !defined(HOST_WIN)
 if(mkdir(txn,0700))fail("Cannot exclusively create transaction directory");
#else
 if(mkdir(txn))fail("Cannot exclusively create transaction directory");
#endif
 checkpoint("created-transaction");
 for(i=0;i<1+have_shell;i++){join(p,txn,saved[i]);write_new(p,(unsigned char *)original[i],(unsigned)strlen(original[i]));if(!exact(p,oldhash[i],-1))fail("Backup readback failed");join(p,txn,fresh[i]);write_new(p,(unsigned char *)replacement[i],(unsigned)strlen(replacement[i]));if(!exact(p,newhash[i],-1))fail("Starter stage readback failed");}
 checkpoint("saved-starters");join(z,txn,"XTEST.NEW");build_loader(z);join(p,home,"XTCLEAN.COM");join(q,txn,"CLEAN.NEW");copy_new(p,q);checkpoint("staged-private");
 sprintf(meta,"WAVEXT01\r\n%s\r\n%s\r\n%d\r\n%s\r\n%s\r\n%s\r\n%s\r\n",win,home,have_shell,oldhash[0],newhash[0],have_shell?oldhash[1]:"-",have_shell?newhash[1]:"-");join(p,txn,"META.TXT");write_new(p,(unsigned char *)meta,(unsigned)strlen(meta));hashtext(meta,h);if(!exact(p,h,-1))fail("Metadata readback failed");checkpoint("staged-metadata");
}
static void read_line(FILE *f,char *s,unsigned cap){char line[PTH];unsigned n;if(!fgets(line,sizeof(line),f))fail("Truncated transaction metadata");n=(unsigned)strlen(line);if(!n||line[n-1]!='\n')fail("Metadata line too long");while(n&&(line[n-1]=='\r'||line[n-1]=='\n'))line[--n]=0;if(n>=cap)fail("Metadata field too long");strcpy(s,line);}
static void load_txn(void){FILE *f;char line[PTH];int i;join(p,txn,"META.TXT");if(kind(p)!=1)fail("Incomplete transaction; original starters untouched unless known sidecars exist");f=fopen(p,"rb");if(!f)fail("Cannot read metadata");read_line(f,line,PTH);if(strcmp(line,"WAVEXT01"))fail("Unknown transaction");read_line(f,line,PTH);if(strcmp(line,win))fail("Transaction Windows path mismatch");read_line(f,line,PTH);if(strcmp(line,home))fail("Transaction support path mismatch");read_line(f,line,PTH);if(strcmp(line,"0")&&strcmp(line,"1"))fail("Bad transaction shell flag");have_shell=line[0]=='1';read_line(f,oldhash[0],65);read_line(f,newhash[0],65);read_line(f,oldhash[1],65);read_line(f,newhash[1],65);if(fgetc(f)!=EOF||ferror(f)||fclose(f))fail("Metadata trailing data/read error");
 for(i=0;i<1+have_shell;i++){char recorded[65];strcpy(recorded,newhash[i]);join(p,txn,saved[i]);textread(p,original[i]);{char h[65];hashtext(original[i],h);if(strcmp(h,oldhash[i]))fail("Original backup changed");}patch(i);if(strcmp(recorded,newhash[i]))fail("Metadata replacement hash changed");join(p,txn,fresh[i]);if(!exact(p,newhash[i],-1))fail("Staged starter changed");}
 join(p,txn,"XTEST.NEW");if(!exact(p,expected_com(),39427))fail("Staged private loader changed");join(p,txn,"CLEAN.NEW");if(!exact(p,clean_sha,1071))fail("Staged wrapper changed");
}
/* Inspect every target before any resumed operation mutates a name. */
static int starter_state(int i){int l,o,n;join(p,home,bat[i]);join(q,home,prior[i]);join(z,home,next[i]);writable(p);writable(q);writable(z);l=!kind(p)?0:exact(p,oldhash[i],-1)?1:exact(p,newhash[i],-1)?2:-1;o=!kind(q)?0:exact(q,oldhash[i],-1)?1:-1;n=!kind(z)?0:exact(z,newhash[i],-1)?1:-1;
 if(l==1&&o==0&&(n==0||n==1))return 1;if(l==2&&o==1&&n==0)return 2;if(l==0&&o==1&&n==1)return 3;fail("Unknown/conflicting starter/backup/stage state");return 0;
}
static void marker_preflight(void){char h[65];hashtext(marker,h);join(p,home,"WAVE.RDY");join(q,home,"WAVE.OFF");if((kind(p)&&!exact(p,h,-1))||(kind(q)&&!exact(q,h,-1))||(kind(p)&&kind(q)))fail("Conflicting activation marker");}
static void binaries_preflight(int require){join(p,win,"XTTEST.COM");if((kind(p)&&!exact(p,expected_com(),39427))||(require&&!kind(p)))fail("Private live loader missing/changed");join(p,win,"XTCLEAN.COM");if((kind(p)&&!exact(p,clean_sha,1071))||(require&&!kind(p)))fail("Live wrapper missing/changed");}
static void apply(void){int i,s;char markhash[65];load_txn();payload_check();marker_preflight();binaries_preflight(0);for(i=0;i<1+have_shell;i++)starter_state(i);space_check();
 join(p,txn,"XTEST.NEW");join(q,win,"XTTEST.COM");if(!kind(q))copy_new(p,q);join(p,txn,"CLEAN.NEW");join(q,win,"XTCLEAN.COM");if(!kind(q))copy_new(p,q);checkpoint("installed-private");
 for(i=0;i<1+have_shell;i++){s=starter_state(i);if(s==2)continue;if(s==1){join(p,txn,fresh[i]);join(q,home,next[i]);if(!kind(q))copy_new(p,q);join(p,home,bat[i]);join(q,home,prior[i]);move_new(p,q);checkpoint(i?"shell-gap":"plain-gap");}join(p,home,next[i]);join(q,home,bat[i]);move_new(p,q);checkpoint(i?"shell-live":"plain-live");if(starter_state(i)!=2)fail("Starter commit readback failed");}
 join(p,home,"WAVE.RDY");join(q,home,"WAVE.OFF");if(!kind(p)){if(kind(q))move_new(q,p);else write_new(p,(const unsigned char *)marker,(unsigned)strlen(marker));}hashtext(marker,markhash);if(!exact(p,markhash,-1))fail("Activation marker readback failed");checkpoint("activated");puts("APPLIED: qualified Color wave enabled; Mono/other display profiles stay static. WIN.COM and settings untouched.");
}
static void restore(void){int i,s;load_txn();marker_preflight();for(i=0;i<1+have_shell;i++)starter_state(i);join(p,home,"WAVE.RDY");join(q,home,"WAVE.OFF");if(kind(p))move_new(p,q);checkpoint("disabled");
 for(i=0;i<1+have_shell;i++){s=starter_state(i);if(s==1)continue;if(s==2){join(p,home,bat[i]);join(q,home,next[i]);move_new(p,q);checkpoint(i?"restore-shell-gap":"restore-plain-gap");}join(p,home,prior[i]);join(q,home,bat[i]);move_new(p,q);if(starter_state(i)!=1)fail("Starter restoration readback failed");}puts("RESTORED: exact original starters. Private add-on/recognized stages retained inactive; Windows/settings untouched.");
}
static int eligible(void){FILE *f;char line[256],*v,*e;int boot=0,seen=0,color=0;join(p,win,"SYSTEM.INI");if(kind(p)!=1)fail("SYSTEM.INI missing/nonregular");f=fopen(p,"rb");if(!f)fail("Cannot read display selection");while(fgets(line,sizeof(line),f)){v=line;while(isspace(*v))v++;if(*v=='['){e=strchr(v,']');if(!e)fail("Malformed INI section");*e=0;boot=!stricmp(v+1,"boot");continue;}if(boot&&!strnicmp(v,"display.drv=",12)){if(seen++)fail("Ambiguous display selection");v+=12;e=v+strlen(v);while(e>v&&isspace(e[-1]))*--e=0;color=!stricmp(v,"TR53216.DRV")||!stricmp(v,"TANDY88.DRV");}}
 if(ferror(f)||fclose(f)||seen!=1)fail("Cannot verify selected display profile");return color?0:1;
}
int main(int argc,char **argv){int i,verify;
 if(!selftest()||sizeof(U32)!=4)fail("SHA implementation self-test failed");if(argc==2&&!strcmp(argv[1],"SELFTEST")){puts("PASS SHA256");return 0;}
 if(argc!=4){puts("WAVEXT CHECK|APPLY|RESTORE|VERIFY Windows-dir support-dir\nUse plain DOS. No WIN.COM/OS/settings writes. Mono/other modes retain static startup.");return 2;}paths(argv[2],argv[3]);not_windows();verify=!stricmp(argv[1],"VERIFY");
 if(!stricmp(argv[1],"RESTORE")){restore();return 0;}
 if(!verify&&stricmp(argv[1],"CHECK")&&stricmp(argv[1],"APPLY"))return 2;
 if(!kind(txn)){if(verify)fail("Activation transaction missing");if(!stricmp(argv[1],"CHECK")){payload_check();space_check();join(p,home,"WINXT.BAT");writable(p);textread(p,original[0]);patch(0);join(p,home,"TSTART.BAT");if(kind(p)){writable(p);textread(p,original[1]);patch(1);}join(p,win,"XTTEST.COM");if(kind(p))fail("Existing private loader");join(p,win,"XTCLEAN.COM");if(kind(p))fail("Existing private wrapper");marker_preflight();join(p,home,"WAVE.RDY");join(q,home,"WAVE.OFF");if(kind(p)||kind(q))fail("Marker without transaction");for(i=0;i<2;i++){join(p,home,prior[i]);join(q,home,next[i]);if(kind(p)||kind(q))fail("Starter sidecar conflict");}puts("CHECK PASS: no files changed; apply creates a new verified transaction.");return 0;}create_txn();}
 if(kind(txn)!=2)fail("Transaction path is not a directory");load_txn();marker_preflight();for(i=0;i<1+have_shell;i++){int s=starter_state(i);if(verify&&s!=2)fail("Incomplete starter transaction; use CHECK/RESTORE");}
 if(verify){char h[65];hashtext(marker,h);join(p,home,"WAVE.RDY");if(!exact(p,h,-1))fail("Wave activation missing");binaries_preflight(1);return eligible();}
 if(!stricmp(argv[1],"CHECK")){payload_check();binaries_preflight(0);puts("CHECK PASS: recognized transaction; no files changed.");return 0;}apply();return 0;
}
