#ifndef TDSOUND_H
#define TDSOUND_H
#ifdef TDSOUND_HOST
#include "SNDSTUB.H"
#else
#ifndef WINVER
#define WINVER 0x0300
#endif
#include <windows.h>
#endif

#define TD_SND_REVEAL  1
#define TD_SND_VICTORY 2
#define TD_SND_WRONG   3
#define TD_SND_COUNT   3
#define TD_SND_REVEAL_MS  400
#define TD_SND_VICTORY_MS 600
#define TD_SND_WRONG_MS   400

/* Begin result: a skipped cue is harmless and must not block gameplay. */
#define TD_SND_STARTED   1
#define TD_SND_DISABLED  0
#define TD_SND_BUSY     -1
#define TD_SND_FAILED   -2
#define TD_SND_BADARG   -3
#define TD_SND_INACTIVE -4

typedef struct {
    DWORD attempts, starts[TD_SND_COUNT], completions[TD_SND_COUNT];
    DWORD busySkips, disabledSkips, inactiveSkips, failures;
    DWORD stops, lateAborts, ownershipLosses, portWrites, notes;
    DWORD cleanupFailures;
    unsigned supported, enabled, playing, cue, durationMs;
} TDSNDSTAT;

/* Call once after checking the caller's 100 ms UI SetTimer result.
   No timer is created here. timerReady=0 disables all hardware access.
   Return 1 means real-mode Tandy guard and caller timer both passed.
   Initial Init/Begin do not write PSG; replacing an owned cue mutes it. */
int TpSoundInit(HWND owner,HINSTANCE instance,int timerReady);
void TpSoundEnable(int enabled);
int TpSoundEnabled(void);
int TpSoundBegin(HWND owner,int cue,DWORD now);
void TpSoundTick(HWND owner,DWORD now);
void TpSoundStop(HWND owner);
void TpSoundGetStats(TDSNDSTAT *out);

#endif
