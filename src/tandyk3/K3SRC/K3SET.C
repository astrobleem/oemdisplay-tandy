/* K3SET: conservative DOS 3.3+ / 8086 SYSTEM.INI keyboard transaction.
 * Build: MSC 6 /AS /G0 (DOS runtime, never /Gw or Windows libraries).
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
#include <unistd.h>
#include <stdint.h>
typedef uint32_t U32;
#define O_BINARY 0
#define S_IREAD S_IRUSR
#define S_IWRITE S_IWUSR
#else
#include <io.h>
#include <dos.h>
typedef unsigned long U32;
#endif

#define MAXINI 14000
#define HEAD 144
#define CAP (MAXINI+HEAD+1)
#define PLEN 128
#define SEL "TNDYK3.DRV"
static unsigned char orig[CAP], cur[CAP], dest[CAP];
static char ini[PLEN], jrn[PLEN], bak[PLEN], sav[PLEN];
static char tmp[PLEN], old[PLEN], rst[PLEN];
static char names[64][64];
static unsigned on, cn, dn;
static int steps;

typedef struct { unsigned a, b; } Keyboard;
static Keyboard os, cs;

static void die(const char *s)
{ fprintf(stderr,"K3SET: %s\nNo unsafe fallback was attempted.\n",s); exit(1); }
static int eqi(const char *a,const char *b)
{ while (*a && *b) { if(toupper((unsigned char)*a)!=toupper((unsigned char)*b)) return 0; ++a; ++b; } return *a==*b; }
static int space(unsigned char c) { return c==' ' || c=='\t'; }
static int exists(const char *p)
{ struct stat st; if(!stat((char*)p,&st)) return 1; if(errno==ENOENT) return 0; die("Cannot inspect a file."); return 0; }
static void writable(const char *p)
{
#ifdef HOST_TEST
    struct stat st;
    if(stat((char*)p,&st) || !S_ISREG(st.st_mode) || !(st.st_mode&0222)) die("File is not a writable regular file.");
#else
    unsigned a;
    if(_dos_getfileattr(p,&a) || (a&0x1f)) die("File has unsupported attributes or is unavailable.");
#endif
}
static void checkpoint(void)
{
#ifndef HOST_TEST
    union REGS r; r.h.ah=0x0d; intdos(&r,&r);
#else
    const char *p;
    ++steps; p=getenv("K3_CRASH");
    if(p && atoi(p)==steps) _exit(99);
#endif
}
static void commit(int fd)
{
#ifdef HOST_TEST
    if(fsync(fd)) die("Cannot flush staged file.");
#else
    union REGS r;
    r.x.ax=0x6800; r.x.bx=fd; intdos(&r,&r);
    if(r.x.cflag) die("Cannot commit staged file (DOS 3.3+ required).");
#endif
}
static void out(int fd,const unsigned char *p,unsigned n)
{
    int w;
#ifdef HOST_TEST
    const char *v=getenv("K3_SHORT");
    if(v && atoi(v)==steps+1) {
        if(n>1) write(fd,p,n/2);
        close(fd); die("Injected short write.");
    }
#endif
    w=write(fd,p,n); if(w<0 || (unsigned)w!=n) { close(fd); die("Write failed or disk full. Keep all sidecars."); }
}
static int create(const char *p)
{ int fd; if(exists(p)) die("Staging/backup collision; keep files for inspection."); fd=open(p,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE); if(fd<0) die("Cannot create staged file."); return fd; }
static void finish(int fd)
{ commit(fd); if(close(fd)) die("Close failed. Keep all sidecars."); checkpoint(); }
static unsigned readall(const char *p,unsigned char *b,unsigned lim)
{ int f,n; unsigned z=0; f=open(p,O_RDONLY|O_BINARY); if(f<0) die("Required file cannot be read."); while(z<lim) { n=read(f,b+z,lim-z); if(n<0) { close(f); die("Read failed."); } if(!n) break; z+=(unsigned)n; } if(z==lim) { unsigned char c; n=read(f,&c,1); if(n!=0) {close(f);die("File exceeds safe size limit.");} } if(close(f)) die("Read close failed."); return z; }
static int same(const char *p,const unsigned char *b,unsigned n)
{ unsigned char part[256]; unsigned off=0,k; int f,r; f=open(p,O_RDONLY|O_BINARY); if(f<0) return 0; while(off<n) { k=n-off; if(k>sizeof(part)) k=sizeof(part); r=read(f,part,k); if(r!=(int)k || memcmp(part,b+off,k)) {close(f);return 0;} off+=k; } r=read(f,part,1); close(f); return r==0; }
static unsigned long crc(const unsigned char *p,unsigned n)
{ unsigned long c=0xffffffffUL; unsigned i; while(n--) { c^=*p++; for(i=0;i<8;++i) c=(c&1)?(c>>1)^0xedb88320UL:c>>1; } return (c^0xffffffffUL)&0xffffffffUL; }
static void snapshot(const char *p,const unsigned char *b,unsigned n)
{ unsigned char h[HEAD]; unsigned long c; int f; unsigned i; memset(h,0,HEAD); memcpy(h,"K3SEL01\n",8); strcpy((char*)h+8,ini); h[136]=(unsigned char)n; h[137]=(unsigned char)(n>>8); c=crc(b,n); for(i=0;i<4;++i) h[138+i]=(unsigned char)(c>>(i*8)); f=create(p); out(f,h,HEAD); out(f,b,n); finish(f); }
static unsigned loadsnap(const char *p,unsigned char *b)
{ unsigned n,z,i; unsigned long c=0; z=readall(p,b,MAXINI+HEAD); if(z<HEAD || memcmp(b,"K3SEL01\n",8) || !memchr(b+8,0,PLEN) || strcmp((char*)b+8,ini) || b[142] || b[143]) die("Unknown, corrupt, or wrong-path journal. Keep every file."); n=b[136]+((unsigned)b[137]<<8); if(n>MAXINI || z!=n+HEAD) die("Incomplete journal. Keep every file."); for(i=0;i<4;++i) c|=((unsigned long)b[138+i])<<(i*8); if(crc(b+HEAD,n)!=c) die("Journal checksum mismatch. Keep every file."); memmove(b,b+HEAD,n); return n; }
static void writefile(const char *p,const unsigned char *b,unsigned n)
{ int f=create(p); out(f,b,n); finish(f); if(!same(p,b,n)) die("Staged file reread mismatch."); }
static void movefile(const char *a,const char *b)
{ if(exists(b)) die("Rename destination already exists."); writable(a); if(rename(a,b)) die("Rename failed. Run RESTORE before Windows."); checkpoint(); }
static void remove_known(const char *p,const unsigned char *b,unsigned n)
{ if(!exists(p)) return; if(!same(p,b,n)) die("Unknown sidecar; refusing to delete it."); writable(p); if(remove(p)) die("Cannot remove verified sidecar."); checkpoint(); }
static void remove_snap(const char *p,const unsigned char *b,unsigned n)
{ /* Reread into dest only after it is no longer needed by the caller. */
  unsigned z; if(!exists(p)) return; z=loadsnap(p,dest); if(z!=n || memcmp(dest,b,n)) die("Journal changed during recovery."); writable(p); if(remove(p)) die("Cannot remove verified journal."); checkpoint(); }

