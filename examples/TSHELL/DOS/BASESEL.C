/* SHELLSEL: conservative DOS 3.3+ / 8086 SYSTEM.INI shell transaction.
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
#define O_BINARY 0
#define S_IREAD S_IRUSR
#define S_IWRITE S_IWUSR
#else
#include <io.h>
#include <dos.h>
#endif

#define MAXINI 16000
#define HEAD 144
#define CAP (MAXINI+HEAD+1)
#define PLEN 128
#define SEL "TSHELL.EXE"
static unsigned char orig[CAP], cur[CAP], dest[CAP];
static char ini[PLEN], jrn[PLEN], bak[PLEN], sav[PLEN];
static char tmp[PLEN], old[PLEN], rst[PLEN];
static char names[64][64];
static unsigned on, cn, dn;
static int steps;
typedef struct { unsigned a, b; } Shell;
static Shell os, cs;

static void die(const char *s)
{ fprintf(stderr,"SHELLSEL: %s\nNo unsafe fallback was attempted.\n",s); exit(1); }
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
    ++steps; p=getenv("TS_CRASH");
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
    const char *v=getenv("TS_SHORT");
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
{ unsigned char h[HEAD]; unsigned long c; int f; unsigned i; memset(h,0,HEAD); memcpy(h,"TSHSEL1\n",8); strcpy((char*)h+8,ini); h[136]=(unsigned char)n; h[137]=(unsigned char)(n>>8); c=crc(b,n); for(i=0;i<4;++i) h[138+i]=(unsigned char)(c>>(i*8)); f=create(p); out(f,h,HEAD); out(f,b,n); finish(f); }
static unsigned loadsnap(const char *p,unsigned char *b)
{ unsigned n,z,i; unsigned long c=0; z=readall(p,b,MAXINI+HEAD); if(z<HEAD || memcmp(b,"TSHSEL1\n",8) || !memchr(b+8,0,PLEN) || strcmp((char*)b+8,ini) || b[142] || b[143]) die("Unknown, corrupt, or wrong-path journal. Keep every file."); n=b[136]+((unsigned)b[137]<<8); if(n>MAXINI || z!=n+HEAD) die("Incomplete journal. Keep every file."); for(i=0;i<4;++i) c|=((unsigned long)b[138+i])<<(i*8); if(crc(b+HEAD,n)!=c) die("Journal checksum mismatch. Keep every file."); memmove(b,b+HEAD,n); return n; }
static void writefile(const char *p,const unsigned char *b,unsigned n)
{ int f=create(p); out(f,b,n); finish(f); if(!same(p,b,n)) die("Staged file reread mismatch."); }
static void movefile(const char *a,const char *b)
{ if(exists(b)) die("Rename destination already exists."); writable(a); if(rename(a,b)) die("Rename failed. Run RECOVER before Windows."); checkpoint(); }
static void remove_known(const char *p,const unsigned char *b,unsigned n)
{ if(!exists(p)) return; if(!same(p,b,n)) die("Unknown sidecar; refusing to delete it."); writable(p); if(remove(p)) die("Cannot remove verified sidecar."); checkpoint(); }
static void remove_snap(const char *p,const unsigned char *b,unsigned n)
{ /* Reread into dest only after it is no longer needed by the caller. */
  unsigned z; if(!exists(p)) return; z=loadsnap(p,dest); if(z!=n || memcmp(dest,b,n)) die("Journal changed during recovery."); writable(p); if(remove(p)) die("Cannot remove verified journal."); checkpoint(); }

/* Strict, deterministic INI subset. Preserve every byte except the shell value.
 * Reject ambiguous/duplicate sections and shell keys, embedded NUL/control bytes,
 * malformed section lines, empty/overlong shell values and excessive sections.
 */
