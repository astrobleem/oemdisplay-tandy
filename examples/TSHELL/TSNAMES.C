/* Display-only VFAT bridge. DOS list indices/short aliases own all actions. */
#define WINVER 0x0300
#include <windows.h>
#include <string.h>
#include "TSNAMES.H"
#include "VFAT.H"
#include "RAWREAD.H"
#define ROW_SIZE 16
#define PH_BOOT 1
#define PH_SCAN 2
#define PH_READY 3
typedef struct NAME_WORK {
 VF_WORK work;
 VF_VOLUME volume;
 VF_SLOT slot[TSNAMES_LIMIT];
 char row[TSNAMES_LIMIT][ROW_SIZE];
} NAME_WORK;
static HGLOBAL nameHandle;
static NAME_WORK FAR *names;
static RD_VOLUME disk;
static HWND nativeList,displayList;
static char namePath[VF_PATH_MAX];
static int nameCount,namePhase;
/* DlgDirList's bracket syntax is kept exactly, including parent/drives. */
static int rowkind(const char FAR *s) {
 int n=lstrlen(s);
 if(n>=3&&s[0]=='['&&s[n-1]==']') {
  if(n==5&&s[1]=='-'&&s[3]=='-')return 2;
  if(n==4&&s[1]=='.'&&s[2]=='.')return 2;
  return 1;
 }
 return 0;
}
void TSNamesEnd(void) {
 if(names){VF_Cancel(&names->work);GlobalUnlock(nameHandle);names=NULL;}
 if(nameHandle){GlobalFree(nameHandle);nameHandle=NULL;}
 RdClose(&disk);nativeList=displayList=NULL;nameCount=namePhase=0;
}
int TSNamesBegin(LPCSTR cwd,HWND aliases,HWND visible) {
 int i,n,length,kind;char text[ROW_SIZE],base[ROW_SIZE];
 TSNamesEnd();
 if(!cwd||!aliases||!visible)return 0;
 n=lstrlen(cwd);if(n<3||n>=VF_PATH_MAX)return 0;
 lstrcpy(namePath,cwd);
 for(i=0;i<n;i++)if(namePath[i]>='a'&&namePath[i]<='z')namePath[i]-=32;
 if(!RdPathIdentity(namePath))return 0;
 n=(int)SendMessage(aliases,LB_GETCOUNT,0,0L);
 if(n<=0||n>TSNAMES_LIMIT)return 0;
 if(n!=(int)SendMessage(visible,LB_GETCOUNT,0,0L))return -1;
 nameHandle=GlobalAlloc(GMEM_MOVEABLE|GMEM_ZEROINIT,(DWORD)sizeof(NAME_WORK));
 if(!nameHandle)return 0;
 names=(NAME_WORK FAR *)GlobalLock(nameHandle);
 if(!names){TSNamesEnd();return 0;}
 nameCount=n;nativeList=aliases;displayList=visible;
 for(i=0;i<n;i++){
  length=(int)SendMessage(aliases,LB_GETTEXTLEN,i,0L);
  if(length<1||length>=ROW_SIZE){TSNamesEnd();return 0;}
  if((int)SendMessage(aliases,LB_GETTEXT,i,(LPARAM)(LPSTR)text)!=length){TSNamesEnd();return 0;}
  lstrcpy(names->row[i],text);kind=rowkind(text);
  if(kind==2)continue;
  lstrcpy(base,text+(kind?1:0));if(kind)base[length-2]=0;
  if(VF_Alias((const char FAR *)base,names->slot[i].alias)!=VF_OK){TSNamesEnd();return 0;}
 }
 if(RdOpen(&disk,(unsigned)(namePath[0]-'A'))!=RD_OK){TSNamesEnd();return 0;}
 VF_Begin(&names->work);namePhase=PH_BOOT;return 1;
}
int TSNamesStep(void) {
 int result;
 if(!names||!namePhase)return -1;
 if(namePhase==PH_READY)return TSNAMES_READY;
 if(namePhase==PH_BOOT){
  /* This timer turn's only read. Start itself performs no sector reads. */
  if(RdRead(&disk,0L,names->work.sector)!=RD_OK ||
     !RdBootMatches(&disk,names->work.sector) ||
     VF_Mount(names->work.sector,disk.sectors,&names->volume)!=VF_OK)return -1;
  result=VF_Start(&names->volume,RdRead,&disk,&names->work,
                  (const char FAR *)namePath,names->slot,(VF_WORD)nameCount);
  if(result!=VF_PENDING)return -1;
  namePhase=PH_SCAN;return 1;
 }
 result=VF_Step(&names->work);
 if(result==VF_PENDING)return 1;
 if(result!=VF_OK)return -1;
 namePhase=PH_READY;return TSNAMES_READY;
}
int TSNamesCommit(void) {
 int i,n,kind,length;char text[VF_NAME_MAX+8],row[ROW_SIZE];
 VF_SLOT FAR *slot;
 if(!names||namePhase!=PH_READY||!RdPathIdentity(namePath))return -1;
 if(nameCount!=(int)SendMessage(nativeList,LB_GETCOUNT,0,0L) ||
    nameCount!=(int)SendMessage(displayList,LB_GETCOUNT,0,0L))return -1;
 /* All rows must still match before any visible row is changed. */
 for(i=0;i<nameCount;i++){
  length=(int)SendMessage(nativeList,LB_GETTEXTLEN,i,0L);
  if(length<1||length>=ROW_SIZE)return -1;
  if((int)SendMessage(nativeList,LB_GETTEXT,i,(LPARAM)(LPSTR)row)!=length ||
     lstrcmp(row,names->row[i]))return -1;
 }
 for(i=0;i<nameCount;i++){
  kind=rowkind(names->row[i]);slot=&names->slot[i];
  if(kind==2 || (slot->flags&(VF_MATCH|VF_LONG|VF_INVALID|VF_DUPLICATE))!=(VF_MATCH|VF_LONG) ||
     ((slot->attr&0x10)!=0)!=(kind==1) || !slot->name[0])continue;
  text[0]=0;if(kind)lstrcpy(text,"[");lstrcat(text,slot->name);
  if(slot->flags&VF_TRUNCATED)lstrcat(text,"...");if(kind)lstrcat(text,"]");
  n=(int)SendMessage(displayList,LB_DELETESTRING,i,0L);
  if(n<0)return -2;
  if((int)SendMessage(displayList,LB_INSERTSTRING,i,(LPARAM)(LPSTR)text)!=i)return -2;
 }
 return 0;
}
