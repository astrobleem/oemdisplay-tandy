#ifndef TANDI_H
#define TANDI_H
#define TD_MAXC 2000
#define TD_MAXQ 256
#define TD_SAMPLE 64
#define TD_ROW 96
#define TD_COL 750
#ifdef _MSC_VER
typedef unsigned short U16;
typedef unsigned long U32;
#else
#include <stdint.h>
typedef uint16_t U16;
typedef uint32_t U32;
#endif
typedef unsigned char U8;
typedef struct {
    U16 nc,nq,rb,cb;
    U32 qo,co,ro,mo,so,size,bytes,seeks;
    int error;
} TDB;
typedef struct {
    short score[TD_MAXC];
    U8 rejected[TD_MAXC],asked[TD_MAXQ];
    U8 cache[TD_SAMPLE][TD_ROW];
    U16 sample[TD_SAMPLE];
    U8 weight[TD_SAMPLE];
    int count,turn,evidence,current,best,second;
    long utility,yesw,now,unknownw;
    U32 examined;
} ENGINE;
int db_open(TDB *,const char *);
void db_close(void);
int db_question(TDB *,int,char *);
int db_name(TDB *,int,char *);
int db_row(TDB *,int,U8 *);
int db_column(TDB *,int,U8 *);
int db_value(const U8 *,int);
void eng_reset(ENGINE *,TDB *);
void eng_rank(ENGINE *,TDB *);
int eng_answer(ENGINE *,TDB *,int);
int eng_choose(ENGINE *,TDB *);
int eng_confident(ENGINE *,TDB *);
void eng_reject(ENGINE *,TDB *);
#endif
