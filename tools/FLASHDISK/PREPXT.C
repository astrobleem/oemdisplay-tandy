/* PREPXT.C - own-media WINXT staging, DOS 3.3+, 8086/8088.
 * Build with Microsoft C 6: CL /AS /G0 /W3 PREPXT.C
 * No Windows bytes are embedded. All accepted content is SHA-256 pinned.
 * Source media and Windows are read-only. Output is fresh C:\WINXT only.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <signal.h>
#include <dos.h>
#include <direct.h>
#include <fcntl.h>
#include <io.h>
#define PTH 80
#define MAXFONT 6000
#define DEST "C:\\WINXT"
typedef unsigned long U32;
struct pin { char *name; char *hex; U32 size; int kind; };
/* kind: 0 public runtime, 1 user-owned support, 2 locally derived font. */
#include "XTPINS.H"
#define NPINS (sizeof(pins)/sizeof(pins[0]))
struct sha { U32 h[8], bytes; unsigned used; unsigned char block[64]; };
static struct sha state;
static unsigned char io[4096], verifybuf[4096], work[MAXFONT], derived[MAXFONT], ring[4096];
static char dirs[7][PTH], chosen[8][PTH], runtime[PTH], windir[PTH];
static int ndirs, made, opened=-1;
static volatile int cancelled;
static U32 w[64];
static U32 kk[64]={
 0x428a2f98UL,0x71374491UL,0xb5c0fbcfUL,0xe9b5dba5UL,0x3956c25bUL,0x59f111f1UL,0x923f82a4UL,0xab1c5ed5UL,
 0xd807aa98UL,0x12835b01UL,0x243185beUL,0x550c7dc3UL,0x72be5d74UL,0x80deb1feUL,0x9bdc06a7UL,0xc19bf174UL,
 0xe49b69c1UL,0xefbe4786UL,0x0fc19dc6UL,0x240ca1ccUL,0x2de92c6fUL,0x4a7484aaUL,0x5cb0a9dcUL,0x76f988daUL,
 0x983e5152UL,0xa831c66dUL,0xb00327c8UL,0xbf597fc7UL,0xc6e00bf3UL,0xd5a79147UL,0x06ca6351UL,0x14292967UL,
 0x27b70a85UL,0x2e1b2138UL,0x4d2c6dfcUL,0x53380d13UL,0x650a7354UL,0x766a0abbUL,0x81c2c92eUL,0x92722c85UL,
 0xa2bfe8a1UL,0xa81a664bUL,0xc24b8b70UL,0xc76c51a3UL,0xd192e819UL,0xd6990624UL,0xf40e3585UL,0x106aa070UL,
 0x19a4c116UL,0x1e376c08UL,0x2748774cUL,0x34b0bcb5UL,0x391c0cb3UL,0x4ed8aa4aUL,0x5b9cca4fUL,0x682e6ff3UL,
 0x748f82eeUL,0x78a5636fUL,0x84c87814UL,0x8cc70208UL,0x90befffaUL,0xa4506cebUL,0xbef9a3f7UL,0xc67178f2UL};
