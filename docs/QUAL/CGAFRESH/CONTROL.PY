from pathlib import Path
import json,time
out=Path(__file__).resolve().parent/'fresh-native-02'
stage=0;sent=-1;since=None;start=time.monotonic()
while time.monotonic()-start<700:
    if (out/'RESULT.json').exists():break
    try:live=json.loads((out/'LIVE.json').read_text());txt=(out/'SCREEN.txt').read_text(encoding='utf-8')
    except (OSError,ValueError):time.sleep(1);continue
    if (out/'ACTION.json').exists() or live['actions']<=sent:time.sleep(1);continue
    action=None
    if stage==0 and 'Please insert the: Windows XT CGA fresh Setup' in txt:
        action=dict(contains='Windows XT CGA fresh Setup',keys='{HOME}'+'{DEL}'*24+r'C:\CGAPK\FRESH640'+'{ENTER}',settle=3);stage=1
    elif stage==1 and 'No Changes:' in txt and 'Display:         Windows XT IBM CGA' in txt:
        action=dict(contains='No Changes:',keys='{ENTER}',capture='SELECTED',settle=3);stage=2
    elif stage==2 and 'Microsoft Windows 3.0 Disk #1' in txt:
        action=dict(contains='Microsoft Windows 3.0 Disk #1',keys='{HOME}'+'{DEL}'*24+r'C:\W30SRC'+'{ENTER}',settle=3);stage=3
    if stage>=2 and live['mode']==6:
        if since is None:since=time.monotonic();print('Graphical mode reached',live,flush=True)
        if time.monotonic()-since>45:action=dict(capture='GUI-EXACT-CANDIDATE');stage=4
    if action:
        sent=live['actions'];(out/'ACTION.json').write_text(json.dumps(action));print(stage,action,flush=True)
        if stage==4:break
    time.sleep(1)
print('Controller ended at stage',stage,flush=True)
