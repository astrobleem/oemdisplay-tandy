/* DOS 3.20+ / 8088 app packet extractor. No installed OS file is modified.
 * FILES.H pins a flat stored ZIP appended to this DOS executable.
 * Existing complete files are reused; foreign files are never overwritten.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <io.h>
#ifndef HOST_TEST
#include <dos.h>
#include <direct.h>
#else
#include <direct.h>
#endif
#ifdef DOS_API_MOCK
#include "TESTS/DOSMOCK.H"
#endif
typedef unsigned long U32;
struct entry { char *name; U32 size, crc; long offset; };
#include "FILES.H"
/* Driver packets may supply a plain-DOS completion message in FILES.H. */
#ifndef APP_READY
#define APP_READY(where) do { \
 puts(APP_TITLE " is ready. Start your usual guarded Windows 3.0 desktop."); \
 printf("In Tandy Start or Program Manager, choose Run: %s\\%s\n",(where),RUN_NAME); \
 puts("All app files stay in that folder. No Windows or boot settings were changed."); \
} while(0)
#endif
#define COUNT (sizeof(files)/sizeof(files[0]))
#define PATHLEN 128
static unsigned char buf[2048];
static char target[PATHLEN], output[PATHLEN];
static FILE *packet;
static int created;
static unsigned word(unsigned char *p) { return p[0]|((unsigned)p[1]<<8); }
static U32 dword(unsigned char *p) { return (U32)word(p)|((U32)word(p+2)<<16); }
static U32 crc(U32 c,unsigned char *p,unsigned n)
{
 unsigned i;while(n--){c^=*p++;for(i=0;i<8;i++)c=(c&1)?(c>>1)^0xedb88320UL:c>>1;}
 return c;
}
static void fail(char *s)
{
 if(created){if(remove(output))fprintf(stderr,"Keep incomplete %s for inspection.\n",output);created=0;}
 fprintf(stderr,"APPSET: %s\n",s);exit(1);
}
static void join(char *out,char *base,char *name)
{
 if(strlen(base)+strlen(name)+2>=PATHLEN)fail("Path too long.");
 strcpy(out,base);if(out[strlen(out)-1]!='\\'&&out[strlen(out)-1]!='/')strcat(out,"\\");strcat(out,name);
}
static void destination(char *s)
{
 unsigned i,start=3,dot=0;
#ifdef HOST_TEST
 if(strlen(s)>=PATHLEN-14)fail("Path too long.");strcpy(target,s);return;
#endif
 if(strlen(s)<4||strlen(s)>=PATHLEN-14||!isalpha((unsigned char)s[0])||s[1]!=':'||s[2]!='\\')fail("Use a full DOS directory, such as " DEFAULT_DIR ".");
 for(i=3;s[i];i++){
  if(s[i]=='\\'){if(i==start||i-start>12)fail("Use DOS 8.3 directory names.");start=i+1;dot=0;continue;}
  if(s[i]=='.'){if(dot||i==start||i-start>8)fail("Use DOS 8.3 directory names.");dot=i+1;continue;}
  else if(!isalnum((unsigned char)s[i])&&s[i]!='_'&&s[i]!='-'&&s[i]!='$'&&s[i]!='~')fail("Use DOS paths without spaces or wildcards.");
  if((dot&&i-dot>=3)||(!dot&&i-start>=8))fail("Use DOS 8.3 directory names.");
 }
 if(i==start||s[i-1]=='.')fail("Use a directory below a drive root.");strcpy(target,s);
}
static int exists(char *path)
{
 struct stat st;if(!stat(path,&st))return 1;if(errno!=ENOENT)fail("Cannot inspect destination.");return 0;
}
static int valid(char *path,struct entry *e)
{
 FILE *f;unsigned n;U32 total=0,c=0xffffffffUL;
 f=fopen(path,"rb");if(!f)return 0;
 while((n=fread(buf,1,sizeof(buf),f))!=0){total+=n;if(total>e->size){fclose(f);return 0;}c=crc(c,buf,n);}
 n=ferror(f);if(fclose(f))n=1;return !n&&total==e->size&&(c^0xffffffffUL)==e->crc;
}
static void scan(void)
{
 unsigned char h[30];char name[14];unsigned i,n;long offset;U32 left,c;
 if(fread(h,1,6,packet)!=6||h[0]!='M'||h[1]!='Z')fail("Use the complete supplied app EXE.");
 offset=(long)word(h+4)*512L;if(word(h+2))offset-=512L-word(h+2);
 for(i=0;i<COUNT;i++){
  if(fseek(packet,offset,SEEK_SET)||fread(h,1,30,packet)!=30||memcmp(h,"PK\003\004",4))fail("Incomplete app packet.");
  n=word(h+26);
  if(word(h+6)||word(h+8)||word(h+28)||n<1||n>12||dword(h+18)!=files[i].size||dword(h+22)!=files[i].size||dword(h+14)!=files[i].crc)fail("App packet header differs from this installer.");
  if(fread(name,1,n,packet)!=n)fail("Truncated packet filename.");name[n]=0;
  if(strcmp(name,files[i].name))fail("Unexpected app packet filename.");
  files[i].offset=offset+30+n;left=files[i].size;c=0xffffffffUL;
  while(left){n=left>sizeof(buf)?sizeof(buf):(unsigned)left;if(fread(buf,1,n,packet)!=n)fail("Truncated app packet data.");c=crc(c,buf,n);left-=n;}
  if((c^0xffffffffUL)!=files[i].crc)fail("App packet data is damaged.");
  offset=files[i].offset+(long)files[i].size;
 }
}
/* _dos_creatnew returns a raw DOS handle, not a registered CRT descriptor. */
static int output_write(int fd,unsigned char *data,unsigned count)
{
#if defined(HOST_TEST) && !defined(DOS_API_MOCK)
 return write(fd,data,count);
#else
 unsigned wrote;
 if(_dos_write(fd,data,count,&wrote))return -1;
 return (int)wrote;
#endif
}
static int output_close(int fd)
{
#if defined(HOST_TEST) && !defined(DOS_API_MOCK)
 return close(fd);
#else
 return _dos_close(fd);
#endif
}
static void copy_entry(unsigned i)
{
 int fd=-1;unsigned n,serial;char final[PATHLEN],temp[13];U32 left=files[i].size;
 join(final,target,files[i].name);
 if(exists(final)){if(!valid(final,&files[i]))fail("App destination changed after checking.");return;}
 for(serial=0;serial<1000;serial++){
  sprintf(temp,"AS%05u.NEW",serial);join(output,target,temp);
  if(exists(output))continue;
#if defined(HOST_TEST) && !defined(DOS_API_MOCK)
  fd=open(output,O_WRONLY|O_CREAT|O_EXCL|O_BINARY,S_IREAD|S_IWRITE);
  if(fd<0)fail("Cannot create a new app file.");
#else
  if(_dos_creatnew(output,_A_NORMAL,&fd))fail("Cannot create a new app file.");
#endif
  break;
 }
 if(fd<0)fail("No free temporary filename in the app folder.");
 created=1;
 if(fseek(packet,files[i].offset,SEEK_SET)) {output_close(fd);fail("Cannot seek app packet.");}
 while(left){n=left>sizeof(buf)?sizeof(buf):(unsigned)left;
#ifdef HOST_TEST
  if(getenv("APPSET_SHORT_WRITE")){output_write(fd,buf,n/2);output_close(fd);fail("Injected disk-full write.");}
#endif
  if(fread(buf,1,n,packet)!=n||output_write(fd,buf,n)!=(int)n){output_close(fd);fail("Copy failed or disk full. Rerun the same installer to finish.");}left-=n;
 }
 if(output_close(fd))fail("Cannot close the new app file.");
 if(!valid(output,&files[i]))fail("New app file failed readback.");
 if(exists(final)||rename(output,final))fail("Cannot commit the new app file.");created=0;
}
int main(int argc,char **argv)
{
 unsigned i;struct stat st;char *source=argv[0];
#ifdef HOST_TEST
 if(getenv("APPSET_PACKET"))source=getenv("APPSET_PACKET");
#endif
#ifndef HOST_TEST
 union REGS r;r.h.ah=0x30;intdos(&r,&r);
 if(r.h.al<3||(r.h.al==3&&r.h.ah<20))fail("DOS 3.20 or later required.");
#endif
 if(argc>2){puts("Usage: " SETUP_NAME " [" DEFAULT_DIR "]");return 1;}
 destination(argc==2?argv[1]:DEFAULT_DIR);
 packet=fopen(source,"rb");if(!packet)fail("Cannot read the supplied app installer.");scan();
 if(exists(target)){if(stat(target,&st)||!(st.st_mode&S_IFDIR))fail("Destination is not a directory.");}
 /* Validate every collision before copying any files. */
 for(i=0;i<COUNT;i++){join(output,target,files[i].name);if(exists(output)&&!valid(output,&files[i]))fail("A different app file exists. Choose a new app folder.");}
 if(!exists(target)&&mkdir(target))fail("Cannot create app folder. Its parent directory must exist.");
 for(i=0;i<COUNT;i++)copy_entry(i);
 if(fclose(packet))fail("App packet close failed.");
 APP_READY(target);
 return 0;
}