#define R(x,n) (((x)>>(n))|((x)<<(32-(n))))
static void block(struct sha *s)
{
 U32 a,b,c,d,e,f,g,h,t,u,x,y; unsigned i; unsigned char *p;
 for(i=0;i<16;i++){p=s->block+4*i;w[i]=((U32)p[0]<<24)|((U32)p[1]<<16)|((U32)p[2]<<8)|p[3];}
 for(i=16;i<64;i++){x=w[i-15];y=w[i-2];w[i]=w[i-16]+(R(x,7)^R(x,18)^(x>>3))+w[i-7]+(R(y,17)^R(y,19)^(y>>10));}
 a=s->h[0];b=s->h[1];c=s->h[2];d=s->h[3];e=s->h[4];f=s->h[5];g=s->h[6];h=s->h[7];
 for(i=0;i<64;i++){t=h+(R(e,6)^R(e,11)^R(e,25))+((e&f)^((~e)&g))+kk[i]+w[i];u=(R(a,2)^R(a,13)^R(a,22))+((a&b)^(a&c)^(b&c));h=g;g=f;f=e;e=d+t;d=c;c=b;b=a;a=t+u;}
 s->h[0]+=a;s->h[1]+=b;s->h[2]+=c;s->h[3]+=d;s->h[4]+=e;s->h[5]+=f;s->h[6]+=g;s->h[7]+=h;
}
static void sha_init(struct sha *s)
{
 s->h[0]=0x6a09e667UL;s->h[1]=0xbb67ae85UL;s->h[2]=0x3c6ef372UL;s->h[3]=0xa54ff53aUL;
 s->h[4]=0x510e527fUL;s->h[5]=0x9b05688cUL;s->h[6]=0x1f83d9abUL;s->h[7]=0x5be0cd19UL;s->bytes=0;s->used=0;
}
static void sha_add(struct sha *s,unsigned char *p,unsigned n)
{
 unsigned k;s->bytes+=n;
 while(n){k=64-s->used;if(k>n)k=n;memcpy(s->block+s->used,p,k);s->used+=k;p+=k;n-=k;if(s->used==64){block(s);s->used=0;}}
}
static void sha_end(struct sha *s,char *hex)
{
 unsigned i,j;U32 bits=s->bytes<<3;unsigned char pad[64];static char digits[]="0123456789abcdef";
 memset(pad,0,sizeof(pad));pad[0]=0x80;sha_add(s,pad,s->used<56?56-s->used:120-s->used);
 memset(pad,0,8);pad[4]=(unsigned char)(bits>>24);pad[5]=(unsigned char)(bits>>16);pad[6]=(unsigned char)(bits>>8);pad[7]=(unsigned char)bits;sha_add(s,pad,8);
 for(i=0;i<8;i++)for(j=0;j<8;j++)hex[i*8+j]=digits[(unsigned)((s->h[i]>>(28-4*j))&15)];hex[64]=0;
}
static void stop(char *message,char *detail)
{
 if(opened>=0){_dos_close(opened);opened=-1;}
 printf("\nREFUSED: %s\n%s\n",message,detail?detail:"");
 puts("Windows, source media and boot files were not changed. Setup was not started.");
 if(made)puts("C:\\WINXT is incomplete. Do not run it. Review/remove that new folder to retry.");
 else puts("No output folder or installation marker was created.");
 exit(1);
}
static void onbreak(int sig){sig=sig;cancelled=1;signal(SIGINT,onbreak);}
static void checkcancel(void){if(cancelled)stop("Cancelled.","");}
static void join(char *out,char *dir,char *name)
{
 unsigned n=strlen(dir);if(n+strlen(name)+2>PTH)stop("Path too long.",dir);
 strcpy(out,dir);if(n && out[n-1]!='\\')strcat(out,"\\");strcat(out,name);
}
static int attr(char *path,unsigned *a)
{
 unsigned r=_dos_getfileattr(path,a);if(!r)return 1;if(r==2||r==3)return 0;stop("Cannot safely inspect path.",path);return 0;
}
static void directory(char *path)
{
 unsigned a;if(!attr(path,&a)||!(a&_A_SUBDIR))stop("Directory missing or not readable.",path);
}
static void absolute(char *out,char *in)
{
 unsigned n;char *p;
 if(strlen(in)>63||!_fullpath(out,in,PTH))stop("Cannot resolve DOS path.",in);
 strupr(out);n=strlen(out);if(n>3&&out[n-1]=='\\')out[--n]=0;
 if(n>63||n<3||!isalpha((unsigned char)out[0])||out[1]!=':'||out[2]!='\\')stop("Use a DOS drive:\\directory path.",in);
 for(p=out+3;*p;p++)if(!isalnum((unsigned char)*p)&&*p!='_'&&*p!='-'&&*p!='~'&&*p!='$'&&*p!='.'&&*p!='\\')stop("Use DOS paths without spaces or wildcards.",in);
 directory(out);
}
static void adddir(char *path)
{
 int i;for(i=0;i<ndirs;i++)if(!stricmp(dirs[i],path))return;
 if(ndirs>=7)stop("Too many source directories.",path);strcpy(dirs[ndirs++],path);
}
static void hashmem(unsigned char *p,unsigned n,char *expected,char *name)
{
 char hex[65];checkcancel();sha_init(&state);sha_add(&state,p,n);sha_end(&state,hex);
 if(strcmp(hex,expected))stop("SHA-256 mismatch (corrupt or different Windows/runtime version).",name);
}
static void hashfile(char *path,struct pin *p)
{
 FILE *f;unsigned n;U32 size=0;char hex[65];unsigned a;
 if(!attr(path,&a)||(a&(_A_SUBDIR|_A_VOLID)))stop("Required regular file is missing.",path);
 f=fopen(path,"rb");if(!f)stop("Cannot read file.",path);sha_init(&state);
 while((n=fread(io,1,sizeof(io),f))!=0){checkcancel();size+=n;if(size>p->size){fclose(f);stop("File size does not match the pinned release.",path);}sha_add(&state,io,n);}
 if(ferror(f)){fclose(f);stop("Read error.",path);}fclose(f);sha_end(&state,hex);
 if(size!=p->size||strcmp(hex,p->hex))stop("SHA-256/size mismatch in pinned file.",path);
}
/* Only exact, <=6000-byte pinned support files are accepted, never arbitrary
 * expansion sizes. The 4096-byte SZDD ring and every stream read are bounded. */
