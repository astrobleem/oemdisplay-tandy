#include <stdio.h>
#include <string.h>
#include "../src/TANDI.H"
static TDB d;static ENGINE e;static U8 row[TD_ROW],col[TD_COL];
static int failures=0;
#define CHECK(x) do{if(!(x)){printf("FAIL line %d: %s\n",__LINE__,#x);failures++;}}while(0)
int main(int argc,char **argv){
    int i,q,c,old,chosen,soft,strong;unsigned char asked[TD_MAXQ];
    char text[80];
    if(argc!=2)return 2;
    CHECK(db_open(&d,argv[1]));if(d.error)return 3;
    for(c=0;c<d.nc;c++){
        CHECK(db_name(&d,c,text));CHECK(db_row(&d,c,row));
        for(q=0;q<d.nq;q++){
            CHECK(db_column(&d,q,col));CHECK(db_value(row,q)==db_value(col,c));
        }
    }
    eng_reset(&e,&d);q=eng_choose(&e,&d);CHECK(q>=0);
    CHECK(!eng_answer(&e,&d,-1));CHECK(!eng_answer(&e,&d,5));
    CHECK(e.turn==0);CHECK(eng_answer(&e,&d,2));
    for(i=0;i<d.nc;i++)CHECK(e.score[i]==0);
    CHECK(!eng_answer(&e,&d,4));CHECK(e.turn==1);
    memset(asked,0,sizeof(asked));asked[q]=1;
    while(e.turn<25){q=eng_choose(&e,&d);CHECK(q>=0&&!asked[q]);
        if(q<0)break;
        asked[q]=1;CHECK(eng_answer(&e,&d,2));}
    CHECK(eng_confident(&e,&d));CHECK(e.evidence==0);
    old=e.best;eng_reject(&e,&d);CHECK(e.best!=old);CHECK(e.rejected[old]);
    while(e.best>=0)eng_reject(&e,&d);
    CHECK(eng_choose(&e,&d)==-1);CHECK(!eng_confident(&e,&d));
    eng_reset(&e,&d);CHECK(e.turn==0);CHECK(!e.rejected[old]);
    /* Same start state must choose the same question. */
    chosen=eng_choose(&e,&d);eng_reset(&e,&d);CHECK(eng_choose(&e,&d)==chosen);
    CHECK(db_column(&d,chosen,col));c=-1;
    for(i=0;i<d.nc;i++)if(db_value(col,i)==4){c=i;break;}
    CHECK(c>=0);
    if(c>=0){
        CHECK(eng_answer(&e,&d,3));soft=e.score[c];
        eng_reset(&e,&d);CHECK(eng_choose(&e,&d)==chosen);
        CHECK(eng_answer(&e,&d,4));strong=e.score[c];CHECK(strong>soft);
        eng_reset(&e,&d);eng_choose(&e,&d);CHECK(eng_answer(&e,&d,0));
        CHECK(e.score[c]<0);CHECK(!e.rejected[c]);
    }
    printf("Checks complete. Failures=%d Characters=%u Questions=%u\n",failures,d.nc,d.nq);
    db_close();return failures?1:0;
}
