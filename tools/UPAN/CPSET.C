/* CPSET: lean DOS 3.3+ / 8086 SETUP.INF Computer-profile registration.
 * Build: MSC 6 /AL /G0 /Gs (DOS runtime, never /Gw or Windows libraries).
 * Every input/output is bounded, binary, sequential; no 16-bit seek math.
 * Copyright 2026. Permission to use, modify and redistribute this source.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/stat.h>
#ifdef HOST_TEST
#include <io.h>
#include <process.h>
#include <windows.h>
#include <stdint.h>
#ifdef HOST_WINDOWS
#include <io.h>
#include <process.h>
#endif
typedef uint32_t U32;
#ifndef HOST_WINDOWS
#define O_BINARY 0
#define S_IREAD S_IRUSR
#define S_IWRITE S_IWUSR
#endif
#else
#include <io.h>
#include <dos.h>
#include <direct.h>
typedef unsigned long U32;
#endif

#define MAXINI 60000U
#define HEAD 144
#define CAP (MAXINI+HEAD+1)
#define PLEN 128
#define SEL "TNDYK3.DRV"
/* Large-model malloc returns far pointers. Each object is <64 KiB.
 * Keep the same bounded working set out of the executable image. */
static unsigned char *orig, *cur, *dest;
static char ini[PLEN], jrn[PLEN], bak[PLEN], sav[PLEN];
static char tmp[PLEN], old[PLEN], rst[PLEN];
static char names[64][64];
static unsigned on, cn, dn;
static int steps;

typedef struct { unsigned a, b; } Keyboard;
static Keyboard os, cs;

static void die(const char *s)
{ fprintf(stderr,"CPSET: %s\nNo unsafe fallback was attempted.\n",s); exit(1); }
static int eqi(const char *a,const char *b)
{ while (*a && *b) { if(toupper((unsigned char)*a)!=toupper((unsigned char)*b)) return 0; ++a; ++b; } return *a==*b; }
static int space(unsigned char c) { return c==' ' || c=='\t'; }
static int exists(const char *p)
{ struct stat st; if(!stat((char*)p,&st)) return 1; if(errno==ENOENT) return 0; die("Cannot inspect a file."); return 0; }
static void writable(const char *p)
{
#ifdef HOST_TEST
    struct stat st;
    if(stat((char*)p,&st) || !(st.st_mode&S_IFREG) || !(st.st_mode&0222)) die("File is not a writable regular file.");
#else
    unsigned a;
    if(_dos_getfileattr(p,&a) || (a&0x1f)) die("File has unsupported attributes or is unavailable.");
#endif
}
static void checkpoint(void)
{
#ifndef HOST_TEST
    union REGS r; r.h.ah=0x0d; intdos(&r,&r);
#ifdef CP_FAULT
    { const char *p; ++steps; p=getenv("CP_CRASH"); if(p && atoi(p)==steps) exit(99); }
#endif
#else
    const char *p;
    ++steps; p=getenv("CP_CRASH");
    if(p && atoi(p)==steps) _exit(99);
#endif
}
static void commit(int fd)
{
#ifdef HOST_TEST
    if(!FlushFileBuffers((HANDLE)_get_osfhandle(fd))) die("Cannot flush staged file.");
#else
    union REGS r;
    r.x.ax=0x6800; r.x.bx=fd; intdos(&r,&r);
    if(r.x.cflag) die("Cannot commit staged file (DOS 3.3+ required).");
#endif
}
static void out(int fd,const unsigned char *p,unsigned n)
{ unsigned k; int w;
#if defined(HOST_TEST) || defined(CP_FAULT)
 const char *v=getenv("CP_SHORT");
 if(v && atoi(v)==steps+1) { if(n>1)write(fd,p,n/2);close(fd);die("Injected short write."); }
#endif
 while(n) { k=n>16000?16000:n;w=write(fd,p,k);if(w<0 || (unsigned)w!=k){close(fd);die("Write failed; preserve sidecars.");}p+=k;n-=k;}
}
static int create(const char *p)
{ int fd; if(exists(p)) die("Staging/backup collision; keep files for inspection."); fd=open(p,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE); if(fd<0) die("Cannot create staged file."); return fd; }
static void finish(int fd)
{ commit(fd); if(close(fd)) die("Close failed. Keep all sidecars."); checkpoint(); }
static unsigned readall(const char *p,unsigned char *b,unsigned lim)
{ int f,n; unsigned z=0; f=open(p,O_RDONLY|O_BINARY); if(f<0) die("Required file cannot be read."); while(z<lim) { n=read(f,b+z,(lim-z)>16000?16000:(lim-z)); if(n<0) { close(f); die("Read failed."); } if(!n) break; z+=(unsigned)n; } if(z==lim) { unsigned char c; n=read(f,&c,1); if(n!=0) {close(f);die("File exceeds safe size limit.");} } if(close(f)) die("Read close failed."); return z; }
static int same(const char *p,const unsigned char *b,unsigned n)
{ unsigned char part[256]; unsigned off=0,k; int f,r; f=open(p,O_RDONLY|O_BINARY); if(f<0) return 0; while(off<n) { k=n-off; if(k>sizeof(part)) k=sizeof(part); r=read(f,part,k); if(r!=(int)k || memcmp(part,b+off,k)) {close(f);return 0;} off+=k; } r=read(f,part,1); if(close(f)) return 0; return r==0; }
static char win[PLEN], sysini[PLEN], curpath[PLEN],drvpath[PLEN];
static int selected;
static const char label[]="Tandy 1000 EX/HX (WindowsXT)";
static const char prefix[]="\r\n; WindowsXT optional Computer preset; run CPSET CHECK before selecting.\r\n    \"Tandy 1000 EX/HX (WindowsXT)\",\"78\"\r\n        system\r\n        ";
static const char suffix[]="\r\n        t1s0pcxt\r\n        nomouse\r\n        cga\r\n        sound\r\n        comm\r\n        nohimemswitch\r\n        ebios\r\n\r\n";
static unsigned locate(const char *s);
/* Only the exact currently packaged grabber metadata is a new variant. */
static U32 current_metadata_crc(void)
{ U32 crc=0xffffffffUL;unsigned i,bit;
 for(i=0;i<on;i++){crc^=orig[i];for(bit=0;bit<8;bit++)crc=(crc&1)?(crc>>1)^0xedb88320UL:crc>>1;}
 return crc^0xffffffffUL;
}
static void source(void)
{ char h[65];unsigned i;int eof=0;
 /* Current grabber metadata expands two fields by eight bytes. */
 if(on!=49840U&&(on!=49848U||current_metadata_crc()!=0x073140f6UL))die("Prepared Windows XT Setup metadata differs; run FIXXT.");locate("xtkbd = a:TNDYK3.DRV");locate("xtwheel = a:WHEEL.DRV");locate("\"Tandy 1000 EX/HX (WindowsXT)\",\"78\"");
 for(i=0;i<on;i++){if(orig[i]==26){eof=1;continue;}if(eof&&orig[i]!='\r'&&orig[i]!='\n')die("Invalid SETUP.INF EOF padding.");if(!orig[i]||(orig[i]<32&&orig[i]!='\r'&&orig[i]!='\n'&&orig[i]!='\t'))die("Invalid SETUP.INF text.");}
 locate("[setup]");locate("[keyboard.drivers]");locate("[io.device]");

 }
