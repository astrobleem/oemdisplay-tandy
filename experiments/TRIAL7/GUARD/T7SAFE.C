/* T7SAFE: one-shot, default-layout, rollback-safe TRIAL7 border/text test overlay.
 * Copyright 2026. Permission to use, modify and redistribute this source.
 * Build: Microsoft C 6.0 /AS /G0 /W3 (DOS, no Windows libraries).
 * Never changes INIs, boot files, launchers, WINXT sources or OEM media.
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
#include <stdint.h>
#include <unistd.h>
typedef uint32_t U32;
#define O_BINARY 0
#define S_IREAD S_IRUSR
#define S_IWRITE S_IWUSR
#define stricmp strcasecmp
#include <strings.h>
#else
#include <io.h>
#include <dos.h>
#include <direct.h>
#include <process.h>
typedef unsigned long U32;
#endif
#define ROOT "C:\\TRIAL7"
#define SHELL "C:\\WINXT\\SHELLSEL.EXE"
#define CHECK "C:\\WINXT\\TSCHECK.EXE"
#define INI "C:\\WINDOWS\\SYSTEM.INI"
#define USED ROOT "\\USED.TAG"
typedef struct { char *arg,*name; unsigned long os; char *oh; unsigned long ns; char *nh; } Mode;
#include "PINS.H"
static unsigned char buf[1024], inibuf[16001];
static char current[80], original[80], candidate[80], backup[80], source[80];
static char marker[80];
static int modified;
static void fail(const char *s)
{ fprintf(stdout,"TRIAL7: %s\n",s); if(modified) fputs("Keep the kit and every backup. Do not start Windows until RESTORE succeeds.\n",stdout); exit(1); }
#ifdef HOST_TEST
/* Host tests use a private root, never real DOS paths. */
static char hostpath[512];
static const char *path(const char *p)
{ const char *r=getenv("TR7_ROOT"); unsigned i,n; if(!r) fail("TR7_ROOT missing."); if(strncmp(p,"C:\\",3)) fail("Bad internal path."); if(strlen(r)+strlen(p)>sizeof(hostpath)-1) fail("Host path too long."); strcpy(hostpath,r); strcat(hostpath,"/"); n=(unsigned)strlen(hostpath); for(i=3;p[i];i++) hostpath[n++]=p[i]=='\\'?'/':p[i]; hostpath[n]=0; return hostpath; }
static void checkpoint(void)
{ static int step; const char *s; ++step; s=getenv("TR7_CRASH"); if(s && atoi(s)==step) _exit(99); }
#else
static const char *path(const char *p) { return p; }
static void checkpoint(void) { union REGS r; r.h.ah=0x0d; intdos(&r,&r); }
#endif
static int exists(const char *p)
{ struct stat s; if(!stat((char*)path(p),&s)) return 1; if(errno==ENOENT) return 0; fail("Cannot inspect path."); return 0; }
static void regular(const char *p,int writable)
{
#ifdef HOST_TEST
 struct stat s; if(stat((char*)path(p),&s)||!S_ISREG(s.st_mode)||(writable && !(s.st_mode&0222))) fail("Required regular writable file is unavailable.");
#else
 unsigned a; if(_dos_getfileattr(p,&a)||(a&0x1e)||(writable && (a&1))) fail("Required file is missing or has unsupported attributes.");
#endif
}
static void directory(const char *p)
{ struct stat s; if(stat((char*)path(p),&s)||!(s.st_mode&S_IFDIR)) fail("Required default-layout directory is missing."); }
static void flushclose(int f)
{
#ifdef HOST_TEST
 if(fsync(f)) fail("File commit failed.");
#else
 union REGS r; r.x.ax=0x6800; r.x.bx=f; intdos(&r,&r); if(r.x.cflag) fail("File commit failed; DOS 3.3 or later required.");
#endif
 if(close(f)) fail("File close failed."); checkpoint();
}
/* Standard SHA-256; all working words are exactly 32 bits. */
static U32 h[8], w[64]; static unsigned char block[64];
static unsigned bn; static U32 total;
static const U32 k[64]={
0x428a2f98UL,0x71374491UL,0xb5c0fbcfUL,0xe9b5dba5UL,0x3956c25bUL,0x59f111f1UL,0x923f82a4UL,0xab1c5ed5UL,
0xd807aa98UL,0x12835b01UL,0x243185beUL,0x550c7dc3UL,0x72be5d74UL,0x80deb1feUL,0x9bdc06a7UL,0xc19bf174UL,
0xe49b69c1UL,0xefbe4786UL,0x0fc19dc6UL,0x240ca1ccUL,0x2de92c6fUL,0x4a7484aaUL,0x5cb0a9dcUL,0x76f988daUL,
0x983e5152UL,0xa831c66dUL,0xb00327c8UL,0xbf597fc7UL,0xc6e00bf3UL,0xd5a79147UL,0x06ca6351UL,0x14292967UL,
0x27b70a85UL,0x2e1b2138UL,0x4d2c6dfcUL,0x53380d13UL,0x650a7354UL,0x766a0abbUL,0x81c2c92eUL,0x92722c85UL,
0xa2bfe8a1UL,0xa81a664bUL,0xc24b8b70UL,0xc76c51a3UL,0xd192e819UL,0xd6990624UL,0xf40e3585UL,0x106aa070UL,
0x19a4c116UL,0x1e376c08UL,0x2748774cUL,0x34b0bcb5UL,0x391c0cb3UL,0x4ed8aa4aUL,0x5b9cca4fUL,0x682e6ff3UL,
0x748f82eeUL,0x78a5636fUL,0x84c87814UL,0x8cc70208UL,0x90befffaUL,0xa4506cebUL,0xbef9a3f7UL,0xc67178f2UL};
#define RR(x,n) (((x)>>(n))|((x)<<(32-(n))))
static void transform(void)
{ U32 a,b,c,d,e,f,g,j,t1,t2; unsigned i;
 for(i=0;i<16;i++) w[i]=((U32)block[i*4]<<24)|((U32)block[i*4+1]<<16)|((U32)block[i*4+2]<<8)|block[i*4+3];
 for(i=16;i<64;i++) w[i]=w[i-16]+(RR(w[i-15],7)^RR(w[i-15],18)^(w[i-15]>>3))+w[i-7]+(RR(w[i-2],17)^RR(w[i-2],19)^(w[i-2]>>10));
 a=h[0];b=h[1];c=h[2];d=h[3];e=h[4];f=h[5];g=h[6];j=h[7];
 for(i=0;i<64;i++) { t1=j+(RR(e,6)^RR(e,11)^RR(e,25))+((e&f)^(~e&g))+k[i]+w[i];t2=(RR(a,2)^RR(a,13)^RR(a,22))+((a&b)^(a&c)^(b&c));j=g;g=f;f=e;e=d+t1;d=c;c=b;b=a;a=t1+t2; }
 h[0]+=a;h[1]+=b;h[2]+=c;h[3]+=d;h[4]+=e;h[5]+=f;h[6]+=g;h[7]+=j;
}
static void hashinit(void)
{ h[0]=0x6a09e667UL;h[1]=0xbb67ae85UL;h[2]=0x3c6ef372UL;h[3]=0xa54ff53aUL;h[4]=0x510e527fUL;h[5]=0x9b05688cUL;h[6]=0x1f83d9abUL;h[7]=0x5be0cd19UL;bn=0;total=0; }
static void hashbyte(unsigned char c) { block[bn++]=c; if(bn==64) {transform();bn=0;} }
static void hashfinal(char *out)
{ static char hex[]="0123456789abcdef"; U32 bits=total*8; unsigned i; unsigned char b;
 hashbyte(128);while(bn!=56) hashbyte(0);for(i=0;i<4;i++) hashbyte(0);for(i=0;i<4;i++) hashbyte((unsigned char)(bits>>(24-8*i)));
 for(i=0;i<32;i++) {b=(unsigned char)(h[i/4]>>(24-8*(i%4)));out[i*2]=hex[b>>4];out[i*2+1]=hex[b&15];} out[64]=0;
}
static void pin(const char *p,unsigned long size,const char *hash)
{ int fd,n; unsigned i; unsigned long count=0; char out[65]; regular(p,0); fd=open(path(p),O_RDONLY|O_BINARY); if(fd<0) fail("Cannot open pinned file.");hashinit();
 while((n=read(fd,buf,sizeof(buf)))>0) {count+=n;if(count>size) fail("Pinned file length mismatch.");for(i=0;i<(unsigned)n;i++) hashbyte(buf[i]);}
 if(n<0||close(fd)) fail("Pinned file read failed."); if(count!=size) fail("Pinned file length mismatch.");total=(U32)count;hashfinal(out);if(strcmp(out,hash)) fail("Pinned file SHA-256 mismatch.");
}
static void exact(const char *a,const char *b)
{
#ifdef HOST_TEST
 unsigned char other[1024]; int x,y,n,m; x=open(path(a),O_RDONLY|O_BINARY);y=open(path(b),O_RDONLY|O_BINARY);if(x<0||y<0) fail("Compare open failed."); do {n=read(x,buf,sizeof(buf));m=read(y,other,sizeof(other));if(n<0||m<0||n!=m||memcmp(buf,other,n)) fail("Byte comparison failed.");}while(n);if(close(x)||close(y)) fail("Compare close failed.");
#else
 if(spawnl(P_WAIT,CHECK,CHECK,a,b,NULL)) fail("TSCHECK byte verification failed.");
#endif
}
static void copymode(const char *from,const char *to,int isnew)
{ int a,b,n; unsigned chunks=0;
#ifndef HOST_TEST
 unsigned date,time;
#endif
 a=open(path(from),O_RDONLY|O_BINARY);if(a<0) fail("Cannot open copy source.");
 b=open(path(to),O_WRONLY|O_BINARY|(isnew?(O_CREAT|O_EXCL):O_TRUNC),S_IREAD|S_IWRITE);if(b<0) fail("Cannot open copy destination; no overwrite fallback.");
#ifndef HOST_TEST
 if(_dos_getftime(a,&date,&time)) fail("Cannot read source timestamp.");
#endif
 while((n=read(a,buf,sizeof(buf)))>0) {if(write(b,buf,n)!=n) fail("Copy failed or disk full."); ++chunks;
#ifdef HOST_TEST
 if(getenv("TR7_SHORT") && atoi(getenv("TR7_SHORT"))==(isnew?1:2) && chunks==3) {flushclose(b);close(a);fail("Injected interrupted copy.");}
#endif
 }
 if(n<0||close(a)) fail("Copy source read or close failed.");
#ifndef HOST_TEST
 if(_dos_setftime(b,date,time)) fail("Cannot preserve file timestamp.");
#endif
 flushclose(b);exact(from,to);
}
static char *trim(char *s)
{ char *e;while(*s==' '||*s=='\t') ++s;e=s+strlen(s);while(e>s&&(e[-1]==' '||e[-1]=='\t')) --e;*e=0;return s; }
static void active(Mode *m)
{ int f,n,z=0;unsigned i;int boot=0,boots=0,keys=0;char *p,*end,*line,*v,*e;
 f=open(path(INI),O_RDONLY|O_BINARY);if(f<0) fail("SYSTEM.INI missing.");while(z<16001&&(n=read(f,inibuf+z,16001-z))>0) z+=n;if(z==16001||n<0||close(f)||!z) fail("SYSTEM.INI unreadable or too large.");
 for(i=0;i<(unsigned)z;i++) if((inibuf[i]<32&&inibuf[i]!=9&&inibuf[i]!=10&&inibuf[i]!=13)||inibuf[i]==127) fail("Unsupported SYSTEM.INI bytes.");inibuf[z]=0;p=(char*)inibuf;end=p+z;
 while(p<end) {line=p;while(p<end&&*p!='\r'&&*p!='\n') ++p;if(p<end) *p++=0;while(p<end&&(*p=='\r'||*p=='\n')) ++p;line=trim(line);if(!*line||*line==';'||*line=='#') continue;
 if(*line=='[') {e=strchr(line,']');if(!e) fail("Malformed INI section.");*e++=0;e=trim(e);if(*e&&*e!=';') fail("Malformed INI section suffix.");boot=!stricmp(trim(line+1),"boot");if(boot) ++boots;continue;}
 if(!boot) continue;v=strchr(line,'=');if(!v) continue;*v++=0;if(stricmp(trim(line),"display.drv")) continue;++keys;v=trim(v);e=strchr(v,';');if(e)*e=0;v=trim(v);if(stricmp(v,m->name)&&stricmp(v,current)) fail("Selected mode is not the active Windows display.");
 }
 if(boots!=1||keys!=1) fail("Need one unambiguous active [boot] display.drv.");
}
static void guard(Mode *m)
{ unsigned i;char p[80];static char *side[]={"TSHELL.JRN","TSHELL.NEW","TSHELL.OLD","TSHELL.RST"};
#ifdef HOST_TEST
 const char *v=getenv("TR7_CWD");if(v&&strcmp(v,ROOT)) fail("Run from C:\\TRIAL7 only.");
#else
 char cwd[80]; union REGS r; r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al&&r.h.al!=0x80) fail("Exit Windows completely first.");r.x.ax=0x4680;int86(0x2f,&r,&r);if(!r.x.ax) fail("Exit Windows completely first.");if(!getcwd(cwd,sizeof(cwd))||stricmp(cwd,ROOT)) fail("Run from C:\\TRIAL7 only.");
