/* SETTEST.C - host tests for PANSET.C, run by HOSTUI.PY.
 *
 * Prints "NAME value" lines, and "TEXT NAME rest" for strings. HOSTUI.PY owns
 * every expectation; this file only measures. It supplies a fake WIN.INI
 * (PANSTORE) and a fake owner engine (PANHOSTOPS). C89.
 */
#include <stdio.h>
#include <string.h>
#include "PANSET.H"

#define LOGMAX 1024
#define MAXTAB 16
#define NOVAL (-12345)
#define NCMD 13
#define NERR 14

typedef struct {
    char sec[16];
    char key[16];
    int val;
} ENTRY;

static ENTRY tab[MAXTAB];
static int ntab;
static int getCalls;
static int putCalls;
static int failPut;                 /* 1-based put that fails, 0 = none */
static char getLog[LOGMAX];
static char putLog[LOGMAX];

static void R(const char *name, int v)
{
    printf("%s %d\n", name, v);
}

static void T(const char *name, const char *s)
{
    printf("TEXT %s %s\n", name, s);
}

static void Note(char *log, const char *sec, const char *key)
{
    if (strlen(log) + strlen(sec) + strlen(key) + 3 < LOGMAX) {
        strcat(log, sec);
        strcat(log, ".");
        strcat(log, key);
        strcat(log, " ");
    }
}

static int FindEntry(const char *sec, const char *key)
{
    int i;
    for (i = 0; i < ntab; i++)
        if (strcmp(tab[i].sec, sec) == 0 && strcmp(tab[i].key, key) == 0)
            return i;
    return -1;
}

static void StoreReset(void)
{
    ntab = 0;
    getCalls = 0;
    putCalls = 0;
    failPut = 0;
    getLog[0] = '\0';
    putLog[0] = '\0';
}

static void StoreSet(const char *sec, const char *key, int val)
{
    int i = FindEntry(sec, key);
    if (i < 0) {
        i = ntab++;
        strcpy(tab[i].sec, sec);
        strcpy(tab[i].key, key);
    }
    tab[i].val = val;
}

static int StoreVal(const char *sec, const char *key)
{
    int i = FindEntry(sec, key);
    return i < 0 ? NOVAL : tab[i].val;
}

static int FGet(void *ctx, const char *sec, const char *key, int def)
{
    int i;
    (void)ctx;
    getCalls++;
    Note(getLog, sec, key);
    i = FindEntry(sec, key);
    return i < 0 ? def : tab[i].val;
}

static int FPut(void *ctx, const char *sec, const char *key, int val)
{
    (void)ctx;
    putCalls++;
    Note(putLog, sec, key);
    if (putCalls == failPut)
        return 0;
    StoreSet(sec, key, val);
    return 1;
}

static PANSTORE store = { NULL, FGet, FPut };

/* Fake owner engine. The "driver" state is what FQuery reports. */
static int drvBackend;
static int drvReadback;
static int drvLost;          /* query and home stop answering */
static int drvViewX;
static int drvApplyRet;      /* PS_OK, or the code apply returns */
static int drvRefuse;        /* XY: hardware refuses mode 1 */
static int drvHomeOK;
static PANSET drvLive;
static int qCalls, aCalls, hCalls;
static int putsAtApply;
static PANSET lastWant;

static int FQuery(void *ctx, PANCAPS *c, PANSET *live)
{
    (void)ctx;
    qCalls++;
    memset(c, 0, sizeof(*c));
    if (drvLost) {
        c->backend = PS_BACK_NONE;
        return 0;
    }
    c->backend = drvBackend;
    c->caps = PanCapsFor(drvBackend, drvReadback);
    c->viewX = drvViewX;
    c->viewY = 0;
    c->viewW = 320;
    c->viewH = 200;
    c->workW = 640;
    c->workH = 400;
    *live = drvLive;
    return 1;
}