/* Strict, deterministic INI subset. Preserve every byte except the keyboard value.
 * Reject ambiguous/duplicate sections and keyboard keys, embedded NUL/control bytes,
 * malformed section lines, empty/overlong keyboard values and excessive sections.
 */
static int keymatch(const unsigned char *b,const char *s,unsigned n)
{ unsigned i; for(i=0;i<n;++i) if(toupper(b[i])!=toupper((unsigned char)s[i])) return 0; return 1; }
static Keyboard parse(const unsigned char *b,unsigned n)
{ unsigned p=0,e,q,t,x,y,k,count=0,boots=0,keys=0; int boot=0; char name[64]; Keyboard s;
  s.a=s.b=0; if(!n) die("Empty SYSTEM.INI.");
  for(k=0;k<n;++k) if((b[k]<32 && b[k]!='\r' && b[k]!='\n' && b[k]!='\t') || b[k]==127) die("Unsupported control byte in INI.");
  while(p<n) {
    e=p; while(e<n && b[e]!='\r' && b[e]!='\n') ++e;
    q=p; while(q<e && space(b[q])) ++q;
    if(q<e && b[q]!=';' && b[q]!='#') {
      if(b[q]=='[') {
        t=q+1; while(t<e && b[t]!=']') ++t; if(t==e) die("Malformed INI section.");
        x=q+1; y=t; while(x<y && space(b[x])) ++x; while(y>x && space(b[y-1])) --y;
        if(y==x || y-x>63 || count==64) die("Unsupported INI section name/count.");
        for(k=0;k<y-x;++k) { name[k]=(char)toupper(b[x+k]); }
        name[y-x]=0;
        for(k=0;k<count;++k) if(!strcmp(names[k],name)) die("Duplicate INI section.");
        strcpy(names[count++],name); boot=!strcmp(name,"BOOT"); if(boot) ++boots;
        q=t+1; while(q<e && space(b[q])) ++q; if(q<e && b[q]!=';') die("Unexpected text after section.");
      } else if(boot) {
        t=q; while(t<e && b[t]!='=') ++t;
        if(t<e) { y=t; while(y>q && space(b[y-1])) --y;
          if(y-q==12 && keymatch(b+q,"keyboard.drv",12)) {
            ++keys; x=t+1; while(x<e && space(b[x])) ++x;
            y=x; while(y<e && b[y]!=';') ++y; while(y>x && space(b[y-1])) --y;
            if(y==x || y-x>255) die("Empty or overlong keyboard value.");
            s.a=x; s.b=y;
          }
        }
      }
    }
    p=e; if(p<n && b[p]=='\r') ++p; if(p<n && b[p]=='\n') ++p;
  }
  if(boots!=1 || keys!=1) die("Need exactly one [boot] section and keyboard key.");
  return s;
}
static int keyboardis(const unsigned char *b,Keyboard s,const char *v)
{ unsigned i,l=(unsigned)strlen(v); if(s.b-s.a!=l) return 0; for(i=0;i<l;++i) if(toupper(b[s.a+i])!=toupper((unsigned char)v[i])) return 0; return 1; }
static int originalkeyboard(const unsigned char *b,Keyboard s)
{ return s.b-s.a==os.b-os.a && !memcmp(b+s.a,orig+os.a,s.b-s.a); }
static unsigned replace(const unsigned char *b,unsigned n,Keyboard s,const unsigned char *v,unsigned l,unsigned char *d)
{ unsigned z; if(n-(s.b-s.a)>(unsigned)MAXINI-l) die("Result exceeds safe size limit."); z=n-(s.b-s.a)+l; memcpy(d,b,s.a); memcpy(d+s.a,v,l); memcpy(d+s.a+l,b+s.b,n-s.b); return z; }
static void baseline(void)
{ unsigned z; if(exists(sav)) { z=loadsnap(sav,dest); parse(dest,z); if(!exists(bak) || !same(bak,dest,z)) die("Saved backup missing or changed."); }
  else if(exists(bak)) die("Backup exists without its ownership record."); }
