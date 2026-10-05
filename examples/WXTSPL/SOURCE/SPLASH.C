/* WindowsXT splash-only updater. C89 / Microsoft C 6 / 8088.
 * No Windows, driver, font or loader binaries are embedded.
 * Only WIN.COM, WIN.WXB (original) and WIN.WXN (new stage) are named.
 * No existing file is opened for writing; no file is deleted.
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
#ifndef O_BINARY
#define O_BINARY 0
#endif
#define PATHMAX 512
#else
#include <io.h>
#include <dos.h>
typedef unsigned long U32;
#define PATHMAX 128
#endif

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
static void finish(SHA *s,char *out){unsigned i,j;U32 bits=s->bytes*8;static const char hex[]="0123456789abcdef";s->b[s->n++]=128;if(s->n>56){while(s->n<64)s->b[s->n++]=0;transform(s);s->n=0;}while(s->n<60)s->b[s->n++]=0;for(i=0;i<4;i++)s->b[60+i]=(unsigned char)(bits>>(24-i*8));transform(s);for(i=0;i<8;i++)for(j=0;j<4;j++){unsigned v=(unsigned)((s->h[i]>>(24-j*8))&255);*out++=hex[v>>4];*out++=hex[v&15];}*out=0;}
static int selftest(void){SHA s;char h[65];init(&s);finish(&s,h);if(strcmp(h,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))return 0;init(&s);update(&s,(const unsigned char *)"abc",3);finish(&s,h);return !strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad");}
static const char *oldhash[2]={"5551ebcd3f32df26f759c5423f806733e006c3cae640a8336e5c618f8d899659","6f07b5a9fc764c74f9b3c5a0e0c521f87cdd1b3507863f1772dee4da814b1907"};
static const char newhash[]="8c8901b4c8482a2aefcf8a0a1beaba2ee07f90af94bf23993a8cf49eb6a30ebc";
static const char rlehash[]="eec3a413bb776bea8eccb19a379428d15f06cbdc0ac41b0871345ff9c24caf1c";
static char live[PATHMAX],backup[PATHMAX],stage[PATHMAX];
/* classify: 0 absent, 1/2 exact originals, 3 exact new, -1 unknown/error. */
static int digest_file(const char *p,char *hex,long *size){FILE *f;SHA s;unsigned char b[512];size_t n;struct stat st;
#ifdef HOST_TEST
 if(lstat(p,&st)){if(errno==ENOENT)return 0;return -1;}if(!S_ISREG(st.st_mode))return -1;
#else
 if(stat((char *)p,&st)){if(errno==ENOENT)return 0;return -1;}if(!(st.st_mode&S_IFREG))return -1;
#endif
 if(st.st_size<0||st.st_size>65280L)return -1;f=fopen(p,"rb");if(!f)return -1;init(&s);*size=0;while((n=fread(b,1,sizeof(b),f))!=0){*size+=(long)n;if(*size>65280L){fclose(f);return -1;}update(&s,b,(unsigned)n);}if(ferror(f)){fclose(f);return -1;}if(fclose(f))return -1;finish(&s,hex);return 1;}
static int classify(const char *p){char h[65];long n;int r=digest_file(p,h,&n);if(r!=1)return r;if(n==11118L&&!strcmp(h,oldhash[0]))return 1;if(n==10266L&&!strcmp(h,oldhash[1]))return 2;if(n==8398L&&!strcmp(h,newhash))return 3;return -1;}
static int exists(const char *p){struct stat st;
#ifdef HOST_TEST
 if(lstat(p,&st)==0)return 1;
#else
 if(stat((char *)p,&st)==0)return 1;
#endif
 return errno==ENOENT?0:1;}
