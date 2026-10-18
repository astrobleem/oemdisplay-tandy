/* Optional original TP cues. Microsoft C6 /G0 /Gw /AS, C89.
   Tone 0 and fixed-rate noise only; no IRQ, PIT, PIC or speaker-control writes.
   The app supplies a yielding 100 ms WM_TIMER and stops on focus/close.
   This is cooperative known-writer exclusion, not a global hardware lock. */
#include "TPSOUND.H"
#ifndef TDSOUND_HOST
#include <conio.h>
#endif

typedef struct { unsigned divisor, endMs, volume; } SNDNOTE;
/* Short, original three-/four-note gestures, not sampled recordings. */
static const SNDNOTE flush[] = {
 {640,100,12},{800,200,10},{520,300,11},{900,400,9},
 {720,500,11},{990,600,10},{810,700,12},{1000,800,11},
 {850,900,13},{1020,1000,12},{900,1100,14},{1020,1200,14}
};
static const SNDNOTE *score;
static unsigned noteCount,noteIndex,cueId;
static HWND target,marker;
static HINSTANCE module;
static int classOwned,allowed,enabled,playing,pending,touched;
static DWORD queuedAt,startedAt;
static TDSNDSTAT stats;
static char markerClass[]="TandyPSGTest";

static int machineReady(void)
{
    if(GetWinFlags()&WF_PMODE)return 0;
#ifdef TDSOUND_HOST
    return TpSoundTestRom()==0x21;
#else
    /* Existing first-party Tandy ROM compatibility guard, not model proof. */
    return *(unsigned char FAR *)0xfc000000UL==0x21;
#endif
}

static int ownMarker(void)
{
    char name[32];
    if(!marker || !IsWindow(marker) ||
       GetWindowWord(marker,GWW_HINSTANCE)!=(WORD)module)return 0;
    if(!GetClassName(marker,name,sizeof(name)))return 0;
    return !lstrcmp(name,markerClass);
}

static int foreignBusy(void)
{
    HWND w;HMODULE h;char name[32];unsigned count;
    if(FindWindow("TandyStartupChime",NULL) ||
       FindWindow("TandyXPStartupChime",NULL) ||
       FindWindow("TandyAutomaticMouth",NULL) ||
       FindWindow("TandyPreExitChime",NULL) ||
       FindWindow("TandyMiniMIDI",NULL) ||
       FindWindow("TandyJoyMIDI",NULL) ||
       FindWindow("TandyBeatsLab",NULL) || GetModuleHandle("TEXIT"))return 1;
    h=GetModuleHandle("SOUND");
    if(h && GetProcAddress(h,"DEBUGTIMER")!=NULL)return 1;
    if(!marker)return FindWindow(markerClass,NULL)!=NULL;
    if(!ownMarker())return 1;
    /* FindWindow alone could find our marker and hide a second PSGPLAY.
       Bounded top-level traversal catches same-class foreign windows. */
    w=GetWindow(marker,GW_HWNDFIRST);count=0;
    while(w && count<256) {
        if(w!=marker) {
            if(!GetClassName(w,name,sizeof(name)))return 1;
            if(!lstrcmp(name,markerClass))return 1;
        }
        w=GetWindow(w,GW_HWNDNEXT);count++;
    }
    return w!=NULL;
}

static void psg(unsigned value)
{
    outp(0xc0,value);stats.portWrites++;
}

static void releaseMarker(void)
{
    if(marker) {
        if(ownMarker()) {
            if(!DestroyWindow(marker)) { stats.cleanupFailures++;return; }
        }
        /* Never destroy a reused handle that no longer belongs to us. */
        marker=NULL;
    }
    if(classOwned) {
        if(UnregisterClass(markerClass,module))classOwned=0;
        else stats.cleanupFailures++;
    }
}

static void finish(int natural)
{
    int own;
    /* Recheck even on ordinary close: a newly opened writer takes priority.
       If ownership is uncertain, abandon without silencing anyone else. */
    own=marker && ownMarker() && !foreignBusy();
    if(playing && !own)stats.ownershipLosses++;
    if(touched && own){psg(0x9f);psg(0xff);}
    if(playing) {
        if(natural)stats.completions[cueId-1]++;
        else stats.stops++;
    }
    playing=pending=touched=0;
    score=NULL;noteCount=noteIndex=cueId=0;
    releaseMarker();
}

