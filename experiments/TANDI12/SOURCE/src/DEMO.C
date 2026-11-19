/* Deterministic, paced demonstration of the unchanged engine. No UI/input/I/O
   writes, settings, random numbers, learning or artificial engine delays. */
#include "DEMO.H"
#include <string.h>
static const char *names[DEMO_ROSTER]={
    "Mario","Lara Croft","Bugs Bunny","Mickey Mouse",
    "SpongeBob SquarePants","Popeye","Snoopy","Charlie Brown"
};
int demo_due(U32 now,U32 due){return (U32)(now-due)<0x80000000UL;}
static int game(TDDEMO *s,ENGINE *e,TDB *d,TDHISTORY *h,U32 now){
    int q;s->target=s->roster[(s->sequence*3)%DEMO_ROSTER];
    s->sequence=(s->sequence+1)%DEMO_ROSTER;
    if(!db_row(d,s->target,s->truth))return 0;
    for(q=0;q<(int)d->nq;q++)if(db_value(s->truth,q)==2)return 0;
    eng_reset(e,d);obs_reset(h);s->phase=DEMO_TITLE;
    s->steps=s->rejections=0;s->due=now+1500UL;return 1;
}
int demo_init(TDDEMO *s,ENGINE *e,TDB *d,TDHISTORY *h,U32 now){
    int n,c,found;char name[40];memset(s,0,sizeof(*s));
    /* Fail closed if an expected authored character is absent/unknown.
       The DAT supplies every answer; no hand-coded answer script exists. */
    for(n=0;n<DEMO_ROSTER;n++){
        found=-1;
        for(c=0;c<(int)d->nc;c++){
            if(!db_name(d,c,name))return 0;
            if(!strcmp(name,names[n])){found=c;break;}
        }
        if(found<0||!db_row(d,found,s->truth))return 0;
        for(c=0;c<(int)d->nq;c++)if(db_value(s->truth,c)==2)return 0;
        s->roster[n]=(U16)found;
    }
    s->enabled=game(s,e,d,h,now);return s->enabled;
}
static int prompt(TDDEMO *s,ENGINE *e,TDB *d,U32 now){
    if(eng_confident(e,d)||eng_choose(e,d)<0){
        if(e->best<0||d->error)return -1;
        s->phase=DEMO_GUESS;s->due=now+2000UL;
        return DEMO_CHANGED|DEMO_REVEAL;
    }
    s->phase=DEMO_QUESTION;s->due=now+1800UL;
    return DEMO_CHANGED;
}
int demo_step(TDDEMO *s,ENGINE *e,TDB *d,TDHISTORY *h,U32 now){
    int result;
    if(!s->enabled||!demo_due(now,s->due))return 0;
    s->side=(s->side+1)%6;
    if(s->phase==DEMO_TITLE)return prompt(s,e,d,now);
    if(s->phase==DEMO_QUESTION){
        s->answer=db_value(s->truth,e->current);s->phase=DEMO_ANSWER;
        s->due=now+700UL;return DEMO_CHANGED;
    }
    if(s->phase==DEMO_ANSWER){
        if(!obs_answer(h,e,d,s->answer))goto failed;
        if(++s->steps>(int)d->nq+(int)d->nc)goto failed;
        result=prompt(s,e,d,now);if(result<0)goto failed;
        if(e->turn%3==0&&s->phase==DEMO_QUESTION){
            s->resume=DEMO_QUESTION;s->phase=DEMO_DARK;
            s->due=now+1500UL;return DEMO_CHANGED|DEMO_STOPCUE;
        }
        return result;
    }
    if(s->phase==DEMO_GUESS){
        if(e->best==s->target){
            s->phase=DEMO_SUCCESS;s->due=now+1800UL;s->games++;
            return DEMO_CHANGED|DEMO_VICTORY;
        }
        if(++s->rejections>=(int)d->nc)goto failed;
        eng_reject(e,d);result=prompt(s,e,d,now);
        if(result<0)goto failed;
        return result;
    }
    if(s->phase==DEMO_SUCCESS){
        s->resume=DEMO_TITLE;s->phase=DEMO_DARK;s->due=now+2200UL;
        return DEMO_CHANGED|DEMO_STOPCUE;
    }
    if(s->phase==DEMO_DARK){
        if(s->resume==DEMO_TITLE){
            if(!game(s,e,d,h,now))goto failed;
            return DEMO_CHANGED;
        }
        s->phase=s->resume;s->due=now+1800UL;return DEMO_CHANGED;
    }
failed:
    s->enabled=0;return -1;
}
