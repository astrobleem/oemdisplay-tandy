/* CPSET: optional DOS 3.3+ / 8086 SETUP.INF Computer-profile transaction.
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
#include <unistd.h>
#include <stdint.h>
#ifdef HOST_WINDOWS
#include <io.h>
#include <process.h>
#define fsync _commit
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
static int steps, deep_verify;

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
    if(fsync(fd)) die("Cannot flush staged file.");
#else
    union REGS r;
    r.x.ax=0x6800; r.x.bx=fd; intdos(&r,&r);
    if(r.x.cflag) die("Cannot commit staged file (DOS 3.3+ required).");
#endif
}
static void out(int fd,const unsigned char *p,unsigned n)
{ unsigned k; int w;
#ifdef HOST_TEST
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
static U32 input_crc(const unsigned char *b,unsigned n);
/* Same CRC32 journal format; share the bounded byte-table implementation. */
static unsigned long crc(const unsigned char *p,unsigned n)
{return (unsigned long)input_crc(p,n);}
static void snapshot(const char *p,const unsigned char *b,unsigned n)
{ unsigned char h[HEAD]; unsigned long c; int f; unsigned i; memset(h,0,HEAD); memcpy(h,"CPINF01\n",8); strcpy((char*)h+8,ini); h[136]=(unsigned char)n; h[137]=(unsigned char)(n>>8); c=crc(b,n); for(i=0;i<4;++i) h[138+i]=(unsigned char)(c>>(i*8)); f=create(p); out(f,h,HEAD); out(f,b,n); finish(f); }
static unsigned loadsnap(const char *p,unsigned char *b)
{ unsigned n,z,i; unsigned long c=0; z=readall(p,b,MAXINI+HEAD); if(z<HEAD || memcmp(b,"CPINF01\n",8) || !memchr(b+8,0,PLEN) || strcmp((char*)b+8,ini) || b[142] || b[143]) die("Unknown, corrupt, or wrong-path journal. Keep every file."); n=b[136]+((unsigned)b[137]<<8); if(n>MAXINI || z!=n+HEAD) die("Incomplete journal. Keep every file."); for(i=0;i<4;++i) c|=((unsigned long)b[138+i])<<(i*8); if(crc(b+HEAD,n)!=c) die("Journal checksum mismatch. Keep every file."); memmove(b,b+HEAD,n); return n; }
static void writefile(const char *p,const unsigned char *b,unsigned n)
{ int f=create(p); out(f,b,n); finish(f); if(!same(p,b,n)) die("Staged file reread mismatch."); }
static void movefile(const char *a,const char *b)
{ if(exists(b)) die("Rename destination already exists."); writable(a); if(rename(a,b)) die("Rename failed. Run RESTORE before Windows."); checkpoint(); }
static void remove_known(const char *p,const unsigned char *b,unsigned n)
{ if(!exists(p)) return; if(!same(p,b,n)) die("Unknown sidecar; refusing to delete it."); writable(p); if(remove(p)) die("Cannot remove verified sidecar."); checkpoint(); }
static void remove_snap(const char *p,const unsigned char *b,unsigned n)
{ /* Reread into dest only after it is no longer needed by the caller. */
  unsigned z; if(!exists(p)) return; z=loadsnap(p,dest); if(z!=n || memcmp(dest,b,n)) die("Journal changed during recovery."); writable(p); if(remove(p)) die("Cannot remove verified journal."); checkpoint(); }

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
#ifdef ZERO_SHA_TEST
 if(!deep_verify)die("Default path attempted SHA transform.");
