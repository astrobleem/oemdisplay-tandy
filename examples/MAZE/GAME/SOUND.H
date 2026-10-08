/*
 * SOUND.H - Tandy Maze sound effects on the Tandy 1000 PSG (SN76496).
 *
 * Same guards as Pinball and the startup chime: direct port writes only
 * in real mode, only with the Tandy ROM signature, and only while this
 * app holds the Windows sound device. Every exit path mutes the chip.
 * Effects are queued and start after the frame is on screen. Notes are
 * timed by the clock, not by counting WM_TIMER messages: Windows merges
 * or delays timer messages while an app is busy drawing (half a second
 * a frame on an 8088), which stretched or clipped notes.
 */
#define PSG 0xC0

#define SFX_STEP  1
#define SFX_TURN  2
#define SFX_BUMP  3
#define SFX_EXIT  4
#define SFX_LEVEL 5

static int soundok;
static int pend;                        /* effect waiting for the frame  */
static const int *seq;                  /* notes playing: hz, ms ...     */
static DWORD seqend;                    /* when this note ends           */
static int sound = 1;

/* Pairs of hz, ms: hz > 0 tone on channel 0, hz < 0 white noise (rate
   -hz-1), hz 0 ends the effect. */
static const int s_step[] = { -2, 40, 0 };
static const int s_turn[] = { -3, 25, 0 };
static const int s_bump[] = { 98, 140, 0 };
static const int s_exit[] = { 523, 110, 659, 110, 784, 110, 1047, 300, 0 };
static const int s_level[] = { 392, 110, 523, 170, 0 };

static void psgmute(void)
{
    int i;
    for (i = 0; i < 4; ++i) outp(PSG, 0x9F | (i << 5));
}

static void note(int hz)
{
    unsigned div;
    psgmute();
    if (hz > 0) {
        div = (unsigned)(111861L / hz);
        if (div > 1023) div = 1023;
        outp(PSG, 0x80 | (div & 15));
        outp(PSG, (div >> 4) & 63);
        outp(PSG, 0x92);                /* channel 0, loud               */
    } else if (hz < 0) {
        outp(PSG, 0xE4 | ((-hz - 1) & 3));  /* white noise               */
        outp(PSG, 0xF3);
    }
}

static int tandypsg(void)
{
    unsigned char far *sig = (unsigned char far *)0xF000C000L;
    if (GetWinFlags() & WF_PMODE) return 0;
    return *sig == 0x21;
}

static void soundinit(void)
{
    soundok = tandypsg() && OpenSound() > 0;
    if (soundok) psgmute();
}

static void soundclose(void)
{
    if (soundok) { psgmute(); CloseSound(); }
    soundok = 0;
}

/* Silence now and forget anything queued (pause, focus loss). */
static void soundstop(void)
{
    pend = 0;
    seq = NULL;
    if (soundok) psgmute();
}

static void sfx(int id)
{
    if (!soundok || !sound) return;
    if (id >= pend) pend = id;          /* the bigger event wins         */
}

/* Called right after the frame is drawn. */
static void sounds_now(void)
{
    int id = pend;
    pend = 0;
    if (!id || !soundok || !sound) return;
    seq = id == SFX_STEP ? s_step : id == SFX_TURN ? s_turn :
          id == SFX_BUMP ? s_bump : id == SFX_EXIT ? s_exit : s_level;
    note(seq[0]);
    seqend = GetTickCount() + (DWORD)seq[1];
}

/* From the timer and after each frame: end or advance due notes. */
static void soundtick(void)
{
    DWORD now;
    if (!seq) return;
    now = GetTickCount();
    if ((long)(now - seqend) < 0) return;
    seq += 2;
    if (!seq[0] || !soundok || !sound) {
        if (soundok) psgmute();
        seq = NULL;
        return;
    }
    note(seq[0]);
    seqend = now + (DWORD)seq[1];
}