static int movefile(const char *a,const char *b){if(exists(b)){printf("REFUSED: destination exists: %s\n",b);return 0;}if(rename(a,b)){printf("Rename failed: %s -> %s. Original remains recoverable.\n",a,b);return 0;}return 1;}
static int makepaths(const char *dir){size_t n=strlen(dir);unsigned i;char sep;
#ifdef HOST_TEST
 sep='/';
#else
 sep='\\';
#endif
 if(!n||n+10>=PATHMAX)return 0;for(i=0;i<n;i++)if(dir[i]=='*'||dir[i]=='?')return 0;strcpy(live,dir);if(dir[n-1]!='/'&&dir[n-1]!='\\'){live[n++]=sep;live[n]=0;}strcpy(backup,live);strcpy(stage,live);strcat(live,"WIN.COM");strcat(backup,"WIN.WXB");strcat(stage,"WIN.WXN");return 1;}
static int windows_running(void){
#ifdef HOST_TEST
 return 0;
#else
 union REGS r;memset(&r,0,sizeof(r));r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al!=0&&r.h.al!=0x80)return 1;memset(&r,0,sizeof(r));r.x.ax=0x4680;int86(0x2f,&r,&r);return r.x.ax==0;
#endif
}
#ifdef HOST_TEST
static void checkpoint(const char *label){const char *p=getenv("WXT_FAILPOINT");if(p&&!strcmp(p,label))exit(99);}
#else
#define checkpoint(label) ((void)0)
#endif
static int copybytes(FILE *f,int fd,long count){unsigned char b[512];unsigned n;int got;while(count){n=(unsigned)(count>512L?512L:count);got=(int)fread(b,1,n,f);if(got!=(int)n||write(fd,b,n)!=(int)n)return 0;count-=n;}return 1;}
static int artwork_ok(void){char h[65];long size;return digest_file("WXTSPL01.RLE",h,&size)==1&&size==4062L&&!strcmp(h,rlehash);}
static int buildstage(const char *original){FILE *src,*art;int fd,ok;if(!artwork_ok()){puts("REFUSED: WXTSPL01.RLE missing or not the exact approved artwork in current directory.");return 0;}
 src=fopen(original,"rb");if(!src)return 0;art=fopen("WXTSPL01.RLE","rb");if(!art){fclose(src);return 0;}
 fd=open(stage,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);if(fd<0){fclose(src);fclose(art);puts("REFUSED: cannot create an exclusive stage file.");return 0;}
 checkpoint("created-stage");ok=copybytes(src,fd,4336L);checkpoint("copied-prefix");if(ok)ok=copybytes(art,fd,4062L);checkpoint("copied-art");if(fclose(src))ok=0;if(fclose(art))ok=0;if(close(fd))ok=0;checkpoint("closed-stage");if(!ok||classify(stage)!=3){puts("Stage verification failed. Original was not changed. Preserve/move WIN.WXN aside before retry.");return 0;}return 1;}
