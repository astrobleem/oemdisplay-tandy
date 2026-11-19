#ifndef OBSERVE_H
#define OBSERVE_H
/* The approved native game hard ceiling is forty answers. */
#define TD_EXPLAIN_MAX 40
#include "TANDI.H"
/* At most one accepted answer per question, not per 25-question guess cap. */
typedef struct {
    U16 q[TD_MAXQ];
    U8 a[TD_MAXQ];
    int count;
} TDHISTORY;
typedef struct {
    int eligible,leading;
    short cutoff;
} TDPOOL;
typedef struct {
    U16 q;
    U8 answer,leaderFact,otherFact;
    short leaderDelta,otherDelta,difference;
} TDCLUE;
typedef struct {
    int leader,other,count,valid;
    short leaderScore,otherScore;
    long sum;
    TDCLUE clue[TD_EXPLAIN_MAX];
} TDEXPLAIN;
void obs_reset(TDHISTORY *);
int obs_answer(TDHISTORY *,ENGINE *,TDB *,int);
void obs_pool(ENGINE *,TDB *,TDPOOL *);
int obs_explain(TDHISTORY *,ENGINE *,TDB *,TDEXPLAIN *);
#endif