static int FApply(void *ctx, const PANSET *want, PANSET *actual,
                  char *note, int noteCap)
{
    const char *txt = "HW REFUSED";
    int i = 0;
    (void)ctx;
    aCalls++;
    if (aCalls == 1)
        putsAtApply = putCalls;
    lastWant = *want;
    if (drvApplyRet != PS_OK)
        return drvApplyRet;
    *actual = *want;
    if (drvRefuse && drvBackend == PS_BACK_XY && want->mode == 1) {
        actual->mode = 0;
        while (txt[i] && i < noteCap - 1) {
            note[i] = txt[i];
            i++;
        }
        note[i] = '\0';
    }
    drvLive = *actual;
    return PS_OK;
}

static int FHome(void *ctx)
{
    (void)ctx;
    hCalls++;
    if (!drvHomeOK)
        return 0;
    drvViewX = 0;
    return 1;
}

static PANHOSTOPS ops = { NULL, FQuery, FApply, FHome };

static PANSET Full(void)
{
    PANSET s, x;
    memset(&s, 0, sizeof(s));
    memset(&x, 0, sizeof(x));
    PanSetDefaults(PS_BACK_VERT, &s);
    PanSetDefaults(PS_BACK_XY, &x);
    s.edgeOn = x.edgeOn;
    s.repeat = x.repeat;
    s.followDlg = x.followDlg;
    s.mode = x.mode;
    return s;
}

static PANCAPS CapsOf(int backend, int readback)
{
    PANCAPS c;
    memset(&c, 0, sizeof(c));
    c.backend = backend;
    c.caps = PanCapsFor(backend, readback);
    c.viewW = 320;
    c.viewH = 200;
    c.workW = 640;
    c.workH = 400;
    return c;
}

static void DrvReset(int backend, int readback)
{
    drvBackend = backend;
    drvReadback = readback;
    drvLost = 0;
    drvViewX = 0;
    drvApplyRet = PS_OK;
    drvRefuse = 0;
    drvHomeOK = 1;
    drvLive = Full();
    qCalls = 0;
    aCalls = 0;
    hCalls = 0;
    putsAtApply = -1;
    memset(&lastWant, 0, sizeof(lastWant));
}

static void Scenario(int backend, int readback, const PANSET *live,
                     PANMODEL *m)
{
    DrvReset(backend, readback);
    drvLive = *live;
    StoreReset();
    memset(m, 0, sizeof(*m));
    PanModelOpen(m, &ops);
}

static int Same(const PANSET *a, const PANSET *b)
{
    return memcmp(a, b, sizeof(PANSET)) == 0;
}

/* ---- sections ---- */

static void DefaultsTests(void)
{
    PANSET s;
    memset(&s, 0, sizeof(s));
    PanSetDefaults(PS_BACK_VERT, &s);
    R("def.v.step", s.step);
    R("def.v.dwell", s.dwell);
    R("def.v.edge", s.edge);
    R("def.v.follow", s.follow);
    memset(&s, 0, sizeof(s));
    PanSetDefaults(PS_BACK_XY, &s);
    R("def.x.edgeOn", s.edgeOn);
    R("def.x.repeat", s.repeat);
    R("def.x.followDlg", s.followDlg);
    R("def.x.mode", s.mode);
}

static void EmptyLoadTests(void)
{
    PANCAPS cv = CapsOf(PS_BACK_VERT, 1), cx = CapsOf(PS_BACK_XY, 1);
    PANSET s;
    StoreReset();
    memset(&s, 0, sizeof(s));
    PanSetLoad(&cv, &s, &store);
    R("load.empty.v.step", s.step);
    R("load.empty.v.dwell", s.dwell);
    R("load.empty.v.edge", s.edge);
    R("load.empty.v.follow", s.follow);
    memset(&s, 0, sizeof(s));
    PanSetLoad(&cx, &s, &store);
    R("load.empty.x.edgeOn", s.edgeOn);
    R("load.empty.x.repeat", s.repeat);
    R("load.empty.x.followDlg", s.followDlg);
    R("load.empty.x.mode", s.mode);
}

