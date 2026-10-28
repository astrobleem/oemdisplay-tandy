/* Native DOS install/undo. No display/keyboard/sound or OS media changes.
   The optional shell refresh accepts only the kit's pinned Windows XT shell.
   Failed/stopped renames keep the original in TSHCUBE.BAK for /UNDO. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include <io.h>
typedef unsigned long U32;
#include "CRCFAST.H"
#include "CUBEPINS.H"
static char source[128],target[128],staged[128],backup[128],appnew[128],app[128];
static unsigned char buffer[2048];
static int present(const char *p){return access(p,0)==0;}
static int matches(const char *p,U32 size,U32 crc)
{
 FILE *f;unsigned n;U32 count=0,sum=0xffffffffUL;
 f=fopen(p,"rb");if(!f)return 0;
 while((n=fread(buffer,1,sizeof(buffer),f))!=0){count+=n;sum=fast_crc(sum,buffer,n);}
 n=ferror(f);if(fclose(f))n=1;
 return !n&&count==size&&(sum^0xffffffffUL)==crc;
}
static int copy(const char *from,const char *to,U32 size,U32 crc)
{
 FILE *a,*b;unsigned n;int ok=1;
 if(present(to))return 0;
 a=fopen(from,"rb");if(!a)return 0;b=fopen(to,"wb");if(!b){fclose(a);return 0;}
 while((n=fread(buffer,1,sizeof(buffer),a))!=0)if(fwrite(buffer,1,n,b)!=n){ok=0;break;}
 if(ferror(a))ok=0;if(fclose(a))ok=0;if(fclose(b))ok=0;
 return ok&&matches(to,size,crc);
}
static int absolute(const char *s)
{
 int i,n=strlen(s);
 if(n<4||n>100||s[1]!=':'||s[2]!='\\'||s[n-1]=='\\')return 0;
 if(!((s[0]>='A'&&s[0]<='Z')||(s[0]>='a'&&s[0]<='z')))return 0;
 for(i=0;i<n;i++)if(s[i]<33||s[i]=='/'||s[i]=='*'||s[i]=='?'||s[i]=='"'||(s[i]==':'&&i!=1))return 0;
 return 1;
}
int main(int argc,char **argv)
{
 char win[128],shellexe[128];int apponly=0,undo=0,arg=1,i;union REGS r;
 puts("Windows XT rotating cube installer (DOS 3.3+)");
 if(argc>1&&argv[1][0]=='/'){
  if(!stricmp(argv[1],"/APPONLY"))apponly=1;
  else if(!stricmp(argv[1],"/UNDO"))undo=1;
  else goto usage;arg++;
 }
 if(argc!=arg+1||!absolute(argv[arg]))goto usage;
 r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al&&r.h.al!=0x80)goto windows;
 r.x.ax=0x4680;int86(0x2f,&r,&r);if(!r.x.ax)goto windows;
 strcpy(win,argv[arg]);strcpy(target,win);strcat(target,"\\TSHELL.EXE");
 strcpy(staged,win);strcat(staged,"\\CUBESH.NEW");
 strcpy(backup,win);strcat(backup,"\\TSHCUBE.BAK");
 strcpy(shellexe,win);strcat(shellexe,"\\SYSTEM.INI");
 if(!present(shellexe)){puts("No installed Windows SYSTEM.INI at that path.");return 1;}
 if(undo){
  if(!matches(backup,OLD_SIZE,OLD_CRC)){puts("Original shell backup missing or changed. Nothing restored.");return 1;}
  if(present(target)){
   if(!matches(target,SHELL_SIZE,SHELL_CRC)){puts("Current shell changed; preserve it before restoring.");return 1;}
   if(remove(target)){puts("Cannot remove cube shell. Backup retained.");return 1;}
  }
  if(rename(backup,target)){puts("Restore failed. TSHCUBE.BAK retained; retry /UNDO.");return 1;}
  puts("Original Tandy Start restored. Cube files/settings retained.");return 0;
 }
 if(!apponly&&present(target)&&!matches(target,OLD_SIZE,OLD_CRC)){
  if(matches(target,SHELL_SIZE,SHELL_CRC)&&matches("C:\\WINXT\\CUBE.EXE",CUBE_SIZE,CUBE_CRC)){
   puts("This cube kit is already installed.");return 0;
  }
  puts("Unrecognized Tandy Start. Nothing installed. Use /APPONLY for standalone Cube.");return 1;
 }
 if(!apponly&&(present(backup)||present(staged))){puts("Prior shell transaction exists. Use /UNDO or inspect CUBESH.NEW first.");return 1;}
 if(strlen(argv[0])>110){puts("Kit source path too long.");return 1;}
 strcpy(source,argv[0]);for(i=strlen(source)-1;i>=0&&source[i]!='\\'&&source[i]!=':';i--);source[i+1]=0;
 if(strlen(source)>110){puts("Kit source path too long.");return 1;}
 strcat(source,"CUBE.EXE");
 if(!matches(source,CUBE_SIZE,CUBE_CRC)){puts("CUBE.EXE missing or differs from this exact kit.");return 1;}
 strcpy(shellexe,source);strcpy(shellexe+strlen(shellexe)-8,"CUBESHL.EXE");
 if(!apponly&&present(target)&&!matches(shellexe,SHELL_SIZE,SHELL_CRC)){
  puts("CUBESHL.EXE missing or differs from this exact kit.");return 1;
 }
 strcpy(app,"C:\\WINXT\\CUBE.EXE");strcpy(appnew,"C:\\WINXT\\CUBE.NEW");
 if(present(app)&&!matches(app,CUBE_SIZE,CUBE_CRC)){
  puts("C:\\WINXT\\CUBE.EXE already exists and differs. Preserve it first.");return 1;
 }
 mkdir("C:\\WINXT");
 if(!present(app)){
  if(!copy(source,appnew,CUBE_SIZE,CUBE_CRC)||rename(appnew,app)){
   puts("App copy failed; installed shell unchanged. Inspect CUBE.NEW.");return 1;
  }
 }
 if(!apponly&&present(target)){
  if(!copy(shellexe,staged,SHELL_SIZE,SHELL_CRC)){
   puts("Shell staging failed; original unchanged. Inspect CUBESH.NEW.");return 1;
  }
  if(rename(target,backup)){puts("Cannot preserve original shell; it is unchanged.");return 1;}
  if(rename(staged,target)){
   if(rename(backup,target))puts("Restore needed: run CUBESET /UNDO with this Windows path.");
   puts("Shell update failed. Original retained.");return 1;
  }
  puts("Installed. In Tandy Start: System > Screen saver > Cube > Apply.");
  puts("Options opens Cube settings. Existing choice/delay are preserved.");
  puts("Undo shell: CUBESET /UNDO followed by this full Windows path.");
 }else puts("Standalone installed. Run C:\\WINXT\\CUBE.EXE /C inside Windows.");
 puts("Cube preview: C:\\WINXT\\CUBE.EXE /S. Not a password lock.");return 0;
windows:
 puts("Exit Windows completely. Use a real DOS prompt.");return 1;
usage:
 puts("Usage: CUBESET [/APPONLY | /UNDO] C:\\WINDOWS");return 1;
}