static void join(char *p,const char *name,int system)
{ unsigned n=(unsigned)strlen(win);if(n+strlen(name)+10>=PLEN)die("Path too long.");strcpy(p,win);
#ifdef HOST_TEST
 strcat(p,system?"/SYSTEM/":"/");
#else
 strcat(p,system?"\\SYSTEM\\":"\\");
#endif
 strcat(p,name); }
static void paths(const char *w)
{ unsigned i;if(strlen(w)>90||strlen(w)<3)die("Use an absolute Windows directory.");strcpy(win,w);
#ifdef HOST_TEST
 #ifdef HOST_WINDOWS
 if(!(isalpha((unsigned char)win[0]) && win[1]==':' && (win[2]=='/' || win[2]=='\\')))die("Absolute path required.");
#else
 if(win[0]!='/')die("Absolute path required.");
#endif
#else
 if(!isalpha(win[0])||win[1]!=':'||win[2]!='\\')die("Use C:\\WINDOWS or another absolute 8.3 directory.");
 for(i=0;win[i];++i){if(i!=1 && !isalnum((unsigned char)win[i])&&win[i]!='\\'&&win[i]!='_'&&win[i]!='-'&&win[i]!='~')die("Use a simple DOS path without dots or spaces.");win[i]=(char)toupper(win[i]);}
 {unsigned n=0;for(i=3;win[i];++i){if(win[i]=='\\'){if(!n||n>8)die("Use 8.3 directory names.");n=0;}else ++n;}if(!n||n>8)die("Use 8.3 directory names.");}
#endif
 if(strstr(win,".."))die("Parent-relative paths forbidden.");
 join(ini,"SETUP.INF",1);join(sysini,"SYSTEM.INI",0);join(bak,"CPINFO.BAK",1);join(sav,"CPINFO.SAV",1);join(tmp,"CPINFO.NEW",1);join(old,"CPINFO.OLD",1);join(rst,"CPINFO.RST",1);join(curpath,"CPINFO.CUR",1);
}
static void not_windows(void)
{
#ifdef HOST_TEST
 if(getenv("CP_WINDOWS"))die("Exit Windows completely.");
#else
 union REGS r;memset(&r,0,sizeof(r));r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al&&r.h.al!=0x80)die("Exit Windows completely.");memset(&r,0,sizeof(r));r.x.ax=0x4680;int86(0x2f,&r,&r);if(!r.x.ax)die("Exit Windows completely.");
