/* XTMODE: conservative DOS 3.3+ / 8086 display-mode transaction.
 * Build: MSC 6 /AL /G0 (DOS runtime, never /Gw or Windows libraries).
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
#include <process.h>
#ifdef HOST_TEST
#include <io.h>
#include <process.h>
#define fsync _commit


#else
#include <io.h>
#include <dos.h>
#endif

#define MAXINI 16000U
#define HEAD 144
#define CAP (MAXINI+HEAD+1)
#define PLEN 128

/* Large-model pointers and separate <64 KiB allocations keep DGROUP small. */
static unsigned char *orig, *cur, *dest;
static char ini[PLEN], jrn[PLEN];
static char tmp[PLEN], old[PLEN], rst[PLEN];
static char names[64][64];
static unsigned on, cn, dn;
#if defined(HOST_TEST) || defined(XM_FAULT)
static int steps, writes, renames;
#endif
static unsigned target;
typedef struct { unsigned a[6], b[6],linea,lineb; } Config;
static Config os, cs;

static void die(const char *s)
{ fprintf(stderr,"XTMODE: %s\nNo unsafe fallback was attempted.\n",s); exit(1); }
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
#endif
#if defined(HOST_TEST) || defined(XM_FAULT)
    {
    const char *p;
    ++steps; p=getenv("XM_CRASH");
    if(p && atoi(p)==steps) _exit(99);
    }
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
#if defined(HOST_TEST) || defined(XM_FAULT)
    const char *v=getenv("XM_SHORT");
    ++writes;
    if(v && atoi(v)==writes) {
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
{ unsigned char h[HEAD]; unsigned long c; int f; unsigned i; memset(h,0,HEAD); memcpy(h,"XTMODE1\n",8); strcpy((char*)h+8,ini); h[136]=(unsigned char)n; h[137]=(unsigned char)(n>>8); h[142]=(unsigned char)target; c=crc(b,n); for(i=0;i<4;++i) h[138+i]=(unsigned char)(c>>(i*8)); f=create(p); out(f,h,HEAD); out(f,b,n); finish(f); }
static unsigned loadsnap(const char *p,unsigned char *b)
{ unsigned n,z,i; unsigned long c=0; z=readall(p,b,MAXINI+HEAD); if(z<HEAD || memcmp(b,"XTMODE1\n",8) || !memchr(b+8,0,PLEN) || strcmp((char*)b+8,ini) || b[142]<1 || b[142]>6 || b[143]) die("Unknown, corrupt, or wrong-path journal. Keep every file."); n=b[136]+((unsigned)b[137]<<8); if(n>MAXINI || z!=n+HEAD) die("Incomplete journal. Keep every file."); for(i=0;i<4;++i) c|=((unsigned long)b[138+i])<<(i*8); if(crc(b+HEAD,n)!=c) die("Journal checksum mismatch. Keep every file."); target=b[142]; memmove(b,b+HEAD,n); return n; }
static void writefile(const char *p,const unsigned char *b,unsigned n)
{ int f=create(p); out(f,b,n); finish(f); if(!same(p,b,n)) die("Staged file reread mismatch."); }
static void movefile(const char *a,const char *b)
{
#if defined(HOST_TEST) || defined(XM_FAULT)
 const char *v=getenv("XM_RENAME");++renames;
 if(v&&atoi(v)==renames)die("Injected rename refusal; run RECOVER.");
#endif
 if(exists(b)){die("Rename destination already exists.");}writable(a); if(rename(a,b)) die("Rename failed. Run RECOVER before Windows."); checkpoint();
}
static void remove_known(const char *p,const unsigned char *b,unsigned n)
{ if(!exists(p)) return; if(!same(p,b,n)) die("Unknown sidecar; refusing to delete it."); writable(p); if(remove(p)) die("Cannot remove verified sidecar."); checkpoint(); }
static void remove_snap(const char *p,const unsigned char *b,unsigned n)
{ /* Reread into dest only after it is no longer needed by the caller. */
  unsigned z; if(!exists(p)) return; z=loadsnap(p,dest); if(z!=n || memcmp(dest,b,n)) die("Journal changed during recovery."); writable(p); if(remove(p)) die("Cannot remove verified journal."); checkpoint(); }


typedef struct {
 const char *id, *v[6]; unsigned driver, sys, fixed, oem;
} Mode;
static const Mode modes[] = {
 {"32016",{"TR53216.DRV","XTESYS.FON","XTEFIX.FON","XTEOEM.FON","CGA.GR2","Tandy EX/HX 320x200 16 colors"},0,6,7,8},
 {"6404",{"TR56404.DRV","XTCSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2","Tandy EX/HX 640x200 4 colors"},1,9,10,11},
 {"16016",{"TR51616.DRV","XTCSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2","Tandy EX/HX 160x200 16 colors"},2,9,10,11},
 {"3204",{"TR53204.DRV","XTCSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2","Tandy EX/HX 320x200 4 colors"},3,9,10,11},
 {"6402",{"TR56402.DRV","XTCSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2","Tandy EX/HX 640x200 2 colors"},4,9,10,11},
 {"TEXT",{"TXTMODE.DRV","XTTSYS.FON","XTCFIX.FON","XTCOEM.FON","CGA.GR2","EXPERIMENTAL 80x25 text (character corruption)"},5,12,10,11}
};
typedef struct {
 const char *name; unsigned long size, checksum;
 unsigned ne, font, height, ascent, charset;
 const char *module,*face;unsigned width_sum;
} Payload;
#include "XTPINS.H"
static const char *keys[] = {"DISPLAY.DRV","FONTS.FON","FIXEDFON.FON","OEMFONTS.FON","286GRABBER","DISPLAY.DRV"};
static char previous[6][256];

/* Deterministic INI subset. Reject ambiguity; retain all unrelated bytes,
 * original spacing, comments, section order and line endings. */
static Config parse(const unsigned char *b,unsigned n)
{
 Config s; unsigned p=0,e,q,t,x,y,k,count=0,i,seen[6]; int section=0;
 char name[64]; memset(&s,0,sizeof(s));memset(seen,0,sizeof(seen));
 if(!n)die("Empty SYSTEM.INI.");
 for(k=0;k<n;++k)if((b[k]<32&&b[k]!='\r'&&b[k]!='\n'&&b[k]!='\t')||b[k]==127)die("Unsupported INI control byte.");
 while(p<n){
  e=p;while(e<n&&b[e]!='\r'&&b[e]!='\n')++e;
  q=p;while(q<e&&space(b[q]))++q;
  if(q<e&&b[q]!=';'&&b[q]!='#'){
   if(b[q]=='['){
    t=q+1;while(t<e&&b[t]!=']')++t;if(t==e)die("Malformed section.");
    x=q+1;y=t;while(x<y&&space(b[x]))++x;while(y>x&&space(b[y-1]))--y;
    if(y==x||y-x>63||count==64)die("Unsupported section name/count.");
    for(k=0;k<y-x;++k){name[k]=(char)toupper(b[x+k]);}name[y-x]=0;
    for(k=0;k<count;++k)if(!strcmp(names[k],name))die("Duplicate section.");
    strcpy(names[count++],name);section=!strcmp(name,"BOOT")?1:(!strcmp(name,"BOOT.DESCRIPTION")?2:0);
    q=t+1;while(q<e&&space(b[q]))++q;if(q<e&&b[q]!=';')die("Text after section.");
   }else if(section){
    t=q;while(t<e&&b[t]!='=')++t;
    if(t<e){
     y=t;while(y>q&&space(b[y-1]))--y;
     for(i=section==1?0:5;i<(unsigned)(section==1?5:6);++i){
      if(y-q!=strlen(keys[i]))continue;
      for(k=0;k<y-q;++k)if(toupper(b[q+k])!=keys[i][k])break;
      if(k!=y-q)continue;
      if(++seen[i]!=1)die("Duplicate controlled display key.");
      x=t+1;while(x<e&&space(b[x]))++x;y=x;while(y<e&&b[y]!=';')++y;
      while(y>x&&space(b[y-1])){--y;}if(y==x||y-x>255)die("Empty/overlong display value.");
      s.a[i]=x;s.b[i]=y;
      if(i==0){if(e-q>255)die("Display line exceeds reversible mode limit.");s.linea=q;s.lineb=e;}
      break;
     }
    }
   }
  }
  p=e;if(p<n&&b[p]=='\r')++p;if(p<n&&b[p]=='\n')++p;
 }
 for(i=0;i<6;++i)if(seen[i]!=1)die("Need all five [boot] display keys and [boot.description] display.drv exactly once.");
 return s;
}
static int valuesis(const unsigned char *b,Config s,const char *const *v)
{ unsigned i,k,l;for(i=0;i<6;++i){l=(unsigned)strlen(v[i]);if(s.b[i]-s.a[i]!=l)return 0;for(k=0;k<l;++k)if(toupper(b[s.a[i]+k])!=toupper((unsigned char)v[i][k]))return 0;}return 1; }
static int selected(const unsigned char *b,Config s)
{ char line[40];unsigned i,l;if(target<1||target>6||!valuesis(b,s,modes[target-1].v))return 0;sprintf(line,"display.drv=%s",modes[target-1].v[0]);l=(unsigned)strlen(line);if(s.lineb-s.linea!=l)return 0;for(i=0;i<l;++i)if(toupper(b[s.linea+i])!=toupper((unsigned char)line[i]))return 0;return 1; }
static int original(const unsigned char *b,Config s)
{ unsigned i;if(s.lineb-s.linea!=os.lineb-os.linea||memcmp(b+s.linea,orig+os.linea,s.lineb-s.linea))return 0;for(i=1;i<6;++i)if(s.b[i]-s.a[i]!=os.b[i]-os.a[i]||memcmp(b+s.a[i],orig+os.a[i],s.b[i]-s.a[i]))return 0;return 1; }
static unsigned replace(const unsigned char *b,unsigned n,Config s,const char *const *v,unsigned char *d)
{
 unsigned i,j,k,used=0,p=0,z=0,l,done[6];memset(done,0,sizeof(done));
 for(i=0;i<6;++i){
  k=6;for(j=0;j<6;++j)if(!done[j]&&(k==6||s.a[j]<s.a[k]))k=j;
  l=(unsigned)strlen(v[k]);used=s.a[k]-p;
  if(z>MAXINI-used||z+used>MAXINI-l)die("Output exceeds INI limit.");
  memcpy(d+z,b+p,used);z+=used;memcpy(d+z,v[k],l);z+=l;p=s.b[k];done[k]=1;
 }
 if(z>MAXINI-(n-p)){die("Output exceeds INI limit.");}memcpy(d+z,b+p,n-p);return z+n-p;
}
static unsigned restore_values(const unsigned char *b,unsigned n,Config s,unsigned char *d)
{ const char *v[6];unsigned i,l;for(i=0;i<6;++i){l=i?os.b[i]-os.a[i]:os.lineb-os.linea;memcpy(previous[i],orig+(i?os.a[i]:os.linea),l);previous[i][l]=0;v[i]=previous[i];}s.a[0]=s.linea;s.b[0]=s.lineb;return replace(b,n,s,v,d); }
static unsigned mode_values(const unsigned char *b,unsigned n,Config s,unsigned m,unsigned char *d)
{ const char *v[6];char line[40];unsigned i;for(i=0;i<6;++i)v[i]=modes[m-1].v[i];sprintf(line,"display.drv=%s",v[0]);v[0]=line;s.a[0]=s.linea;s.b[0]=s.lineb;return replace(b,n,s,v,d); }
static void pathof(char *outp,const char *name)
{ char *p;strcpy(outp,ini);p=strrchr(outp,'\\');
#ifdef HOST_TEST
 if(!p)p=strrchr(outp,'/');
#endif
 if(!p||strlen(ini)-strlen(p)+strlen(name)+1>=PLEN){die("Path too long.");}strcpy(p+1,name);
}
static void dospath(const char *p)
{
 unsigned a=0,b=0;int dot=0;
 if(!isalpha((unsigned char)p[0])||p[1]!=':'||p[2]!='\\')die("Use absolute DOS drive:\\directory paths.");
 p+=3;
 while(*p){
  if(*p=='\\'){
   if(!a||a>8||b>3||(dot&&!b))die("Use DOS 8.3 path components.");
   a=b=0;dot=0;
  }else if(*p=='.'){
   if(dot||!a){die("Invalid DOS path component.");}dot=1;
  }else{
   if(!isalnum((unsigned char)*p)&&*p!='_'&&*p!='-'&&*p!='~')die("Unsupported character in DOS path.");
   if(dot)++b;else ++a;
  }
  ++p;
 }
 if(!a||a>8||b>3||(dot&&!b))die("Use DOS 8.3 path components.");
}
static void setup(const char *p)
{
 unsigned i;char *base;
 if(strlen(p)>=PLEN-16||strlen(p)<11){die("Path too long/invalid.");}strcpy(ini,p);
#ifdef HOST_TEST
 base=strrchr(ini,'/');if(!base)base=strrchr(ini,'\\');
#else
 if(!isalpha(ini[0])||ini[1]!=':'||ini[2]!='\\')die("Use absolute DOS drive:\\directory\\SYSTEM.INI.");
 for(i=0;ini[i];++i){if(ini[i]=='/'||ini[i]==' '||ini[i]=='"'||ini[i]=='*'||ini[i]=='?')die("Use an unquoted DOS 8.3 path.");ini[i]=(char)toupper((unsigned char)ini[i]);}
 dospath(ini);
 base=strrchr(ini,'\\');
#endif
 if(!base||!eqi(base+1,"SYSTEM.INI"))die("Filename must be SYSTEM.INI.");
 for(i=0;ini[i];++i)if(ini[i]=='.'&&ini[i+1]=='.')die("Parent-relative path forbidden.");
 pathof(jrn,"XTMODE.JRN");pathof(tmp,"XTMODE.NEW");pathof(old,"XTMODE.OLD");pathof(rst,"XTMODE.RST");
}
static void not_windows(void)
{
#ifndef HOST_TEST
 union REGS r;memset(&r,0,sizeof(r));r.x.ax=0x1600;int86(0x2f,&r,&r);
 if(r.h.al&&r.h.al!=0x80)die("Exit Windows completely.");
 memset(&r,0,sizeof(r));r.x.ax=0x4680;int86(0x2f,&r,&r);
 if(!r.x.ax)die("Exit Windows completely (real/standard mode).");
#else
 if(getenv("XM_WINDOWS"))die("Exit Windows completely (host guard injection).");
#endif
}
static unsigned word(const unsigned char *b){return b[0]+((unsigned)b[1]<<8);}
static unsigned long dword(const unsigned char *b){return (unsigned long)word(b)+((unsigned long)word(b+2)<<16);}
static void freadat(FILE *f,unsigned long off,unsigned char *b,unsigned n)
{ if(fseek(f,(long)off,SEEK_SET)||fread(b,1,n,f)!=n)die("Truncated resource/header."); }
static void systempath(char *p,const char *name)
{ char n[48];
#ifdef HOST_TEST
 strcpy(n,"SYSTEM/");
#else
 strcpy(n,"SYSTEM\\");
#endif
 strcat(n,name);pathof(p,n);
}
static void payload_at(const char *p,unsigned index,int full)
{
 const Payload *v=payloads+index;unsigned char h[128],chunk[256];
 FILE *f;unsigned shift,count,kind,i,woff,width,end,first,last,found=0,a1=0,a2=0,j;unsigned long at,off,len,actual,c=0xffffffffUL;size_t n;
 f=fopen(p,"rb");if(!f)die("Required mode file missing; install all mode files first.");
 if(fseek(f,0,SEEK_END)||(long)(actual=ftell(f))<0||actual!=v->size)die("Mode payload size mismatch.");
 if(v->ne){
  freadat(f,0,h,64);if(memcmp(h,"MZ",2)||dword(h+60)!=v->ne)die("Wrong MZ/NE header.");
  freadat(f,v->ne,h,64);if(memcmp(h,"NE",2))die("Missing NE signature.");
  off=v->ne+word(h+38);freadat(f,off,chunk,1);j=chunk[0];if(j>63)die("NE module name too long.");
  freadat(f,off+1,chunk,j);chunk[j]=0;if(strcmp((char*)chunk,v->module))die("Wrong mode resource module identity.");
  at=v->ne+word(h+36);if(at>actual-2)die("NE resource table outside file.");
  freadat(f,at,h,2);shift=word(h);if(shift>16)die("NE resource alignment too large.");at+=2;
  for(i=0;i<64;++i){
   if(at>actual-2){die("Truncated resource table.");}freadat(f,at,h,2);kind=word(h);if(!kind)break;
   freadat(f,at,h,8);count=word(h+2);if(count>64)die("Resource count too large.");at+=8;
   while(count--){
    freadat(f,at,h,12);off=(unsigned long)word(h)<<shift;len=(unsigned long)word(h+2)<<shift;at+=12;
    if(!len||off>actual||len>actual-off)die("NE resource outside file.");
    if(kind==0x8008){
     if(len<122){die("FONT resource too short.");}freadat(f,off,h,118);
     if(word(h)!=0x200||dword(h+2)>len||word(h+66)!=0||!word(h+88)||word(h+74)>word(h+88))die("Invalid bitmap FNT metrics.");
     first=(unsigned)h[95];last=(unsigned)h[96];if(last<first||(unsigned)h[97]>last-first||(unsigned)h[98]>last-first)die("Invalid FNT character coverage.");
     if(dword(h+2)<118UL+4UL*(last-first+2))die("FNT table outside resource.");
     if(dword(h+105)>=dword(h+2)||dword(h+113)<118UL+4UL*(last-first+2)||dword(h+113)>dword(h+2))die("FNT face/bitmap offset invalid.");
     if(off==(unsigned long)v->font){++found;if(word(h+88)!=v->height||word(h+74)!=v->ascent||(unsigned)h[85]!=v->charset)die("Required system font metrics changed.");}
     j=0;do{if(j>=63||dword(h+105)+j>=dword(h+2))die("FNT face outside resource.");freadat(f,off+dword(h+105)+j,chunk+j,1);}while(chunk[j++]);
     if(off==(unsigned long)v->font&&strcmp((char*)chunk,v->face)){die("Wrong font face identity.");}a1=a2=0;
     for(end=0;end<=last-first;++end){
      freadat(f,off+118UL+4UL*end,chunk,4);width=word(chunk);woff=word(chunk+2);
      if(width>word(h+93)||(unsigned long)woff<dword(h+113)||(unsigned long)woff>dword(h+2)||(((unsigned long)width+7UL)/8UL)*(unsigned long)word(h+88)>dword(h+2)-(unsigned long)woff)die("FNT width/bitmap boundary invalid.");
      a1=(a1+chunk[0])%255;a2=(a2+a1)%255;a1=(a1+chunk[1])%255;a2=(a2+a1)%255;
     }
     if(off==(unsigned long)v->font&&((a2<<8)|a1)!=v->width_sum)die("Required glyph advances changed.");
    }
   }
  }
  if(i==64){die("Unterminated resource table.");}if(v->font&&found!=1)die("Required FONT resource missing/duplicated.");
 }else{
  freadat(f,0,h,8);if(index==13&&memcmp(h,"LOGO",4))die("Static logo signature invalid.");
  if(index==14&&memcmp(h,"BM",2))die("RLE header invalid.");
 }
 if(full){
  if(fseek(f,0,SEEK_SET))die("Cannot seek payload.");
  while((n=fread(chunk,1,sizeof(chunk),f))!=0){unsigned j,k;for(j=0;j<(unsigned)n;++j){c^=chunk[j];for(k=0;k<8;++k)c=(c&1)?(c>>1)^0xedb88320UL:c>>1;}}
  if(ferror(f)||(c^0xffffffffUL)!=v->checksum)die("Explicit CRC32 payload verification failed.");
 }
 if(fclose(f))die("Cannot close payload.");
}
static void payload(unsigned index,int full)
{ char p[PLEN];systempath(p,payloads[index].name);payload_at(p,index,full); }
static void common(void)
{
 char p[PLEN];FILE *f;unsigned char h[24];long size;unsigned i;
 systempath(p,"CGA.GR2");f=fopen(p,"rb");if(!f)die("Owned Windows CGA.GR2 missing.");
 fseek(f,0,SEEK_END);size=ftell(f);if(size!=2104L)die("Owned CGA.GR2 size mismatch.");freadat(f,0,h,24);
 for(i=0;i<8;++i){if(h[3*i]!=0xe9||3UL*i+3UL+word(h+3*i+1)>=2104UL)die("CGA.GR2 jump contract invalid.");}fclose(f);
 pathof(p,"WIN.COM");f=fopen(p,"rb");if(!f)die("Private common WIN.COM missing.");
 fseek(f,0,SEEK_END);size=ftell(f);if(size!=7879L)die("WIN.COM must be this static-logo revision's common 7879-byte loader.");
 freadat(f,3456UL,h,8);if(memcmp(h,"LOGO",4))die("WIN.COM static component missing.");
 freadat(f,3817UL,h,2);if(memcmp(h,"BM",2))die("WIN.COM RLE component missing.");fclose(f);
}
static void resources(unsigned m,int full)
{ const Mode *v=modes+m-1;payload(v->driver,full);payload(v->sys,full);payload(v->fixed,full);payload(v->oem,full);payload(13,full);payload(14,full);common(); }
static void no_temps(void)
{ if(exists(tmp)||exists(old)||exists(rst))die("Pending mode transaction; run RECOVER before Windows."); }
#define FH 272
static char source[PLEN], fjrn[PLEN], fnew[PLEN], ready[PLEN];
static void filepaths(void)
{ pathof(fjrn,"XTFILES.JRN");pathof(fnew,"XTFILES.NEW");pathof(ready,"XTFILES.RDY"); }
static void sourcepath(char *p,const char *name)
{
 if(strlen(source)+strlen(name)+2>=PLEN){die("Source path too long.");}strcpy(p,source);
#ifdef HOST_TEST
 strcat(p,"/");
#else
 strcat(p,"\\");
#endif
 strcat(p,name);
}
static void setsource(const char *p)
{
 unsigned i;if(strlen(p)>=PLEN-16||strlen(p)<4)die("Source path too long/invalid.");strcpy(source,p);
#ifndef HOST_TEST
 for(i=0;source[i];++i)source[i]=(char)toupper((unsigned char)source[i]);dospath(source);
#else
 (void)i;
#endif
}
static void fheader(unsigned char *h,unsigned index)
{
 unsigned i;unsigned long c;memset(h,0,FH);memcpy(h,"XTFILES1",8);strcpy((char*)h+8,ini);strcpy((char*)h+136,source);h[264]=(unsigned char)index;c=crc(h,268);
 for(i=0;i<4;++i)h[268+i]=(unsigned char)(c>>(8*i));
}
static unsigned fload(const char *p,unsigned char *h)
{
 unsigned i,z;unsigned long c=0;z=readall(p,h,FH);
 if(z!=FH||memcmp(h,"XTFILES1",8)||!memchr(h+8,0,PLEN)||!memchr(h+136,0,PLEN)||strcmp((char*)h+8,ini)||h[265]||h[266]||h[267]||(h[264]>=NPAY&&h[264]!=255))die("Unknown/incomplete/wrong-path resource journal; retain files.");
 for(i=0;i<4;++i){c|=(unsigned long)h[268+i]<<(8*i);}if(crc(h,268)!=c)die("Resource journal checksum mismatch.");return h[264];
}
static void fremove(const char *p,const unsigned char *h)
{ unsigned char actual[FH];if(fload(p,actual)!=h[264]||memcmp(h,actual,FH))die("Resource ownership record changed.");writable(p);if(remove(p))die("Cannot remove resource ownership record.");checkpoint(); }
static int equalfile(const char *a,const char *b,int prefix)
{
 FILE *fa,*fb;unsigned char ba[512],bb[512];size_t na,nb;int result=1;
 fa=fopen(a,"rb");fb=fopen(b,"rb");if(!fa||!fb){if(fa)fclose(fa);if(fb)fclose(fb);return 0;}
 for(;;){na=fread(ba,1,sizeof(ba),fa);nb=fread(bb,1,sizeof(bb),fb);
  if(na>nb||(!prefix&&na!=nb)||memcmp(ba,bb,na)){result=0;break;}
  if(na<sizeof(ba))break;
 }
 if(ferror(fa)||ferror(fb)){result=0;}fclose(fa);fclose(fb);return result;
}
static void copy_guard(void)
{
 unsigned char h[FH];filepaths();if(exists(fjrn)||exists(fnew))die("Pending resource copy; rerun XTMODE INSTALL before Windows.");
 if(exists(ready)&&fload(ready,h)!=255)die("Resource completion record invalid.");
}
static void copyone(unsigned index)
{
 unsigned char h[FH];char from[PLEN],to[PLEN];int f,in,r;unsigned long used;
 sourcepath(from,payloads[index].name);systempath(to,payloads[index].name);fheader(h,index);
 if(exists(fjrn)){
  unsigned char saved[FH];if(fload(fjrn,saved)!=index||memcmp(saved,h,FH))die("Resource recovery source/record differs; retain all files.");
 }else{if(exists(fnew))die("Unowned resource copy staging file.");writefile(fjrn,h,FH);}
 if(exists(fnew)){
  if(!equalfile(fnew,from,1)){die("Unknown/corrupt resource copy staging bytes.");}writable(fnew);if(remove(fnew))die("Cannot remove verified partial resource copy.");checkpoint();
 }
 if(exists(to)){
  if(!equalfile(to,from,0)){die("Existing resource differs from this owned copy transaction.");}fremove(fjrn,h);return;
 }
 f=create(fnew);in=open(from,O_RDONLY|O_BINARY);if(in<0)die("Cannot open source during copy.");used=0;
 for(;;){r=read(in,cur,4096);if(r<0)die("Resource copy read failed.");if(!r)break;out(f,cur,(unsigned)r);used+=(unsigned)r;}
 if(close(in)){die("Source close failed.");}finish(f);
 if(used!=payloads[index].size||!equalfile(fnew,from,0))die("Resource copy reread differs; retain staging files.");
 payload_at(fnew,index,0);movefile(fnew,to);if(!equalfile(to,from,0))die("Installed resource reread differs.");fremove(fjrn,h);
}
static void install_files(const char *folder)
{
 unsigned i,index;unsigned char h[FH];char p[PLEN];setsource(folder);filepaths();common();
 /* Validate every source and existing destination before beginning any copy. */
 for(i=0;i<NPAY;++i){sourcepath(p,payloads[i].name);payload_at(p,i,0);systempath(p,payloads[i].name);if(exists(p))payload_at(p,i,0);}
 if(exists(fnew)&&!exists(fjrn))die("Resource staging exists without an ownership journal.");
 if(exists(fjrn)){
  index=fload(fjrn,h);if(index>=NPAY||strcmp((char*)h+136,source))die("Resource copy recovery source differs.");copyone(index);
 }
 for(i=0;i<NPAY;++i){systempath(p,payloads[i].name);if(!exists(p))copyone(i);}
 resources(1,0);fheader(h,255);
 if(exists(ready)){unsigned char actual[FH];if(fload(ready,actual)!=255||memcmp(h,actual,FH))die("Resource completion record differs.");}
 else writefile(ready,h,FH);
 puts("Resources for all six modes installed once. No active INI, boot file or loader changed.");
}
static void cleanup_restored(void)
{
 unsigned z;Config s;z=readall(ini,cur,MAXINI);s=parse(cur,z);if(!original(cur,s))die("Restoration proof failed; journal retained.");
 no_temps();remove_snap(jrn,orig,on);puts("Previous display tuple restored; unrelated INI bytes retained.");
}
static void recover(int force)
{
 unsigned z;
 copy_guard();
 if(!exists(jrn)){no_temps();if(!exists(ini))die("SYSTEM.INI missing without journal.");parse(cur,readall(ini,cur,MAXINI));puts("No mode recovery needed.");return;}
 on=loadsnap(jrn,orig);os=parse(orig,on);
 if(exists(rst)){
  cn=loadsnap(rst,cur);cs=parse(cur,cn);if(!selected(cur,cs))die("Recovery snapshot is not the selected tuple.");
  dn=restore_values(cur,cn,cs,dest);
  if(exists(old)&&!same(old,cur,cn))die("Recovery old-file identity mismatch.");
  if(exists(tmp)&&!same(tmp,dest,dn))die("Recovery temporary identity mismatch.");
  if(!(exists(ini)&&same(ini,dest,dn))){
   if(exists(ini)&&!same(ini,cur,cn))die("SYSTEM.INI changed during recovery.");
   if(!exists(ini)&&!exists(old))die("Missing INI without interrupted rename proof.");
   if(!exists(tmp)){if(!exists(ini))die("Recovery output missing; inspect manually.");writefile(tmp,dest,dn);}
   if(exists(ini)){if(exists(old))die("Unexpected current and old files.");movefile(ini,old);}
   movefile(tmp,ini);if(!same(ini,dest,dn))die("Recovery reread failed.");
  }
  remove_known(tmp,dest,dn);remove_known(old,cur,cn);remove_snap(rst,cur,cn);cleanup_restored();return;
 }
 dn=mode_values(orig,on,os,target,dest);
 if(exists(old)&&!same(old,orig,on))die("Selection old-file identity mismatch.");
 if(exists(tmp)&&!same(tmp,dest,dn))die("Selection temporary identity mismatch.");
 if(!exists(ini)){
  if(!exists(old)||!exists(tmp))die("Missing INI without selection rename proof.");
  movefile(old,ini);remove_known(tmp,dest,dn);cleanup_restored();return;
 }
 if(exists(old)||exists(tmp)){
  if(!same(ini,orig,on)&&!same(ini,dest,dn))die("INI changed during incomplete selection.");
  remove_known(tmp,dest,dn);remove_known(old,orig,on);force=1;
 }
 cn=readall(ini,cur,MAXINI);cs=parse(cur,cn);
 if(original(cur,cs)){cleanup_restored();return;}
 if(!selected(cur,cs))die("Controlled display tuple changed; retain journal for inspection.");
 if(!force){puts("Committed mode transaction intact; undo available.");return;}
 writable(ini);snapshot(rst,cur,cn);z=loadsnap(rst,dest);if(z!=cn||memcmp(dest,cur,cn))die("Recovery snapshot reread failed.");recover(1);
}
static void set_mode(unsigned m)
{
 unsigned z,wanted=m;
 copy_guard();
 resources(m,0);
 if(exists(jrn)){
  recover(0);
  if(exists(jrn)){
   if(target==wanted){puts("Requested mode already selected.");return;}
   remove_snap(jrn,orig,on); /* Current mode is valid here even if power fails. */
  }
 }
 no_temps();writable(ini);on=readall(ini,orig,MAXINI);os=parse(orig,on);target=wanted;
 if(selected(orig,os)){puts("Requested tuple already selected; no write.");return;}
 snapshot(jrn,orig,on);z=loadsnap(jrn,dest);if(z!=on||memcmp(dest,orig,on))die("Journal reread failed.");
 dn=mode_values(orig,on,os,target,dest);writefile(tmp,dest,dn);
 if(!same(ini,orig,on))die("INI changed before mode selection.");
 movefile(ini,old);movefile(tmp,ini);if(!same(ini,dest,dn))die("Selected output reread failed.");
 remove_known(old,orig,on);cs=parse(dest,dn);if(!selected(dest,cs))die("Mode tuple verification failed.");
 printf("Selected %s. Use the guarded WINXT launcher; UNDO restores the previous tuple.\n",modes[target-1].id);
}
static void check(int full)
{
 unsigned i,z;Config s;
 copy_guard();
 no_temps();z=readall(ini,cur,MAXINI);s=parse(cur,z);
 for(i=1;i<=6;++i)if(valuesis(cur,s,modes[i-1].v))break;
 if(i==7)die("Current display tuple is outside this installed mode set.");
 if(exists(jrn)){on=loadsnap(jrn,orig);os=parse(orig,on);if(target!=i)die("Current tuple disagrees with mode journal.");}
 resources(i,full);printf("Current mode: %s. %s check passed.\n",modes[i-1].id,full?"Explicit payload CRC32":"Header/size/font-boundary");
}
static void guard(void)
{
 unsigned i,z;Config s;copy_guard();no_temps();z=readall(ini,cur,MAXINI);s=parse(cur,z);
 for(i=1;i<=6;++i)if(valuesis(cur,s,modes[i-1].v))break;
 if(i==7){if(exists(jrn))die("Foreign tuple with a mode journal.");puts("No active switcher tuple; existing Windows selection retained.");return;}
 check(0);
}
static void forget(void)
{
 unsigned char h[FH];recover(1);filepaths();if(exists(ready)){if(fload(ready,h)!=255)die("Invalid resource completion record.");fremove(ready,h);}puts("Mode history and completion marker deactivated; copied resources remain.");
}
static void accept(void)
{ recover(0);if(exists(jrn))remove_snap(jrn,orig,on);puts("Current mode retained; undo history accepted before Setup."); }
static void menu(void)
{
 char answer[16];unsigned i;Config s;copy_guard();no_temps();s=parse(cur,readall(ini,cur,MAXINI));
 printf("Current display: %.*s\n",(int)(s.b[5]-s.a[5]),cur+s.a[5]);
 for(i=0;i<5;++i)printf("%u. %s\n",i+1,modes[i].v[5]);
 puts("T. Experimental text (known character corruption)\nU. Undo previous mode\nQ. Quit");
 printf("Selection: ");if(!fgets(answer,sizeof(answer),stdin))return;
 if(answer[0]>='1'&&answer[0]<='5'){set_mode((unsigned)(answer[0]-'0'));return;}
 if(toupper((unsigned char)answer[0])=='U'){recover(1);return;}
 if(toupper((unsigned char)answer[0])=='T'){
  puts("Type TEXT to accept the experimental text mode:");if(fgets(answer,sizeof(answer),stdin)&&(!strcmp(answer,"TEXT\n")||!strcmp(answer,"TEXT\r\n")))set_mode(6);
 }
}
static void usage(void)
{
 puts("XTMODE host/native source slice - DOS 3.3+, exit Windows completely.");
 puts("XTMODE LIST | MENU path | CHECK path | VERIFY path | SET path mode [/TEXT]");
 puts("XTMODE INSTALL path source-folder | UNDO path | RECOVER path | GUARD path | FORGET path | ACCEPT path");
 puts("Modes: 32016, 6404 (red/green), 16016, 3204 (cyan/magenta), 6402, TEXT.");
 puts("TEXT is experimental with known character corruption; requires /TEXT.");
 puts("Install every driver/font once; preserve WINXT reservation and wave/static routing.");
}
int main(int argc,char **argv)
{
 unsigned i;
#ifdef HOST_TEST
 if(argc==3&&eqi(argv[1],"PATHCHECK")){dospath(argv[2]);return 0;}
#endif
 if(argc==2&&eqi(argv[1],"LIST")){usage();return 0;}
 if(argc<3){usage();return 2;}setup(argv[2]);not_windows();
 orig=(unsigned char*)malloc(CAP);cur=(unsigned char*)malloc(CAP);dest=(unsigned char*)malloc(CAP);
 if(!orig||!cur||!dest)die("Insufficient memory for bounded mode transaction.");
 if(argc==4&&eqi(argv[1],"INSTALL")){install_files(argv[3]);return 0;}
 if(argc==3&&eqi(argv[1],"GUARD")){guard();return 0;}
 if(argc==3&&eqi(argv[1],"FORGET")){forget();return 0;}
 if(argc==3&&eqi(argv[1],"ACCEPT")){accept();return 0;}
 if(argc==3&&eqi(argv[1],"MENU")){menu();return 0;}
 if(argc==3&&eqi(argv[1],"RECOVER")){recover(0);return 0;}
 if(argc==3&&eqi(argv[1],"UNDO")){recover(1);return 0;}
 if(argc==3&&eqi(argv[1],"CHECK")){check(0);return 0;}
 if(argc==3&&eqi(argv[1],"VERIFY")){check(1);return 0;}
 if((argc==4||argc==5)&&eqi(argv[1],"SET")){
  for(i=1;i<=6;++i)if(eqi(argv[3],modes[i-1].id))break;
  if(i==7)die("Unknown mode.");
  if(i==6&&(argc!=5||!eqi(argv[4],"/TEXT")))die("Experimental TEXT requires explicit /TEXT.");
  if(i!=6&&argc!=4){die("Unexpected mode argument.");}set_mode(i);return 0;
 }
 usage();return 2;
}
