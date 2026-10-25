#include <stdio.h>
#include <string.h>
#include <assert.h>
#define FAR
#define PASCAL
typedef int HMODULE;
typedef void (*FARPROC)(void);
static int driver=1,api=1,task=1,owner,raw,busy,claims,releases,opens,closes,mutes;
static int lease(unsigned v,unsigned op) {
    if(v!=1)return -1;
    if(owner!=task)return -1;
    if(op==1){claims++;if(busy)return -3;raw=1;return 0;}
    if(op==2){if(!raw)return -1;releases++;raw=0;mutes++;return 0;}
    return -1;
}
static HMODULE GetModuleHandle(char *name){assert(!strcmp(name,"SOUND"));return driver;}
static FARPROC GetProcAddress(HMODULE h,char *name){assert(h==1);return api&&!strcmp(name,"TANDYPSGLEASE")?(FARPROC)lease:NULL;}
static int OpenSound(void){if(owner)return -1;opens++;owner=task;return 3;}
static void CloseSound(void){if(owner==task){closes++;owner=raw=0;}}
#include "PSGOWN.H"
int main(void) {
    PSG_OWNER state;
    memset(&state,0,sizeof(state));
    assert(PsgOwnerAcquire(&state)&&opens==1&&owner==1&&raw);
    assert(PsgOwnerAcquire(&state)&&opens==1&&claims==2);
    assert(PsgOwnerHeld(&state)&&claims==3);
    PsgOwnerRelease(&state);
    assert(!state.opened&&!owner&&!raw&&closes==1&&mutes==1);
    PsgOwnerRelease(&state);assert(closes==1&&mutes==1);
    driver=0;assert(!PsgOwnerAcquire(&state)&&opens==1);driver=1;
    api=0;assert(!PsgOwnerAcquire(&state)&&opens==1);api=1;
    owner=2;assert(!PsgOwnerAcquire(&state)&&opens==1);owner=0;
    busy=1;assert(!PsgOwnerAcquire(&state)&&opens==2&&closes==2&&!owner);busy=0;
    assert(PsgOwnerAcquire(&state));task=2;
    assert(!PsgOwnerHeld(&state));PsgOwnerRelease(&state);
    assert(owner==1&&raw&&closes==2&&mutes==1);
    task=1;owner=raw=0;
    puts("PASS: owner acquire/reentry/release, absent API, busy and foreign task guards");
    return 0;
}
