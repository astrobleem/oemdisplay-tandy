#ifndef SVCORE_H
#define SVCORE_H
#ifdef HOST_TEST
#include <stdint.h>
typedef uint32_t SVTICK;
#else
typedef unsigned long SVTICK;
#endif
typedef struct { SVTICK since, generation; int known; } SVSTATE;
void SvReset(SVSTATE *state, SVTICK now, SVTICK generation);
int SvDue(SVSTATE *state, SVTICK now, SVTICK generation,
          SVTICK delay, int ready);
#endif