#endif
}
static int equalpart(const unsigned char *b,unsigned n,const char *s)
{unsigned i;if(n!=strlen(s))return 0;for(i=0;i<n;++i)if(toupper(b[i])!=toupper((unsigned char)s[i]))return 0;return 1;}
/* Default keyboard recognition: known filename/size and bounded Windows NE
 * tables/segments. Same-size body identity is explicit /VERIFY only. */
static unsigned le16(const unsigned char *b,unsigned p)
{return (unsigned)b[p]|((unsigned)b[p+1]<<8);}
static U32 le32(const unsigned char *b,unsigned p)
{return (U32)le16(b,p)|((U32)le16(b,p+2)<<16);}
static void keyboard_layout(void)
{
 unsigned n,ne,ns,align,table,i,entry,entries,res;U32 off,len;
 n=readall(drvpath,cur,8000);
 if(n!=(selected?7640U:7041U)||cur[0]!='M'||cur[1]!='Z'||le32(cur,60)!=128UL)die("Unsupported keyboard size/DOS header.");
 ne=128;if(cur[ne]!='N'||cur[ne+1]!='E'||cur[ne+54]!=2||!(le16(cur,ne+12)&0x8000))die("Keyboard Windows NE header invalid.");
 ns=le16(cur,ne+28);align=le16(cur,ne+50);table=le16(cur,ne+34);entry=le16(cur,ne+4);entries=le16(cur,ne+6);res=le16(cur,ne+38);
 if(!ns||ns>32||align>12||table<64||(U32)ne+table+(U32)ns*8>n||!entries||(U32)ne+entry+entries>n||entry<table+ns*8||(U32)ne+res+11>n)die("Keyboard NE table bounds invalid.");
 if(cur[ne+res]!=8||memcmp(cur+ne+res+1,"KEYBOARD",8)||le16(cur,ne+res+9))die("Keyboard NE module identity invalid.");
 for(i=0;i<ns;i++){unsigned at=ne+table+i*8;off=(U32)le16(cur,at)<<align;len=le16(cur,at+2);if(off){if(!len)len=65536UL;if(off>n||len>n-off)die("Keyboard NE segment extent invalid.");}}
}
static void installed(void)
{ unsigned n,p=0,e,q,t,v,z,i,keys[4]={0,0,0,0},sections=0,descsections=0,desckeys=0;int boot=0;char values[4][40],h[65],other[PLEN];const char *kn[4]={"system.drv","sound.drv","comm.drv","keyboard.drv"};
 n=readall(sysini,cur,14000);for(i=0;i<n;++i)if(!cur[i]||(cur[i]<32&&cur[i]!='\r'&&cur[i]!='\n'&&cur[i]!='\t'))die("Unsupported SYSTEM.INI content.");
 while(p<n){e=p;while(e<n&&cur[e]!='\r'&&cur[e]!='\n')++e;q=p;while(q<e&&space(cur[q]))++q;
  if(q<e&&cur[q]=='['){t=q+1;while(t<e&&cur[t]!=']')++t;if(t==e)die("Malformed SYSTEM.INI section.");v=q+1;z=t;while(v<z&&space(cur[v]))++v;while(z>v&&space(cur[z-1]))--z;boot=equalpart(cur+v,z-v,"boot")?1:(equalpart(cur+v,z-v,"boot.description")?2:0);if(boot==1)++sections;if(boot==2)++descsections;z=t+1;while(z<e&&space(cur[z]))++z;if(z<e&&cur[z]!=';')die("Unexpected text after INI section.");}
  else if(boot==1&&q<e&&cur[q]!=';'){t=q;while(t<e&&cur[t]!='=')++t;z=t;while(z>q&&space(cur[z-1]))--z;if(t<e)for(i=0;i<4;++i)if(equalpart(cur+q,z-q,kn[i])){++keys[i];v=t+1;while(v<e&&space(cur[v]))++v;z=v;while(z<e&&cur[z]!=';')++z;while(z>v&&space(cur[z-1]))--z;if(z-v>39)die("Overlong driver name.");memcpy(values[i],cur+v,z-v);values[i][z-v]=0;}}
  else if(boot==2&&q<e&&cur[q]!=';'){t=q;while(t<e&&cur[t]!='=')++t;z=t;while(z>q&&space(cur[z-1]))--z;if(t<e&&equalpart(cur+q,z-q,"system.drv")){++desckeys;v=t+1;while(v<e&&space(cur[v]))++v;z=v;while(z<e&&cur[z]!=';')++z;while(z>v&&space(cur[z-1]))--z;if(!equalpart(cur+v,z-v,"MS-DOS or PC-DOS System")&&!equalpart(cur+v,z-v,label))die("Computer is not the generic DOS or WindowsXT profile.");}}
  p=e;if(p<n&&cur[p]=='\r')++p;if(p<n&&cur[p]=='\n')++p;
 }
 if(descsections!=1||desckeys!=1)die("Missing or ambiguous Computer description.");if(sections!=1)die("Need exactly one [boot] section.");for(i=0;i<4;++i)if(keys[i]!=1)die("Missing or duplicate core driver entry.");
 if(!eqi(values[0],"system.drv")||!eqi(values[1],"sound.drv")||!eqi(values[2],"comm.drv"))die("Non-generic system/sound/communications selection.");
 if(eqi(values[3],"keyboard.drv"))selected=0;else if(eqi(values[3],"tndyk3.drv"))selected=1;else die("Unknown keyboard selection.");
 join(drvpath,selected?"TNDYK3.DRV":"KEYBOARD.DRV",1);join(other,selected?"TNDYK3.DRV":"KEYBOARD.DRV",0);if(exists(other))die("Keyboard in Windows root makes driver lookup ambiguous.");keyboard_layout();
}
static unsigned locate(const char *s)
{unsigned i,l=(unsigned)strlen(s),found=0,count=0;for(i=0;i+l<=on;++i)if(!memcmp(orig+i,s,l)){found=i;++count;}if(count!=1)die("Unexpected SETUP.INF structure.");return found;}
static void append(const unsigned char *p,unsigned n)
{if(n>(unsigned)MAXINI-dn)die("Result too large.");memcpy(dest+dn,p,n);dn+=n;}
static void textadd(const char *s){append((const unsigned char*)s,(unsigned)strlen(s));}
static void generate(int k3)
{ dn=0;append(orig,on); }
static void buffers(void)
{
 unsigned i; unsigned char **p[3];
 p[0]=&orig; p[1]=&cur; p[2]=&dest;
 for(i=0;i<3;i++) {
#ifdef HOST_TEST
  const char *f=getenv("CP_ALLOCFAIL");
  *p[i]=(f && atoi(f)==(int)i+1)?NULL:(unsigned char *)malloc(CAP);
#else
  *p[i]=(unsigned char *)malloc(CAP);
#endif
  if(!*p[i]) {
   while(i) free(*p[--i]);
   die("Not enough conventional memory for bounded profile buffers.");
  }
 }
}