#endif
 for(i=0;i<16;i++)w[i]=((U32)s->b[i*4]<<24)|((U32)s->b[i*4+1]<<16)|((U32)s->b[i*4+2]<<8)|s->b[i*4+3];
 for(i=16;i<64;i++){a=w[i-15];b=w[i-2];w[i]=w[i-16]+(RR(a,7)^RR(a,18)^(a>>3))+w[i-7]+(RR(b,17)^RR(b,19)^(b>>10));}
 a=s->h[0];b=s->h[1];c=s->h[2];d=s->h[3];e=s->h[4];f=s->h[5];g=s->h[6];h=s->h[7];
 for(i=0;i<64;i++){t=h+(RR(e,6)^RR(e,11)^RR(e,25))+((e&f)^((~e)&g))+K[i]+w[i];u=(RR(a,2)^RR(a,13)^RR(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+t;d=c;c=b;b=a;a=t+u;}
 s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void init(SHA *s){static const U32 h[8]={0x6a09e667UL,0xbb67ae85UL,0x3c6ef372UL,0xa54ff53aUL,0x510e527fUL,0x9b05688cUL,0x1f83d9abUL,0x5be0cd19UL};
#ifdef ZERO_SHA_TEST
 if(!deep_verify)die("Default path attempted SHA initialization.");
#endif
memcpy(s->h,h,sizeof(h));s->n=0;s->bytes=0;}
static void update(SHA *s,const unsigned char *p,unsigned n){s->bytes+=n;while(n--){s->b[s->n++]=*p++;if(s->n==64){transform(s);s->n=0;}}}
static void sha_finish(SHA *s,char *out){unsigned i,j;U32 bits=s->bytes*8;static const char hex[]="0123456789abcdef";s->b[s->n++]=128;if(s->n>56){while(s->n<64)s->b[s->n++]=0;transform(s);s->n=0;}while(s->n<60)s->b[s->n++]=0;for(i=0;i<4;i++)s->b[60+i]=(unsigned char)(bits>>(24-i*8));transform(s);for(i=0;i<8;i++)for(j=0;j<4;j++){unsigned v=(unsigned)((s->h[i]>>(24-j*8))&255);*out++=hex[v>>4];*out++=hex[v&15];}*out=0;}
static int selftest(void){SHA s;char h[65];init(&s);sha_finish(&s,h);if(strcmp(h,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))return 0;init(&s);update(&s,(const unsigned char *)"abc",3);sha_finish(&s,h);return !strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");}

#define SOURCE_SHA "4f4b65bdc0ce2d4a23859494f8936376296e857872a554b0037ceb068f2202f2"
#define KBD_SHA "2554384b3da7f9925e56d9b0063e240d65c619cb2089819e4eaf3964e3eb769f"
#define K3_SHA "e2abb52ec3f148ccfda49ae39a6d56e38d93e1431986cd2a94d26a404120b3a5"
static char win[PLEN], sysini[PLEN], curpath[PLEN],drvpath[PLEN];
static int selected;
static const char label[]="Tandy 1000 EX/HX (WindowsXT)";
static const char prefix[]="\r\n; WindowsXT optional Computer preset; run CPSET CHECK before selecting.\r\n    \"Tandy 1000 EX/HX (WindowsXT)\",\"78\"\r\n        system\r\n        ";
static const char suffix[]="\r\n        t1s0pcxt\r\n        nomouse\r\n        cga\r\n        sound\r\n        comm\r\n        nohimemswitch\r\n        ebios\r\n\r\n";
static void hashmem(const unsigned char *b,unsigned n,char *h) { SHA s;init(&s);update(&s,b,n);sha_finish(&s,h); }
static void hashfile(const char *p,char *h)
{ SHA s;int f,r;unsigned char b[512];init(&s);f=open(p,O_RDONLY|O_BINARY);if(f<0)die("Selected keyboard file unavailable.");while((r=read(f,b,sizeof(b)))>0)update(&s,b,(unsigned)r);if(r<0||close(f))die("Keyboard file read failed.");sha_finish(&s,h); }
static unsigned locate(const char *s);
/* Exact two installed-OS inputs, not a general Windows-version matrix.
 * CRC bounds the default known-input check; /VERIFY retains full SHA256.
 * The actual INF is kept unchanged for patching and exact rollback.
 * Byte shifting avoids the 8086 compiler's slow 32-bit shift loop. */
static const U32 metadata_crc[256]={
 0x00000000UL,0x77073096UL,0xee0e612cUL,0x990951baUL,0x076dc419UL,0x706af48fUL,0xe963a535UL,0x9e6495a3UL,
 0x0edb8832UL,0x79dcb8a4UL,0xe0d5e91eUL,0x97d2d988UL,0x09b64c2bUL,0x7eb17cbdUL,0xe7b82d07UL,0x90bf1d91UL,
 0x1db71064UL,0x6ab020f2UL,0xf3b97148UL,0x84be41deUL,0x1adad47dUL,0x6ddde4ebUL,0xf4d4b551UL,0x83d385c7UL,
 0x136c9856UL,0x646ba8c0UL,0xfd62f97aUL,0x8a65c9ecUL,0x14015c4fUL,0x63066cd9UL,0xfa0f3d63UL,0x8d080df5UL,
 0x3b6e20c8UL,0x4c69105eUL,0xd56041e4UL,0xa2677172UL,0x3c03e4d1UL,0x4b04d447UL,0xd20d85fdUL,0xa50ab56bUL,
 0x35b5a8faUL,0x42b2986cUL,0xdbbbc9d6UL,0xacbcf940UL,0x32d86ce3UL,0x45df5c75UL,0xdcd60dcfUL,0xabd13d59UL,
 0x26d930acUL,0x51de003aUL,0xc8d75180UL,0xbfd06116UL,0x21b4f4b5UL,0x56b3c423UL,0xcfba9599UL,0xb8bda50fUL,
 0x2802b89eUL,0x5f058808UL,0xc60cd9b2UL,0xb10be924UL,0x2f6f7c87UL,0x58684c11UL,0xc1611dabUL,0xb6662d3dUL,
 0x76dc4190UL,0x01db7106UL,0x98d220bcUL,0xefd5102aUL,0x71b18589UL,0x06b6b51fUL,0x9fbfe4a5UL,0xe8b8d433UL,
 0x7807c9a2UL,0x0f00f934UL,0x9609a88eUL,0xe10e9818UL,0x7f6a0dbbUL,0x086d3d2dUL,0x91646c97UL,0xe6635c01UL,
 0x6b6b51f4UL,0x1c6c6162UL,0x856530d8UL,0xf262004eUL,0x6c0695edUL,0x1b01a57bUL,0x8208f4c1UL,0xf50fc457UL,
 0x65b0d9c6UL,0x12b7e950UL,0x8bbeb8eaUL,0xfcb9887cUL,0x62dd1ddfUL,0x15da2d49UL,0x8cd37cf3UL,0xfbd44c65UL,
 0x4db26158UL,0x3ab551ceUL,0xa3bc0074UL,0xd4bb30e2UL,0x4adfa541UL,0x3dd895d7UL,0xa4d1c46dUL,0xd3d6f4fbUL,
 0x4369e96aUL,0x346ed9fcUL,0xad678846UL,0xda60b8d0UL,0x44042d73UL,0x33031de5UL,0xaa0a4c5fUL,0xdd0d7cc9UL,
 0x5005713cUL,0x270241aaUL,0xbe0b1010UL,0xc90c2086UL,0x5768b525UL,0x206f85b3UL,0xb966d409UL,0xce61e49fUL,
 0x5edef90eUL,0x29d9c998UL,0xb0d09822UL,0xc7d7a8b4UL,0x59b33d17UL,0x2eb40d81UL,0xb7bd5c3bUL,0xc0ba6cadUL,
 0xedb88320UL,0x9abfb3b6UL,0x03b6e20cUL,0x74b1d29aUL,0xead54739UL,0x9dd277afUL,0x04db2615UL,0x73dc1683UL,
 0xe3630b12UL,0x94643b84UL,0x0d6d6a3eUL,0x7a6a5aa8UL,0xe40ecf0bUL,0x9309ff9dUL,0x0a00ae27UL,0x7d079eb1UL,
 0xf00f9344UL,0x8708a3d2UL,0x1e01f268UL,0x6906c2feUL,0xf762575dUL,0x806567cbUL,0x196c3671UL,0x6e6b06e7UL,
 0xfed41b76UL,0x89d32be0UL,0x10da7a5aUL,0x67dd4accUL,0xf9b9df6fUL,0x8ebeeff9UL,0x17b7be43UL,0x60b08ed5UL,
 0xd6d6a3e8UL,0xa1d1937eUL,0x38d8c2c4UL,0x4fdff252UL,0xd1bb67f1UL,0xa6bc5767UL,0x3fb506ddUL,0x48b2364bUL,
 0xd80d2bdaUL,0xaf0a1b4cUL,0x36034af6UL,0x41047a60UL,0xdf60efc3UL,0xa867df55UL,0x316e8eefUL,0x4669be79UL,
 0xcb61b38cUL,0xbc66831aUL,0x256fd2a0UL,0x5268e236UL,0xcc0c7795UL,0xbb0b4703UL,0x220216b9UL,0x5505262fUL,
 0xc5ba3bbeUL,0xb2bd0b28UL,0x2bb45a92UL,0x5cb36a04UL,0xc2d7ffa7UL,0xb5d0cf31UL,0x2cd99e8bUL,0x5bdeae1dUL,
 0x9b64c2b0UL,0xec63f226UL,0x756aa39cUL,0x026d930aUL,0x9c0906a9UL,0xeb0e363fUL,0x72076785UL,0x05005713UL,
 0x95bf4a82UL,0xe2b87a14UL,0x7bb12baeUL,0x0cb61b38UL,0x92d28e9bUL,0xe5d5be0dUL,0x7cdcefb7UL,0x0bdbdf21UL,
 0x86d3d2d4UL,0xf1d4e242UL,0x68ddb3f8UL,0x1fda836eUL,0x81be16cdUL,0xf6b9265bUL,0x6fb077e1UL,0x18b74777UL,
 0x88085ae6UL,0xff0f6a70UL,0x66063bcaUL,0x11010b5cUL,0x8f659effUL,0xf862ae69UL,0x616bffd3UL,0x166ccf45UL,
 0xa00ae278UL,0xd70dd2eeUL,0x4e048354UL,0x3903b3c2UL,0xa7672661UL,0xd06016f7UL,0x4969474dUL,0x3e6e77dbUL,
 0xaed16a4aUL,0xd9d65adcUL,0x40df0b66UL,0x37d83bf0UL,0xa9bcae53UL,0xdebb9ec5UL,0x47b2cf7fUL,0x30b5ffe9UL,
 0xbdbdf21cUL,0xcabac28aUL,0x53b39330UL,0x24b4a3a6UL,0xbad03605UL,0xcdd70693UL,0x54de5729UL,0x23d967bfUL,
 0xb3667a2eUL,0xc4614ab8UL,0x5d681b02UL,0x2a6f2b94UL,0xb40bbe37UL,0xc30c8ea1UL,0x5a05df1bUL,0x2d02ef8dUL};
static U32 input_crc(const unsigned char *b,unsigned n)
{U32 c=0xffffffffUL;unsigned i;union {U32 value;unsigned char byte[4];} u;
 while(n--){u.value=c;i=(unsigned)(u.byte[0]^*b++);u.byte[0]=u.byte[1];
  u.byte[1]=u.byte[2];u.byte[2]=u.byte[3];u.byte[3]=0;c=u.value^metadata_crc[i];}
 return ~c;
}
/* Validate real section lines and disk records before generate() uses its
 * insertion anchors. Comments or duplicate/misordered headers cannot stand
 * in for the required sections. Each supported layout has one disk table. */
static void metadata_layout(void)
{static const char *required[4]={"[setup]","[keyboard.drivers]","[io.device]","[disks]"};
 unsigned seen[4]={0,0,0,0},at[4]={0,0,0,0};
 unsigned p=0,e,q,z,t,i,id,mask=0,disks=0,want=on==49046U?4U:5U;
 while(p<on){e=p;while(e<on&&orig[e]!='\r'&&orig[e]!='\n'&&orig[e]!=26)++e;
  q=p;while(q<e&&space(orig[q]))++q;
  if(q<e&&orig[q]=='['){z=q;while(z<e&&orig[z]!=']')++z;
   if(z==e)die("Malformed SETUP.INF section.");
   t=z+1;while(t<e&&space(orig[t]))++t;
   if(t<e&&orig[t]!=';')die("Unexpected text after SETUP.INF section.");
   disks=0;for(i=0;i<4;++i)if(z-q+1==strlen(required[i])&&!memcmp(orig+q,required[i],z-q+1)){
    if(++seen[i]!=1)die("Duplicate SETUP.INF section.");at[i]=q;if(i==3)disks=1;}
  }else if(disks&&q<e&&orig[q]!=';'){
   id=0;t=q;while(t<e&&orig[t]>='0'&&orig[t]<='9'){
    id=id*10U+(unsigned)(orig[t++]-'0');if(id>want)die("Unexpected SETUP.INF disk record.");}
   if(t==q||!id)die("Malformed SETUP.INF disk record.");
   while(t<e&&space(orig[t]))++t;
   if(t==e||orig[t]!='='||(mask&(1U<<id)))die("Duplicate or malformed SETUP.INF disk record.");
   mask|=1U<<id;
  }
  if(e<on&&orig[e]==26)break;
  p=e;if(p<on&&orig[p]=='\r')++p;if(p<on&&orig[p]=='\n')++p;
 }
 for(i=0;i<4;++i)if(seen[i]!=1)die("Missing SETUP.INF section.");
 if(!(at[0]<at[3]&&at[3]<at[1]&&at[1]<at[2]))die("SETUP.INF sections out of order.");
 if(mask!=((1U<<(want+1))-2U))die("Incomplete SETUP.INF disk table.");
}
static void source(void)
{ char h[65];unsigned i;int eof=0;
 if(on!=49046U&&on!=49095U)die("Unsupported SETUP.INF size.");
 if(input_crc(orig,on)!=(on==49046U?0x92333a90UL:0xa8246e14UL))die("Unknown or modified SETUP.INF. Nothing is overwritten.");
 for(i=0;i<on;i++){if(orig[i]==26){eof=1;continue;}if(eof&&orig[i]!='\r'&&orig[i]!='\n')die("Invalid SETUP.INF EOF padding.");if(!orig[i]||(orig[i]<32&&orig[i]!='\r'&&orig[i]!='\n'&&orig[i]!='\t'))die("Invalid SETUP.INF text.");}
 metadata_layout();
 if(deep_verify){if(!selftest())die("SHA256 self-test failed.");hashmem(orig,on,h);if(strcmp(h,on==49046U?SOURCE_SHA:"aa4a92022c88750d9dee4a8c4b003de295d44f82f70f2d5430023f1984e6d84c"))die("Unknown or modified SETUP.INF. Nothing is overwritten.");}
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
 join(drvpath,selected?"TNDYK3.DRV":"KEYBOARD.DRV",1);join(other,selected?"TNDYK3.DRV":"KEYBOARD.DRV",0);if(exists(other))die("Keyboard in Windows root makes driver lookup ambiguous.");keyboard_layout();if(deep_verify){hashfile(drvpath,h);if(strcmp(h,selected?K3_SHA:KBD_SHA))die("Keyboard binary does not match the verified version.");}
}
static unsigned locate(const char *s)
{unsigned i,l=(unsigned)strlen(s),found=0,count=0;for(i=0;i+l<=on;++i)if(!memcmp(orig+i,s,l)){found=i;++count;}if(count!=1)die("Unexpected SETUP.INF structure.");return found;}
static void append(const unsigned char *p,unsigned n)
{if(n>(unsigned)MAXINI-dn)die("Result too large.");memcpy(dest+dn,p,n);dn+=n;}
static void textadd(const char *s){append((const unsigned char*)s,(unsigned)strlen(s));}
static void generate(int k3)
{unsigned m=locate("[io.device]"),k=locate("[keyboard.drivers]")+18;dn=0;if(k3){append(orig,k);textadd("\r\nxtkbd = 0:tndyk3.drv");append(orig+k,m-k);}else append(orig,m);textadd(prefix);textadd(k3?"xtkbd":"kbd");textadd(suffix);append(orig+m,on-m);}
static int patched(const char *p)
{generate(0);if(same(p,dest,dn))return 1;generate(1);return same(p,dest,dn)?2:0;}
static void rm_patch(const char *p)
{if(!exists(p))return;if(!patched(p))die("Unknown staged patch; preserve files.");remove_known(p,dest,dn);}
static void clean_original(void)
{if(!same(ini,orig,on))die("Original restoration did not verify.");if(!exists(bak))writefile(bak,orig,on);remove_known(old,orig,on);remove_known(rst,orig,on);rm_patch(tmp);rm_patch(curpath);puts("Original SETUP.INF restored and verified. Active Windows settings unchanged.");}
static int loaded(void)
{if(!exists(sav)){if(exists(bak)||exists(tmp)||exists(old)||exists(rst)||exists(curpath))die("Unowned sidecar collision; preserve files.");return 0;}on=loadsnap(sav,orig);source();if(exists(bak)&&!same(bak,orig,on))die("Backup changed; preserve files.");return 1;}
static void restore(void)
{if(!loaded()){puts("No owned profile transaction. Nothing changed.");return;}
 if(exists(old)&&!same(old,orig,on))die("Unknown old-file sidecar.");if(exists(rst)&&!same(rst,orig,on))die("Unknown restore sidecar.");if(exists(tmp)&&!patched(tmp))die("Unknown staged patch.");if(exists(curpath)&&!patched(curpath))die("Unknown saved patched metadata.");
 if(!exists(ini)){if(exists(old)){movefile(old,ini);}else if(exists(curpath)&&exists(rst)){movefile(rst,ini);}else die("Missing SETUP.INF without proven interrupted rename.");clean_original();return;}
 if(same(ini,orig,on)){clean_original();return;}
 if(!patched(ini))die("SETUP.INF changed after preparation; refusing to overwrite edits.");if(exists(curpath))die("Both live and recovery metadata exist unexpectedly.");remove_known(old,orig,on);if(!exists(rst))writefile(rst,orig,on);movefile(ini,curpath);movefile(rst,ini);clean_original();
}
static void check(int apply)
{int owned=loaded(),variant;unsigned z;installed();
 if(owned){if(!exists(bak))die("Incomplete backup: run RESTORE first.");if(exists(tmp)||exists(old)||exists(rst)||exists(curpath)||!exists(ini))die("Interrupted transaction: run RESTORE first.");variant=patched(ini);if(variant){if(variant!=selected+1)die("Keyboard changed: RESTORE then APPLY before selecting Computer.");puts("Matching Tandy Computer choice already prepared. Nothing changed.");return;}if(!same(ini,orig,on))die("SETUP.INF changed; preserve edits and backups.");}
 else {on=readall(ini,orig,MAXINI);source();}
 generate(selected);printf("Ready: %s, preserving %s.\n",label,selected?"TNDYK3.DRV":"KEYBOARD.DRV");if(!apply){puts("CHECK only: no files changed.");return;}writable(ini);
 if(!owned){snapshot(sav,orig,on);z=loadsnap(sav,cur);if(z!=on||memcmp(cur,orig,on))die("Ownership reread failed.");writefile(bak,orig,on);}
 generate(selected);writefile(tmp,dest,dn);if(!same(ini,orig,on))die("SETUP.INF changed before replacement.");movefile(ini,old);movefile(tmp,ini);if(!same(ini,dest,dn))die("Patched metadata reread failed.");remove_known(old,orig,on);puts("Choice added. Nothing selected; no active driver or SYSTEM.INI changed.");puts("Run Windows DOS SETUP to select it. Run CPSET CHECK first each time.");
}
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
int main(int argc,char **argv)
{int verify;
 setbuf(stdout,NULL);if(argc>1&&eqi(argv[argc-1],"/VERIFY")){deep_verify=1;argc--;}
 verify=argc==3&&eqi(argv[1],"VERIFY");if(verify)deep_verify=1;
 if(argc!=3||(!eqi(argv[1],"CHECK")&&!eqi(argv[1],"APPLY")&&!eqi(argv[1],"RESTORE")&&!verify)){puts("Usage: CPSET CHECK|APPLY|RESTORE|VERIFY C:\\WINDOWS [/VERIFY]");return 2;}
 puts(deep_verify?"CPSET deep SHA verification ON.":"CPSET bounded checks; SHA verification OFF.");
 paths(argv[2]);not_windows();buffers();if(eqi(argv[1],"RESTORE"))restore();else check(eqi(argv[1],"APPLY"));free(dest);free(cur);free(orig);return 0;
}
