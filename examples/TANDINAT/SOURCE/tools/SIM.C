#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include "../src/TANDI.H"
static TDB db;
static ENGINE engine;
static U8 truth[TD_ROW];
static int questions[TD_MAXC],firsts[TD_MAXC];
static char names[TD_MAXC][40];
static int compare(const void *a,const void *b){return *(const int *)a-*(const int *)b;}
static void quoted(const char *s){
    putchar('"');
    while(*s){if(*s=='"'||*s=='\\')putchar('\\');putchar(*s++);}
    putchar('"');
}
int main(int argc,char **argv){
    int c,i,mode,q,a,tries,success,first,total,worst,failed;
    int uncertain,flipped,rejections,maxreject,duplicates=0;
    clock_t start;double seconds;
    if(argc<2){fprintf(stderr,"Usage: SIM TANDY.DAT [trace-character-id]\n");return 2;}
    start=clock();if(!db_open(&db,argv[1])){fprintf(stderr,"Invalid database\n");return 2;}
    printf("{\"characters\":%u,\"questions\":%u,\"load_host_ms\":%.3f,",
           db.nc,db.nq,1000.0*(clock()-start)/CLOCKS_PER_SEC);
    for(c=0;c<db.nc;c++)db_name(&db,c,names[c]);
    printf("\"engine_bytes_host\":%lu,\"runs\":[",(unsigned long)sizeof(engine));
    for(mode=0;mode<6;mode++){
        success=first=total=worst=failed=rejections=maxreject=0;start=clock();
        if(mode)printf(",");
        printf("{\"mode\":\"%s\",\"characters\":[",mode==0?"truthful":mode==1?"one_wrong":mode==2?"one_uncertain":mode==3?"two_wrong":mode==4?"decisive":"cautious");
        for(c=0;c<db.nc;c++){
            db_row(&db,c,truth);eng_reset(&engine,&db);tries=uncertain=flipped=0;
            for(;;){
                q=eng_confident(&engine,&db)?-1:eng_choose(&engine,&db);
                if(q<0){
                    if(engine.best==c){success++;if(!tries)first++;break;}
                    if(engine.best<0||tries>=10){failed++;break;}
                    tries++;eng_reject(&engine,&db);
                    if(engine.turn<25)continue;
                    /* At the limit rank remaining guesses without more questions. */
                    continue;
                }
                a=db_value(truth,q);
                if(mode==1&&engine.turn>=3&&a!=2&&!flipped){a=4-a;flipped++;}
                if(mode==2&&engine.turn>=3&&a!=2&&!uncertain){a=2;uncertain++;}
                if(mode==3&&engine.turn>=3&&a!=2&&flipped<2){a=4-a;flipped++;}
                if(mode==4){if(a==1)a=0;else if(a==3)a=4;}
                if(mode==5){if(a==0)a=1;else if(a==4)a=3;}
                if(argc>2&&atoi(argv[2])==c){
                    char text[80];db_question(&db,q,text);
                    fprintf(stderr,"%s mode%d Q%d %s -> %d\n",names[c],mode,engine.turn+1,text,a);
                }
                if(!eng_answer(&engine,&db,a)){fprintf(stderr,"Engine error\n");return 3;}
            }
            questions[c]=engine.turn;firsts[c]=tries;
            total+=engine.turn;if(engine.turn>worst)worst=engine.turn;
            rejections+=tries;if(tries>maxreject)maxreject=tries;
            if(c)printf(",");
            printf("{\"name\":");quoted(names[c]);
            printf(",\"questions\":%d,\"wrong_guesses\":%d,\"success\":%s}",
                   engine.turn,tries,engine.best==c?"true":"false");
        }
        seconds=(double)(clock()-start)/CLOCKS_PER_SEC;
        qsort(questions,db.nc,sizeof(int),compare);
        printf("],\"success\":%d,\"first_guess_success\":%d,\"failed\":%d,\"mean_questions\":%.4f,\"median_questions\":%d,\"worst_questions\":%d,\"wrong_guesses\":%d,\"max_wrong_guesses\":%d,\"host_seconds\":%.4f}",
               success,first,failed,(double)total/db.nc,questions[db.nc/2],worst,rejections,maxreject,seconds);
    }
    /* Verify no duplicate full answer profiles. */
    for(c=0;c<db.nc;c++){
        db_row(&db,c,truth);
        for(i=c+1;i<db.nc;i++){
            U8 other[TD_ROW];db_row(&db,i,other);
            if(!memcmp(truth,other,db.rb))duplicates++;
        }
    }
    printf("],\"duplicate_profiles\":%d,\"io_bytes\":%lu,\"io_seeks\":%lu}\n",
           duplicates,(unsigned long)db.bytes,(unsigned long)db.seeks);
    db_close();return 0;
}