static void ValidateTests(void)
{
    PANCAPS cv = CapsOf(PS_BACK_VERT, 1), cx = CapsOf(PS_BACK_XY, 1);
    PANSET s;

    s = Full(); s.step = 8;
    R("val.v.step8", PanSetValidate(&cv, &s));
    s.step = 7;
    R("val.v.step7", PanSetValidate(&cv, &s));
    s.step = 400;
    R("val.v.step400", PanSetValidate(&cv, &s));
    s.step = 401;
    R("val.v.step401", PanSetValidate(&cv, &s));
    s.step = 57;
    R("val.v.step57", PanSetValidate(&cv, &s));

    s = Full(); s.edge = 1;
    R("val.v.edge1", PanSetValidate(&cv, &s));
    s.edge = 0;
    R("val.v.edge0", PanSetValidate(&cv, &s));
    s.edge = 100;
    R("val.v.edge100", PanSetValidate(&cv, &s));
    s.edge = 101;
    R("val.v.edge101", PanSetValidate(&cv, &s));

    s = Full(); s.dwell = 0;
    R("val.v.dwell0", PanSetValidate(&cv, &s));
    s.dwell = 10000;
    R("val.v.dwell10000", PanSetValidate(&cv, &s));
    s.dwell = 10001;
    R("val.v.dwell10001", PanSetValidate(&cv, &s));
    s.dwell = -1;
    R("val.v.dwellm1", PanSetValidate(&cv, &s));

    s = Full(); s.follow = 2;
    R("val.v.follow2", PanSetValidate(&cv, &s));
    s.follow = 0;
    R("val.v.follow0", PanSetValidate(&cv, &s));

    s = Full(); s.repeat = 100;
    R("val.x.repeat100", PanSetValidate(&cx, &s));
    s.repeat = 200;
    R("val.x.repeat200", PanSetValidate(&cx, &s));
    s.repeat = 500;
    R("val.x.repeat500", PanSetValidate(&cx, &s));
    s.repeat = 150;
    R("val.x.repeat150", PanSetValidate(&cx, &s));
    s.repeat = 0;
    R("val.x.repeat0", PanSetValidate(&cx, &s));
    s.repeat = 1000;
    R("val.x.repeat1000", PanSetValidate(&cx, &s));

    s = Full(); s.edgeOn = 0;
    R("val.x.edgeOn0", PanSetValidate(&cx, &s));
    s.edgeOn = 1;
    R("val.x.edgeOn1", PanSetValidate(&cx, &s));
    s.edgeOn = 2;
    R("val.x.edgeOn2", PanSetValidate(&cx, &s));

    s = Full(); s.followDlg = 0;
    R("val.x.followDlg0", PanSetValidate(&cx, &s));
    s.followDlg = 1;
    R("val.x.followDlg1", PanSetValidate(&cx, &s));
    s.followDlg = 2;
    R("val.x.followDlg2", PanSetValidate(&cx, &s));

    s = Full(); s.mode = 0;
    R("val.x.mode0", PanSetValidate(&cx, &s));
    s.mode = 1;
    R("val.x.mode1", PanSetValidate(&cx, &s));
    s.mode = 2;
    R("val.x.mode2", PanSetValidate(&cx, &s));
    s.mode = -1;
    R("val.x.modem1", PanSetValidate(&cx, &s));
    s.mode = 3;
    R("val.x.mode3", PanSetValidate(&cx, &s));
    s.mode = 255;
    R("val.x.mode255", PanSetValidate(&cx, &s));
}

static void ParseTests(void)
{
    static const char *in[] = { "12", "  7 ", "", " ", "1x", "-5", "+5",
                                "123456", "1 2", "12345" };
    char name[32];
    int i, rc, v;
    for (i = 0; i < 10; i++) {
        v = 999;
        rc = PanParseInt(in[i], &v);
        sprintf(name, "pi%d.rc", i);
        R(name, rc);
        sprintf(name, "pi%d.val", i);
        R(name, v);
    }
}

