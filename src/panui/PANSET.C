/* PANSET.C - implementation of the shared panning settings model.
 *
 * Pure C89. Only PANSET.H is included: no libc, no Windows calls, no
 * allocation and no mutable static state.
 */
#include "PANSET.H"

#define PS_NULL              ((void *)0)
#define PS_STEP_DEFAULT      50
#define PS_DWELL_DEFAULT     400
#define PS_EDGE_DEFAULT      3
#define PS_FOLLOW_DEFAULT    1
#define PS_REPEAT_DEFAULT    100
#define PS_DWELL_MAX         10000
#define PS_STEP_MIN          8
#define PS_EDGE_MIN          1
#define PS_INT_MAX_TEXT      32767L
#define PS_STATUS_CAP        80
#define PS_NOTE_CAP          80

static int ps_is_blank(char ch)
{
    return ch == ' ' || ch == '\t';
}

static char ps_upper(char ch)
{
    if (ch >= 'a' && ch <= 'z') {
        return (char)(ch - 'a' + 'A');
    }
    return ch;
}

static int ps_word_nocase(const char *s, const char *word)
{
    if (s == PS_NULL) {
        return 0;
    }
    while (*word != '\0') {
        if (*s == '\0' || ps_upper(*s) != ps_upper(*word)) {
            return 0;
        }
        s++;
        word++;
    }
    return *s == '\0';
}

static void ps_copy_status(char *dst, const char *src)
{
    int i;

    for (i = 0; i < PS_STATUS_CAP - 1 && src[i] != '\0'; i++) {
        dst[i] = src[i];
    }
    dst[i] = '\0';
}

static int ps_differs(unsigned caps, const PANSET *a, const PANSET *b)
{
    if ((caps & PS_CAP_STEP) && a->step != b->step) {
        return 1;
    }
    if ((caps & PS_CAP_EDGE) && a->edge != b->edge) {
        return 1;
    }
    if ((caps & PS_CAP_DWELL) && a->dwell != b->dwell) {
        return 1;
    }
    if ((caps & PS_CAP_FOLLOW) && a->follow != b->follow) {
        return 1;
    }
    if ((caps & PS_CAP_EDGEON) && a->edgeOn != b->edgeOn) {
        return 1;
    }
    if ((caps & PS_CAP_REPEAT) && a->repeat != b->repeat) {
        return 1;
    }
    if ((caps & PS_CAP_FOLLOWD) && a->followDlg != b->followDlg) {
        return 1;
    }
    if ((caps & PS_CAP_MODE) && a->mode != b->mode) {
        return 1;
    }
    return 0;
}

static int ps_repeat_ok(int v)
{
    return v == 100 || v == 200 || v == 500;
}

void PanSetDefaults(int backend, PANSET *s)
{
    if (s == PS_NULL) {
        return;
    }
    /* Vertical and XY defaults are the same field values: each backend
     * leaves the fields it does not own at these values. */
    (void)backend;
    s->step = PS_STEP_DEFAULT;
    s->dwell = PS_DWELL_DEFAULT;
    s->edge = PS_EDGE_DEFAULT;
    s->follow = PS_FOLLOW_DEFAULT;
    s->edgeOn = 0;
    s->repeat = PS_REPEAT_DEFAULT;
    s->followDlg = 0;
    s->mode = PS_MODE_SOFT;
}

unsigned PanCapsFor(int backend, int modeReadback)
{
    unsigned caps;

    caps = 0;
    if (backend == PS_BACK_VERT) {
        caps = PS_CAP_STEP | PS_CAP_EDGE | PS_CAP_DWELL | PS_CAP_FOLLOW |
               PS_CAP_HOME | PS_CAP_SOFT;
    } else if (backend == PS_BACK_XY) {
        caps = PS_CAP_EDGEON | PS_CAP_REPEAT | PS_CAP_FOLLOWD | PS_CAP_HOME |
               PS_CAP_SOFT;
        if (modeReadback) {
            caps |= PS_CAP_MODE | PS_CAP_HARD;
        }
    }
    return caps;
}