static Shell parse(const unsigned char *b,unsigned n)
{ unsigned p=0,e,q,t,x,y,k,count=0,boots=0,keys=0; int boot=0; char name[64]; Shell s;
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
          if(y-q==5 && toupper(b[q])=='S' && toupper(b[q+1])=='H' && toupper(b[q+2])=='E' && toupper(b[q+3])=='L' && toupper(b[q+4])=='L') {
            ++keys; x=t+1; while(x<e && space(b[x])) ++x;
            y=x; while(y<e && b[y]!=';') ++y; while(y>x && space(b[y-1])) --y;
            if(y==x || y-x>255) die("Empty or overlong shell value.");
            s.a=x; s.b=y;
          }
        }
      }
    }
    p=e; if(p<n && b[p]=='\r') ++p; if(p<n && b[p]=='\n') ++p;
  }
  if(boots!=1 || keys!=1) die("Need exactly one [boot] section and shell key.");
  return s;
}
static int shellis(const unsigned char *b,Shell s,const char *v)
{ unsigned i,l=(unsigned)strlen(v); if(s.b-s.a!=l) return 0; for(i=0;i<l;++i) if(toupper(b[s.a+i])!=toupper((unsigned char)v[i])) return 0; return 1; }
static int originalshell(const unsigned char *b,Shell s)
{ return s.b-s.a==os.b-os.a && !memcmp(b+s.a,orig+os.a,s.b-s.a); }
static unsigned replace(const unsigned char *b,unsigned n,Shell s,const unsigned char *v,unsigned l,unsigned char *d)
{ unsigned z; if(n-(s.b-s.a)>(unsigned)MAXINI-l) die("Result exceeds safe size limit."); z=n-(s.b-s.a)+l; memcpy(d,b,s.a); memcpy(d+s.a,v,l); memcpy(d+s.a+l,b+s.b,n-s.b); return z; }
static void baseline(void)
{ unsigned z; if(exists(sav)) { z=loadsnap(sav,dest); parse(dest,z); if(!exists(bak) || !same(bak,dest,z)) die("Saved backup missing or changed."); }
  else if(exists(bak)) die("Backup exists without its ownership record."); }
static void no_temps(void)
{ if(exists(tmp)||exists(old)||exists(rst)) die("Unresolved staging files; run RECOVER or inspect manually."); }
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
  pathof(jrn,"TSHELL.JRN"); pathof(bak,"TSHELL.BAK"); pathof(sav,"TSHELL.SAV"); pathof(tmp,"TSHELL.NEW"); pathof(old,"TSHELL.OLD"); pathof(rst,"TSHELL.RST");
}
static void require_app(void)
{ char p[PLEN]; unsigned char h[64]; unsigned skip,k; unsigned long off; int f;
  pathof(p,"TSHELL.EXE"); f=open(p,O_RDONLY|O_BINARY);
  if(f<0) die("TSHELL.EXE missing beside SYSTEM.INI.");
  if(read(f,h,64)!=64 || h[0]!='M' || h[1]!='Z') { close(f); die("TSHELL.EXE has no valid MZ header."); }
  off=(unsigned long)h[60]+((unsigned long)h[61]<<8)+((unsigned long)h[62]<<16)+((unsigned long)h[63]<<24);
  if(off<64 || off>8192) { close(f); die("Unsupported TSHELL.EXE NE header offset."); }
  skip=(unsigned)off-64;
  while(skip) { k=skip; if(k>64) k=64; if(read(f,h,k)!=(int)k) { close(f); die("Truncated TSHELL.EXE."); } skip-=k; }
  if(read(f,h,64)!=64 || h[0]!='N' || h[1]!='E' || h[0x36]!=2 || (h[0x0d]&0x80)) { close(f); die("TSHELL.EXE must be a Windows NE application."); }
  close(f);
  pathof(p,"WIN.COM"); f=open(p,O_RDONLY|O_BINARY);
  if(f<0) die("WIN.COM missing beside SYSTEM.INI.");
  if(read(f,h,4)!=4 || !((h[0]==0xeb && h[2]=='X' && h[3]=='W') || (h[0]=='M' && h[1]=='Z'))) { close(f); die("WIN.COM is not a recognized Windows loader."); }
  close(f);
}
static void not_windows(void)
{
#ifndef HOST_TEST
  union REGS r; r.x.ax=0x1600; int86(0x2f,&r,&r);
  if(r.h.al && r.h.al!=0x80) die("Exit Windows completely before using SHELLSEL.");
  r.x.ax=0x4680; int86(0x2f,&r,&r);
  if(!r.x.ax) die("Exit Windows completely before using SHELLSEL.");
#endif
}

