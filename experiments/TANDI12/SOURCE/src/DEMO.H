#ifndef DEMO_H
#define DEMO_H
#include "OBSERVE.H"
#define DEMO_ROSTER 8
#define DEMO_TITLE 0
#define DEMO_QUESTION 1
#define DEMO_ANSWER 2
#define DEMO_GUESS 3
#define DEMO_SUCCESS 4
#define DEMO_DARK 5
#define DEMO_REVEAL 1
#define DEMO_VICTORY 2
#define DEMO_CHANGED 4
#define DEMO_STOPCUE 8
#define DEMO_IDLE_MS 60000UL
typedef struct {
    U16 roster[DEMO_ROSTER];
    U8 truth[TD_ROW];
    int enabled,phase,resume,target,sequence,answer,side,steps,rejections;
    U32 due,games;
} TDDEMO;
int demo_init(TDDEMO *,ENGINE *,TDB *,TDHISTORY *,U32);
int demo_step(TDDEMO *,ENGINE *,TDB *,TDHISTORY *,U32);
int demo_due(U32,U32);
#endif