int PanSetValidate(const PANCAPS *c, const PANSET *s)
{
    int upper;

    if (c == PS_NULL || s == PS_NULL) {
        return PS_E_BACKEND;
    }
    if (c->backend == PS_BACK_NONE || c->caps == 0) {
        return PS_E_BACKEND;
    }
    if (c->caps & PS_CAP_STEP) {
        if (s->step < PS_STEP_MIN || s->step > c->workH) {
            return PS_E_STEP;
        }
    }
    if (c->caps & PS_CAP_EDGE) {
        upper = c->viewH / 2;
        if (upper < 1) {
            upper = 1;
        }
        if (s->edge < PS_EDGE_MIN || s->edge > upper) {
            return PS_E_EDGE;
        }
    }
    if (c->caps & PS_CAP_DWELL) {
        if (s->dwell < 0 || s->dwell > PS_DWELL_MAX) {
            return PS_E_DWELL;
        }
    }
    if (c->caps & PS_CAP_FOLLOW) {
        if (s->follow != 0 && s->follow != 1) {
            return PS_E_FOLLOW;
        }
    }
    if (c->caps & PS_CAP_EDGEON) {
        if (s->edgeOn != 0 && s->edgeOn != 1) {
            return PS_E_EDGEON;
        }
    }
    if (c->caps & PS_CAP_REPEAT) {
        if (!ps_repeat_ok(s->repeat)) {
            return PS_E_REPEAT;
        }
    }
    if (c->caps & PS_CAP_FOLLOWD) {
        if (s->followDlg != 0 && s->followDlg != 1) {
            return PS_E_FOLLOWD;
        }
    }
    if (c->caps & PS_CAP_MODE) {
        if (s->mode != PS_MODE_SOFT && s->mode != PS_MODE_HARD &&
            s->mode != PS_MODE_DESK) {
            return PS_E_MODE;
        }
        if ((s->mode == PS_MODE_SOFT && !(c->caps & PS_CAP_SOFT)) ||
            (s->mode == PS_MODE_HARD && !(c->caps & PS_CAP_HARD)) ||
            (s->mode == PS_MODE_DESK && !(c->caps & PS_CAP_DESK))) {
            return PS_E_MODE;
        }
    }
    return PS_OK;
}

const char *PanSetErrorText(int code)
{
    switch (code) {
    case PS_OK:
        return "OK.";
    case PS_E_BACKEND:
        return "No usable pan engine is running.";
    case PS_E_STEP:
        return "Step must be 8 up to the workspace height.";
    case PS_E_EDGE:
        return "Edge band must be 1 up to half the viewport height.";
    case PS_E_DWELL:
        return "Dwell must be 0 to 10000 ms.";
    case PS_E_FOLLOW:
        return "Follow active must be 0 or 1.";
    case PS_E_EDGEON:
        return "Edge panning must be 0 or 1.";
    case PS_E_REPEAT:
        return "Repeat must be 100, 200 or 500 ms.";
    case PS_E_FOLLOWD:
        return "Follow dialogs must be 0 or 1.";
    case PS_E_MODE:
        return "Choose an available movement mode.";
    case PS_E_TEXT:
        return "Enter a plain decimal number.";
    case PS_E_STORE:
        return "Settings could not be written to WIN.INI.";
    case PS_E_APPLY:
        return "The driver refused the settings.";
    case PS_E_LOST:
        return "The driver no longer answers.";
    default:
        return "Unknown error.";
    }
}

int PanParseInt(const char *text, int *value)
{
    const char *p;
    long acc;
    int digits;

    if (text == PS_NULL || value == PS_NULL) {
        return PS_E_TEXT;
    }
    p = text;
    while (ps_is_blank(*p)) {
        p++;
    }
    acc = 0;
    digits = 0;
    while (*p >= '0' && *p <= '9') {
        if (digits >= 5) {
            return PS_E_TEXT;
        }
        acc = acc * 10L + (long)(*p - '0');
        digits++;
        p++;
    }
    while (ps_is_blank(*p)) {
        p++;
    }
    if (digits == 0 || *p != '\0') {
        return PS_E_TEXT;
    }
    if (acc > PS_INT_MAX_TEXT) {
        return PS_E_TEXT;
    }
    *value = (int)acc;
    return PS_OK;
}