static void cleanup_restored(void)
{ unsigned z; Shell s;
  z=readall(ini,cur,MAXINI); s=parse(cur,z);
  if(!originalshell(cur,s)) die("Restoration proof failed; journal retained.");
  if(exists(tmp)||exists(old)||exists(rst)) die("Unresolved transaction before journal cleanup.");
  remove_snap(jrn,orig,on); puts("Original shell restored and reread verified.");
}
static void recover(void)
{ unsigned z; Shell s;
  if(!exists(jrn)) { no_temps(); baseline(); if(!exists(ini)) die("SYSTEM.INI missing; no active recovery journal."); z=readall(ini,cur,MAXINI); s=parse(cur,z); if(shellis(cur,s,SEL)) die("TSHELL is selected without an active journal."); puts("No active shell selection; SYSTEM.INI unchanged."); return; }
  on=loadsnap(jrn,orig); os=parse(orig,on); if(shellis(orig,os,SEL)) die("Journal original shell is already TSHELL."); if(exists(sav) && !exists(bak)) {
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
  if(exists(rst)) {
    cn=loadsnap(rst,cur); cs=parse(cur,cn); if(!shellis(cur,cs,SEL)) die("Recovery journal does not contain selected shell.");
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
  if(originalshell(cur,cs)) { cleanup_restored(); return; }
  if(!shellis(cur,cs,SEL)) die("Shell changed unexpectedly. Keep journal and inspect manually.");
  writable(ini); snapshot(rst,cur,cn);
  z=loadsnap(rst,dest); if(z!=cn || memcmp(dest,cur,cn)) die("Recovery journal reread failed.");
  /* Re-enter to use precisely the same recovery path after every checkpoint. */
  recover();
}
static void select_shell(void)
{ unsigned z; Shell s;
  require_app();
  if(exists(jrn)) {
    on=loadsnap(jrn,orig); os=parse(orig,on);
    if(!exists(tmp)&&!exists(old)&&!exists(rst)&&exists(ini)) {
      cn=readall(ini,cur,MAXINI); cs=parse(cur,cn);
      if(shellis(cur,cs,SEL) && !shellis(orig,os,SEL)) { baseline(); puts("TSHELL selection already active."); return; }
    }
    recover();
  }
  no_temps(); baseline(); writable(ini);
  on=readall(ini,orig,MAXINI); os=parse(orig,on); if(shellis(orig,os,SEL)) die("TSHELL selected without a recoverable original.");
  snapshot(jrn,orig,on); z=loadsnap(jrn,dest); if(z!=on || memcmp(dest,orig,on)) die("Journal reread failed.");
  if(!exists(sav)) { snapshot(sav,orig,on); z=loadsnap(sav,dest); if(z!=on || memcmp(dest,orig,on)) die("Backup record reread failed."); }
  if(!exists(bak)) writefile(bak,orig,on);
  baseline();
  dn=replace(orig,on,os,(const unsigned char*)SEL,(unsigned)strlen(SEL),dest);
  writefile(tmp,dest,dn);
  if(!same(ini,orig,on)) die("SYSTEM.INI changed before selection.");
  movefile(ini,old); movefile(tmp,ini);
  if(!same(ini,dest,dn)) die("Selected output reread failed.");
  remove_known(old,orig,on);
  cn=readall(ini,cur,MAXINI); s=parse(cur,cn); if(!shellis(cur,s,SEL)) die("Selected shell verification failed.");
  puts("TSHELL selected. Run WIN /R, then SHELLSEL RECOVER.");
}
static void status(void)
{ unsigned z; Shell s; baseline(); if(exists(jrn)) { on=loadsnap(jrn,orig); os=parse(orig,on); puts("Active recovery journal present."); } else if(exists(tmp)||exists(old)||exists(rst)) die("Unowned transaction sidecar present.");
  if(!exists(ini)) die("SYSTEM.INI missing; RECOVER required.");
  z=readall(ini,cur,MAXINI); s=parse(cur,z);
  printf("Current shell: %.*s\n",(int)(s.b-s.a),cur+s.a);
  if(shellis(cur,s,SEL) && !exists(jrn)) die("TSHELL has no active journal.");
  if(exists(jrn) && !shellis(cur,s,SEL) && !originalshell(cur,s)) die("Unexpected shell change.");
  if(exists(tmp)||exists(old)||exists(rst)) { puts("Interrupted transaction: run RECOVER before Windows."); exit(1); }
}
int main(int argc,char **argv)
{ if(argc!=3 || (!eqi(argv[1],"SELECT")&&!eqi(argv[1],"RECOVER")&&!eqi(argv[1],"STATUS"))) { puts("Usage: SHELLSEL SELECT|RECOVER|STATUS C:\\WINDOWS\\SYSTEM.INI"); return 2; }
  setup(argv[2]); not_windows();
  if(eqi(argv[1],"SELECT")) select_shell(); else if(eqi(argv[1],"RECOVER")) recover(); else status(); return 0;
}
