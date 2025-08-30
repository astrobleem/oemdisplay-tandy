#ifndef COMPILER_COMPAT_H
#define COMPILER_COMPAT_H

/* MSC6 doesn't have inline or // comments. */
#ifndef inline
#define inline /* nothing */
#endif

/* MSC6 sometimes chokes on const in old headers; only use if needed */
/* #define const /* nothing */ 

/* Far/near portability */
#ifndef FAR
#define FAR __far
#endif
#ifndef NEAR
#define NEAR __near
#endif
#ifndef PASCAL
#define PASCAL __pascal
#endif

/* memset/memcpy for far pointers (Windows 3.x) */
#include <string.h>
#define fmemcpy _fmemcpy
#define fmemset _fmemset

#endif
