#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "SCFGCORE.H"
static int checks;
#define CHECK(x) do { ++checks; if (!(x)) { printf("FAIL line %d: %s\n", __LINE__, #x); exit(1); } } while (0)
typedef struct { SCCONFIG c; int writes, reads, failwrite, failread, partial, persistent, mismatch; } TEST;
static int readkey(void *v,int k,char *s,int n) {
 TEST *t=v; ++t->reads;
 if(t->failread && t->reads>=t->failread)return -1;
 if(t->mismatch && t->writes && k==SC_CHOICE){strcpy(s,"wrong");return 1;}
 if(!t->c.present[k])return 0;
 if(strlen(t->c.value[k])>=(unsigned)n)return -1;
 strcpy(s,t->c.value[k]);return 1;
}
static int writekey(void *v,int k,const char *s) {
 TEST *t=v; int fail; ++t->writes;
 fail=t->failwrite && (t->writes==t->failwrite || (t->persistent && t->writes>=t->failwrite));
 if(!fail||t->partial){t->c.present[k]=s!=0;if(s)strcpy(t->c.value[k],s);else t->c.value[k][0]=0;}
 return !fail;
}
static void init(TEST *t,SCIO *io) {
 memset(t,0,sizeof(*t));io->read=readkey;io->write=writekey;io->context=t;
}
static void set(TEST *t,int k,const char *s){t->c.present[k]=1;strcpy(t->c.value[k],s);}
int main(void) {
 TEST t; SCIO io; SCCONFIG before,after; int i; char path[128],command[128];
 const char *bad[]={"","0","9","3601","9999","10000","+10","-10"," 10","10 ","1.0","10s","00010"};
 CHECK(ScSeconds("10")==10);CHECK(ScSeconds("3600")==3600);CHECK(ScSeconds("15")==15);CHECK(ScSeconds("0300")==300);
 for(i=0;i<(int)(sizeof(bad)/sizeof(*bad));++i)CHECK(!ScSeconds(bad[i]));
 CHECK(ScAbsolute("C:\\CUSTOM\\MX.EXE"));CHECK(ScAbsolute("c:\\a.exe"));
 CHECK(!ScAbsolute("MATRIX.EXE"));CHECK(!ScAbsolute("C:MX.EXE"));CHECK(!ScAbsolute("C:\\My App.exe"));CHECK(!ScAbsolute("C:\\MX.EXE /S"));CHECK(!ScAbsolute("C:\\"));CHECK(!ScAbsolute("C:\\D:X"));
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);CHECK(!ScEnabled(&before));CHECK(ScChoice(&before)==SC_MATRIX);CHECK(!strcmp(ScValue(&before,SC_SECONDS),"300"));CHECK(!strcmp(ScProgram(&before,SC_MAZE),"C:\\TSTART\\MAZE.EXE"));
 set(&t,SC_ENABLED,"2");set(&t,SC_CHOICE,"mAzE");set(&t,SC_SECONDS,"17");set(&t,SC_MATRIXPATH,"C:\\CUSTOM\\MX.EXE");set(&t,SC_MAZEPATH,"C:\\CUSTOM\\MZ.EXE");
 CHECK(ScRead(&io,&before)==SC_OK);CHECK(ScEnabled(&before));CHECK(ScChoice(&before)==SC_MAZE);
 CHECK(ScSave(&io,&before,"17",SC_MATRIX,&after)==SC_OK);CHECK(t.writes==2);CHECK(!strcmp(ScProgram(&after,SC_MATRIX),"C:\\CUSTOM\\MX.EXE"));CHECK(!strcmp(ScProgram(&after,SC_MAZE),"C:\\CUSTOM\\MZ.EXE"));
 before=after;t.writes=0;CHECK(ScSave(&io,&before,"17",SC_NONE,&after)==SC_OK);CHECK(t.writes==1);CHECK(!ScEnabled(&after));CHECK(ScChoice(&after)==SC_MATRIX);CHECK(!strcmp(ScValue(&after,SC_SECONDS),"17"));
 before=after;t.writes=0;CHECK(ScSave(&io,&before,"17",SC_NONE,&after)==SC_OK);CHECK(t.writes==0);
 CHECK(ScSave(&io,&before,"9",SC_MAZE,&after)==SC_BADSECONDS);CHECK(!t.writes);CHECK(ScSave(&io,&before,"10",9,&after)==SC_BADCHOICE);CHECK(!t.writes);
 set(&t,SC_SECONDS,"18");CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_CONFLICT);CHECK(!t.writes);
 for(i=1;i<=3;++i){init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failwrite=i;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_WRITEFAIL);CHECK(!t.c.present[0]&&!t.c.present[1]&&!t.c.present[2]);}
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failwrite=2;t.partial=1;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_WRITEFAIL);CHECK(!t.c.present[0]&&!t.c.present[1]&&!t.c.present[2]);
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failwrite=1;t.persistent=1;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_WRITEFAIL);CHECK(!t.c.present[0]);
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failwrite=2;t.persistent=1;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_UNCERTAIN);CHECK(t.c.present[0]);
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failread=t.reads+1;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_READFAIL);CHECK(!t.writes);
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failread=t.reads+SC_KEYS+1;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_UNCERTAIN);
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.mismatch=1;CHECK(ScSave(&io,&before,"10",SC_MAZE,&after)==SC_UNCERTAIN);

 CHECK(ScSpeed("1")==1);CHECK(ScSpeed("2")==2);CHECK(ScSpeed("3")==3);
 CHECK(!ScSpeed("0"));CHECK(!ScSpeed("4"));CHECK(!ScSpeed("02"));CHECK(!ScSpeed("2 "));
 CHECK(ScStars("16")==16);CHECK(ScStars("32")==32);CHECK(ScStars("64")==64);
 CHECK(!ScStars("0"));CHECK(!ScStars("17"));CHECK(!ScStars("128"));CHECK(!ScStars("032"));
 init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);CHECK(!strcmp(ScProgram(&before,SC_STARFIELD),"C:\\TSTART\\STARFLD.EXE"));
 CHECK(ScSpeed(ScValue(&before,SC_SPEED))==2);CHECK(ScStars(ScValue(&before,SC_STARS))==32);
 set(&t,SC_STARPATH,"D:\\CUSTOM\\ST.EXE");set(&t,SC_CHOICE,"sTaRfIeLd");CHECK(ScRead(&io,&before)==SC_OK);CHECK(ScChoice(&before)==SC_STARFIELD);
 CHECK(ScSaveOptions(&io,&before,"17",SC_STARFIELD,"3","64",&after)==SC_OK);
 CHECK(!strcmp(ScProgram(&after,SC_STARFIELD),"D:\\CUSTOM\\ST.EXE"));CHECK(ScSpeed(ScValue(&after,SC_SPEED))==3);CHECK(ScStars(ScValue(&after,SC_STARS))==64);
 before=after;t.writes=0;CHECK(ScSaveOptions(&io,&before,"17",SC_NONE,0,0,&after)==SC_OK);CHECK(ScChoice(&after)==SC_STARFIELD);CHECK(ScSpeed(ScValue(&after,SC_SPEED))==3);CHECK(t.writes==1);
 before=after;t.writes=0;CHECK(ScSaveOptions(&io,&before,"17",SC_STARFIELD,"4","64",&after)==SC_BADOPTIONS);CHECK(!t.writes);
 CHECK(ScSaveOptions(&io,&before,"17",SC_STARFIELD,"2","17",&after)==SC_BADOPTIONS);CHECK(!t.writes);
 CHECK(ScSaveOptions(&io,&before,"17",SC_STARFIELD,"2",0,&after)==SC_BADOPTIONS);CHECK(!t.writes);
 set(&t,SC_STARS,"32");CHECK(ScSaveOptions(&io,&before,"17",SC_STARFIELD,"2","16",&after)==SC_CONFLICT);CHECK(!t.writes);
 for(i=1;i<=5;++i){init(&t,&io);CHECK(ScRead(&io,&before)==SC_OK);t.failwrite=i;CHECK(ScSaveOptions(&io,&before,"10",SC_STARFIELD,"3","64",&after)==SC_WRITEFAIL);CHECK(!t.c.present[0]&&!t.c.present[1]&&!t.c.present[2]&&!t.c.present[6]&&!t.c.present[7]);}
 CHECK(ScCommand("C:\\TSTART\\STARFLD.EXE",1,16,command,sizeof(command)));CHECK(!strcmp(command,"C:\\TSTART\\STARFLD.EXE /S /V1 /N16"));
 CHECK(ScCommand("C:\\TSTART\\STARFLD.EXE",3,64,command,sizeof(command)));CHECK(!strcmp(command,"C:\\TSTART\\STARFLD.EXE /S /V3 /N64"));
 strcpy(path,"C:\\");memset(path+3,'A',111);path[114]=0;CHECK(ScCommand(path,2,32,command,sizeof(command)));CHECK(strlen(command)==126);
 path[114]='A';path[115]=0;strcpy(command,"unchanged");CHECK(!ScCommand(path,2,32,command,sizeof(command)));CHECK(!strcmp(command,"unchanged"));CHECK(strlen(path)==115);
 CHECK(ScCommand(path,0,0,command,sizeof(command)));CHECK(strlen(command)==118);
 memset(path+3,'A',119);path[122]=0;CHECK(ScCommand(path,0,0,command,sizeof(command)));CHECK(strlen(command)==125);
 path[122]='A';path[123]=0;CHECK(!ScCommand(path,0,0,command,sizeof(command)));
 CHECK(!ScCommand("C:\\ST.EXE",0,32,command,sizeof(command)));CHECK(!ScCommand("C:\\ST.EXE",2,17,command,sizeof(command)));CHECK(!ScCommand("C:\\ST.EXE",2,32,command,10));
 printf("PASS %d checks\n",checks);return 0;
}
