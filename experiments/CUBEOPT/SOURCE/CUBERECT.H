/* Conservative bounds for the one-pixel cosmetic pen and its filled faces.
   Right/bottom are exclusive. No bitmap bytes outside dirty are transferred. */
#ifndef CUBERECT_H
#define CUBERECT_H
typedef struct { int left,top,right,bottom; } CBOX;
static void CubeDirtyBounds(const CFRAME *f,int width,int height,
 const CBOX *previous,int havePrevious,CBOX *current,CBOX *dirty)
{
 int n,x,y;
 current->left=current->right=f->point[0].x;
 current->top=current->bottom=f->point[0].y;
 for(n=1;n<8;n++){
  x=f->point[n].x;y=f->point[n].y;
  if(x<current->left)current->left=x;
  if(x>current->right)current->right=x;
  if(y<current->top)current->top=y;
  if(y>current->bottom)current->bottom=y;
 }
 current->left=current->left>0?current->left-1:0;
 current->top=current->top>0?current->top-1:0;
 current->right=current->right<width-1?current->right+2:width;
 current->bottom=current->bottom<height-1?current->bottom+2:height;
 *dirty=*current;
 if(havePrevious){
  if(previous->left<dirty->left)dirty->left=previous->left;
  if(previous->top<dirty->top)dirty->top=previous->top;
  if(previous->right>dirty->right)dirty->right=previous->right;
  if(previous->bottom>dirty->bottom)dirty->bottom=previous->bottom;
 }
}
#endif
