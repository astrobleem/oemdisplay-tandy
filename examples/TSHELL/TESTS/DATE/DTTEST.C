/* Host tests: fake clock only. Never links TSDATE.C or calls a clock setter. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "DTCORE.H"

static unsigned long checks;
#define CHECK(c) do { ++checks; if (!(c)) { \
    fprintf(stderr, "FAIL line %d: %s\n", __LINE__, #c); exit(1); \
} } while (0)

typedef struct {
    DTVALUE now;
    int reads, dates, times, failDate, failTime, failReadAt;
    int advance, corruptDate, corruptTime;
    char order[16];
    int calls;
} FAKE;

static int refDays(int year, int month)
{
    static const int lengths[] = {31,28,31,30,31,30,31,31,30,31,30,31};
    return lengths[month - 1] + (month == 2 && year % 4 == 0);
}

static void tick(DTVALUE *v)
{
    if (++v->second < 60) return;
    v->second = 0;
    if (++v->minute < 60) return;
    v->minute = 0;
    if (++v->hour < 24) return;
    v->hour = 0;
    if (++v->day <= refDays(v->year, v->month)) return;
    v->day = 1;
    if (++v->month <= 12) return;
    v->month = 1; ++v->year;
}

static int readFake(void *context, DTVALUE *v)
{
    FAKE *f = (FAKE *)context;
    int n;
    f->order[f->calls++] = 'R'; ++f->reads;
    if (f->reads == f->failReadAt) return 0;
    if (f->reads == 2) for (n = 0; n < f->advance; ++n) tick(&f->now);
    *v = f->now;
    return 1;
}

static int dateFake(void *context, const DTVALUE *v)
{
    FAKE *f = (FAKE *)context;
    f->order[f->calls++] = 'D'; ++f->dates;
    if (f->failDate) return 0;
    f->now.year = v->year; f->now.month = v->month;
    f->now.day = v->day + f->corruptDate;
    return 1;
}

static int timeFake(void *context, const DTVALUE *v)
{
    FAKE *f = (FAKE *)context;
    f->order[f->calls++] = 'T'; ++f->times;
    if (f->failTime) return 0;
    f->now.hour = v->hour + f->corruptTime;
    f->now.minute = v->minute; f->now.second = v->second;
    return 1;
}

static void init(FAKE *f, DTIO *io)
{
    memset(f, 0, sizeof(*f));
    CHECK(DtDate("2026-10-04", &f->now));
    CHECK(DtTime("13:14:15", &f->now));
    io->read = readFake; io->setdate = dateFake; io->settime = timeFake;
    io->context = f;
}

static void parseTests(void)
{
    DTVALUE value, parsed;
    char date[11], time[9], text[32];
    const char *badDates[] = {
        "", "2026", "2026-1-01", "2026-01-1", " 2026-01-01", "2026-01-01 ",
        "2026/01/01", "2026-01-010", "20x6-01-01", "2026-0x-01", "2026-01-x1",
        "1979-12-31", "2100-01-01", "2026-00-01", "2026-13-01", "2026-01-00",
        "2026-02-29", "2001-02-29", "2026-04-31", "2026-01-32", "2026-+1-01"
    };
    const char *badTimes[] = {
        "", "0:00:00", "00:0:00", "00:00:0", " 00:00:00", "00:00:00 ",
        "00.00.00", "00:00:000", "0x:00:00", "00:0x:00", "00:00:0x",
        "24:00:00", "23:60:00", "23:59:60", "-1:00:00", "00:+1:00", "12:34:5\n"
    };
    unsigned i;
    int year, month, day, hour, minute, second;
    memset(&value, 0, sizeof(value));
    CHECK(!DtDate(NULL, &value)); CHECK(!DtTime(NULL, &value));
    for (i = 0; i < sizeof(badDates) / sizeof(badDates[0]); ++i)
        CHECK(!DtDate(badDates[i], &value));
    for (i = 0; i < sizeof(badTimes) / sizeof(badTimes[0]); ++i)
        CHECK(!DtTime(badTimes[i], &value));
    for (year = 1980; year <= 2099; ++year)
        for (month = 1; month <= 12; ++month)
            for (day = 0; day <= 32; ++day) {
                sprintf(text, "%04d-%02d-%02d", year, month, day);
                CHECK(DtDate(text, &value) == (day > 0 && day <= refDays(year, month)));
            }
    CHECK(DtDate("2000-02-29", &value));
    for (hour = 0; hour < 24; ++hour)
        for (minute = 0; minute < 60; ++minute)
            for (second = 0; second < 60; ++second) {
                sprintf(text, "%02d:%02d:%02d", hour, minute, second);
                CHECK(DtTime(text, &value));
                DtFormat(&value, date, time);
                CHECK(!strcmp(date, "2000-02-29") && !strcmp(time, text));
                CHECK(DtDate(date, &parsed) && DtTime(time, &parsed) && DtValid(&parsed));
            }
    value.year = 2100; CHECK(!DtValid(&value));
    value.year = 2000; value.second = -1; CHECK(!DtValid(&value));
}

static void applyTests(void)
{
    FAKE f;
    DTIO io;
    DTRESULT r;
    init(&f, &io);
    DtApply("2026-10-04", "12:00:00", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_NOCHANGE && !r.requested && !r.written && !f.calls);
    CHECK(f.now.hour == 13 && f.now.minute == 14 && f.now.second == 15);

    init(&f, &io);
    DtApply("2026-02-30", "01:00:00", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_BADDATE && !f.calls);
    DtApply("2026-10-05", "24:00:00", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_BADTIME && !f.calls);

    init(&f, &io);
    DtApply("2026-10-05", "12:00:00", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_OK && r.requested == DT_DATE && r.written == DT_DATE && r.readback);
    CHECK(f.dates == 1 && !f.times && !strcmp(f.order, "RDR"));
    CHECK(f.now.day == 5 && f.now.hour == 13 && f.now.minute == 14 && f.now.second == 15);

    init(&f, &io);
    f.now.day = 5; /* The date advanced while the editor was open. */
    DtApply("2026-10-04", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_OK && r.written == DT_TIME && !f.dates && f.times == 1);
    CHECK(f.now.day == 5 && f.now.hour == 4 && f.now.minute == 5 && f.now.second == 6);
    CHECK(!strcmp(f.order, "RTR"));

    init(&f, &io); f.advance = 2;
    DtApply("2028-02-28", "23:59:59", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_OK && r.written == (DT_DATE | DT_TIME));
    CHECK(f.now.day == 29 && f.now.hour == 0 && f.now.second == 1);
    CHECK(!strcmp(f.order, "RDTR"));

    init(&f, &io); f.advance = 2;
    DtApply("2027-12-31", "23:59:59", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_OK && f.now.year == 2028 && f.now.month == 1 && f.now.day == 1);

    init(&f, &io); f.advance = 3;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_VERIFYFAIL && r.written == 3 && r.readback);

    init(&f, &io); f.failReadAt = 1;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_READFAIL && !r.written && !f.dates && !f.times);

    init(&f, &io); f.now.month = 13;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_READFAIL && !r.written && !f.dates && !f.times);

    init(&f, &io); f.failDate = 1;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_DATEFAIL && !r.written && !f.times && !strcmp(f.order, "RD"));
    CHECK(f.now.day == 4 && f.now.hour == 13);

    init(&f, &io); f.failTime = 1;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_TIMEFAIL && r.written == DT_DATE && r.readback);
    CHECK(f.dates == 1 && f.times == 1 && f.now.day == 5 && f.now.hour == 13);
    CHECK(!strcmp(f.order, "RDTR")); /* No rollback. */

    init(&f, &io); f.failTime = 1; f.failReadAt = 2;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_TIMEFAIL && r.written == DT_DATE && !r.readback);

    init(&f, &io); f.failTime = 1;
    DtApply("2026-10-04", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_TIMEFAIL && !r.written && !f.dates && !strcmp(f.order, "RT"));

    init(&f, &io); f.failReadAt = 2;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_READBACKFAIL && r.written == 3 && !r.readback);

    init(&f, &io); f.corruptDate = 1;
    DtApply("2026-10-05", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_VERIFYFAIL && r.written == 3 && r.readback);

    init(&f, &io); f.corruptTime = 1;
    DtApply("2026-10-04", "04:05:06", "2026-10-04", "12:00:00", &io, &r);
    CHECK(r.code == DT_VERIFYFAIL && r.written == DT_TIME && r.readback);
}

int main(void)
{
    parseTests(); applyTests();
    printf("PASS: %lu checks; pure parser/calendar and fake clock writes only.\n", checks);
    return 0;
}