int TpSoundInit(HWND owner,HINSTANCE instance,int timerReady)
{
    allowed=enabled=0;
    if(playing || marker || classOwned)finish(0);
    if(marker || classOwned) { stats.failures++;return 0; }
    target=owner;module=instance;
    allowed=owner && instance && timerReady && machineReady();
    enabled=allowed;
    return allowed;
}

void TpSoundEnable(int on)
{
    if(!on)finish(0);
    enabled=on && allowed;
}

int TpSoundEnabled(void) { return enabled; }

static int activeOwner(HWND owner)
{
    return owner && owner==target && IsWindow(owner) &&
        GetActiveWindow()==owner && IsWindowEnabled(owner) && !IsIconic(owner);
}

int TpSoundBegin(HWND owner,int cue,DWORD now)
{
    WNDCLASS c;
    stats.attempts++;
    if(owner!=target || cue<TD_SND_REVEAL || cue>TD_SND_WRONG)
        return TD_SND_BADARG;
    if(!enabled || !allowed) { stats.disabledSkips++;return TD_SND_DISABLED; }
    if(!activeOwner(owner)) {
        stats.inactiveSkips++;finish(0);return TD_SND_INACTIVE;
    }
    /* Replace only this app's cue. Do not queue sounds behind slow gameplay. */
    if(playing || marker || classOwned)finish(0);
    if(marker || classOwned) { stats.failures++;return TD_SND_FAILED; }
    if(foreignBusy()) { stats.busySkips++;return TD_SND_BUSY; }
    c.style=0;c.lpfnWndProc=DefWindowProc;c.cbClsExtra=c.cbWndExtra=0;
    c.hInstance=module;c.hIcon=NULL;c.hCursor=NULL;c.hbrBackground=NULL;
    c.lpszMenuName=NULL;c.lpszClassName=markerClass;
    /* Register our own local class. Never instantiate a foreign class after
       RegisterClass failure. DefWindowProc requires no app callback export. */
    if(!RegisterClass(&c)) { stats.failures++;return TD_SND_FAILED; }
    classOwned=1;
    marker=CreateWindow(markerClass,"TP sound busy",WS_POPUP,
                        0,0,0,0,NULL,NULL,module,NULL);
    if(!marker) { stats.failures++;releaseMarker();return TD_SND_FAILED; }
    if(foreignBusy()) { stats.busySkips++;releaseMarker();return TD_SND_BUSY; }
    score=flush;noteCount=12;
    cueId=cue;noteIndex=0;queuedAt=now;playing=pending=1;touched=0;
    stats.starts[cue-1]++;
    return TD_SND_STARTED;
}

static void playNote(void)
{
    unsigned divisor;
    divisor=score[noteIndex].divisor;
    /* Mute only tone 0 before retuning; batches do not yield to Windows. */
    psg(0x9f);psg(0x80|(divisor&15));psg((divisor>>4)&63);
    psg(0x90|score[noteIndex].volume);
    /* Original flush: fixed-rate white noise fades while tone0 gurgles. */
    psg(0xe6);psg(0xf0|(noteIndex<5?5:noteIndex+3));
    touched=1;stats.notes++;
}

void TpSoundTick(HWND owner,DWORD now)
{
    DWORD elapsed;unsigned next;
    if(owner!=target || !playing)return;
    if(!enabled || !allowed || !activeOwner(owner)) { finish(0);return; }
    if(!ownMarker() || foreignBusy()) { finish(0);return; }
    if(pending) {
        /* The caller should service us every 100 ms. A long first delay
           drops the cue rather than playing it after the moment passed. */
        if((DWORD)(now-queuedAt)>300UL) { stats.lateAborts++;finish(0);return; }
        pending=0;startedAt=now;playNote();return;
    }
    elapsed=(DWORD)(now-startedAt);
    if(elapsed<score[noteIndex].endMs)return;
    if(elapsed-(DWORD)score[noteIndex].endMs>220UL) {
        stats.lateAborts++;finish(0);return;
    }
    if(elapsed>=score[noteCount-1].endMs) { finish(1);return; }
    next=noteIndex+1;
    while(next<noteCount && elapsed>=score[next].endMs)next++;
    noteIndex=next;playNote();
}

void TpSoundStop(HWND owner)
{
    if(owner==target)finish(0);
}

void TpSoundGetStats(TDSNDSTAT *out)
{
    if(!out)return;
    *out=stats;
    out->supported=allowed;out->enabled=enabled;out->playing=playing;
    out->cue=cueId;out->durationMs=score?score[noteCount-1].endMs:0;
}