static void GateTests(void)
{
    PANCAPS cv = CapsOf(PS_BACK_VERT, 1), cx = CapsOf(PS_BACK_XY, 1);
    PANCAPS cx0 = CapsOf(PS_BACK_XY, 0), cv0 = CapsOf(PS_BACK_VERT, 0);
    PANCAPS cn = CapsOf(PS_BACK_NONE, 1), cz = CapsOf(PS_BACK_VERT, 1);
    PANSET s;

    cn.caps = 0;
    cz.caps = 0;

    /* VERT caps: XY fields are garbage, must be ignored everywhere. */
    s = Full();
    s.edgeOn = 5; s.repeat = 150; s.followDlg = 7; s.mode = 2;
    R("gate.v.validate", PanSetValidate(&cv, &s));
    StoreReset();
    R("gate.v.save", PanSetSave(&cv, &s, &store));
    R("gate.v.puts", putCalls);
    T("gate.v.log", putLog);

    /* XY caps: vertical fields are garbage. */
    s = Full();
    s.step = 3; s.edge = 0; s.dwell = -1; s.follow = 7;
    R("gate.x.validate", PanSetValidate(&cx, &s));
    StoreReset();
    R("gate.x.save", PanSetSave(&cx, &s, &store));
    R("gate.x.puts", putCalls);
    T("gate.x.log", putLog);

    /* No backend, and a backend with no capabilities. */
    s = Full();
    R("gate.none.validate", PanSetValidate(&cn, &s));
    StoreReset();
    R("gate.none.save", PanSetSave(&cn, &s, &store));
    StoreReset();
    R("gate.zero.save", PanSetSave(&cz, &s, &store));

    /* XY without a readable mode: mode is neither offered nor saved. */
    R("gate.x0.hasMode", (cx0.caps & PS_CAP_MODE) != 0);
    s = Full();
    s.mode = 1;
    R("gate.x0.validateMode1", PanSetValidate(&cx0, &s));
    s.mode = 2;
    R("gate.x0.validateMode2", PanSetValidate(&cx0, &s));
    s.mode = 1;
    StoreReset();
    R("gate.x0.save", PanSetSave(&cx0, &s, &store));
    R("gate.x0.puts", putCalls);
    T("gate.x0.log", putLog);
    R("gate.x1.hasMode", (cx.caps & PS_CAP_MODE) != 0);

    /* Capability masks. */
    R("gate.v.badcaps", cv.caps & (PS_CAP_MODE | PS_CAP_EDGEON |
                                   PS_CAP_REPEAT | PS_CAP_FOLLOWD));
    R("gate.v0.badcaps", cv0.caps & (PS_CAP_MODE | PS_CAP_EDGEON |
                                     PS_CAP_REPEAT | PS_CAP_FOLLOWD));
    R("gate.v.goodcaps", cv.caps & (PS_CAP_STEP | PS_CAP_EDGE |
                                    PS_CAP_DWELL | PS_CAP_FOLLOW));
    R("gate.x.badcaps", cx.caps & (PS_CAP_STEP | PS_CAP_EDGE |
                                   PS_CAP_DWELL | PS_CAP_FOLLOW));
    R("gate.x.goodcaps", cx.caps & (PS_CAP_EDGEON | PS_CAP_REPEAT |
                                    PS_CAP_FOLLOWD));
    R("gate.x0.goodcaps", cx0.caps & (PS_CAP_EDGEON | PS_CAP_REPEAT |
                                      PS_CAP_FOLLOWD));
}