static unsigned expand(char *path,unsigned want)
{
 FILE *f;unsigned n,pos=0,cursor=4080,flags,bit,off,len,i;int a,b,c;U32 declared;unsigned char hdr[14];
 f=fopen(path,"rb");if(!f)stop("Cannot read Windows support file.",path);
 n=fread(hdr,1,14,f);
 if(n>=8&&!memcmp(hdr,"SZDD\210\360\047\063",8)){
  if(n!=14||hdr[8]!='A'){fclose(f);stop("Unsupported or truncated SZDD header.",path);}
  declared=(U32)hdr[10]|((U32)hdr[11]<<8)|((U32)hdr[12]<<16)|((U32)hdr[13]<<24);
  if(declared!=want||declared>MAXFONT){fclose(f);stop("SZDD expanded size differs from the pinned support file.",path);}
  memset(ring,' ',sizeof(ring));
  while(pos<want){checkcancel();c=fgetc(f);if(c==EOF){fclose(f);stop("Truncated SZDD flags.",path);}flags=(unsigned)c;
   for(bit=1;bit<256&&pos<want;bit<<=1){
    if(flags&bit){a=fgetc(f);if(a==EOF){fclose(f);stop("Truncated SZDD literal.",path);}work[pos++]=ring[cursor]=(unsigned char)a;cursor=(cursor+1)&4095;}
    else{a=fgetc(f);b=fgetc(f);if(a==EOF||b==EOF){fclose(f);stop("Truncated SZDD reference.",path);}off=(unsigned)a|(((unsigned)b&0xf0)<<4);len=((unsigned)b&15)+3;
     if(len>want-pos){fclose(f);stop("SZDD reference exceeds declared length.",path);}
     for(i=0;i<len;i++){work[pos++]=ring[cursor]=ring[(off+i)&4095];cursor=(cursor+1)&4095;}
    }
   }
  }
  if(fgetc(f)!=EOF||ferror(f)){fclose(f);stop("Trailing bytes or read error after SZDD stream.",path);}
 }else{
  if(n>want||want>MAXFONT){fclose(f);stop("Invalid Windows support size.",path);}memcpy(work,hdr,n);pos=n;
  while(pos<want){n=fread(work+pos,1,want-pos,f);if(!n)break;pos+=n;checkcancel();}
  if(pos!=want||fgetc(f)!=EOF||ferror(f)){fclose(f);stop("Expanded Windows support size/read mismatch.",path);}
 }
 fclose(f);return pos;
}
static void find_support(int k)
{
 int i,v,found=0;char path[PTH],name[13];unsigned a;
 for(i=0;i<ndirs;i++)for(v=0;v<2;v++){
  strcpy(name,pins[k].name);if(v)name[strlen(name)-1]='_';join(path,dirs[i],name);
  if(attr(path,&a)){
   if(a&(_A_SUBDIR|_A_VOLID))stop("Support candidate is not a regular file.",path);
   printf("Checking %s\n",path);expand(path,(unsigned)pins[k].size);hashmem(work,(unsigned)pins[k].size,pins[k].hex,path);
   if(!found){strcpy(chosen[k],path);found=1;}
  }
 }
 if(!found){printf("\nMissing: %s\n",pins[k].name);stop("Need matching original Windows 3.0 files in Windows or a media folder.","Add the original files to a hard-disk media folder, then retry with that path.");}
}
static int pinindex(char *name)
{
 unsigned i;for(i=0;i<NPINS;i++)if(!strcmp(pins[i].name,name))return i;stop("Internal pin table error.",name);return 0;
}
static void derive_font(void)
{
 int a=pinindex("CGASYS.FON"),b=pinindex("CGAFIX.FON"),d=pinindex("TXTSYS.FON");
 expand(chosen[a],(unsigned)pins[a].size);hashmem(work,(unsigned)pins[a].size,pins[a].hex,chosen[a]);memcpy(derived,work,(unsigned)pins[a].size);
 expand(chosen[b],(unsigned)pins[b].size);hashmem(work,(unsigned)pins[b].size,pins[b].hex,chosen[b]);
 /* Pinned NE resource locations: FONTDIR (1216,128), FONT 27
  * (1344,2832 in CGAFIX; 1344,2992 in CGASYS). Exact input hashes above
  * guarantee these offsets. Preserve CGASYS NE metadata and zero tail. */
 memcpy(derived+1216,work+1216,128);memcpy(derived+1344,work+1344,2832);memset(derived+4176,0,160);
 hashmem(derived,(unsigned)pins[d].size,pins[d].hex,"locally derived TXTSYS.FON");
}
static void diskspace(void)
{
 struct diskfree_t d;U32 cluster,needed,avail;unsigned i;
 if(_dos_getdiskfree(3,&d)||!d.bytes_per_sector||!d.sectors_per_cluster)stop("Cannot determine free space on C:.","");
 cluster=(U32)d.bytes_per_sector*d.sectors_per_cluster;
 /* DOS 3.x FAT directory: 45 entries plus dot entries; rounded clusters.
  * Reserve another 128 KiB for filesystem overhead/headroom. Installer later
  * separately checks its Windows backup requirement. */
 needed=((NPINS+2UL)*32+cluster-1)/cluster*cluster+131072UL;
 for(i=0;i<NPINS;i++)needed+=(pins[i].size+cluster-1)/cluster*cluster;
 avail=(U32)d.avail_clusters*cluster;
 printf("C: free %lu bytes; staging requires %lu bytes including headroom.\n",avail,needed);
 if(avail<needed)stop("Not enough free space on C:. No staging was attempted.","Free space, then retry. The later installer also needs space for backups.");
}
static void createout(char *path)
{
 if(_dos_creatnew(path,_A_NORMAL,&opened))stop("Cannot create a new output file; no overwrite is allowed.",path);
}
static void putbytes(unsigned char *p,unsigned n,char *path)
{
 unsigned wrote;checkcancel();if(_dos_write(opened,p,n,&wrote)||wrote!=n)stop("Write error or disk full.",path);
}
static void closeout(char *path)
{
 int h=opened;opened=-1;if(_dos_close(h))stop("Cannot close output file.",path);
}
/* Read back after closing the DOS output handle. Compare exact bytes against
 * the source whose SHA was just checked, or verified support bytes in memory.
 * A mismatch is fatal; INSTALL.BAT is still withheld until the last file. */
