#!/usr/bin/env python3
"""Stage the existing native INI transaction for the CGA-only installer.

The original T80SET.C and all published installers stay byte-identical.
Only the private staged copy gets CGA names, selected fonts, 286grabber and
one-pixel compact borders. SETUP.C owns payload verification/copying.
"""
import hashlib
from pathlib import Path
from STAGECGA import read, write, once

T80_SHA = 'd9108e8460b816a1be49886461dda80d77509d19ef9ef6a1e9dffccabdc35a3b'
CRC_SHA = 'dd29ef85d0e3f6935fd7eaa0e416f553f29283f96d597f5fec2698035efd5ed8'
HERE = Path(__file__).resolve().parent


def ini_source(repo):
    raw=(repo/'src/text80/T80SET.C').read_bytes()
    if hashlib.sha256(raw).hexdigest()!=T80_SHA:
        raise ValueError('Unreviewed T80SET.C transaction input')
    s=raw.replace(b'\r\n',b'\n').decode('ascii')
    s=once(s,'static char drv[40], sysset[4][60], helper[40];',
           'static char drv[40], sysset[5][60], helper[40];')
    s=once(s,'const char *sset[4], *fadd[2], *wset[2];',
           'const char *sset[5], *fadd[2], *wset[2];')
    for old,new in (
        ('strcpy(sysset[1], "fonts.fon=XTTSYS.FON");',
         'strcpy(sysset[1], cga_small ? "fonts.fon=CG1SYS.FON" : cga_medium ? "fonts.fon=CG2SYS.FON" : "fonts.fon=XTCSYS.FON");'),
        ('strcpy(sysset[2], "fixedfon.fon=XTCFIX.FON");',
         'strcpy(sysset[2], (cga_small || cga_medium) ? "fixedfon.fon=CG1FIX.FON" : "fixedfon.fon=XTCFIX.FON");'),
        ('strcpy(sysset[3], "oemfonts.fon=XTCOEM.FON");',
         'strcpy(sysset[3], (cga_small || cga_medium) ? "oemfonts.fon=CG1OEM.FON" : "oemfonts.fon=XTCOEM.FON");\n'
         '        strcpy(sysset[4], "286grabber=CGAGRAB.GR2");'),
        ('sset[3] = sysset[3];','sset[3] = sysset[3];\n        sset[4] = sysset[4];'),
        ('edit(\'S\', "[boot]", sset, 4, NULL, 0, NULL)',
         'edit(\'S\', "[boot]", sset, 5, NULL, 0, NULL)'),
        ('"Helv 8x8 (TEXT80)=T80HELV.FON"','cga_small ? "Helv 3x5 (CGA100)=CG1HELV.FON" : cga_medium ? "Helv 4x6 (CGA320)=CG2HELV.FON" : "Helv 8x8 (CGA640)=T80HELV.FON"'),
        ('"Courier 8x8 (TEXT80)=T80COUR.FON"','cga_small ? "Courier 4x5 (CGA100)=CG1COUR.FON" : cga_medium ? "Courier 4x6 (CGA320)=CG1FIX.FON" : "Courier 8x8 (CGA640)=T80COUR.FON"'),
    ): s=once(s,old,new)
    s=s.replace('SYSTEM.T80','SYSTEM.CG0').replace('WIN.T80','WIN.CG0')
    s=s.replace('.T8N','.CGN').replace('.T8O','.CGO')
    s=s.replace('T80SET','CGASET').replace('TEXT80','CGA').replace('BorderWidth=7','BorderWidth=1')
    s=s.replace('8x8 system/fixed/OEM fonts','selected system/fixed/OEM fonts')
    # Leave room for CRC/copy state, three C6 stream buffers and a 4 KB stack
    # in the 64 KB small-model data group. The 20 KB candidate left only
    # 1.5 KB of heap; progress output could make payload I/O unbuffered.
    # Oversized INIs are refused before configuration changes.
    s=s.replace('24000','18000')
    s=once(s,'        remove(in(OLDF[0]));\n        remove(in(OLDF[1]));\n        return 1;',
           '        if (remove(in(OLDF[0])) || remove(in(OLDF[1]))) return -1;\n        return 1;')
    # Record successful restoration before discarding any safety/state files.
    # Root SETUP can then retry only its own cleanup if a deletion fails.
    s=once(s,'    remove(in("SYSTEM.CG0"));\n    remove(in("WIN.CG0"));\n    remove(in("CGASET.STA"));\n    printf(',
           '    if (!cga_discard()) return fail("settings restored; cleanup marker failed, backups kept");\n'
           '    remove(in("SYSTEM.CG0"));\n    remove(in("WIN.CG0"));\n    remove(in("CGASET.STA"));\n    printf(')
    s=once(s,'        remove(in("CGASET.STA"));\n        remove(in("SYSTEM.CG0"));\n        remove(in("WIN.CG0"));\n        printf(',
           '        if (!cga_discard()) return fail("settings restored; cleanup marker failed, backups kept");\n'
           '        remove(in("CGASET.STA"));\n        remove(in("SYSTEM.CG0"));\n        remove(in("WIN.CG0"));\n        printf(')
    s=s.replace('CGASET:','SETUP:').replace('CGASET OFF','SETUP UNDO').replace('CGASET RESTORE','SETUP RESTORE')
    return ('/* Generated CGA adaptation of the exact retained T80SET transaction. */\n'
            '#define main cga_ini_main\n'+s+'\n#undef main\n')


def stage(repo,out,header):
    crc=repo/'tools/DOSINST/CRCFAST.H'
    if hashlib.sha256(crc.read_bytes()).hexdigest()!=CRC_SHA:
        raise ValueError('Unreviewed shared CRC header')
    out.mkdir(parents=True,exist_ok=False)
    write(out/'INICGA.C',ini_source(repo))
    (out/'SETUP.C').write_bytes((HERE/'SETUP.C').read_bytes())
    (out/'CRCFAST.H').write_bytes(crc.read_bytes())
    write(out/'CGAPINS.H',header)
    return {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in out.iterdir()}