static void PersistTests(void)
{
    PANCAPS cv = CapsOf(PS_BACK_VERT, 1), cx = CapsOf(PS_BACK_XY, 1);
    PANSET s, t;

    s = Full();
    s.step = 120; s.dwell = 700; s.edge = 5; s.follow = 0;
    StoreReset();
    R("rt.v.save", PanSetSave(&cv, &s, &store));
    R("rt.v.puts", putCalls);
    T("rt.v.log", putLog);
    t = Full();
    t.step = 0; t.dwell = 0; t.edge = 0; t.follow = 0;
    PanSetLoad(&cv, &t, &store);
    R("rt.v.step", t.step);
    R("rt.v.dwell", t.dwell);
    R("rt.v.edge", t.edge);
    R("rt.v.follow", t.follow);

    s = Full();
    s.edgeOn = 1; s.repeat = 200; s.followDlg = 1; s.mode = 1;
    StoreReset();
    R("rt.x.save", PanSetSave(&cx, &s, &store));
    R("rt.x.puts", putCalls);
    T("rt.x.log", putLog);
    t = Full();
    t.edgeOn = 0; t.repeat = 100; t.followDlg = 0; t.mode = 0;
    PanSetLoad(&cx, &t, &store);
    R("rt.x.edgeOn", t.edgeOn);
    R("rt.x.repeat", t.repeat);
    R("rt.x.followDlg", t.followDlg);
    R("rt.x.mode", t.mode);

    s = Full();
    s.step = 7;
    StoreReset();
    R("save.invalid.rc", PanSetSave(&cv, &s, &store));
    R("save.invalid.puts", putCalls);

    s = Full();
    StoreReset();
    failPut = 2;
    R("save.fail.rc", PanSetSave(&cv, &s, &store));
    R("save.fail.puts", putCalls);

    StoreReset();
    StoreSet("XTPan", "Step", 3);
    StoreSet("XTPan", "Edge", 0);
    StoreSet("XTPan", "FollowActive", 7);
    t = Full();
    PanSetLoad(&cv, &t, &store);
    R("clamp.v.step", t.step);
    R("clamp.v.edge", t.edge);
    R("clamp.v.follow", t.follow);

    StoreReset();
    StoreSet("XYPan", "RepeatMs", 150);
    StoreSet("XYPan", "EdgeOn", 5);
    StoreSet("XYPan", "Mode", 1);
    t = Full();
    t.mode = 0;
    PanSetLoad(&cx, &t, &store);
    R("clamp.x.repeat", t.repeat);
    R("clamp.x.edgeOn", t.edgeOn);
    R("load.x.mode", t.mode);
    T("load.x.getlog", getLog);
}

