/* Native DOS install/undo. Configuration and drivers are preserved.
   Shell/input are staged together; exact originals survive failed renames. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <dos.h>
#include <direct.h>
#include <io.h>
typedef unsigned long U32;
#include "CRCFAST.H"
#include "CUBEPINS.H"
typedef struct {
 const char *name,*installed,*temporary,*original;
 U32 size,crc,oldsize,oldcrc;
 char from[128],target[128],stage[128],backup[128];
} PART;
static PART parts[2]={
 {"CUBESHL.EXE","TSHELL.EXE","CUBESH.NEW","TSHCUBE.BAK",SHELL_SIZE,SHELL_CRC,OLD_SIZE,OLD_CRC},
 {"TSINPUT.DLL","TSINPUT.DLL","CUBEIN.NEW","TICUBE.BAK",IDLE_SIZE,IDLE_CRC,OLDIDLE_SIZE,OLDIDLE_CRC}
};
static char source[128],cube[128],app[]="C:\\WINXT\\CUBE.EXE",appnew[]="C:\\WINXT\\CUBE.NEW";
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
static void path(char *out,const char *directory,const char *name)
{strcpy(out,directory);strcat(out,"\\");strcat(out,name);}
static int absolute(const char *s)
{
 int i,n=strlen(s);
 if(n<4||n>100||s[1]!=':'||s[2]!='\\'||s[n-1]=='\\')return 0;
 if(!((s[0]>='A'&&s[0]<='Z')||(s[0]>='a'&&s[0]<='z')))return 0;
 for(i=0;i<n;i++)if(s[i]<33||s[i]=='/'||s[i]=='*'||s[i]=='?'||s[i]=='"'||(s[i]==':'&&i!=1))return 0;
 return 1;
}
static int restore(int requireBackup)
{
 int i,any=0;PART *p;
 for(i=0;i<2;i++)if(present(parts[i].backup))any=1;
 if(requireBackup&&!any){puts("No original backups. Nothing restored.");return 0;}
 /* Validate the entire pair before changing either file. */
 for(i=0;i<2;i++){
  p=&parts[i];
  if(present(p->backup)){
   if(!matches(p->backup,p->oldsize,p->oldcrc)){
    puts("Original backup changed. Nothing restored.");return 0;
   }
   if(present(p->target)&&!matches(p->target,p->size,p->crc)&&!matches(p->target,p->oldsize,p->oldcrc)){
    puts("Installed file changed; preserve it before restoring.");return 0;
   }
  }else if(!matches(p->target,p->oldsize,p->oldcrc)){
   puts("Needed original backup missing. Nothing restored.");return 0;
  }
 }
 for(i=0;i<2;i++){
  p=&parts[i];if(!present(p->backup))continue;
  if(matches(p->target,p->oldsize,p->oldcrc)){
   if(remove(p->backup))return 0;
  }else{
   if(present(p->target)&&remove(p->target))return 0;
   if(rename(p->backup,p->target))return 0;
  }
 }
 for(i=0;i<2;i++){
  p=&parts[i];if(!present(p->stage))continue;
  if(!matches(p->stage,p->size,p->crc)||remove(p->stage)){
   puts("Originals restored; inspect the remaining .NEW file.");return 0;
  }
 }
 return 1;
}
int main(int argc,char **argv)
{
 char check[128];int apponly=0,undo=0,arg=1,i,upgrade,newpair;PART *p;union REGS r;
 puts("Windows XT rotating cube installer (DOS 3.3+)");
 if(argc>1&&argv[1][0]=='/'){
  if(!stricmp(argv[1],"/APPONLY"))apponly=1;
  else if(!stricmp(argv[1],"/UNDO"))undo=1;
  else goto usage;arg++;
 }
 if(argc!=arg+1||!absolute(argv[arg]))goto usage;
 r.x.ax=0x1600;int86(0x2f,&r,&r);if(r.h.al&&r.h.al!=0x80)goto windows;
 r.x.ax=0x4680;int86(0x2f,&r,&r);if(!r.x.ax)goto windows;
 path(check,argv[arg],"SYSTEM.INI");
 if(!present(check)){puts("No installed Windows SYSTEM.INI at that path.");return 1;}
 for(i=0;i<2;i++){
  p=&parts[i];path(p->target,argv[arg],p->installed);
  path(p->stage,argv[arg],p->temporary);path(p->backup,argv[arg],p->original);
 }
 if(undo){
  if(!restore(1)){puts("Recovery incomplete. Keep backups and retry /UNDO.");return 1;}
  puts("Original Tandy Start/input restored. Cube files/settings retained.");return 0;
 }
 upgrade=!apponly&&present(parts[0].target);
 if(upgrade){
  newpair=matches(app,CUBE_SIZE,CUBE_CRC);
  for(i=0;i<2;i++){p=&parts[i];if(!matches(p->target,p->size,p->crc))newpair=0;}
  if(newpair){puts("This cube kit is already installed.");return 0;}
  for(i=0;i<2;i++){
   p=&parts[i];if(!matches(p->target,p->oldsize,p->oldcrc)){
    puts("Unrecognized Tandy Start/input. Nothing installed. Use /APPONLY for standalone Cube.");return 1;
   }
  }
 }
 if(!apponly)for(i=0;i<2;i++)if(present(parts[i].backup)||present(parts[i].stage)){
  puts("Prior transaction exists. Use /UNDO or inspect .NEW files first.");return 1;
 }
 if(strlen(argv[0])>110){puts("Kit source path too long.");return 1;}
 strcpy(source,argv[0]);for(i=strlen(source)-1;i>=0&&source[i]!='\\'&&source[i]!=':';i--);source[i+1]=0;
 strcpy(cube,source);strcat(cube,"CUBE.EXE");
 if(!matches(cube,CUBE_SIZE,CUBE_CRC)){puts("CUBE.EXE missing or differs from this exact kit.");return 1;}
 if(upgrade)for(i=0;i<2;i++){
  p=&parts[i];strcpy(p->from,source);strcat(p->from,p->name);
  if(!matches(p->from,p->size,p->crc)){puts("Shell/input payload differs from this kit.");return 1;}
 }
 if(present(app)&&!matches(app,CUBE_SIZE,CUBE_CRC)){
  puts("C:\\WINXT\\CUBE.EXE already differs. Preserve it first.");return 1;
 }
 mkdir("C:\\WINXT");
 if(!present(app)&&(!copy(cube,appnew,CUBE_SIZE,CUBE_CRC)||rename(appnew,app))){
  puts("App copy failed; shell/input unchanged. Inspect CUBE.NEW.");return 1;
 }
 if(upgrade){
  for(i=0;i<2;i++){
   p=&parts[i];if(!copy(p->from,p->stage,p->size,p->crc)){
    puts("Staging failed; originals unchanged. Inspect .NEW files.");return 1;
   }
  }
  /* Input remains compatible with the old shell, so install it first. */
  for(i=1;i>=0;i--){
   p=&parts[i];if(rename(p->target,p->backup)||rename(p->stage,p->target)){
    if(restore(0))puts("Update failed; originals restored.");
    else puts("Update failed. Keep TSHCUBE.BAK/TICUBE.BAK and run /UNDO.");
    return 1;
   }
  }
  puts("Installed. Tandy Start: System > Screen saver > Cube > Apply.");
  puts("Options opens Cube settings. Existing choice/delay are preserved.");
  puts("Undo shell/input: CUBESET /UNDO plus this full Windows path.");
 }else puts("Standalone installed. Run C:\\WINXT\\CUBE.EXE /C inside Windows.");
 puts("Cube preview: C:\\WINXT\\CUBE.EXE /S. Not a password lock.");return 0;
windows:
 puts("Exit Windows completely. Use a real DOS prompt.");return 1;
usage:
 puts("Usage: CUBESET [/APPONLY | /UNDO] C:\\WINDOWS");return 1;
}
