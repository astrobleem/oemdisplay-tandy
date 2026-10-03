/* Independent ABI declarations transcribed from Microsoft SDK 3.1,
   Programmer's Reference Vol2 p413. No implementation header is used. */
#pragma pack(1)
typedef struct tagOFNTEST {
 DWORD lStructSize; HWND hwndOwner; HINSTANCE hInstance;
 LPCSTR lpstrFilter; LPSTR lpstrCustomFilter; DWORD nMaxCustFilter;
 DWORD nFilterIndex; LPSTR lpstrFile; DWORD nMaxFile;
 LPSTR lpstrFileTitle; DWORD nMaxFileTitle; LPCSTR lpstrInitialDir;
 LPCSTR lpstrTitle; DWORD Flags; UINT nFileOffset; UINT nFileExtension;
 LPCSTR lpstrDefExt; LPARAM lCustData;
 UINT (FAR PASCAL *lpfnHook)(HWND,UINT,WPARAM,LPARAM);
 LPCSTR lpTemplateName;
} OFNTEST;
#pragma pack()
BOOL FAR PASCAL GetOpenFileName(OFNTEST FAR *);
BOOL FAR PASCAL GetSaveFileName(OFNTEST FAR *);
DWORD FAR PASCAL CommDlgExtendedError(void);
int FAR PASCAL GetFileTitle(LPCSTR,LPSTR,UINT);