static void ModelTests(void)
{
    PANMODEL m;
    PANSET live, before;
    PANSET xy;
    int rc, q0;

    live = Full();
    live.step = 120;

    Scenario(PS_BACK_VERT, 1, &live, &m);
    R("open.workEqLive", Same(&m.work, &m.live));
    m.work.step = 200;
    PanModelCancel(&m);
    R("cancel.workEqLive", Same(&m.work, &m.live));
    R("cancel.apply", aCalls);
    R("cancel.puts", putCalls);

    Scenario(PS_BACK_VERT, 1, &live, &m);
    before = m.live;
    m.work.step = 7;
    rc = PanModelApply(&m, &ops, &store);
    R("apply.invalid.rc", rc);
    R("apply.invalid.apply", aCalls);
    R("apply.invalid.puts", putCalls);
    R("apply.invalid.liveSame", Same(&m.live, &before));
    R("apply.invalid.statusSet", m.status[0] != '\0');
    T("apply.invalid.status", m.status);

    Scenario(PS_BACK_VERT, 1, &live, &m);
    drvApplyRet = PS_E_APPLY;
    before = m.live;
    m.work.step = 100;
    rc = PanModelApply(&m, &ops, &store);
    R("apply.enginefail.rc", rc);
    R("apply.enginefail.puts", putCalls);
    R("apply.enginefail.liveSame", Same(&m.live, &before));

    Scenario(PS_BACK_VERT, 1, &live, &m);
    drvApplyRet = PS_E_LOST;
    before = m.live;
    m.work.step = 100;
    rc = PanModelApply(&m, &ops, &store);
    R("apply.lost.rc", rc);
    R("apply.lost.backend", m.caps.backend);
    R("apply.lost.puts", putCalls);
    R("apply.lost.liveSame", Same(&m.live, &before));

    Scenario(PS_BACK_VERT, 1, &live, &m);
    m.work.step = 120;
    m.work.dwell = 500;
    m.work.edge = 4;
    m.work.follow = 0;
    rc = PanModelApply(&m, &ops, &store);
    R("apply.ok.rc", rc);
    R("apply.ok.calls", aCalls);
    R("apply.ok.wantIsWork", Same(&lastWant, &m.work));
    R("apply.ok.putsAtApply", putsAtApply);
    R("apply.ok.puts", putCalls);
    R("apply.ok.liveEqActual", Same(&m.live, &drvLive));
    R("apply.ok.liveStep", m.live.step);
    R("apply.ok.differs", m.differs);
    R("apply.ok.storeStep", StoreVal("XTPan", "Step"));
    R("apply.ok.storeDwell", StoreVal("XTPan", "Dwell"));
    R("apply.ok.storeEdge", StoreVal("XTPan", "Edge"));
    R("apply.ok.storeFollow", StoreVal("XTPan", "FollowActive"));
    T("apply.ok.status", m.status);

    Scenario(PS_BACK_VERT, 1, &live, &m);
    m.work.step = 90;
    failPut = 1;
    rc = PanModelApply(&m, &ops, &store);
    R("apply.savefail.rc", rc);
    R("apply.savefail.liveStep", m.live.step);
    R("apply.savefail.drvStep", drvLive.step);

    xy = Full();
    Scenario(PS_BACK_XY, 1, &xy, &m);
    drvRefuse = 1;
    m.work.mode = 1;
    m.work.edgeOn = 1;
    rc = PanModelApply(&m, &ops, &store);
    R("hw.refused.rc", rc);
    R("hw.refused.differs", m.differs);
    R("hw.refused.liveMode", m.live.mode);
    R("hw.refused.wantMode", lastWant.mode);
    R("hw.refused.puts", putCalls);
    T("hw.refused.status", m.status);
    T("hw.refused.log", putLog);

    Scenario(PS_BACK_XY, 1, &xy, &m);
    m.work.mode = 1;
    rc = PanModelApply(&m, &ops, &store);
    R("hw.granted.rc", rc);
    R("hw.granted.differs", m.differs);
    R("hw.granted.liveMode", m.live.mode);

    Scenario(PS_BACK_VERT, 1, &live, &m);
    m.caps.viewX = 55;
    drvViewX = 200;
    m.work.step = 77;
    q0 = qCalls;
    hCalls = 0;
    rc = PanModelHome(&m, &ops);
    R("home.rc", rc);
    R("home.calls", hCalls);
    R("home.queryDelta", qCalls - q0);
    R("home.viewX", m.caps.viewX);
    R("home.workKept", m.work.step == 77);

    Scenario(PS_BACK_VERT, 1, &live, &m);
    drvHomeOK = 0;
    rc = PanModelHome(&m, &ops);
    R("home.fail.rc", rc);
}

static void RouteTests(void)
{
    static const char *cmds[NCMD] = { "", NULL, "OFF", "off", "Off",
        "SETTINGS", "settings", "/SETTINGS", "/settings", " OFF", "OFFX",
        "x", "SETTINGS now" };
    char name[32];
    int i, r, e;
    for (i = 0; i < NCMD; i++) {
        sprintf(name, "cmd.%d", i);
        R(name, PanCmdParse(cmds[i]));
    }
    for (r = 0; r < 2; r++)
        for (e = 0; e < 2; e++) {
            sprintf(name, "route.%d%d", r, e);
            R(name, PanRoute(r, e));
            sprintf(name, "own.%d%d", r, e);
            R(name, PanOwnerStart(r, e));
        }
    for (i = 0; i < NERR; i++) {
        const char *t = PanSetErrorText(i);
        sprintf(name, "errtext.%d", i);
        R(name, t != NULL && t[0] != '\0');
    }
}

int main(void)
{
    DefaultsTests();
    EmptyLoadTests();
    ValidateTests();
    ParseTests();
    GateTests();
    PersistTests();
    ModelTests();
    RouteTests();
    return 0;
}
