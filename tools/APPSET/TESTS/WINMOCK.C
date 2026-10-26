#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "windows.h"
static FILE *openfiles[8];
static char *scenario,*directory;
static int loadcount,execcount,freecount,errors,loaded;
static char loadpath[260],execpath[260];
HFILE _lopen(char *path,int flags)
{
 int i;flags=flags;for(i=0;i<8;i++)if(!openfiles[i]){openfiles[i]=fopen(path,"rb");return openfiles[i]?i:HFILE_ERROR;}return HFILE_ERROR;
}
UINT _lread(HFILE f,void *data,UINT n)
{size_t got=fread(data,1,n,openfiles[f]);return ferror(openfiles[f])?(UINT)-1:(UINT)got;}
int _lclose(HFILE f){int result=fclose(openfiles[f]);openfiles[f]=NULL;return result;}
int MessageBox(void *parent,char *text,char *title,int flags)
{parent=parent;title=title;flags=flags;errors++;printf("ERROR %s\n",text);return 1;}
UINT GetWinFlags(void){return !strcmp(scenario,"enhanced")?WF_ENHANCED:0;}
UINT GetModuleFileName(HINSTANCE instance,char *path,int capacity)
{
 char text[260];
 if(instance==1&&!strcmp(scenario,"badpath"))strcpy(text,"MINERUN.EXE");
 else sprintf(text,"%s\\%s",directory,instance==1?"MINERUN.EXE":!strcmp(scenario,"same")?"WMABT.DLL":"FOREIGN.DLL");
 if((int)strlen(text)>=capacity)return 0;strcpy(path,text);return (UINT)strlen(path);
}
HINSTANCE GetModuleHandle(char *name)
{name=name;return !strcmp(scenario,"foreign")||!strcmp(scenario,"same")?70:0;}
HINSTANCE LoadLibrary(char *path)
{loadcount++;strcpy(loadpath,path);if(!strcmp(scenario,"loadfail"))return 2;loaded=1;return 80;}
void FreeLibrary(HINSTANCE h){h=h;freecount++;loaded=0;}
UINT WinExec(char *path,int show)
{show=show;execcount++;strcpy(execpath,path);if(!loaded)exit(90);return !strcmp(scenario,"execfail")?2:90;}
char *lstrcpy(char *to,char *from){return strcpy(to,from);}
char *lstrcat(char *to,char *from){return strcat(to,from);}
#include "../../MINEAPP/MINERUN.C"
int main(int argc,char **argv)
{
 int result;if(argc!=3)return 99;scenario=argv[1];directory=argv[2];
 result=WinMain(1,0,!strcmp(scenario,"args")?"/BAD":"",1);
 printf("RESULT %d LOAD %d EXEC %d FREE %d ERRORS %d\n",result,loadcount,execcount,freecount,errors);
 printf("DLL %s\nAPP %s\n",loadpath,execpath);return result;
}