static int wantbackup,wantverify;
static char readyfile[PLEN],leansave[PLEN],leannew[PLEN],leanold[PLEN],leanjrn[PLEN];
static unsigned occurrences(const unsigned char *b,unsigned n,const char *q,unsigned *at){unsigned i,c=0,l=(unsigned)strlen(q);for(i=0;i+l<=n;i++)if(!memcmp(b+i,q,l)){*at=i;c++;}return c;}
static int strip(const char *q){unsigned at=0,n=(unsigned)strlen(q),c=occurrences(orig,on,q,&at);if(c>1)die("Duplicate owned profile fragment.");if(!c)return 0;memmove(orig+at,orig+at+n,on-at-n);on-=n;orig[on]=0;return 1;}
static void base_live(void){on=readall(ini,orig,MAXINI);cn=on;orig[on]=0;memcpy(cur,orig,on);source();}
static void lean_paths(void){join(readyfile,"CPREADY.OK",1);join(leannew,"CPLEAN.NEW",1);join(leanold,"CPLEAN.OLD",1);join(leanjrn,"CPLEAN.JRN",1);}
static void recover_lean(void){unsigned n;char text[PLEN+20],expected[PLEN+20];int fd;
 if(!exists(leanjrn)){if(exists(leannew)||exists(leanold))die("Unowned lean temporary file; preserve it.");return;}
 sprintf(expected,"CPLEAN1\r\n%s\r\n",ini);n=readall(leanjrn,(unsigned char*)text,sizeof(text)-1);text[n]=0;if(strcmp(text,expected))die("Foreign lean journal.");
 if(exists(leanold)){if(exists(ini)){if(remove(leanold))die("Cannot finish temporary cleanup.");}else if(rename(leanold,ini))die("Cannot restore interrupted original.");}
 if(!exists(ini))die("Missing Setup metadata after interrupted replacement.");if(exists(leannew)&&remove(leannew))die("Cannot discard incomplete lean staging.");if(remove(leanjrn))die("Cannot close lean journal.");
}
static void marker_text(char *p,unsigned size){sprintf(p,"CPLEAN1\r\n%s\r\n%u\r\n",ini,size);}
static void ready_marker(unsigned size)
{ char text[PLEN+30],previous[PLEN+30];int fd;unsigned n;
 marker_text(text,size);
 if(exists(readyfile)){
  n=readall(readyfile,(unsigned char*)names,sizeof(names));
  if(n==strlen(text)&&!memcmp(names,text,n))return;
  /* APPLY has validated the installed selection and exact current metadata.
   * Upgrade only our preceding same-path marker; never discard foreign state.
   * Both decimal sizes have five digits, so this bounded write cannot leave
   * trailing bytes or require a truncate/delete window. */
  marker_text(previous,49840U);
  if(size!=49848U||on!=49848U||n!=strlen(previous)||memcmp(names,previous,n))
   die("Foreign/stale Computer completion marker.");
  fd=open(readyfile,O_WRONLY|O_BINARY);if(fd<0)die("Cannot update Computer completion marker.");
  out(fd,(const unsigned char*)text,(unsigned)strlen(text));finish(fd);return;
 }
 fd=create(readyfile);out(fd,(const unsigned char*)text,(unsigned)strlen(text));finish(fd);
}
static int fast_ready(void){struct stat st;unsigned n;char text[PLEN+30],got[PLEN+30];if(stat(ini,&st)||st.st_size>MAXINI||!exists(readyfile))return 0;marker_text(text,(unsigned)st.st_size);n=readall(readyfile,(unsigned char*)got,sizeof(got)-1);got[n]=0;return !strcmp(text,got);}
static void apply_lean(int apply){int fd;unsigned i;char text[PLEN+20],name[13];struct stat st;
 recover_lean();installed();base_live();generate(selected);
 if(cn==dn&&!memcmp(cur,dest,dn)){if(apply)ready_marker(dn);puts("Tandy Computer entry already registered; active selections preserved.");return;}
 if(!apply){puts("Generic metadata valid; automatic Tandy registration needed.");return;}
 writable(ini);if(exists(readyfile))die("Stale Computer marker; preserve for review.");
 if(wantbackup){for(i=1;i<1000;i++){sprintf(name,"CPB%03u.BAK",i);join(leansave,name,1);if(!exists(leansave))break;}if(i==1000)die("Backup names exhausted.");fd=create(leansave);out(fd,cur,cn);finish(fd);printf("Requested Computer backup: %s\n",leansave);}
 fd=create(leannew);out(fd,dest,dn);finish(fd);if(stat(leannew,&st)||(unsigned long)st.st_size!=dn)die("Staged length mismatch.");if(wantverify&&!same(leannew,dest,dn))die("Requested Computer readback failed.");
 sprintf(text,"CPLEAN1\r\n%s\r\n",ini);fd=create(leanjrn);out(fd,(unsigned char*)text,(unsigned)strlen(text));finish(fd);
 if(rename(ini,leanold)||rename(leannew,ini))die("Lean rename failed; rerun to repair.");if(remove(leanold)||remove(leanjrn))die("Lean cleanup failed; rerun.");ready_marker(dn);puts("Tandy Computer registered automatically; no default retained backups or SHA. Active selections preserved.");
}
int main(int argc,char **argv){int i,apply;
 setbuf(stdout,NULL);if(argc<3||argc>6){puts("CPSET APPLY|PREFLIGHT|CHECK|READY C:\\WINDOWS [/BACKUP] [/VERIFY]");return 2;}
 for(i=3;i<argc;i++){if(eqi(argv[i],"/BACKUP"))wantbackup=1;else if(eqi(argv[i],"/VERIFY"))wantverify=1;else if(!eqi(argv[i],"/KEEPMS"))die("Unknown lean option.");}
 paths(argv[2]);lean_paths();not_windows();if(eqi(argv[1],"READY")){if(!fast_ready())die("Complete automatic Computer registration first.");return 0;}
 apply=eqi(argv[1],"APPLY");if(!apply&&!eqi(argv[1],"PREFLIGHT")&&!eqi(argv[1],"CHECK"))die("Unknown lean mode.");buffers();apply_lean(apply);free(dest);free(cur);free(orig);return 0;
}
