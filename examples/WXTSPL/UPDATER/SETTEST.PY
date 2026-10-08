"""Check the existing-install Setup route in an actual TINST-generated fixture.

This checks the caller's working directory and absolute OEM source path.
Native Setup completion is separate evidence; this does not emulate Setup.
"""
from pathlib import Path
import re,sys,ntpath

def verify(guest):
    guest=Path(guest);support=guest/'WINXT';win=guest/'WINDOWS'
    assert (win/'WIN.COM').is_file() and (win/'SYSTEM.INI').is_file()
    batch=(support/'WINXT.BAT').read_text(encoding='ascii')
    sections=re.split(r'(?mi)^:SETUP\s*$',batch)
    assert len(sections)==2,'one Setup branch required'
    route=sections[1].split(':RECFAIL')[0].splitlines();cwd=None;executed=False
    for raw in route:
        line=raw.strip()
        if line.upper().startswith('CD '):cwd=ntpath.normpath(line[3:]).upper()
        if re.fullmatch(r'[A-Za-z]:\\.+\\SETUP\.EXE',line,re.I):
            assert ntpath.dirname(line).upper()==r'C:\WINDOWS','use owned Windows Setup'
            assert cwd==r'C:\WINDOWS','Setup must see the existing WIN.COM and SYSTEM.INI in its working directory'
            executed=True;break
    assert executed,'explicit owned Setup call required'
    inf=(support/'OEMSETUP.INF').read_text(encoding='ascii')
    disks=re.split(r'(?mi)^\[disks\]\s*$',inf);assert len(disks)==2
    source=disks[1].split('[')[0]
    assert re.search(r'(?mi)^a\s*=\s*C:\\WINXT\s*,',source),'OEM source must stay absolute while Setup runs in Windows'
    return {'route':'existing Windows configuration','cwd':cwd,'oem_source':r'C:\WINXT'}

if __name__=='__main__':print(verify(sys.argv[1]))
