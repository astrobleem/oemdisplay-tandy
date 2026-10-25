#include <stdio.h>
#include <string.h>
#include <assert.h>
#define TDSOUND_HOST
#include "SNDSTUB.H"
static int driver=1,api=1,openapi=1,closeapi=1,owner,raw,task=1,external,ports,regok=1,createok=1,markerLive,registered,foreignWindow,activeWindow=1,claimBusy;
static int lease(unsigned v,unsigned op){if(v!=1||owner!=task)return -1;if(op==1){if(claimBusy)return -3;raw=1;return 0;}if(op==2){raw=0;return 0;}return -1;}
static int mockOpen(void){if(owner)return -1;owner=task;return 3;}
static void mockClose(void){if(owner==task)owner=raw=0;}
unsigned GetWinFlags(void){return 0;}
unsigned TpSoundTestRom(void){return 0x21;}
int IsWindow(HWND w){return w==1||(w==2&&markerLive);}
unsigned GetWindowWord(HWND w,int i){(void)w;(void)i;return 1;}
int GetClassName(HWND w,char *b,int n){(void)w;(void)n;strcpy(b,"TandyPSGTest");return 12;}
int lstrcmp(char *a,char *b){return strcmp(a,b);}
HWND FindWindow(char *c,char *t){(void)t;if(external&&!strcmp(c,"TandyStartupChime"))return 9;return !strcmp(c,"TandyPSGTest")&&markerLive?2:0;}
HMODULE GetModuleHandle(char *n){return !strcmp(n,"SOUND")?driver:0;}
FARPROC GetProcAddress(HMODULE h,char *n){
 if(!h)return NULL;
 if(!strcmp(n,"DEBUGTIMER")||(api&&!strcmp(n,"TANDYPSGLEASE")))return (FARPROC)lease;
 if(openapi&&!strcmp(n,"OPENSOUND"))return (FARPROC)mockOpen;
 if(closeapi&&!strcmp(n,"CLOSESOUND"))return (FARPROC)mockClose;
 return NULL;
}
HWND GetWindow(HWND w,int op){(void)w;return op==GW_HWNDFIRST?2:foreignWindow?3:0;}
int outp(unsigned p,unsigned b){assert(p==0xc0&&owner==task&&raw);ports++;return b;}
int DestroyWindow(HWND w){assert(w==2);markerLive=0;return 1;}
int UnregisterClass(char *c,HINSTANCE i){(void)c;(void)i;registered=0;return 1;}
HWND GetActiveWindow(void){return activeWindow;}
int IsWindowEnabled(HWND w){(void)w;return 1;}
int IsIconic(HWND w){(void)w;return 0;}
LONG DefWindowProc(void){return 0;}
int RegisterClass(WNDCLASS *c){(void)c;if(!regok)return 0;registered=1;return 1;}
HWND CreateWindow(char *c,char *t,unsigned st,int x,int y,int w,int h,HWND p,void *menu,HINSTANCE i,void *param){(void)c;(void)t;(void)st;(void)x;(void)y;(void)w;(void)h;(void)p;(void)menu;(void)i;(void)param;if(!createok)return 0;markerLive=1;return 2;}
#include "../WHEEL/WIN16/SOURCE/TP/TPSOUND.C"
static void reset(void){
    memset(&stats,0,sizeof(stats));memset(&soundOwner,0,sizeof(soundOwner));
    playing=pending=touched=classOwned=0;marker=0;
    score=NULL;driver=api=openapi=closeapi=regok=createok=task=activeWindow=1;
    owner=raw=external=ports=markerLive=registered=foreignWindow=claimBusy=0;
    assert(TpSoundInit(1,1,1));
}
int main(void){unsigned i;
    reset();assert(TpSoundBegin(1,TD_SND_REVEAL,0)==1&&!ports&&owner==1&&raw);
    for(i=0;i<=12;i++)TpSoundTick(1,(DWORD)i*100);
    assert(stats.notes==12&&stats.completions[0]==1&&!owner&&!raw&&!markerLive&&!registered);
    assert(ports==74);
    reset();owner=2;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!ports&&owner==2);
    reset();driver=0;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!ports&&!owner);
    reset();api=0;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!ports&&!owner);
    reset();openapi=0;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!ports&&!owner);
    reset();closeapi=0;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!ports&&!owner);
    reset();claimBusy=1;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!ports&&!owner);
    reset();external=1;assert(TpSoundBegin(1,1,0)==TD_SND_BUSY&&!owner&&!ports);
    reset();regok=0;assert(TpSoundBegin(1,1,0)==TD_SND_FAILED&&!owner&&!ports);
    reset();createok=0;assert(TpSoundBegin(1,1,0)==TD_SND_FAILED&&!owner&&!ports&&!registered);
    reset();assert(TpSoundBegin(1,1,0)==1);TpSoundTick(1,0);assert(ports==6);
    activeWindow=0;TpSoundTick(1,100);assert(!owner&&!raw&&!playing&&ports==8);
    reset();assert(TpSoundBegin(1,1,0)==1);TpSoundTick(1,0);owner=2;raw=0;
    TpSoundTick(1,100);assert(owner==2&&!playing&&ports==6&&stats.ownershipLosses==1);
    reset();assert(TpSoundBegin(1,1,0)==1);TpSoundStop(1);assert(!owner&&!playing&&!ports);
    assert(TpSoundBegin(1,1,0)==1);TpSoundTick(1,301);assert(!owner&&!ports&&stats.lateAborts==1);
    reset();assert(!TpSoundInit(1,1,0));assert(TpSoundBegin(1,1,0)==TD_SND_DISABLED&&!ports);
    puts("PASS: TP idle driver cue unchanged, busy/failed acquire, focus/close/reopen and ownership loss");
    return 0;
}
