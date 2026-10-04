#include "ENGINE.H"
/* All copy fits an 18-column, four-line body. Keep this when adding events. */
EVENT events[EVENT_COUNT] = {
 {"BREAK ROOM COFFEE\nMACHINE FAILED.\nTOMORROW REQUIRES\nYOUR ASSISTANCE.",2,{
  {"1 Repair","COFFEE RESTORED.\nGRATITUDE WILL BE\nTAKEN FROM BREAK\nTIME.",{-8,14,0}},
  {"2 Remove coffee","HABIT REMOVED.\nFATIGUE IS NOW A\nPERSONAL CHOICE.",{10,-18,0}},
  {"","",{0,0,0}}}},
 {"EMPLOYEE #0047 IS\nUNCERTAIN ABOUT\nTOMORROW. PLEASE\nRESTORE CERTAINTY.",3,{
  {"1 Reassure","TOMORROW HAS BEEN\nEXPLAINED USING\nSMALLER WORDS.",{-4,12,2}},
  {"2 Retrain","TRAINING COMPLETE.\nCONFIDENCE IS UP.\nQUESTIONS HAVE\nDECREASED.",{14,-12,8}},
  {"3 Reassign","UNCERTAINTY MOVED\nTO ANOTHER SECTOR.\nLOCAL CONFIDENCE\nRESTORED.",{18,-22,10}}}},
 {"WHY IS BRIGHTNESS\nMANDATORY? ASKS\nEMPLOYEE #0038.\nA FINE QUESTION.",3,{
  {"1 Explain","BRIGHTER TOMORROW\nIS ITS OWN REASON.\nEMPLOYEE NODDED.",{-6,8,5}},
  {"2 Add light","LIGHT ISSUED.\nEYES MAY ADJUST\nDURING PERSONAL\nTIME.",{8,-10,22}},
  {"3 Lower standard","THE TARGET MOVED.\nTHE SUN HAS BEEN\nNOTIFIED.",{-4,4,-24}}}},
 {"EMPLOYEE #0012\nREQUESTS PERSONAL\nTIME. TOMORROW\nHAS OTHER PLANS.",3,{
  {"1 Approve","TIME GRANTED.\nPLEASE RETURN IT\nIN GOOD CONDITION.",{-14,18,-4}},
  {"2 Deny","PERSONAL TIME HAS\nBEEN RESCHEDULED\nFOR YESTERDAY.",{14,-18,4}},
  {"3 Improve morale","MORALE IMPROVEMENT\nIS NOW COMPULSORY.\nSMILING IS A\nRECORDABLE METRIC.",{8,-24,12}}}},
 {"UNAUTHORIZED\nSHADOW IN SECTOR B\nIT HAS NOT SIGNED\nTHE REGISTER.",2,{
  {"1 Investigate","SHADOW IDENTIFIED\nAS AN EMPLOYEE.\nLIGHTING REQUEST\nWITHDRAWN.",{-8,10,-10}},
  {"2 Add brightness","SHADOW NO LONGER\nREPORTED. BRIGHTER\nTOMORROW IS GLAD.",{12,-16,24}},
  {"","",{0,0,0}}}}
};
void ResetGame(GAME *g) {
 int i; for(i=0;i<3;++i) g->value[i]=60;
 g->event=0;g->phase=PLAYING;g->picked=-1;
}
int Choose(GAME *g,int choice) {
 int i,v;
 if(g->phase!=PLAYING || g->event<0 || g->event>=EVENT_COUNT ||
    choice<0 || choice>=events[g->event].count) return 0;
 g->picked=choice;
 for(i=0;i<3;++i) {
  v=g->value[i]+events[g->event].choice[choice].delta[i];
  if(v<0)v=0;if(v>100)v=100;g->value[i]=v;
 }
 g->phase=RECEIPT;return 1;
}
int ContinueGame(GAME *g) {
 int i;
 if(g->phase!=RECEIPT) return 0;
 for(i=0;i<3;++i) if(g->value[i]<=15) {g->phase=FAILURE;return 1;}
 if(g->event==EVENT_COUNT-1) {
  g->phase=SUCCESS;
  for(i=0;i<3;++i) if(g->value[i]<50)g->phase=FAILURE;
 } else {++g->event;g->phase=PLAYING;g->picked=-1;}
 return 1;
}
