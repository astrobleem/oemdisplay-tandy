/* Main-task saver policy. The separate fixed DLL only observes global input. */
#define WINVER 0x0300
#include <windows.h>
#include "TSBOOT.H"
#include "TSSAVER.H"
#include "TSHOLD.H"
#include "TSSAVCFG.H"
#include "TNOTICE.H"
#include "PROGMENU.H"
#include "SVCORE.H"
typedef BOOL (FAR PASCAL *IDLEBOOL)(void);
typedef DWORD (FAR PASCAL *IDLECOUNT)(void);
static HINSTANCE hookModule, ownInstance, previewInstance;
static HWND policyOwner, previewOwner;
static IDLEBOOL idleInstall, idleRemove, idleReady;
static IDLECOUNT idleGeneration;
static SVSTATE state;
static DWORD delay, previewAt, previewGen, policyRevision;
static int enabled, holding, stopping, inTick, launchBusy, previewWatch;
static char saver[128];
static BYTE previewKeys[256];
static POINT previewPoint;

static void reset(void)
{ SvReset(&state, GetTickCount(), idleGeneration ? idleGeneration() : 0L); }
static int knownAudio(void)
{
    return TandyBootBusy() || GetModuleHandle("TCHIME") ||
        GetModuleHandle("XPCHIME") || GetModuleHandle("TEXIT") ||
        FindWindow("TandyPSGTest", NULL) ||
        FindWindow("TandyAutomaticMouth", NULL) ||
        FindWindow("TandyMiniMIDI", NULL) || FindWindow("TandyJoyMIDI", NULL);
}
static int saverRunning(void)
{ return GetModuleHandle("MATRIX") || GetModuleHandle("MAZE") || GetModuleHandle("STARFLD"); }
static int saverWindow(void)
{ return FindWindow("TandyMatrixSaver", NULL) || FindWindow("TandyMazeSaver", NULL) ||
         FindWindow("TandyStarfieldSaver", NULL); }
