#ifndef TD_LEARN_H
#define TD_LEARN_H
#include "TANDI.H"
#include "OBSERVE.H"
#define LN_CELLS 256
#define LN_SESSIONS 128
#define LN_ANSWERS 40
/* No imported reports; IDs persist through reset. New books archive the old. */
void ln_fixture(int);
int ln_open(TDB *,const char *);
void ln_close(void);
int ln_cells(void);
int ln_sessions(void);
int ln_active(void);
int ln_conflicts(void);
int ln_ready(void);
U32 ln_next(void);
const char *ln_status(void);
int ln_review(TDB *,int,const TDHISTORY *);
int ln_preview(int,int,int);
int ln_detail(TDB *,int,const TDHISTORY *,int,int *,int *);
int ln_save(TDB *,int,const TDHISTORY *,U32,int);
int ln_reset(TDB *);
int ln_fresh(TDB *);
int ln_tie(ENGINE *,TDB *,const TDHISTORY *);
#ifdef LN_HOST
void ln_fault(int);
#endif
#endif
