/* Independent, dependency-free C89 regression oracle for the shipped engine.
 * Compile ENGINE.C as C (uppercase .C otherwise means C++ to GCC).
 * Expected deltas and rules below are deliberately independent of events[].
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <limits.h>
#include "../ENGINE.H"

static long checks = 0L;
static int low_clamps = 0, high_clamps = 0;
static const int counts[5] = {2,3,3,3,2};
static const int deltas[5][3][3] = {
 {{-8,14,0},{10,-18,0},{0,0,0}},
 {{-4,12,2},{14,-12,8},{18,-22,10}},
 {{-6,8,5},{8,-10,22},{-4,4,-24}},
 {{-14,18,-4},{14,-18,4},{8,-24,12}},
 {{-8,10,-10},{12,-16,24},{0,0,0}}
};

static void check(int ok, const char *what, int line)
{
 ++checks;
 if (!ok) {
  printf("FAIL line %d: %s\n",line,what);
  exit(1);
 }
}
#define CHECK(x) check((x), #x, __LINE__)

static int equal_game(const GAME *a, const GAME *b)
{
 return a->value[0]==b->value[0] && a->value[1]==b->value[1] &&
        a->value[2]==b->value[2] && a->event==b->event &&
        a->phase==b->phase && a->picked==b->picked;
}

static void expect_reset(GAME *g)
{
 ResetGame(g);
 CHECK(g->value[0]==60 && g->value[1]==60 && g->value[2]==60);
 CHECK(g->event==0 && g->phase==PLAYING && g->picked==-1);
}

static int clipped(int x)
{
 if (x<0) return 0;
 if (x>100) return 100;
 return x;
}

static void oracle_choice(GAME *g, int choice)
{
 int i;
 for (i=0;i<3;++i)
  g->value[i]=clipped(g->value[i]+deltas[g->event][choice][i]);
 g->picked=choice;
 g->phase=RECEIPT;
}

static void oracle_continue(GAME *g)
{
 int minimum=g->value[0];
 if (g->value[1]<minimum) minimum=g->value[1];
 if (g->value[2]<minimum) minimum=g->value[2];
 if (minimum<=15) g->phase=FAILURE;
 else if (g->event==4) g->phase=(minimum>=50 ? SUCCESS : FAILURE);
 else {
  ++g->event;
  g->phase=PLAYING;
  g->picked=-1;
 }
}

static void invalid_playing_inputs(GAME *g)
{
 GAME before=*g;
 CHECK(g->phase==PLAYING);
 CHECK(ContinueGame(g)==0);
 CHECK(equal_game(g,&before));
 CHECK(Choose(g,-1)==0);
 CHECK(equal_game(g,&before));
 CHECK(Choose(g,counts[g->event])==0);
 CHECK(equal_game(g,&before));
 CHECK(Choose(g,INT_MIN)==0);
 CHECK(equal_game(g,&before));
 CHECK(Choose(g,INT_MAX)==0);
 CHECK(equal_game(g,&before));
}

static void blocked_choice(GAME *g)
{
 GAME before=*g;
 int i;
 for (i=-1;i<=3;++i) {
  CHECK(Choose(g,i)==0);
  CHECK(equal_game(g,&before));
 }
}

static void check_terminal(GAME *g)
{
 GAME before=*g;
 CHECK(g->phase==SUCCESS || g->phase==FAILURE);
 blocked_choice(g);
 CHECK(ContinueGame(g)==0);
 CHECK(equal_game(g,&before));
 expect_reset(g);
}

static void test_data_and_guards(void)
{
 GAME g,before;
 int e,c,i,p;
 CHECK(EVENT_COUNT==5 && CHOICE_MAX==3);
 CHECK(PLAYING!=RECEIPT && RECEIPT!=SUCCESS && SUCCESS!=FAILURE);
 for (e=0;e<5;++e) {
  CHECK(events[e].count==counts[e]);
  for (c=0;c<counts[e];++c) {
   CHECK(events[e].choice[c].label[0]!='\0');
   CHECK(events[e].choice[c].receipt[0]!='\0');
   for (i=0;i<3;++i)
    CHECK(events[e].choice[c].delta[i]==deltas[e][c][i]);
  }
 }
 for (p=PLAYING;p<=FAILURE;++p) {
  g.value[0]=0;g.value[1]=100;g.value[2]=15;
  g.event=4;g.phase=p;g.picked=2;
  expect_reset(&g);
 }
 expect_reset(&g);
 g.event=-1;before=g;
 CHECK(Choose(&g,0)==0 && equal_game(&g,&before));
 g.event=5;before=g;
 CHECK(Choose(&g,0)==0 && equal_game(&g,&before));
 g.event=INT_MAX;before=g;
 CHECK(Choose(&g,0)==0 && equal_game(&g,&before));
 g.event=0;g.phase=17;before=g;
 CHECK(Choose(&g,0)==0 && equal_game(&g,&before));
 CHECK(ContinueGame(&g)==0 && equal_game(&g,&before));
 printf("PASS data contract, reset, invalid choice/event/phase guards\n");
}

static void test_all_routes(void)
{
 GAME g,oracle;
 int route[5],n,remainder,e,c,successes=0,failures=0;
 int early[5]={0,0,0,0,0};
 for (n=0;n<108;++n) {
  remainder=n;
  for (e=4;e>=0;--e) {
   route[e]=remainder%counts[e];
   remainder/=counts[e];
  }
  CHECK(remainder==0);
  expect_reset(&g);oracle=g;
  for (e=0;e<5;++e) {
   c=route[e];
   CHECK(g.phase==PLAYING && g.event==e);
   invalid_playing_inputs(&g);
   CHECK(Choose(&g,c)==1);
   oracle_choice(&oracle,c);
   CHECK(equal_game(&g,&oracle));
   blocked_choice(&g); /* Receipt cannot reapply any choice. */
   CHECK(ContinueGame(&g)==1);
   oracle_continue(&oracle);
   CHECK(equal_game(&g,&oracle));
   if (g.phase==SUCCESS || g.phase==FAILURE) break;
  }
  if (g.phase==SUCCESS) ++successes;
  else {
   CHECK(g.phase==FAILURE);
   ++failures;
   if (e<4) ++early[e];
  }
  check_terminal(&g);
 }
 CHECK(successes+failures==108);
 printf("PASS all 108 nominal routes: %d success, %d failure\n",
        successes,failures);
 printf("     Early endings by event 1..4: %d, %d, %d, %d\n",
        early[0],early[1],early[2],early[3]);
 printf("     Counts include nominal suffixes skipped after early termination.\n");
}

