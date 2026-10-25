#include <stdio.h>
#include <string.h>
#include <assert.h>
#define FAR
#define PASCAL
typedef int HMODULE;
typedef void (*FARPROC)(void);
static int driver=1,api=1,openapi=1,closeapi=1,task=1,owner,raw,busy,claims,releases,opens,closes,mutes;
static int lease(unsigned v,unsigned op) {
    if(v!=1)return -1;
    if(owner!=task)return -1;
    if(op==1){claims++;if(busy)return -3;raw=1;return 0;}
    if(op==2){if(!raw)return -1;releases++;raw=0;mutes++;return 0;}
    return -1;
}
static HMODULE GetModuleHandle(char *name){assert(!strcmp(name,"SOUND"));return driver;}
static int mockOpen(void){if(owner)return -1;opens++;owner=task;return 3;}
static void mockClose(void){assert(owner==task);closes++;owner=raw=0;}
static FARPROC GetProcAddress(HMODULE h,char *name){
    assert(h==1);
    if(api&&!strcmp(name,"TANDYPSGLEASE"))return (FARPROC)lease;
    if(openapi&&!strcmp(name,"OPENSOUND"))return (FARPROC)mockOpen;
    if(closeapi&&!strcmp(name,"CLOSESOUND"))return (FARPROC)mockClose;
    return NULL;
}
#include "PSGOWN.H"
int main(void) {
    PSG_OWNER state;
    state.lease=NULL;state.opened=0; /* Existing manual local initialization. */
    closeapi=0;
    assert(!PsgOwnerAcquire(&state)&&!state.lease&&!state.closeSound&&!state.opened&&!opens&&!closes);
    closeapi=1;
    assert(PsgOwnerAcquire(&state)&&opens==1&&owner==1&&raw);
    assert(PsgOwnerAcquire(&state)&&opens==1&&claims==2);
    assert(PsgOwnerHeld(&state)&&claims==3);
    PsgOwnerRelease(&state);
    assert(!state.opened&&!state.lease&&!state.closeSound&&!owner&&!raw&&closes==1&&mutes==1);
    PsgOwnerRelease(&state);assert(closes==1&&mutes==1);
    driver=0;assert(!PsgOwnerAcquire(&state)&&opens==1);driver=1;
    api=0;assert(!PsgOwnerAcquire(&state)&&opens==1&&closes==1);api=1;
    openapi=0;assert(!PsgOwnerAcquire(&state)&&opens==1&&closes==1);openapi=1;
    closeapi=0;assert(!PsgOwnerAcquire(&state)&&opens==1&&closes==1);closeapi=1;
    owner=2;assert(!PsgOwnerAcquire(&state)&&opens==1);owner=0;
    busy=1;assert(!PsgOwnerAcquire(&state)&&opens==2&&closes==2&&!owner);busy=0;
    assert(PsgOwnerAcquire(&state));task=2;
    assert(!PsgOwnerHeld(&state));PsgOwnerRelease(&state);
    assert(owner==1&&raw&&closes==2&&mutes==1);
    assert(!state.opened&&!state.lease&&!state.closeSound);
    task=1;owner=raw=0;
    assert(PsgOwnerAcquire(&state));raw=0; /* Own StopSound revocation. */
    PsgOwnerRelease(&state);assert(!owner&&!raw&&closes==3&&mutes==2);
    puts("PASS: dynamic Open/Close/lease discovery, missing exports, own cleanup and foreign task protection");
    return 0;
}
