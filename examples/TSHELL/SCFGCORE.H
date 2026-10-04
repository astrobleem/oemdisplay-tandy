#ifndef SCFGCORE_H
#define SCFGCORE_H
#define SC_KEYS 8
#define SC_VALUE 128
#define SC_ENABLED 0
#define SC_SECONDS 1
#define SC_CHOICE 2
#define SC_MATRIXPATH 3
#define SC_MAZEPATH 4
#define SC_STARPATH 5
#define SC_SPEED 6
#define SC_STARS 7
#define SC_NONE 0
#define SC_MATRIX 1
#define SC_MAZE 2
#define SC_STARFIELD 3
#define SC_OK 0
#define SC_READFAIL 1
#define SC_BADSECONDS 2
#define SC_BADCHOICE 3
#define SC_CONFLICT 4
#define SC_WRITEFAIL 5
#define SC_UNCERTAIN 6
#define SC_BADOPTIONS 7
typedef struct { int present[SC_KEYS]; char value[SC_KEYS][SC_VALUE]; } SCCONFIG;
/* read: -1 failure/truncation, 0 missing, 1 present. write NULL deletes key. */
typedef struct {
    int (*read)(void *, int, char *, int);
    int (*write)(void *, int, const char *);
    void *context;
} SCIO;
int ScRead(SCIO *io, SCCONFIG *config);
const char *ScValue(const SCCONFIG *config, int key);
int ScEnabled(const SCCONFIG *config);
int ScSeconds(const char *text);
int ScSpeed(const char *text);
int ScStars(const char *text);
int ScChoice(const SCCONFIG *config);
int ScAbsolute(const char *path);
int ScCommand(const char *path, int speed, int stars, char *out, int capacity);
const char *ScProgram(const SCCONFIG *config, int choice);
int ScSave(SCIO *io, const SCCONFIG *before, const char *seconds,
           int choice, SCCONFIG *after);
int ScSaveOptions(SCIO *io, const SCCONFIG *before, const char *seconds,
                  int choice, const char *speed, const char *stars, SCCONFIG *after);
#endif