void PanSetLoad(const PANCAPS *c, PANSET *s, const PANSTORE *st)
{
    int v;
    unsigned caps;

    if (s == PS_NULL) {
        return;
    }
    if (c != PS_NULL) {
        PanSetDefaults(c->backend, s);
        caps = c->caps;
    } else {
        PanSetDefaults(PS_BACK_NONE, s);
        caps = 0;
    }
    if (st == PS_NULL || st->get == PS_NULL) {
        return;
    }

    if (caps & PS_CAP_STEP) {
        v = st->get(st->ctx, PS_SEC_VERT, PS_KEY_STEP, PS_STEP_DEFAULT);
        if (v < PS_STEP_MIN) {
            v = PS_STEP_MIN;
        }
        s->step = v;
    }
    if (caps & PS_CAP_DWELL) {
        s->dwell = st->get(st->ctx, PS_SEC_VERT, PS_KEY_DWELL,
                           PS_DWELL_DEFAULT);
    }
    if (caps & PS_CAP_EDGE) {
        v = st->get(st->ctx, PS_SEC_VERT, PS_KEY_EDGE, PS_EDGE_DEFAULT);
        if (v < PS_EDGE_MIN) {
            v = PS_EDGE_MIN;
        }
        s->edge = v;
    }
    if (caps & PS_CAP_FOLLOW) {
        v = st->get(st->ctx, PS_SEC_VERT, PS_KEY_FOLLOW, PS_FOLLOW_DEFAULT);
        s->follow = (v != 0) ? 1 : 0;
    }
    if (caps & PS_CAP_EDGEON) {
        v = st->get(st->ctx, PS_SEC_XY, PS_KEY_EDGEON, 0);
        s->edgeOn = (v == 0 || v == 1) ? v : 0;
    }
    if (caps & PS_CAP_REPEAT) {
        v = st->get(st->ctx, PS_SEC_XY, PS_KEY_REPEAT, PS_REPEAT_DEFAULT);
        s->repeat = ps_repeat_ok(v) ? v : PS_REPEAT_DEFAULT;
    }
    if (caps & PS_CAP_FOLLOWD) {
        v = st->get(st->ctx, PS_SEC_XY, PS_KEY_FOLLOWD, 0);
        s->followDlg = (v == 0 || v == 1) ? v : 0;
    }
    /* The mode is never loaded: it stays at software. */
}

int PanSetSave(const PANCAPS *c, const PANSET *s, const PANSTORE *st)
{
    int code;

    code = PanSetValidate(c, s);
    if (code != PS_OK) {
        return code;
    }
    if (st == PS_NULL || st->put == PS_NULL) {
        return PS_E_STORE;
    }
    if (c->caps & PS_CAP_STEP) {
        if (!st->put(st->ctx, PS_SEC_VERT, PS_KEY_STEP, s->step)) {
            return PS_E_STORE;
        }
    }
    if (c->caps & PS_CAP_DWELL) {
        if (!st->put(st->ctx, PS_SEC_VERT, PS_KEY_DWELL, s->dwell)) {
            return PS_E_STORE;
        }
    }
    if (c->caps & PS_CAP_EDGE) {
        if (!st->put(st->ctx, PS_SEC_VERT, PS_KEY_EDGE, s->edge)) {
            return PS_E_STORE;
        }
    }
    if (c->caps & PS_CAP_FOLLOW) {
        if (!st->put(st->ctx, PS_SEC_VERT, PS_KEY_FOLLOW, s->follow)) {
            return PS_E_STORE;
        }
    }
    if (c->caps & PS_CAP_EDGEON) {
        if (!st->put(st->ctx, PS_SEC_XY, PS_KEY_EDGEON, s->edgeOn)) {
            return PS_E_STORE;
        }
    }
    if (c->caps & PS_CAP_REPEAT) {
        if (!st->put(st->ctx, PS_SEC_XY, PS_KEY_REPEAT, s->repeat)) {
            return PS_E_STORE;
        }
    }
    if (c->caps & PS_CAP_FOLLOWD) {
        if (!st->put(st->ctx, PS_SEC_XY, PS_KEY_FOLLOWD, s->followDlg)) {
            return PS_E_STORE;
        }
    }
    return PS_OK;
}

