
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include <assert.h>
#include "GRPREAD.H"
#define PM_PATH 144
#define PM_BUNDLED 12
#define HFILE_ERROR -1
#define OF_EXIST 0
#define lstrcpy strcpy
#define lstrcat strcat
#define wsprintf sprintf
typedef struct { int unused; } OFSTRUCT;
typedef struct {char name[PM_NAME_MAX+1],command[PM_CMD_MAX+1];} PmBundled;
static PmBundled pmBundled[PM_BUNDLED];
static int pmBundleCount;
static char pmWindows[PM_PATH]="C:\\WINDOWS";
static int configuredCount;
static char configuredName[14][140],configuredCommand[14][260];
static int available[14];
int GetPrivateProfileInt(const char *s,const char *k,int d,const char *p)
{(void)s;(void)k;(void)d;assert(!strcmp(p,"C:\\WINDOWS\\TSHELL.INI"));return configuredCount;}
int GetPrivateProfileString(const char *section,const char *key,const char *def,char *dest,unsigned cap,const char *profile)
{const char *s;unsigned n;int i;(void)section;(void)def;(void)profile;
 i=atoi(key+(key[0]=='N'?4:7));assert(i>0&&i<14);
 s=key[0]=='N'?configuredName[i]:configuredCommand[i];n=(unsigned)strlen(s);if(n>=cap)n=cap-1;
 memcpy(dest,s,n);dest[n]=0;return (int)n;}
int OpenFile(const char *token,OFSTRUCT *of,int mode)
{int i;char t[128];(void)of;(void)mode;for(i=1;i<14;i++)if(available[i]&&PmCommandToken(configuredCommand[i],t,sizeof(t))&&!strcmp(t,token))return 1;return HFILE_ERROR;}
/* PRODUCTION */
static void reset(void){configuredCount=1;memset(configuredName,0,sizeof(configuredName));memset(configuredCommand,0,sizeof(configuredCommand));memset(available,0,sizeof(available));strcpy(configuredName[1],"Pinball");strcpy(configuredCommand[1],"C:\\WINXT\\PINBALL.EXE");available[1]=1;}
int main(void){int i;reset();pmbundles();assert(pmBundleCount==1);assert(!strcmp(pmBundled[0].name,"Pinball"));assert(!strcmp(pmBundled[0].command,"C:\\WINXT\\PINBALL.EXE"));
 available[1]=0;pmbundles();assert(pmBundleCount==0);
 reset();strcpy(configuredCommand[1],"PINBALL.EXE");pmbundles();assert(pmBundleCount==0);
 strcpy(configuredCommand[1],"C:PINBALL.EXE");pmbundles();assert(pmBundleCount==0);
 strcpy(configuredCommand[1],"\\WINXT\\PINBALL.EXE");pmbundles();assert(pmBundleCount==0);
 reset();strcpy(configuredCommand[1],"\"C:\\WINXT\\PINBALL.EXE\" /Preview  KeepCase");pmbundles();assert(pmBundleCount==1);assert(!strcmp(pmBundled[0].command,configuredCommand[1]));
 reset();memset(configuredName[1],'N',64);configuredName[1][64]=0;pmbundles();assert(pmBundleCount==0);
 configuredName[1][63]=0;pmbundles();assert(pmBundleCount==1);
 reset();memset(configuredCommand[1],'C',127);configuredCommand[1][127]=0;pmbundles();assert(pmBundleCount==0);
 reset();configuredCount=-1;pmbundles();assert(pmBundleCount==0);configuredCount=13;pmbundles();assert(pmBundleCount==0);
 reset();configuredCount=12;for(i=1;i<=12;i++){sprintf(configuredName[i],"App%d",i);sprintf(configuredCommand[i],"C:\\WINXT\\A%d.EXE",i);available[i]=1;}pmbundles();assert(pmBundleCount==12);
 configuredName[5][0]=0;available[7]=0;pmbundles();assert(pmBundleCount==10);assert(!strcmp(pmBundled[4].name,"App6"));
 puts("PASS: production bundle discovery: existing/missing apps, absolute paths, quoted command preservation, name/command bounds, count bounds, maximum capacity and gaps");return 0;}
