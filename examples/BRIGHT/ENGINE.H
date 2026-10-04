/* BRIGHT: deterministic game core, C89 / 16-bit int safe. */
#ifndef BRIGHT_ENGINE_H
#define BRIGHT_ENGINE_H
#define EVENT_COUNT 5
#define CHOICE_MAX 3
#define PLAYING 0
#define RECEIPT 1
#define SUCCESS 2
#define FAILURE 3
typedef struct { char *label; char *receipt; int delta[3]; } CHOICE;
typedef struct { char *text; int count; CHOICE choice[CHOICE_MAX]; } EVENT;
typedef struct { int value[3]; int event; int phase; int picked; } GAME;
extern EVENT events[EVENT_COUNT];
void ResetGame(GAME *g);
int Choose(GAME *g, int choice);
int ContinueGame(GAME *g);
#endif