static void test_boundaries(void)
{
 static const int seeds[8]={0,1,15,16,49,50,99,100};
 GAME g,oracle;
 int e,c,a,b,d,i,raw,choice_cases=0,continue_cases=0;
 for (e=0;e<5;++e) {
  for (a=0;a<8;++a) for (b=0;b<8;++b) for (d=0;d<8;++d) {
   for (c=0;c<counts[e];++c) {
    g.value[0]=seeds[a];g.value[1]=seeds[b];g.value[2]=seeds[d];
    g.event=e;g.phase=PLAYING;g.picked=-1;oracle=g;
    for (i=0;i<3;++i) {
     raw=g.value[i]+deltas[e][c][i];
     if (raw<0) ++low_clamps;
     if (raw>100) ++high_clamps;
    }
    CHECK(Choose(&g,c)==1);
    oracle_choice(&oracle,c);
    CHECK(equal_game(&g,&oracle));
    blocked_choice(&g);
    ++choice_cases;
   }
   g.value[0]=seeds[a];g.value[1]=seeds[b];g.value[2]=seeds[d];
   g.event=e;g.phase=RECEIPT;g.picked=0;oracle=g;
   CHECK(ContinueGame(&g)==1);
   oracle_continue(&oracle);
   CHECK(equal_game(&g,&oracle));
   if (g.phase==PLAYING) invalid_playing_inputs(&g);
   else check_terminal(&g);
   ++continue_cases;
  }
 }
 CHECK(choice_cases==6656 && continue_cases==2560);
 CHECK(low_clamps>0 && high_clamps>0);
 printf("PASS %d choice boundary cases; %d continuation boundary cases\n",
        choice_cases,continue_cases);
 printf("     Clamp cases exercised: %d below 0, %d above 100\n",
        low_clamps,high_clamps);
}

static void test_named_routes(void)
{
 static const int good[5]={0,1,0,0,1};
 static const int bad[4]={1,2,1,2};
 GAME g;
 int e;
 expect_reset(&g);
 for (e=0;e<5;++e) {
  CHECK(Choose(&g,good[e])==1);
  CHECK(g.phase==RECEIPT);
  CHECK(ContinueGame(&g)==1);
 }
 CHECK(g.phase==SUCCESS && g.event==4);
 CHECK(g.value[0]==58 && g.value[1]==72 && g.value[2]==93);
 printf("PASS success route 1,2,1,1,2 -> 58/72/93, SUCCESS\n");
 check_terminal(&g);
 for (e=0;e<4;++e) {
  CHECK(Choose(&g,bad[e])==1);
  CHECK(g.phase==RECEIPT);
  CHECK(ContinueGame(&g)==1);
  if (g.phase==FAILURE) break;
 }
 CHECK(e==2 && g.event==2 && g.phase==FAILURE);
 CHECK(g.value[0]==96 && g.value[1]==10 && g.value[2]==92);
 CHECK(Choose(&g,bad[3])==0);
 printf("PASS early-failure route 2,3,2,3 stops after event 3 -> 96/10/92\n");
 printf("     Fourth choice is correctly blocked; restart resets all state.\n");
 check_terminal(&g);
}

static int audit_string(const char *s, const char *kind, int event, int choice,
                        int max_lines)
{
 const char *start=s,*p=s;
 int line=1,width=0,issues=0;
 for (;;) {
  if (*p=='\n' || *p=='\0') {
   if (width>18) {
    printf("OVERFLOW event %d %s %d line %d: %d columns: %.*s\n",
           event,kind,choice,line,width,width,start);
    ++issues;
   }
   if (*p=='\0') break;
   ++line;width=0;start=p+1;
  } else ++width;
  ++p;
 }
 if (line>max_lines) {
  printf("OVERFLOW event %d %s %d: %d lines (limit %d)\n",
         event,kind,choice,line,max_lines);
  ++issues;
 }
 return issues;
}

static int audit_copy(void)
{
 int e,c,issues=0;
 for (e=0;e<5;++e) {
  issues+=audit_string(events[e].text,"prompt",e+1,0,4);
  for (c=0;c<events[e].count;++c) {
   issues+=audit_string(events[e].choice[c].label,"label",e+1,c+1,1);
   issues+=audit_string(events[e].choice[c].receipt,"receipt",e+1,c+1,4);
  }
 }
 printf("%s engine copy audit: %d violation(s) of 18-column/four-line bound\n",
        issues ? "FAIL" : "PASS",issues);
 return issues ? 1 : 0;
}

int main(int argc, char **argv)
{
 if (argc==2 && strcmp(argv[1],"--copy")==0) return audit_copy();
 if (argc!=1) {
  fprintf(stderr,"Usage: engine_oracle [--copy]\n");
  return 2;
 }
 test_data_and_guards();
 test_all_routes();
 test_boundaries();
 test_named_routes();
 printf("PASS gameplay: %ld assertions\n",checks);
 return 0;
}