static int original(int k){return k==1||k==2;}
static int apply(int l,int b,int n){int before;
 if(l==3){if(n!=0||!(b==0||original(b)))return 0;puts("ALREADY APPLIED: WIN.COM is the exact approved WindowsXT version.");if(!b)puts("No original backup exists; RESTORE is unavailable.");return 1;}
 if(original(l)&&b==0&&(n==0||n==3)){
  before=l;if(!n&&!buildstage(live))return 0;
  if(classify(live)!=before||classify(stage)!=3||exists(backup))return 0;
  if(!movefile(live,backup))return 0;checkpoint("original-renamed");if(classify(backup)!=before){puts("STOP: backup verification failed; preserve all files.");return 0;}
  if(!movefile(stage,live)){puts("Run RESTORE to put the verified original back, or APPLY to finish.");return 0;}
  checkpoint("new-live");if(classify(live)!=3||classify(backup)!=before)return 0;puts("APPLIED: verified original retained as WIN.WXB. Only WIN.COM changed.");return 1;
 }
 if(l==0&&original(b)&&(n==0||n==3)){
  before=b;if(!n&&!buildstage(backup))return 0;
  if(classify(backup)!=before||classify(stage)!=3||exists(live))return 0;
  if(!movefile(stage,live))return 0;if(classify(live)!=3||classify(backup)!=before)return 0;puts("RECOVERED APPLY: WIN.COM restored with approved splash; original in WIN.WXB.");return 1;
 }
 return 0;
}
static int restore(int l,int b,int n){int before;
 if(original(l)&&b==0){puts("ALREADY ORIGINAL: WIN.COM recognized. Any stage file is left untouched.");if(n!=0&&n!=3)puts("Unrecognized stage still blocks APPLY; preserve/move it aside manually.");return 1;}
 if(l==0&&original(b)){
  before=b;if(classify(backup)!=before||exists(live))return 0;if(!movefile(backup,live))return 0;checkpoint("restored-live");if(classify(live)!=before)return 0;puts("RESTORED: original WIN.COM recovered. Stage, if any, left untouched.");return 1;
 }
 if(l==3&&original(b)&&n==0){
  before=b;if(classify(live)!=3||classify(backup)!=before)return 0;
  if(!movefile(live,stage))return 0;checkpoint("restore-gap");if(classify(stage)!=3||classify(backup)!=before)return 0;
  if(!movefile(backup,live)){puts("Run RESTORE again to finish; original remains in WIN.WXB.");return 0;}
  checkpoint("restored-live");if(classify(live)!=before)return 0;puts("RESTORED: original WIN.COM. Approved replacement retained as WIN.WXN.");return 1;
 }
 return 0;
}
int main(int argc,char **argv){int l,b,n,mode,i,ok;char command[16];
 puts("WindowsXT splash-only updater 0.2 - CHECK before APPLY; exit Windows first.");
 if(!selftest()){puts("REFUSED: SHA-256 self-test failed.");return 2;}
 if(argc==2&&!strcmp(argv[1],"SELFTEST")){puts("PASS SHA-256 empty and abc vectors.");return 0;}
 if(argc!=3||strlen(argv[1])>=sizeof(command)||!makepaths(argv[2])){puts("Usage: WXTSPL CHECK|APPLY|RESTORE C:\\WINDOWS");return 2;}
 strcpy(command,argv[1]);for(i=0;command[i];i++)command[i]=(char)toupper((unsigned char)command[i]);mode=!strcmp(command,"CHECK")?0:!strcmp(command,"APPLY")?1:!strcmp(command,"RESTORE")?2:-1;if(mode<0)return 2;
 if(windows_running()){puts("REFUSED: Windows or a task switcher is active. Exit fully to DOS first.");return 2;}
 l=classify(live);b=classify(backup);n=classify(stage);printf("States: WIN.COM=%d WIN.WXB=%d WIN.WXN=%d\n",l,b,n);puts("0 absent; 1 stock; 2 old Tandy; 3 approved XT; -1 unknown/refused.");
 if(!mode){
  ok=(original(l)&&b==0&&(n==0||n==3))||(l==3&&(b==0||original(b))&&n==0)||(l==0&&original(b)&&(n==0||n==3));
  if(ok){if(l!=3&&n==0&&!artwork_ok()){puts("CHECK REFUSED: exact WXTSPL01.RLE needed in current directory for APPLY. No files changed.");return 2;}puts("CHECK PASS: recognized layout. No files changed.");if(l==0)puts("Interrupted state: choose APPLY or RESTORE before starting Windows.");if(l==3&&b==0)puts("No original backup; RESTORE unavailable.");return 0;}
  puts("CHECK REFUSED: unknown or conflicting files. No files changed.");if(l==0&&original(b))puts("RESTORE can recover verified WIN.WXB while leaving unknown stage untouched.");return 2;
 }
 ok=mode==1?apply(l,b,n):restore(l,b,n);
 if(!ok){puts("REFUSED/INCOMPLETE: preserve WIN.WXB and all existing files. Run CHECK.");return 2;}return 0;
}