static void closeSaver(void)
{
    HWND w = FindWindow("TandyMatrixSaver", NULL);
    if (w) PostMessage(w, WM_CLOSE, 0, 0L);
    w = FindWindow("TandyMazeSaver", NULL);
    if (w) PostMessage(w, WM_CLOSE, 0, 0L);
    w = FindWindow("TandyStarfieldSaver", NULL);
    if (w) PostMessage(w, WM_CLOSE, 0, 0L);
}
static void releaseHook(void)
{
    if (!hookModule) return;
    /* An unhook failure must never leave a live callback in freed code. */
    if (!idleRemove || idleRemove()) {
        FreeLibrary(hookModule); hookModule = 0;
        idleInstall = idleRemove = idleReady = NULL; idleGeneration = NULL;
    }
}
void TSSaverStop(HWND w)
{ ++policyRevision; enabled = 0; KillTimer(w, SAVER_TIMER); closeSaver(); releaseHook(); }
void TSSaverHold(int enter)
{
    TandyHoldBlock(enter);
    if (enter) ++holding;
    else if (holding) --holding;
    reset();
}
void TSSaverShutdown(int pending)
{ stopping = pending; TandyHoldShutdown(pending); reset(); if (pending) { ++policyRevision; closeSaver(); } }
int TSSaverShortcutBusy(void)
{ return holding || stopping || launchBusy || previewWatch; }
int TSSaverPrimary(void)
{ return policyOwner != NULL; }
static int beginPolicy(HWND w, HINSTANCE instance)
{
    SCCONFIG config;
    char dll[144];
    int n, secs;
    OFSTRUCT of;
    if (SaverConfigRead(&config) != SC_OK) {
        TinyNotice(w, instance, "Saver", "Cannot read\nTSHELL.INI.\nIdle disabled."); return 0;
    }
    if (!ScEnabled(&config)) return 1;
    secs = ScSeconds(ScValue(&config, SC_SECONDS));
    if (!secs) {
        TinyNotice(w, instance, "Saver", "Bad idle delay.\nSee TSHELL.INI."); return 0;
    }
    if (!SaverConfigProgram(w, instance, &config, ScChoice(&config), saver)) return 0;
    delay = (DWORD)secs * 1000L;
    n = GetWindowsDirectory(dll, sizeof(dll));
    if (!n || n >= sizeof(dll) - 13) goto failed;
    lstrcat(dll, "\\TSINPUT.DLL");
    /* Win3's loader opens an oversized system dialog for a missing DLL. */
    if (OpenFile(dll, &of, OF_EXIST) == HFILE_ERROR) {
        TinyNotice(w, instance, "Saver", "TSINPUT missing.\nIdle disabled."); return 0;
    }
    hookModule = LoadLibrary(dll);
    if ((UINT)hookModule < 32) { hookModule = 0; goto failed; }
    idleInstall = (IDLEBOOL)GetProcAddress(hookModule, "IdleInstall");
    idleRemove = (IDLEBOOL)GetProcAddress(hookModule, "IdleRemove");
    idleReady = (IDLEBOOL)GetProcAddress(hookModule, "IdleReady");
    idleGeneration = (IDLECOUNT)GetProcAddress(hookModule, "IdleGeneration");
    if (!idleInstall || !idleRemove || !idleReady || !idleGeneration) goto failed;
    if (!idleInstall()) goto failed;
    /* Do not alter a modal hold or a pending shutdown during Apply. */
    reset(); enabled = 1;
    if (SetTimer(w, SAVER_TIMER, 1000, NULL)) return 1;
failed:
    TSSaverStop(w);
    TinyNotice(w, instance, "Saver", "Idle hook failed.\nIdle disabled."); return 0;
}
void TSSaverBegin(HWND w, HINSTANCE instance)
{
    /* Shell calls this only in its elected primary instance, even if disabled. */
    policyOwner = w; ownInstance = instance;
    if (enabled || hookModule || stopping) return;
    beginPolicy(w, instance);
}
int TSSaverReconfigure(void)
{
    if (!policyOwner || stopping) return 0;
    TSSaverStop(policyOwner);
    if (hookModule) {
        TinyNotice(policyOwner, ownInstance, "Saver", "Saved. Idle off.\nRestart shell.");
        return -1;
    }
    return beginPolicy(policyOwner, ownInstance) ? 1 : -1;
}
void TSSaverTick(HWND w)
{
    BOOL ready;
    DWORD gen, revision;
    UINT result;
    if (!enabled || inTick || launchBusy) return;
    /* Preview's startup guard needs real input generations, not modal polls. */
    if (previewWatch) { reset(); return; }
    inTick = 1;
    ready = idleReady(); gen = idleGeneration();
    if (holding || stopping || !IsWindowEnabled(w) || knownAudio() || saverRunning()) ready = FALSE;
    if (SvDue(&state, GetTickCount(), gen, delay, ready)) {
        revision = policyRevision;
        ++holding; TandyHoldBlock(1); launchBusy = 1;
        result = PmLaunchShow(w, saver, SW_SHOWNORMAL);
        /* WinExec may yield while loading; new input/shutdown cancels the saver. */
        if (stopping || revision != policyRevision || !idleGeneration ||
            idleGeneration() != gen) closeSaver();
        launchBusy = 0; --holding; TandyHoldBlock(0); reset();
        if (result < 32 && IsWindow(w) && !stopping && revision == policyRevision) {
            TSSaverStop(w);
            TinyNotice(w, ownInstance, "Saver", "Saver failed.\nIdle disabled.");
        }
    }
    inTick = 0;
}
static int previewInput(void)
{
    BYTE keys[256];
    POINT p;
    int i;
    if (idleGeneration && idleGeneration() != previewGen) return 1;
    GetCursorPos(&p);
    if (p.x != previewPoint.x || p.y != previewPoint.y) return 1;
    GetKeyboardState(keys);
    for (i = 0; i < 256; ++i)
        if ((keys[i] & 0x80) != (previewKeys[i] & 0x80)) return 1;
    return 0;
}
void TSSaverPreviewEnd(HWND w)
{
    KillTimer(w, SAVER_PREVIEW_TIMER);
    if (previewOwner == w) { previewOwner = NULL; previewWatch = 0; reset(); }
}
void TSSaverPreviewTick(HWND w)
{
    int cancelled;
    if (!previewWatch || previewOwner != w || launchBusy) return;
    if (saverWindow()) { TSSaverPreviewEnd(w); return; }
    cancelled = stopping || previewInput() || GetActiveWindow() != w;
    if (cancelled) { TSSaverPreviewEnd(w); return; }
    if ((DWORD)(GetTickCount() - previewAt) < 1000L) return;
    TSSaverPreviewEnd(w);
    TinyNotice(w, previewInstance, "Saver", "Preview did not\nstart. Check\nsaver setup.");
}
void TSSaverPreview(HWND w, HINSTANCE instance, char *command)
{
    UINT result;
    if (launchBusy || previewWatch || stopping || !IsWindowEnabled(w)) return;
    if (knownAudio() || GetCapture() || GetSysModalWindow() || saverRunning()) {
        TinyNotice(w, instance, "Saver", "Saver busy.\nTry again later."); return;
    }
    previewOwner = w; previewInstance = instance; previewAt = GetTickCount();
    previewGen = idleGeneration ? idleGeneration() : 0L;
    GetKeyboardState(previewKeys); GetCursorPos(&previewPoint);
    previewWatch = 1;
    if (!SetTimer(w, SAVER_PREVIEW_TIMER, 100, NULL)) {
        TSSaverPreviewEnd(w);
        TinyNotice(w, instance, "Saver", "Preview timer\nfailed."); return;
    }
    launchBusy = 1; ++holding; TandyHoldBlock(1);
    result = PmLaunchShow(w, command, SW_SHOWNORMAL);
    if (stopping || previewInput()) closeSaver();
    launchBusy = 0; --holding; TandyHoldBlock(0); reset();
    if (result < 32 || stopping || previewInput()) TSSaverPreviewEnd(w);
    else TSSaverPreviewTick(w);
}