int PanModelOpen(PANMODEL *m, const PANHOSTOPS *ops)
{
    if (m == PS_NULL || ops == PS_NULL || ops->query == PS_NULL) {
        return PS_E_LOST;
    }
    if (!ops->query(ops->ctx, &m->caps, &m->live)) {
        m->caps.backend = PS_BACK_NONE;
        ps_copy_status(m->status, "Driver unavailable");
        return PS_E_LOST;
    }
    m->work = m->live;
    m->differs = 0;
    ps_copy_status(m->status, "Ready.");
    return PS_OK;
}

void PanModelCancel(PANMODEL *m)
{
    if (m == PS_NULL) {
        return;
    }
    m->work = m->live;
    m->differs = 0;
    ps_copy_status(m->status, "Unchanged.");
}

int PanModelApply(PANMODEL *m, const PANHOSTOPS *ops, const PANSTORE *st)
{
    int code;
    PANSET request;
    PANSET actual;
    char note[PS_NOTE_CAP];

    if (m == PS_NULL || ops == PS_NULL || ops->apply == PS_NULL) {
        return PS_E_LOST;
    }
    code = PanSetValidate(&m->caps, &m->work);
    if (code != PS_OK) {
        ps_copy_status(m->status, PanSetErrorText(code));
        return code;
    }

    request = m->work;
    actual = m->work;
    note[0] = '\0';
    code = ops->apply(ops->ctx, &request, &actual, note, PS_NOTE_CAP);
    note[PS_NOTE_CAP - 1] = '\0';
    if (code != PS_OK) {
        if (code == PS_E_LOST) {
            m->caps.backend = PS_BACK_NONE;
        }
        ps_copy_status(m->status, PanSetErrorText(code));
        return code;
    }

    m->live = actual;
    m->work = actual;
    m->differs = ps_differs(m->caps.caps, &actual, &request);

    if (PanSetSave(&m->caps, &actual, st) != PS_OK) {
        ps_copy_status(m->status,
                       "Applied but could not be saved to WIN.INI.");
        return PS_E_STORE;
    }
    if (m->differs && note[0] != '\0') {
        ps_copy_status(m->status, note);
    } else {
        ps_copy_status(m->status, "Applied and saved.");
    }
    return PS_OK;
}

int PanModelHome(PANMODEL *m, const PANHOSTOPS *ops)
{
    PANCAPS caps;
    PANSET live;

    if (m == PS_NULL || ops == PS_NULL || ops->home == PS_NULL ||
        ops->query == PS_NULL) {
        return PS_E_LOST;
    }
    if (!ops->home(ops->ctx)) {
        ps_copy_status(m->status, "Home failed.");
        return PS_E_APPLY;
    }
    if (!ops->query(ops->ctx, &caps, &live)) {
        m->caps.backend = PS_BACK_NONE;
        ps_copy_status(m->status, "Driver unavailable");
        return PS_E_LOST;
    }
    m->caps = caps;
    m->live = live;
    ps_copy_status(m->status, "At home.");
    return PS_OK;
}

int PanCmdParse(const char *cmd)
{
    if (cmd == PS_NULL) {
        return PS_CMD_ENABLE;
    }
    if (ps_word_nocase(cmd, "OFF")) {
        return PS_CMD_OFF;
    }
    if (ps_word_nocase(cmd, "SETTINGS") ||
        ps_word_nocase(cmd, PS_ARG_SETTINGS)) {
        return PS_CMD_SETTINGS;
    }
    return PS_CMD_ENABLE;
}

int PanRoute(int ownerRunning, int enabled)
{
    if (ownerRunning) {
        return PS_ROUTE_POST;
    }
    if (enabled) {
        return PS_ROUTE_START;
    }
    return PS_ROUTE_OFF;
}

int PanOwnerStart(int otherRunning, int settingsRequested)
{
    if (!otherRunning) {
        return PS_OWN_RUN;
    }
    if (settingsRequested) {
        return PS_OWN_FORWARD;
    }
    return PS_OWN_EXIT;
}
