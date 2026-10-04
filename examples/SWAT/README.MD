FLY SWAT 1.1 - VISIBLE SWATTER FIX
================================

The swatter is now white with a black outline, including while idle,
swinging and paused. Both the windowed and fullscreen paths use the same
contrast mask. The windowed version no longer uses the stock crosshair.

UPDATE
------
Close Fly Swat. Keep a backup of your previous SWAT.EXE, then replace only
SWAT.EXE in your existing Fly Swat folder with this version. Launch it the
same way from your working Windows 3.0 setup. No display-driver installation
or Windows configuration change is required. No companion DLL is needed.

PLAY
----
Click in the field or click NEW to start. Move the swatter with the mouse.
Click a fly for 10 points. Empty clicks or escaped flies cost one of three
hearts. PAUSE/PLAY, P or Space pauses/resumes. NEW, N or R starts again.
EXIT or Esc closes. One fly at a time; no sound or saved high score.

The original exact driver-name safety check is unchanged. Accepted legacy
TANDY88 names select fast fullscreen; other names, including the current
TRIAL aliases, select the normal windowed GDI path. /G forces windowed play.
Fullscreen closes on focus loss; windowed play pauses.

Game rules, score, hitboxes and timer interval are unchanged. This build
passed automated native Windows 3.0 checks in five display formats. The
updated pointer still needs confirmation on your physical Tandy.

Development switches run tests and write logs; omit them for normal play.
Matching C/build/test files are in this directory. TESTS.MD summarizes
recorded native coverage and remaining limits; no raw reports or screenshots
are added by this follow-up. BUILDING.MD gives reproduction commands.
The original examples/TANDYLAB pack is unchanged historical content. Replace
only SWAT.EXE when applying this update to an existing installation.
