/* Shared, deterministic C89 engine. No Windows calls, floats or heap. */
#include "TANDI.H"
#include <string.h>
static U8 column[TD_COL];
/* UNKNOWN user answers and unknown database facts carry no evidence. */
static const short delta[5][5]={
 {4,2,0,-4,-8},{2,2,0,-2,-4},{0,0,0,0,0},
 {-4,-2,0,2,2},{-8,-4,0,2,4}
};
void eng_rank(ENGINE *e,TDB *d){
    int i;e->best=e->second=-1;
    for(i=0;i<(int)d->nc;i++)if(!e->rejected[i]){
        if(e->best<0||e->score[i]>e->score[e->best]){
            e->second=e->best;e->best=i;
        }else if(e->second<0||e->score[i]>e->score[e->second])
            e->second=i;
    }
}
void eng_reset(ENGINE *e,TDB *d){
    memset(e,0,sizeof(*e));e->current=-1;eng_rank(e,d);
}
int eng_answer(ENGINE *e,TDB *d,int answer){
    int i,v,q=e->current;
    if(answer<0||answer>4||q<0||q>=(int)d->nq||e->asked[q])return 0;
    if(!db_column(d,q,column))return 0;
    for(i=0;i<(int)d->nc;i++)if(!e->rejected[i]){
        v=db_value(column,i);e->score[i]+=delta[answer][v];e->examined++;
    }
    e->asked[q]=1;e->turn++;if(answer!=2)e->evidence++;
    e->current=-1;eng_rank(e,d);return 1;
}
int eng_confident(ENGINE *e,TDB *d){
    int best=e->best;(void)d;
    if(best<0)return 0;
    if(e->turn>=25)return 1;
    if(e->evidence<7)return 0;
    if(e->score[best]<e->evidence*2)return 0;
    return e->second<0||e->score[best]-e->score[e->second]>=10;
}
int eng_choose(ENGINE *e,TDB *d){
    int i,q,v,pool=0,seen=0,taken=0,best,dist,target,threshold;
    long y,n,u,utility,bestutil=-2147483647L;
    eng_rank(e,d);best=e->best;if(best<0)return -1;
    threshold=e->score[best]-24;
    for(i=0;i<(int)d->nc;i++)if(!e->rejected[i]&&e->score[i]>=threshold)pool++;
    /* Always include leader, then evenly sample the plausible set. */
    e->sample[taken++]=(U16)best;
    target=(pool<TD_SAMPLE)?pool:TD_SAMPLE;
    for(i=0;i<(int)d->nc&&taken<target;i++){
        if(i==best||e->rejected[i]||e->score[i]<threshold)continue;
        seen++;
        if(pool<=TD_SAMPLE||
           (long)seen*(target-1)/(pool-1)>(long)(seen-1)*(target-1)/(pool-1))
            e->sample[taken++]=(U16)i;
    }
    e->count=taken;
    for(i=0;i<taken;i++){
        if(!db_row(d,e->sample[i],e->cache[i]))return -1;
        dist=e->score[best]-e->score[e->sample[i]];
        e->weight[i]=(U8)(16/(1+dist/3));e->examined++;
    }
    e->current=-1;
    for(q=0;q<(int)d->nq;q++)if(!e->asked[q]){
        y=n=u=0;
        for(i=0;i<taken;i++){
            v=db_value(e->cache[i],q);
            if(v==2)u+=4*e->weight[i];
            else {y+=(long)v*e->weight[i];n+=(long)(4-v)*e->weight[i];}
        }
        utility=4*((y<n)?y:n)-u;
        if(utility>bestutil){
            bestutil=utility;e->current=q;
            e->utility=utility;e->yesw=y;e->now=n;e->unknownw=u;
        }
    }
    return e->current;
}
void eng_reject(ENGINE *e,TDB *d){
    if(e->best>=0)e->rejected[e->best]=1;
    eng_rank(e,d);
}
