/* Unsigned elapsed-time arithmetic is intentional: GetTickCount wraps. */
#include "SVCORE.H"
void SvReset(SVSTATE *s, SVTICK now, SVTICK generation)
{ s->since=now; s->generation=generation; s->known=1; }
int SvDue(SVSTATE *s, SVTICK now, SVTICK generation, SVTICK delay, int ready)
{
    if (!s->known || !ready || generation!=s->generation) {
        SvReset(s,now,generation); return 0;
    }
    if ((SVTICK)(now-s->since)<delay) return 0;
    SvReset(s,now,generation); return 1;
}
