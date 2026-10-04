/* Portable configuration validation and checked, rollback-capable writes. */
#include <string.h>
#include "SCFGCORE.H"
static const char *defaults[SC_KEYS] = {
    "0", "300", "Matrix", "C:\\TSTART\\MATRIX.EXE", "C:\\TSTART\\MAZE.EXE",
    "C:\\TSTART\\STARFLD.EXE", "2", "32"
};
static int equalcase(const char *a, const char *b)
{
    int aa, bb;
    do {
        aa = *a++; bb = *b++;
        if (aa >= 'a' && aa <= 'z') aa -= 'a' - 'A';
        if (bb >= 'a' && bb <= 'z') bb -= 'a' - 'A';
        if (aa != bb) return 0;
    } while (aa);
    return 1;
}
int ScRead(SCIO *io, SCCONFIG *c)
{
    int i, result;
    memset(c, 0, sizeof(*c));
    for (i = 0; i < SC_KEYS; ++i) {
        result = io->read(io->context, i, c->value[i], SC_VALUE);
        if (result < 0) return SC_READFAIL;
        c->present[i] = result != 0;
    }
    return SC_OK;
}
const char *ScValue(const SCCONFIG *c, int key)
{ return c->present[key] ? c->value[key] : defaults[key]; }
int ScEnabled(const SCCONFIG *c)
{
    const char *s = ScValue(c, SC_ENABLED);
    int nonzero = 0;
    /* Keep the prior GetPrivateProfileInt decimal-prefix behavior. */
    while (*s == ' ' || *s == '\t') ++s;
    if (*s == '-' || *s == '+') ++s;
    while (*s >= '0' && *s <= '9') { if (*s != '0') nonzero = 1; ++s; }
    return nonzero;
}
int ScSeconds(const char *s)
{
    int n = 0, i = 0;
    while (s[i] >= '0' && s[i] <= '9') {
        if (i == 4) return 0;
        n = n * 10 + s[i++] - '0';
    }
    return !s[i] && n >= 10 && n <= 3600 ? n : 0;
}
int ScChoice(const SCCONFIG *c)
{
    const char *s = ScValue(c, SC_CHOICE);
    if (equalcase(s, "Matrix")) return SC_MATRIX;
    if (equalcase(s, "Maze")) return SC_MAZE;
    if (equalcase(s, "Starfield")) return SC_STARFIELD;
    return -1;
}
int ScSpeed(const char *s)
{ return s[0] >= '1' && s[0] <= '3' && !s[1] ? s[0] - '0' : 0; }
int ScStars(const char *s)
{
    if (!strcmp(s, "16")) return 16;
    if (!strcmp(s, "32")) return 32;
    if (!strcmp(s, "64")) return 64;
    return 0;
}
int ScAbsolute(const char *s)
{
    int i, n = strlen(s);
    if (n < 4 || n > 122 || s[1] != ':' || s[2] != '\\') return 0;
    if (!((s[0] >= 'A' && s[0] <= 'Z') || (s[0] >= 'a' && s[0] <= 'z'))) return 0;
    for (i = 0; i < n; ++i)
        if ((unsigned char)s[i] < 33 || s[i] == '"' || s[i] == '/' ||
            s[i] == '*' || s[i] == '?' || (s[i] == ':' && i != 1)) return 0;
    return s[n - 1] != '\\';
}
const char *ScProgram(const SCCONFIG *c, int choice)
{ return ScValue(c, choice == SC_STARFIELD ? SC_STARPATH :
                 choice == SC_MAZE ? SC_MAZEPATH : SC_MATRIXPATH); }
int ScCommand(const char *path, int speed, int stars, char *out, int capacity)
{
    char tail[16];
    int length;
    if (!ScAbsolute(path)) return 0;
    if (!speed && !stars) strcpy(tail, " /S");
    else {
        if (speed < 1 || speed > 3 || (stars != 16 && stars != 32 && stars != 64)) return 0;
        strcpy(tail, " /S /V2 /N32");
        tail[6] = (char)('0' + speed); tail[10] = (char)('0' + stars / 10);
        tail[11] = (char)('0' + stars % 10);
    }
    length = strlen(path) + strlen(tail);
    if (length > 126 || length >= capacity) return 0;
    strcpy(out, path); strcat(out, tail); return 1;
}
static int same(const SCCONFIG *a, const SCCONFIG *b)
{
    int i;
    for (i = 0; i < SC_KEYS; ++i)
        if (a->present[i] != b->present[i] ||
            (a->present[i] && strcmp(a->value[i], b->value[i]))) return 0;
    return 1;
}
int ScSave(SCIO *io, const SCCONFIG *before, const char *seconds,
           int choice, SCCONFIG *after)
{ return ScSaveOptions(io, before, seconds, choice, 0, 0, after); }
int ScSaveOptions(SCIO *io, const SCCONFIG *before, const char *seconds,
                  int choice, const char *speed, const char *stars, SCCONFIG *after)
{
    SCCONFIG *want = after, actual;
    int i, last = -1, failed = 0, changed[SC_KEYS];
    if (!ScSeconds(seconds)) return SC_BADSECONDS;
    if (choice != SC_NONE && choice != SC_MATRIX && choice != SC_MAZE &&
        choice != SC_STARFIELD) return SC_BADCHOICE;
    if ((speed || stars) && (!speed || !stars || !ScSpeed(speed) || !ScStars(stars))) return SC_BADOPTIONS;
    if (ScRead(io, &actual) != SC_OK) return SC_READFAIL;
    if (!same(before, &actual)) return SC_CONFLICT;
    /* Reuse the caller's result buffer to keep the Win16 stack bounded. */
    *want = *before;
    want->present[SC_ENABLED] = want->present[SC_SECONDS] = 1;
    strcpy(want->value[SC_ENABLED], choice == SC_NONE ? "0" : "1");
    strcpy(want->value[SC_SECONDS], seconds);
    if (choice != SC_NONE) {
        want->present[SC_CHOICE] = 1;
        strcpy(want->value[SC_CHOICE], choice == SC_STARFIELD ? "Starfield" :
               choice == SC_MAZE ? "Maze" : "Matrix");
    }
    if (speed) {
        want->present[SC_SPEED] = want->present[SC_STARS] = 1;
        strcpy(want->value[SC_SPEED], speed); strcpy(want->value[SC_STARS], stars);
    }
    for (i = 0; i < SC_KEYS; ++i) {
        changed[i] = want->present[i] != before->present[i] ||
            (want->present[i] && strcmp(want->value[i], before->value[i]));
        if (!changed[i]) continue;
        last = i;
        if (!io->write(io->context, i, want->present[i] ? want->value[i] : 0)) {
            failed = 1; break;
        }
    }
    if (!failed && ScRead(io, &actual) == SC_OK && same(want, &actual)) {
        *after = actual; return SC_OK;
    }
    /* A failed setter may still have changed its key. Restore it as well. */
    for (i = 0; i <= last; ++i)
        if (changed[i]) io->write(io->context, i,
            before->present[i] ? before->value[i] : 0);
    /* Read-only files can reject both write and rollback yet remain exact. */
    return ScRead(io, &actual) == SC_OK && same(before, &actual) ? SC_WRITEFAIL : SC_UNCERTAIN;
}