static void no_temps(void)
{ if(exists(tmp)||exists(old)||exists(rst)) die("Unresolved staging files; run RESTORE or inspect manually."); }
static void pathof(char *outp,const char *name)
{ char *p; strcpy(outp,ini); p=strrchr(outp,'\\');
#ifdef HOST_TEST
  if(!p) p=strrchr(outp,'/');
#endif
  if(!p) die("An absolute SYSTEM.INI path is required.");
  strcpy(p+1,name); }
#ifndef HOST_TEST
static void dospath(const char *p)
{ unsigned a=0,b=0; int dot=0;
  p+=3;
  while(*p) {
    if(*p=='\\') {
      if(!a || a>8 || b>3 || (dot&&!b)) die("Use DOS 8.3 path components.");
      a=b=0; dot=0;
    } else if(*p=='.') {
      if(dot || !a) die("Invalid DOS path component."); dot=1;
    } else {
      if(!isalnum((unsigned char)*p) && *p!='_' && *p!='-' && *p!='~') die("Unsupported character in DOS path.");
      if(dot) ++b; else ++a;
    }
    ++p;
  }
  if(!a || a>8 || b>3 || (dot&&!b)) die("Use DOS 8.3 path components.");
}
#endif
static void setup(const char *p)
{ unsigned i; char *base;
  if(strlen(p)>=PLEN || strlen(p)<11) die("Path too long or invalid.");
  strcpy(ini,p);
#ifdef HOST_TEST
  if(ini[0]!='/') die("Absolute path required.");
  base=strrchr(ini,'/');
#else
  if(!isalpha(ini[0]) || ini[1]!=':' || ini[2]!='\\') die("Use absolute drive:\\directory\\SYSTEM.INI.");
  for(i=0;ini[i];++i) { if(ini[i]=='/' || ini[i]==' ' || ini[i]=='"' || ini[i]=='*' || ini[i]=='?') die("Use an unquoted DOS 8.3 path without spaces."); ini[i]=(char)toupper((unsigned char)ini[i]); }
  dospath(ini);
  base=strrchr(ini,'\\');
#endif
  if(!base || !eqi(base+1,"SYSTEM.INI")) die("Filename must be SYSTEM.INI.");
  for(i=0;ini[i];++i) if(ini[i]=='.' && ini[i+1]=='.') die("Parent-relative paths are forbidden.");
  pathof(jrn,"K3SEL.JRN"); pathof(bak,"K3SEL.BAK"); pathof(sav,"K3SEL.SAV"); pathof(tmp,"K3SEL.NEW"); pathof(old,"K3SEL.OLD"); pathof(rst,"K3SEL.RST");
}
typedef struct { U32 h[8], bytes; unsigned n; unsigned char b[64]; } SHA;
static const U32 K[64]={
0x428a2f98UL,0x71374491UL,0xb5c0fbcfUL,0xe9b5dba5UL,0x3956c25bUL,0x59f111f1UL,0x923f82a4UL,0xab1c5ed5UL,
0xd807aa98UL,0x12835b01UL,0x243185beUL,0x550c7dc3UL,0x72be5d74UL,0x80deb1feUL,0x9bdc06a7UL,0xc19bf174UL,
0xe49b69c1UL,0xefbe4786UL,0x0fc19dc6UL,0x240ca1ccUL,0x2de92c6fUL,0x4a7484aaUL,0x5cb0a9dcUL,0x76f988daUL,
0x983e5152UL,0xa831c66dUL,0xb00327c8UL,0xbf597fc7UL,0xc6e00bf3UL,0xd5a79147UL,0x06ca6351UL,0x14292967UL,
0x27b70a85UL,0x2e1b2138UL,0x4d2c6dfcUL,0x53380d13UL,0x650a7354UL,0x766a0abbUL,0x81c2c92eUL,0x92722c85UL,
0xa2bfe8a1UL,0xa81a664bUL,0xc24b8b70UL,0xc76c51a3UL,0xd192e819UL,0xd6990624UL,0xf40e3585UL,0x106aa070UL,
0x19a4c116UL,0x1e376c08UL,0x2748774cUL,0x34b0bcb5UL,0x391c0cb3UL,0x4ed8aa4aUL,0x5b9cca4fUL,0x682e6ff3UL,
0x748f82eeUL,0x78a5636fUL,0x84c87814UL,0x8cc70208UL,0x90befffaUL,0xa4506cebUL,0xbef9a3f7UL,0xc67178f2UL};
#define RR(x,n) (((x)>>(n))|((x)<<(32-(n))))
static void transform(SHA *s) {
 U32 w[64],a,b,c,d,e,f,g,h,t,u; unsigned i;
 for(i=0;i<16;i++)w[i]=((U32)s->b[i*4]<<24)|((U32)s->b[i*4+1]<<16)|((U32)s->b[i*4+2]<<8)|s->b[i*4+3];
 for(i=16;i<64;i++){a=w[i-15];b=w[i-2];w[i]=w[i-16]+(RR(a,7)^RR(a,18)^(a>>3))+w[i-7]+(RR(b,17)^RR(b,19)^(b>>10));}
 a=s->h[0];b=s->h[1];c=s->h[2];d=s->h[3];e=s->h[4];f=s->h[5];g=s->h[6];h=s->h[7];
 for(i=0;i<64;i++){t=h+(RR(e,6)^RR(e,11)^RR(e,25))+((e&f)^((~e)&g))+K[i]+w[i];u=(RR(a,2)^RR(a,13)^RR(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+t;d=c;c=b;b=a;a=t+u;}
 s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void init(SHA *s){static const U32 h[8]={0x6a09e667UL,0xbb67ae85UL,0x3c6ef372UL,0xa54ff53aUL,0x510e527fUL,0x9b05688cUL,0x1f83d9abUL,0x5be0cd19UL};memcpy(s->h,h,sizeof(h));s->n=0;s->bytes=0;}
static void update(SHA *s,const unsigned char *p,unsigned n){s->bytes+=n;while(n--){s->b[s->n++]=*p++;if(s->n==64){transform(s);s->n=0;}}}
static void sha_finish(SHA *s,char *out){unsigned i,j;U32 bits=s->bytes*8;static const char hex[]="0123456789abcdef";s->b[s->n++]=128;if(s->n>56){while(s->n<64)s->b[s->n++]=0;transform(s);s->n=0;}while(s->n<60)s->b[s->n++]=0;for(i=0;i<4;i++)s->b[60+i]=(unsigned char)(bits>>(24-i*8));transform(s);for(i=0;i<8;i++)for(j=0;j<4;j++){unsigned v=(unsigned)((s->h[i]>>(24-j*8))&255);*out++=hex[v>>4];*out++=hex[v&15];}*out=0;}
static int selftest(void){SHA s;char h[65];init(&s);sha_finish(&s,h);if(strcmp(h,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))return 0;init(&s);update(&s,(const unsigned char *)"abc",3);sha_finish(&s,h);return !strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");}

#include "K3PIN.H"
static char driver[PLEN], target[PLEN], dstage[PLEN], dbak[PLEN], dsv[PLEN];
static void systempath(char *p,const char *name)
{ unsigned n; pathof(p,"SYSTEM"); n=(unsigned)strlen(p);
  if(n+1+strlen(name)>=PLEN) die("SYSTEM path too long.");
#ifdef HOST_TEST
  p[n++]='/';
#else
  p[n++]='\\';
#endif
  strcpy(p+n,name);
}
static void driver_paths(void)
{ systempath(target,SEL); systempath(dstage,"K3DRV.NEW");
  pathof(dbak,"K3ORIG.BAK"); pathof(dsv,"K3ORIG.SAV"); }
static void resolve_driver(const unsigned char *b,Keyboard k)
{ char name[13],other[PLEN]; unsigned i,n=k.b-k.a,dots=0,first=0,last=0;
  if(n>12 || n<5) die("Original keyboard must be a plain DOS 8.3 filename.");
  for(i=0;i<n;++i) { unsigned char c=b[k.a+i];
    if(c=='.') { if(dots++ || !first) die("Invalid original driver filename."); }
    else { if(!isalnum(c)&&c!='_'&&c!='-'&&c!='~') die("Unsafe original driver filename."); if(dots) ++last; else ++first; }
    name[i]=(char)toupper(c);
  } name[n]=0;
  if(first>8 || last>3 || !dots || !last || eqi(name,SEL) || !eqi(name+n-4,".DRV")) die("Unsupported original driver filename.");
  pathof(driver,name); systempath(other,name);
  if(exists(driver) && exists(other)) die("Original keyboard driver exists in both Windows and SYSTEM; ambiguous.");
  if(exists(other)) strcpy(driver,other);
  if(!exists(driver)) die("Original keyboard driver is missing.");
}
static int pinned(const char *p)
{ int f,r; unsigned char b[512]; unsigned long n=0; SHA sh; char h[65];
  if(!K3_PIN_READY) die("Driver pin is not released; installer disabled.");
  if(!selftest()) die("SHA256 self-test failed.");
  f=open(p,O_RDONLY|O_BINARY); if(f<0) return 0; init(&sh);
  while((r=read(f,b,sizeof(b)))>0) { n+=r; if(n>K3_PIN_SIZE) {close(f);return 0;} update(&sh,b,(unsigned)r); }
  if(r<0) { close(f); return 0; }
  if(close(f)) return 0;
  sha_finish(&sh,h);
  return n==K3_PIN_SIZE && !strcmp(h,K3_PIN_SHA256);
}
/* Driver files are never overwritten or deleted. The original remains in place.
   DSV records its exact bytes; the INI baseline binds its selected filename. */
static void driver_verify(int complete)
{ unsigned n;
  driver_paths(); resolve_driver(orig,os);
  if(exists(dsv)) {
    n=loadsnap(dsv,cur);
    if(!same(driver,cur,n)) die("Original driver changed; refusing rollback to unverified bytes.");
    if(exists(dbak)) { if(!same(dbak,cur,n)) die("Original driver backup changed."); }
    else if(complete) die("Original driver backup incomplete; RESTORE required.");
  } else if(exists(dbak)||exists(target)||exists(dstage)||complete) die("Unowned or incomplete driver files.");
  if(exists(target) && !pinned(target)) die("Foreign target driver; never overwritten.");
  if(exists(dstage) && !pinned(dstage)) die("Unknown partial driver stage; preserve it for inspection.");
  if(complete && (!exists(target)||exists(dstage))) die("Driver installation incomplete.");
}
static void driver_preflight(void)
{ unsigned n; Keyboard k;
  driver_paths(); if(!pinned("TNDYK3.DRV")) die("Run from package directory with exact pinned TNDYK3.DRV.");
  if(exists(jrn)) { on=loadsnap(jrn,orig); os=parse(orig,on); driver_verify(0); return; }
  on=readall(ini,orig,MAXINI); os=parse(orig,on); resolve_driver(orig,os);
  if(exists(sav)) { n=loadsnap(sav,cur); k=parse(cur,n);
    if(k.b-k.a!=os.b-os.a || memcmp(cur+k.a,orig+os.a,k.b-k.a)) die("Original keyboard selection differs from saved baseline."); }
  driver_verify(0);
}
static void driver_prepare(void)
{ unsigned n,z;
  driver_verify(0);
  if(!exists(dsv)) { n=readall(driver,cur,MAXINI); if(!n) die("Empty original keyboard driver.");
    snapshot(dsv,cur,n); z=loadsnap(dsv,dest); if(z!=n||memcmp(cur,dest,n)) die("Driver ownership record reread failed."); }
  n=loadsnap(dsv,cur); if(!same(driver,cur,n)) die("Original driver changed during backup.");
  if(!exists(dbak)) writefile(dbak,cur,n);
  if(!exists(target)) { if(!exists(dstage)) { n=readall("TNDYK3.DRV",cur,MAXINI); if(!pinned("TNDYK3.DRV")) die("Package driver changed."); writefile(dstage,cur,n); }
    if(!pinned(dstage)) die("Driver stage hash mismatch.");
    movefile(dstage,target); }
  else if(exists(dstage)) die("Target and stage both exist; preserve evidence.");
  driver_verify(1);
}
static void not_windows(void)
{
#ifdef HOST_TEST
  if(getenv("K3_WINDOWS")) die("Exit Windows completely.");
#else
  union REGS r; memset(&r,0,sizeof(r)); r.x.ax=0x1600; int86(0x2f,&r,&r);
  if(r.h.al && r.h.al!=0x80) die("Exit Windows completely before using K3SET.");
  memset(&r,0,sizeof(r)); r.x.ax=0x4680; int86(0x2f,&r,&r);
  if(!r.x.ax) die("Exit Windows completely before using K3SET.");
#endif
}

static void cleanup_restored(void)
{ unsigned z; Keyboard s;
  z=readall(ini,cur,MAXINI); s=parse(cur,z);
  if(!originalkeyboard(cur,s)) die("Restoration proof failed; journal retained.");
  if(exists(tmp)||exists(old)||exists(rst)) die("Unresolved transaction before journal cleanup.");
  if(exists(dsv) && !exists(dbak)) { z=loadsnap(dsv,cur); writefile(dbak,cur,z); }
  if(exists(dstage)) { if(!pinned(dstage)) die("Unknown driver stage; preserve evidence."); z=readall(dstage,cur,MAXINI); remove_known(dstage,cur,z); }
  remove_snap(jrn,orig,on); puts("Original keyboard selection restored and reread verified.");
}
static void recover(void)
{ unsigned z;
  if(!exists(jrn)) { no_temps(); baseline(); if(!exists(ini)) die("SYSTEM.INI missing; no active recovery journal."); on=readall(ini,orig,MAXINI); os=parse(orig,on); if(keyboardis(orig,os,SEL)) die("K3SEL is selected without an active journal."); driver_verify(0); puts("No active keyboard selection; SYSTEM.INI unchanged."); return; }
  on=loadsnap(jrn,orig); os=parse(orig,on); driver_verify(0); if(keyboardis(orig,os,SEL)) die("Journal original keyboard is already K3SEL."); if(exists(sav) && !exists(bak)) {
    z=loadsnap(sav,dest);
    if(z!=on || memcmp(dest,orig,on) || !exists(ini) || !same(ini,orig,on) || exists(tmp)||exists(old)||exists(rst)) die("Missing backup outside proven initial preparation.");
    writefile(bak,orig,on);
  }
  baseline();
  if(!exists(sav)) { /* Initial interruption before persistent baseline creation. */
    if(!exists(ini) || !same(ini,orig,on) || exists(tmp)||exists(old)||exists(rst)) die("Incomplete initial backup transaction.");
    snapshot(sav,orig,on); if(loadsnap(sav,dest)!=on || memcmp(dest,orig,on)) die("Backup record reread failed.");
  }
  if(!exists(bak)) writefile(bak,orig,on);
  driver_verify(0);
  if(exists(rst)) {
    cn=loadsnap(rst,cur); cs=parse(cur,cn); if(!keyboardis(cur,cs,SEL)) die("Recovery journal does not contain selected keyboard.");
    dn=replace(cur,cn,cs,orig+os.a,os.b-os.a,dest);
    if(exists(old) && !same(old,cur,cn)) die("Recovery old-file identity mismatch.");
    if(exists(tmp) && !same(tmp,dest,dn)) die("Recovery temporary identity mismatch.");
    if(exists(ini) && same(ini,dest,dn)) { /* Already installed; only verified cleanup remains. */ }
    else {
      if(exists(ini) && !same(ini,cur,cn)) die("SYSTEM.INI changed during interrupted recovery.");
      if(!exists(ini) && !exists(old)) die("Missing SYSTEM.INI without proven interrupted rename.");
      if(!exists(tmp)) { if(!exists(ini)) die("Missing recovery output; manual inspection required."); writefile(tmp,dest,dn); }
      if(exists(ini)) { if(exists(old)) die("Both current and old source exist unexpectedly."); movefile(ini,old); }
      movefile(tmp,ini); if(!same(ini,dest,dn)) die("Recovery output reread failed.");
    }
    remove_known(tmp,dest,dn); remove_known(old,cur,cn);
    remove_snap(rst,cur,cn); cleanup_restored(); return;
  }
  dn=replace(orig,on,os,(const unsigned char*)SEL,(unsigned)strlen(SEL),dest);
  if(exists(old) && !same(old,orig,on)) die("Selection old-file identity mismatch.");
  if(exists(tmp) && !same(tmp,dest,dn)) die("Selection temporary identity mismatch.");
  if(!exists(ini)) {
    if(!exists(old) || !exists(tmp)) die("Missing SYSTEM.INI without proven interrupted selection rename.");
    movefile(old,ini); remove_known(tmp,dest,dn); cleanup_restored(); return;
  }
  if((exists(old)||exists(tmp)) && !same(ini,orig,on) && !same(ini,dest,dn)) die("SYSTEM.INI changed during incomplete selection.");
  remove_known(tmp,dest,dn); remove_known(old,orig,on);
  cn=readall(ini,cur,MAXINI); cs=parse(cur,cn);
  if(originalkeyboard(cur,cs)) { cleanup_restored(); return; }
  if(!keyboardis(cur,cs,SEL)) die("Keyboard changed unexpectedly. Keep journal and inspect manually.");
  writable(ini); snapshot(rst,cur,cn);
  z=loadsnap(rst,dest); if(z!=cn || memcmp(dest,cur,cn)) die("Recovery journal reread failed.");
  /* Re-enter to use precisely the same recovery path after every checkpoint. */
  recover();
}
static void select_keyboard(void)
{ unsigned z; Keyboard s;
  driver_preflight();
  if(exists(jrn)) {
    on=loadsnap(jrn,orig); os=parse(orig,on);
    if(!exists(tmp)&&!exists(old)&&!exists(rst)&&exists(ini)) {
      cn=readall(ini,cur,MAXINI); cs=parse(cur,cn);
      if(keyboardis(cur,cs,SEL) && !keyboardis(orig,os,SEL)) { baseline(); driver_verify(1); puts("K3SEL selection already active."); return; }
    }
    recover();
  }
  no_temps(); baseline(); writable(ini);
  on=readall(ini,orig,MAXINI); os=parse(orig,on); if(keyboardis(orig,os,SEL)) die("K3SEL selected without a recoverable original.");
  snapshot(jrn,orig,on); z=loadsnap(jrn,dest); if(z!=on || memcmp(dest,orig,on)) die("Journal reread failed.");
  if(!exists(sav)) { snapshot(sav,orig,on); z=loadsnap(sav,dest); if(z!=on || memcmp(dest,orig,on)) die("Backup record reread failed."); }
  if(!exists(bak)) writefile(bak,orig,on);
  baseline();
  driver_prepare();
  dn=replace(orig,on,os,(const unsigned char*)SEL,(unsigned)strlen(SEL),dest);
  writefile(tmp,dest,dn);
  if(!same(ini,orig,on)) die("SYSTEM.INI changed before selection.");
  movefile(ini,old); movefile(tmp,ini);
  if(!same(ini,dest,dn)) die("Selected output reread failed.");
  remove_known(old,orig,on);
  cn=readall(ini,cur,MAXINI); s=parse(cur,cn); if(!keyboardis(cur,s,SEL)) die("Selected keyboard verification failed.");
  puts("TNDYK3 selected. RESTORE returns the original keyboard selection.");
}
static void status(void)
{ unsigned z; Keyboard s;
  if(exists(dstage)||(exists(dsv)&&!exists(dbak))) die("Incomplete driver preparation; RESTORE before Windows, APPLY to resume installation.");
  baseline(); if(exists(jrn)) { on=loadsnap(jrn,orig); os=parse(orig,on); puts("Active recovery journal present."); } else if(exists(tmp)||exists(old)||exists(rst)) die("Unowned transaction sidecar present.");
  if(!exists(ini)) die("SYSTEM.INI missing; RESTORE required.");
  z=readall(ini,cur,MAXINI); s=parse(cur,z);
  printf("Current keyboard: %.*s\n",(int)(s.b-s.a),cur+s.a);
  if(keyboardis(cur,s,SEL) && !exists(jrn)) die("K3SEL has no active journal.");
  if(exists(jrn) && !keyboardis(cur,s,SEL) && !originalkeyboard(cur,s)) die("Unexpected keyboard change.");
  if(keyboardis(cur,s,SEL) && exists(jrn)) driver_verify(1);
  if(exists(tmp)||exists(old)||exists(rst)) { puts("Interrupted transaction: run RESTORE before Windows."); exit(1); }
}
int main(int argc,char **argv)
{ if(argc!=3 || (!eqi(argv[1],"APPLY")&&!eqi(argv[1],"RESTORE")&&!eqi(argv[1],"CHECK"))) { puts("Usage: K3SET CHECK|APPLY|RESTORE C:\\WINDOWS\\SYSTEM.INI"); return 2; }
  setup(argv[2]); not_windows();
  if(eqi(argv[1],"APPLY")) select_keyboard(); else if(eqi(argv[1],"RESTORE")) recover(); else { driver_preflight(); status(); } return 0;
}
