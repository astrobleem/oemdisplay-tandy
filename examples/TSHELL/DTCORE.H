#ifndef DTCORE_H
#define DTCORE_H

/* Pure 16-bit C calendar/apply core. No host or DOS clock calls here. */
typedef struct {
    int year, month, day, hour, minute, second;
} DTVALUE;

typedef struct {
    int (*read)(void *, DTVALUE *);
    int (*setdate)(void *, const DTVALUE *);
    int (*settime)(void *, const DTVALUE *);
    void *context;
} DTIO;

#define DT_DATE 1
#define DT_TIME 2
#define DT_NOCHANGE 0
#define DT_OK 1
#define DT_BADDATE 2
#define DT_BADTIME 3
#define DT_READFAIL 4
#define DT_DATEFAIL 5
#define DT_TIMEFAIL 6
#define DT_VERIFYFAIL 7
#define DT_READBACKFAIL 8

typedef struct {
    int code, requested, written, readback;
    DTVALUE actual;
} DTRESULT;

int DtDate(const char *text, DTVALUE *value);
int DtTime(const char *text, DTVALUE *value);
int DtValid(const DTVALUE *value);
void DtFormat(const DTVALUE *value, char *date, char *time);
void DtApply(const char *date, const char *time,
             const char *loadedDate, const char *loadedTime,
             const DTIO *io, DTRESULT *result);

#endif
