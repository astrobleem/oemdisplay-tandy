/* Read-only observations of the unchanged engine. C89, no heap or floats. */
#include "OBSERVE.H"
#include <string.h>
static const short delta[5][5]={
    {4,2,0,-4,-8},{2,2,0,-2,-4},{0,0,0,0,0},
    {-4,-2,0,2,2},{-8,-4,0,2,4}
};
void obs_reset(TDHISTORY *h){memset(h,0,sizeof(*h));}
int obs_answer(TDHISTORY *h,ENGINE *e,TDB *d,int a){
    int i,q=e->current;
    if(h->count<0||h->count>=TD_MAXQ||q<0||q>=(int)d->nq)return 0;
    for(i=0;i<h->count;i++)if((int)h->q[i]==q)return 0;
    if(!eng_answer(e,d,a))return 0;
    h->q[h->count]=(U16)q;h->a[h->count]=(U8)a;h->count++;
    return 1;
}
void obs_pool(ENGINE *e,TDB *d,TDPOOL *p){
    int i;p->eligible=p->leading=0;p->cutoff=0;
    if(e->best<0)return;
    p->cutoff=(short)(e->score[e->best]-24);
    for(i=0;i<(int)d->nc;i++)if(!e->rejected[i]){
        p->eligible++;
        if(e->score[i]>=p->cutoff)p->leading++;
    }
}
static int magnitude(int v){return v<0?-v:v;}
int obs_explain(TDHISTORY *h,ENGINE *e,TDB *d,TDEXPLAIN *x){
    U8 leader[TD_ROW],other[TD_ROW];TDCLUE c;
    int i,j,q,a,v,w;long ls=0,os=0;
    memset(x,0,sizeof(*x));x->leader=e->best;x->other=e->second;
    if(e->best<0||e->second<0||h->count<0||h->count>TD_EXPLAIN_MAX||
       h->count!=e->turn||e->rejected[e->best]||e->rejected[e->second])
        return 0;
    if(!db_row(d,e->best,leader)||!db_row(d,e->second,other))return 0;
    x->leaderScore=e->score[e->best];x->otherScore=e->score[e->second];
    for(i=0;i<h->count;i++){
        q=h->q[i];a=h->a[i];
        if(q<0||q>=(int)d->nq||a<0||a>4||!e->asked[q])return 0;
        for(j=0;j<i;j++)if((int)h->q[j]==q)return 0;
        v=db_value(leader,q);w=db_value(other,q);
        c.q=(U16)q;c.answer=(U8)a;c.leaderFact=(U8)v;
        c.otherFact=(U8)w;c.leaderDelta=delta[a][v];
        c.otherDelta=delta[a][w];
        c.difference=(short)(c.leaderDelta-c.otherDelta);
        x->sum+=c.difference;ls+=c.leaderDelta;os+=c.otherDelta;
        /* Largest signed differences first. Stable ties preserve history.
           Negative clues and neutral/unknown clues are retained too. */
        j=x->count;
        while(j>0&&magnitude(c.difference)>
              magnitude(x->clue[j-1].difference)){
            x->clue[j]=x->clue[j-1];j--;
        }
        x->clue[j]=c;x->count++;
    }
    if(x->sum!=(long)x->leaderScore-x->otherScore||
       ls!=x->leaderScore||os!=x->otherScore)return 0;
    x->valid=1;return 1;
}
