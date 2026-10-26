/* Pure bounded integer model: one detent feeds three logical pixels. */
#define ROLL_MAX 240
static int roll_move(int paper,int delta) {
 long motion=(long)delta;long next;
 if(motion<0)motion=-motion;
 next=(long)paper+motion*3L;
 return next<0?0:(next>ROLL_MAX?ROLL_MAX:(int)next);
}
static int roll_radius(int paper) {return 35-paper*22/240;}
static int roll_tail(int paper) {return 89+paper;}
