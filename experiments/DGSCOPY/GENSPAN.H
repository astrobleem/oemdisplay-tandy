/* General midpoint span hypothesis. No native Windows geometry qualification.
 * HOST_TEST uses exactly int32_t to test the legacy LONG arithmetic contract.
 * Native callers supply h GenSpan records; no drawing or state persists.
 */
#ifndef GENSPAN_H
#define GENSPAN_H
#ifdef HOST_TEST
#include <stdint.h>
typedef int32_t GenLong;
#else
typedef long GenLong;
#endif
typedef struct {int left,right,innerLeft,innerRight;} GenSpan;
int GenEllipse(int width,int height,GenSpan *out);
#endif