static void verifyfile(char *path,char *source,unsigned char *bytes,U32 size)
{
 FILE *a,*b=NULL;unsigned n,m;U32 total=0;
 a=fopen(path,"rb");if(!a)stop("Cannot reopen output for verification.",path);
 if(source){b=fopen(source,"rb");if(!b){fclose(a);stop("Cannot reopen source for byte comparison.",source);}}
 while((n=fread(io,1,sizeof(io),a))!=0){
  checkcancel();if(total+n>size){fclose(a);if(b)fclose(b);stop("Output size changed during readback.",path);}
  if(b){m=fread(verifybuf,1,n,b);if(m!=n||memcmp(io,verifybuf,n)){fclose(a);fclose(b);stop("Output/source byte comparison failed.",path);}}
  else if(memcmp(io,bytes+(unsigned)total,n)){fclose(a);stop("Output/support byte comparison failed.",path);}
  total+=n;
 }
 if(ferror(a)||total!=size){fclose(a);if(b)fclose(b);stop("Output readback error or size mismatch.",path);}fclose(a);
 if(b){if(fgetc(b)!=EOF||ferror(b)){fclose(b);stop("Source changed or read failed during byte comparison.",source);}fclose(b);}
}
static void copyone(unsigned k)
{
 char from[PTH],to[PTH],hex[65];FILE *f;unsigned n;U32 total=0;
 join(to,DEST,!strcmp(pins[k].name,"INSTALL.BAT")?"INSTALL.NEW":pins[k].name);
 if(pins[k].kind==1){expand(chosen[k],(unsigned)pins[k].size);hashmem(work,(unsigned)pins[k].size,pins[k].hex,chosen[k]);createout(to);putbytes(work,(unsigned)pins[k].size,to);closeout(to);}
 else if(pins[k].kind==2){hashmem(derived,(unsigned)pins[k].size,pins[k].hex,pins[k].name);createout(to);putbytes(derived,(unsigned)pins[k].size,to);closeout(to);}
 else{
  join(from,runtime,pins[k].name);f=fopen(from,"rb");if(!f)stop("Cannot reread runtime source.",from);createout(to);sha_init(&state);
  while((n=fread(io,1,sizeof(io),f))!=0){total+=n;if(total>pins[k].size){fclose(f);stop("Runtime source changed after validation.",from);}sha_add(&state,io,n);putbytes(io,n,to);}
  if(ferror(f)){fclose(f);stop("Source read error.",from);}fclose(f);closeout(to);sha_end(&state,hex);
  if(total!=pins[k].size||strcmp(hex,pins[k].hex))stop("Runtime source changed after validation.",from);
 }
 if(pins[k].kind==0)verifyfile(to,from,NULL,pins[k].size);
 else verifyfile(to,NULL,pins[k].kind==1?work:derived,pins[k].size);
 printf("Verified %s\n",to);
}
static void not_windows(void)
{
 union REGS r;r.x.ax=0x1600;int86(0x2f,&r,&r);
 if(r.h.al&&r.h.al!=0x80)stop("Exit Windows completely before running PREPXT.","Use a real DOS prompt, not a Windows DOS session.");
 r.x.ax=0x4680;int86(0x2f,&r,&r);
 if(!r.x.ax)stop("Exit Windows completely before running PREPXT.","Use a real DOS prompt, not a Windows DOS session.");
}
static int selftest(void)
{
 char h[65];static char msg[]="abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq";
 sha_init(&state);sha_end(&state,h);if(strcmp(h,"e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"))return 1;
 sha_init(&state);sha_add(&state,(unsigned char *)"abc",3);sha_end(&state,h);if(strcmp(h,"ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"))return 1;
 sha_init(&state);sha_add(&state,(unsigned char *)msg,strlen(msg));sha_end(&state,h);if(strcmp(h,"248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"))return 1;
 puts("SHA-256 self-test passed (empty, abc, two-block vector).");return 0;
}
int main(int argc,char **argv)
{
 char path[PTH],target[PTH],answer[16];unsigned a,i;int install;union REGS r;
 setbuf(stdout,NULL);signal(SIGINT,onbreak);
 if(argc==2&&!stricmp(argv[1],"/SELFTEST"))return selftest();
 puts("PREPXT - verified own-media preparation for WINXT (8088 / DOS 3.3+)");
 if(argc<3||argc>7){puts("Usage: PREPXT runtime-dir Windows-dir [media-dir ...]\nExample: PREPXT WINXT C:\\WINDOWS C:\\WIN30SRC\nOutput is fresh C:\\WINXT only. No Python or network is needed.\nUse real DOS; leave each source drive mounted for the whole run.");return 1;}
 r.h.ah=0x30;intdos(&r,&r);if(r.h.al<3||(r.h.al==3&&r.h.ah<30))stop("DOS 3.3 or later is required.","");
 not_windows();
 if(sizeof(U32)!=4||selftest())stop("SHA-256 implementation self-test failed.","");
 if(attr(DEST,&a))stop("C:\\WINXT already exists. It will never be overwritten or resumed.","Keep an existing installation. To retry a partial stage, review/remove it first.");
 absolute(runtime,argv[1]);absolute(windir,argv[2]);adddir(runtime);adddir(windir);join(path,windir,"SYSTEM");if(attr(path,&a)){directory(path);adddir(path);}
 for(i=3;i<(unsigned)argc;i++){absolute(path,argv[i]);adddir(path);}
 puts("Checking all sources before creating any output. This can take a while on an 8088.\nProgress is shown for each file; please leave all source drives mounted.");
 for(i=0;i<8;i++)find_support(i);
 derive_font();
 for(i=0;i<NPINS;i++)if(pins[i].kind==0){join(path,runtime,pins[i].name);printf("Checking %s\n",path);hashfile(path,&pins[i]);}
 checkcancel();diskspace();
 puts("All source hashes match. Windows and boot configuration will not be changed.");
 puts("Create the complete, verified C:\\WINXT folder now? Type Y then Enter, or N to cancel:");
 if(!fgets(answer,sizeof(answer),stdin)||toupper((unsigned char)answer[0])!='Y'||(answer[1]!='\n'&&answer[1]!='\r'&&answer[1]!=0))stop("Cancelled.","");
 checkcancel();diskspace();if(attr(DEST,&a))stop("C:\\WINXT appeared after validation; refusing overwrite.","");
 if(mkdir(DEST))stop("Cannot create fresh C:\\WINXT.","");made=1;
 /* INSTALL.BAT is staged as INSTALL.NEW after every other file passes
  * readback. Rename only after its own readback, so no incomplete batch is
  * runnable. PREPXT never writes READY.TAG, PARTIAL.TAG or an install marker. */
 install=pinindex("INSTALL.BAT");for(i=0;i<NPINS;i++)if(i!=(unsigned)install)copyone(i);copyone((unsigned)install);
 checkcancel();join(path,DEST,"INSTALL.NEW");join(target,DEST,"INSTALL.BAT");
 if(attr(target,&a)||rename(path,target))stop("Cannot commit verified INSTALL.BAT.",target);
 made=0;puts("\nComplete C:\\WINXT verified. Preparation succeeded; Setup was not started.");
 printf("Next at DOS: C:\nCD \\WINXT\nINSTALL %s\n",windir);
 puts("Use Windows Setup's Other display choice. Experimental text remains opt-in.");
 return 0;
}
