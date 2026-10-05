/* Calendar validation and explicit, dirty-only clock writes. MSC 6 /G0. */
#include <string.h>
#include "DTCORE.H"

static int monthDays(int year, int month)
{
    static const int days[12] = {31,28,31,30,31,30,31,31,30,31,30,31};
    if (month < 1 || month > 12) return 0;
    if (month == 2 && !(year % 4) &&
        (year % 100 || !(year % 400))) return 29;
    return days[month - 1];
}

static int validDate(const DTVALUE *v)
{
    return v->year >= 1980 && v->year <= 2099 &&
           v->month >= 1 && v->month <= 12 &&
           v->day >= 1 && v->day <= monthDays(v->year, v->month);
}

static int validTime(const DTVALUE *v)
{
    return v->hour >= 0 && v->hour < 24 &&
           v->minute >= 0 && v->minute < 60 &&
           v->second >= 0 && v->second < 60 &&
           v->hsecond >= 0 && v->hsecond < 100;
}

int DtValid(const DTVALUE *v)
{
    return validDate(v) && validTime(v);
}

static int digits(const char *s, int count)
{
    int n = 0;
    while (count--) {
        if (*s < '0' || *s > '9') return -1;
        n = n * 10 + *s++ - '0';
    }
    return n;
}

int DtDate(const char *s, DTVALUE *v)
{
    DTVALUE parsed;
    if (!s || strlen(s) != 10 || s[4] != '-' || s[7] != '-') return 0;
    parsed.year = digits(s, 4);
    parsed.month = digits(s + 5, 2);
    parsed.day = digits(s + 8, 2);
    if (!validDate(&parsed)) return 0;
    v->year = parsed.year; v->month = parsed.month; v->day = parsed.day;
    return 1;
}

int DtTime(const char *s, DTVALUE *v)
{
    DTVALUE parsed;
    if (!s || strlen(s) != 8 || s[2] != ':' || s[5] != ':') return 0;
    parsed.hour = digits(s, 2);
    parsed.minute = digits(s + 3, 2);
    parsed.second = digits(s + 6, 2);
    parsed.hsecond = 0;
    if (!validTime(&parsed)) return 0;
    v->hour = parsed.hour; v->minute = parsed.minute; v->second = parsed.second; v->hsecond = 0;
    return 1;
}

static void twoDigits(char *p, int n)
{
    p[0] = (char)('0' + n / 10); p[1] = (char)('0' + n % 10);
}

void DtFormat(const DTVALUE *v, char *date, char *time)
{
    twoDigits(date, v->year / 100); twoDigits(date + 2, v->year % 100);
    date[4] = '-'; twoDigits(date + 5, v->month);
    date[7] = '-'; twoDigits(date + 8, v->day); date[10] = 0;
    twoDigits(time, v->hour); time[2] = ':'; twoDigits(time + 3, v->minute);
    time[5] = ':'; twoDigits(time + 6, v->second); time[8] = 0;
}

static int sameDate(const DTVALUE *a, const DTVALUE *b)
{
    return a->year == b->year && a->month == b->month && a->day == b->day;
}

static int advanced(const DTVALUE *expected, const DTVALUE *actual, int timeWritten)
{
    DTVALUE next;
    long a, b;
    a = (long)expected->hour * 3600L + expected->minute * 60L + expected->second;
    b = (long)actual->hour * 3600L + actual->minute * 60L + actual->second;
    if (sameDate(expected, actual)) {
        if (b >= a) return b - a <= 2L;
        /* DOS rounds a .00 request down to BIOS ticks. Preserve hundredths
           so only the measured sub-tick predecessor (.94 through .99) is
           accepted, and only after a successful time write. */
        return timeWritten && a - b == 1L && actual->hsecond >= 94;
    }
    next = *expected;
    if (++next.day > monthDays(next.year, next.month)) {
        next.day = 1;
        if (++next.month > 12) { next.month = 1; ++next.year; }
    }
    return sameDate(&next, actual) && b + 86400L - a <= 2L;
}

void DtApply(const char *date, const char *time,
             const char *loadedDate, const char *loadedTime,
             const DTIO *io, DTRESULT *r)
{
    DTVALUE value, expected;
    int failure = 0;
    r->requested = r->written = r->readback = 0;
    r->code = DT_BADDATE;
    if (!DtDate(date, &value)) return;
    r->code = DT_BADTIME;
    if (!DtTime(time, &value)) return;
    if (strcmp(date, loadedDate)) r->requested |= DT_DATE;
    if (strcmp(time, loadedTime)) r->requested |= DT_TIME;
    r->code = DT_NOCHANGE;
    if (!r->requested) return;
    r->code = DT_READFAIL;
    if (!io->read(io->context, &expected) || !DtValid(&expected)) return;
    if (r->requested & DT_DATE) {
        if (!io->setdate(io->context, &value)) { r->code = DT_DATEFAIL; return; }
        r->written |= DT_DATE;
        expected.year = value.year; expected.month = value.month; expected.day = value.day;
    }
    if (r->requested & DT_TIME) {
        if (!io->settime(io->context, &value)) failure = DT_TIMEFAIL;
        else {
            r->written |= DT_TIME;
            expected.hour = value.hour; expected.minute = value.minute;
            expected.second = value.second; expected.hsecond = 0;
        }
    }
    if (r->written) {
        r->readback = io->read(io->context, &r->actual) && DtValid(&r->actual);
        if (failure) { r->code = failure; return; }
        if (!r->readback) { r->code = DT_READBACKFAIL; return; }
        if (!advanced(&expected, &r->actual, r->written & DT_TIME)) { r->code = DT_VERIFYFAIL; return; }
    }
    r->code = failure ? failure : DT_OK;
}