#endif
 directory(ROOT);directory(ROOT "\\BACKUP");directory("C:\\WINDOWS");directory("C:\\WINDOWS\\SYSTEM");directory("C:\\WINXT");regular("C:\\WINDOWS\\WIN.COM",0);regular(INI,0);
 pin(SHELL,shell_size,shell_hash);pin(CHECK,check_size,check_hash);
 for(i=0;i<4;i++) {sprintf(p,"C:\\WINDOWS\\%s",side[i]);if(exists(p)) fail("Pending shell recovery. Use the existing WINXT recovery first.");}
#ifndef HOST_TEST
 if(spawnl(P_WAIT,SHELL,SHELL,"STATUS",INI,NULL)) fail("SHELLSEL safety check failed; no changes made.");
#endif
 active(m);
}
static void checkmarker(void)
{ unsigned n=(unsigned)strlen(marker);int f,r;regular(USED,0);f=open(path(USED),O_RDONLY|O_BINARY);if(f<0) fail("Trial marker missing.");r=read(f,buf,sizeof(buf));if(r!=(int)n||memcmp(buf,marker,n)||close(f)) fail("Trial marker incomplete, changed, or for another mode."); }
static void mark(void)
{ int f;unsigned n=(unsigned)strlen(marker);f=open(path(USED),O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);if(f<0) fail("Cannot create exclusive trial marker.");modified=1;if(write(f,marker,n)!=(int)n) fail("Trial marker write failed.");flushclose(f);checkmarker(); }
int main(int argc,char **argv)
{ unsigned i;int restore;Mode *m=NULL;char p[80];
 if(argc!=4||strcmp(argv[3],"YES")||(strcmp(argv[1],"APPLY")&&strcmp(argv[1],"RESTORE"))) {puts("Use APPLY mode YES or RESTORE mode YES from C:\\TRIAL7 in plain DOS.\nModes: 16016 32016 3204 6404 6402. No paths or extra arguments.");return 2;}
 restore=!strcmp(argv[1],"RESTORE");for(i=0;i<sizeof(modes)/sizeof(modes[0]);i++) if(!strcmp(argv[2],modes[i].arg)) m=&modes[i];if(!m) fail("Unknown mode.");
 sprintf(current,"C:\\WINDOWS\\SYSTEM\\%s",m->name);sprintf(original,ROOT "\\TR5\\%s",m->name);sprintf(candidate,ROOT "\\NEW\\%s",m->name);sprintf(backup,ROOT "\\BACKUP\\%s",m->name);sprintf(source,"C:\\WINXT\\%s",m->name);sprintf(marker,"TRIAL7 one-shot trial\r\n%s\r\n",m->name);
 guard(m);
 if(restore) {checkmarker();pin(backup,m->os,m->oh);if(exists(current)) regular(current,1);else fail("Target is missing; retain files for manual recovery.");puts("Restoring the saved installed driver...");modified=1;copymode(backup,current,0);pin(current,m->os,m->oh);puts("RESTORE VERIFIED. Original installed bytes restored; backup retained.");return 0;}
 if(exists(USED)) fail("This kit has already been used. Restore; do not reapply.");for(i=0;i<sizeof(modes)/sizeof(modes[0]);i++) {sprintf(p,ROOT "\\BACKUP\\%s",modes[i].name);if(exists(p)) fail("Existing backup found. Refusing to overwrite it.");}
 regular(current,1);pin(original,m->os,m->oh);pin(source,m->os,m->oh);pin(current,m->os,m->oh);pin(candidate,m->ns,m->nh);exact(original,current);
#ifndef HOST_TEST
 { struct diskfree_t d;unsigned long bytes;if(_dos_getdiskfree(3,&d)) fail("Cannot check free disk space.");bytes=(unsigned long)d.avail_clusters*d.sectors_per_cluster*d.bytes_per_sector;if(bytes<m->os+m->ns+65536UL) fail("Need at least 192 KB free on C:."); }
#endif
 puts("Saving and verifying the installed original before any overwrite...");mark();copymode(current,backup,1);pin(backup,m->os,m->oh);exact(original,backup);checkpoint();
 puts("Applying test driver...");copymode(candidate,current,0);pin(current,m->ns,m->nh);puts("APPLY VERIFIED. Start only with your existing C:\\WINXT\\WINXT launcher.\nRestore from plain DOS after testing. Keep this entire kit.");return 0;
}
