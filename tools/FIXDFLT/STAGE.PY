"""Private fixed-default installer staging; never accepts or publishes runtime."""
from pathlib import Path
import argparse
import ast
import difflib
import hashlib
import importlib.machinery
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
APP = ('XTPAN.EXE', 'XYCTL.EXE', 'PANCTL.EXE', 'CGACTL.EXE',
       'PANCFG.EXE', 'PAN.EXE', 'PANKEY.DLL')
FIXED = 'TANDY88.DRV'
# Focused native 8088 qualification: stock metrics, bounds, 24 matched frames.
# This binding does not grant release acceptance to the new installer.
FIXED_BYTES = 58864
FIXED_SHA256 = '4486e4afc7656d80b8b0e9033b14919887373f30f97d77b860e4d38763b4f3e0'
HPXY_HOTFIX_BYTES = 62272
HPXY_HOTFIX_SHA256 = '42131bc4e8a131c3e2b7ab927fe4bc640d9b816c8377a1ca9aea5a3bd6fd4bfc'


def require(ok, message):
    if not ok:
        raise ValueError(message)


def once(text, before, after):
    require(text.count(before) == 1, 'Changed adaptation anchor: ' + before[:80])
    return text.replace(before, after)


def write(path, text):
    path.write_bytes(text.replace('\r\n', '\n').replace('\n', '\r\n').encode('ascii'))


def ctext(text):
    # C and JSON agree for the ASCII/control characters used by this recipe.
    import json
    return json.dumps(text, ensure_ascii=True)


def profile_source(source):
    """Preserve live display choices, including displays from other packets."""
    a = source.index('static int profile(void)')
    b = source.index('static void not_windows(void)', a)
    return source[:a] + '''static int profile(void){char v[300],p[PTH],*comment;
 /* The live Windows selection wins over stale PROFILE.TXT. Only MODEXT's
    explicit switches change it. Fresh Setup already selects our default. */
 if(inivalue("display.drv",v)!=1)stop("Missing display selection","");
 comment=strchr(v,';');if(comment)*comment=0;trim(v);
 if(!*v)stop("Empty display selection","");
 if(!stricmp(v,"XRSYNC.DRV")){
  path(p,sys,"XRSYNC.DRV");
  if(kind(p)!=1)stop("Selected XRSYNC driver is missing",p);
  return KEEP_XRSYNC;
 }
 if(forced>=0)return forced;
 if(!stricmp(v,"TANDY88.DRV"))return FIXED_320;
 if(!stricmp(v,"HPXY.DRV"))return 3;
 /* This package does not repair other drivers or their font/startup state. */
 return KEEP_DISPLAY;
}
''' + source[b:]


def adapt_finisher(source, files, setup_size):
    source = once(source, '#define KEEP_XRSYNC 4',
                  '#define KEEP_XRSYNC 4\n#define FIXED_320 5\n#define KEEP_DISPLAY 6\n'
                  '#define FIXED_BYTES %dUL\n#define FIXED_CRC 0x%08xUL' %
                  (len(files['WINXT/'+FIXED]),zlib.crc32(files['WINXT/'+FIXED])))
    source = profile_source(source)
    # Extend the already-staged current inventory without modifying old pins.
    for declaration, extra in [
        ('static const char *names[]', ['"TANDY88.DRV"', '"XTESYS.FON"', '"XTEFIX.FON"', '"XTEOEM.FON"']),
        ('static unsigned long sizes[]', [str(len(files['WINXT/' + n])) + 'UL'
                                         for n in (FIXED, 'XTESYS.FON', 'XTEFIX.FON', 'XTEOEM.FON')]),
        ('static int target[]', ['1', '1', '1', '1']),
    ]:
        match = re.search(re.escape(declaration) + r'=\{(.*?)\};', source)
        require(match is not None, 'Missing finisher inventory')
        source = source[:match.start(1)] + match[1] + ',' + ','.join(extra) + source[match.end(1):]
    match = re.search(r'#define COUNT (\d+)', source)
    source = source[:match.start(1)] + str(int(match[1]) + 4) + source[match.end(1):]
    names = re.findall(r'"([A-Z0-9.]+)"', re.search(r'static const char \*names\[\]=\{(.*?)\};', source)[1])
    match = re.search(r'static unsigned long sizes\[\]=\{(.*?)\};', source)
    sizes = match[1].split(',')
    for i, name in enumerate(names):
        if name == 'SETUP.INF':
            sizes[i] = str(setup_size) + 'UL'
        elif 'WINXT/' + name in files:
            sizes[i] = str(len(files['WINXT/' + name])) + 'UL'
    source = source[:match.start(1)] + ','.join(sizes) + source[match.end(1):]
    source = source.replace('mode==KEEP_XRSYNC', '(mode==KEEP_XRSYNC||mode==KEEP_DISPLAY)')
    source = source.replace('mode!=KEEP_XRSYNC', '(mode!=KEEP_XRSYNC&&mode!=KEEP_DISPLAY)')
    # Register new optional Setup choices during UPDATE without changing the
    # selected foreign display, fonts, grabber or panning startup.
    source = once(source,
                  'if((mode==KEEP_XRSYNC||mode==KEEP_DISPLAY)&&display_payload(names[i]))',
                  'if((mode==KEEP_XRSYNC||(mode==KEEP_DISPLAY&&stricmp(names[i],"SETUP.INF")))&&display_payload(names[i]))')
    source = once(source, 'return !stricmp(name,"C216N6.DRV")',
                  'return !stricmp(name,"TANDY88.DRV")||!stricmp(name,"XTESYS.FON")||\n'
                  '  !stricmp(name,"XTEFIX.FON")||!stricmp(name,"XTEOEM.FON")||!stricmp(name,"C216N6.DRV")')
    source = once(source, 'if((!stricmp(names[i],"C216N6.DRV")',
                  'if((!stricmp(names[i],"TANDY88.DRV")&&mode!=FIXED_320)||\n'
                  '     ((!stricmp(names[i],"XTESYS.FON")||!stricmp(names[i],"XTEFIX.FON")||!stricmp(names[i],"XTEOEM.FON"))&&mode!=FIXED_320)||\n'
                  '     (!stricmp(names[i],"XTCOEM.FON")&&mode==FIXED_320)||(!stricmp(names[i],"C216N6.DRV")')
    source = once(source, '&&mode==0)){needs[i]=0;continue;}',
                  '&&(mode==0||mode==FIXED_320))){needs[i]=0;continue;}')
    source = once(source, 'changeini("boot","display.drv",mode==3?',
                  'changeini("boot","display.drv",mode==FIXED_320?"TANDY88.DRV":mode==3?')
    source = once(source, 'changeini("boot","fonts.fon",mode?',
                  'changeini("boot","fonts.fon",mode==FIXED_320?"XTESYS.FON":mode?')
    source = once(source, 'changeini("boot","fixedfon.fon",mode?',
                  'changeini("boot","fixedfon.fon",mode==FIXED_320?"XTEFIX.FON":mode?')
    source = once(source, 'changeini("boot","oemfonts.fon","XTCOEM.FON")',
                  'changeini("boot","oemfonts.fon",mode==FIXED_320?"XTEOEM.FON":"XTCOEM.FON")')
    source = once(source, 'changeini("boot.description","display.drv",mode==3?',
                  'changeini("boot.description","display.drv",mode==FIXED_320?"Tandy EX/HX 320x200 16 colors, no panning":mode==3?')
    # Legacy /320 meant compact C23216. The new explicit choice is stock-metric fixed.
    source = once(source, 'stricmp(argv[i],"/320")){forced=1;',
                  'stricmp(argv[i],"/320")){forced=FIXED_320;')
    source = once(source, 'mode==3?"HPXY.DRV":mode==2?"PANCMP2.DRV":mode==1?',
                  'mode==FIXED_320?"TANDY88.DRV":mode==3?"HPXY.DRV":mode==2?"PANCMP2.DRV":mode==1?')
    source = once(source, ' path(p,home,"PROFILE.TXT");sprintf(v,',
                  ' if(mode!=KEEP_DISPLAY){path(p,home,"PROFILE.TXT");sprintf(v,')
    source = once(source, 'commit(home,"PROFILE.TXT",n,o,j);}',
                  'commit(home,"PROFILE.TXT",n,o,j);}}')
    # Full-byte comparison protects newly installed fixed display bytes as well.
    source = once(source, '!stricmp(leaf,HPXY_FILE))',
                  '!stricmp(leaf,HPXY_FILE)||!stricmp(leaf,"TANDY88.DRV"))')
    source = once(source, 'if(!stricmp(names[i],HPXY_FILE)&&',
                  'if(!stricmp(names[i],"TANDY88.DRV")&&!pinned_file(p,FIXED_BYTES,FIXED_CRC))stop("Fixed display source identity differs",p);\n'
                  '   if(!stricmp(names[i],HPXY_FILE)&&')
    # PANINT owns pan tokens and migration. This earlier helper owns the wheel.
    source = once(source,
                  'return !stricmp(leaf,"XTPAN.EXE")||!stricmp(leaf,"XYCTL.EXE")||!stricmp(leaf,"WXTWHL.EXE");',
                  'return !stricmp(leaf,"WXTWHL.EXE");')
    return source


def setup_bytes(header, stock):
    require(len(stock) == 49046 and hashlib.sha256(stock).hexdigest() ==
            '4f4b65bdc0ce2d4a23859494f8936376296e857872a554b0037ceb068f2202f2',
            'Exact original Windows Setup metadata required')
    body = header.split('static struct patch_op operations[]={', 1)[1].split('\n};', 1)[0]
    out = bytearray()
    for start, end, text in re.findall(r'\{(\d+),(\d+),(NULL|"(?:[^"\\]|\\.)*")\},', body):
        out.extend(stock[int(start):int(end)] if text == 'NULL' else ast.literal_eval(text).encode('ascii'))
    return bytes(out)


def adapt_operations(header):
    fixed = 'a:TANDY88.DRV, \\"Tandy EX/HX 320x200 16 colors (no panning)\\", \\"133,96,72\\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE'
    old = 'cga = a:HPXY.DRV, \\"Tandy EX/HX HPXY 640x256 hardware pan\\", \\"200,96,48\\", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE'
    header = once(header, old, 'cga = ' + fixed)
    header = once(header, '\\r\\nhpxy = a:HPXY.DRV',
                  '\\r\\nfixed = ' + fixed + '\\r\\nhpxy = a:HPXY.DRV')
    header = once(header, '        hpxy\\r\\n        sound',
                  '        fixed\\r\\n        sound')
    return header


def migration_header(previous, current):
    lines = ['/* Private exact-metadata migration; no owned input is embedded. */',
             'static void default_setup(unsigned size){', ' unsigned o=0;']
    for number, (old, _) in enumerate(previous):
        lines.append((' if' if not number else ' else if') + '(size==%dU){' % len(old))
        old_lines, new_lines = old.splitlines(keepends=True), current.splitlines(keepends=True)
        old_offsets = [0]
        for line in old_lines:
            old_offsets.append(old_offsets[-1]+len(line))
        for tag, a, b, c, d in difflib.SequenceMatcher(None,old_lines,new_lines,autojunk=False).get_opcodes():
            if tag == 'equal':
                size=old_offsets[b]-old_offsets[a]
                lines.append('  memcpy(setup_result+o,setup_bytes+%dU,%dU);o+=%dU;' % (old_offsets[a],size,size))
            elif tag in ('insert', 'replace'):
                body=b''.join(new_lines[c:d]);text=body.decode('ascii')
                lines.append('  memcpy(setup_result+o,%s,%dU);o+=%dU;' % (ctext(text),len(body),len(body)))
        lines.append(' }')
    lines += [' else stop("Unsupported prior Setup metadata","");',
              ' if(o!=SETUP_BYTES||(crc_add(0xffffffffUL,setup_result,o)^0xffffffffUL)!=SETUP_OUTPUT_CRC)',
              '  stop("Fixed-default Setup metadata conversion failed","");',
              ' setup_used=o;', '}']
    return '\n'.join(lines) + '\n'


def adapt_preparer(source, previous):
    source = once(source, '#include "TGUPSET.H"', '#include "DFSETUP.H"')
    source = once(source, '  49840U\n#else', '  SETUP_BYTES\n#else')
    a = source.index('#ifdef EXPANDED_SETUP\n else if(!locate_input("SETUP.INF",49046UL,path)')
    b = source.index('#endif', a)
    choices = ['#ifdef EXPANDED_SETUP']
    for old, crc in previous:
        size = len(old)
        choices.append(''' else if(!locate_input("SETUP.INF",49046UL,path)&&!locate_input("SETUP.INF",49095UL,path)&&locate_input("SETUP.INF",%dUL,path)){
  memset(&setup_sink,0,sizeof(setup_sink));setup_sink.memory=setup_bytes;setup_sink.limit=%dUL;
  read_stream(path,%dUL,&setup_sink);
  if((crc_add(0xffffffffUL,setup_bytes,%dU)^0xffffffffUL)!=0x%08xUL)stop("Prior canonical Setup metadata differs.",path);
  default_setup(%dU);ready_setup=1;
 }''' % (size, size, size, size, crc, size))
    return source[:a] + '\n'.join(choices) + '\n' + source[b:]


def ordinary(source):
    fixed = 'fixed = a:TANDY88.DRV, "Tandy EX/HX 320x200 16 colors (no panning)", "133,96,72", a:TANDYGR.GR2, a:XTSTATIC.LGO,,,, a:WXTSPL01.RLE\n'
    source = once(source, '[display]\n', '[display]\n' + fixed)
    source = once(source, '[sysfonts]\n', '[sysfonts]\na:XTESYS.FON, "XT EGA System", "133,96,72"\n')
    source = once(source, '[fixedfonts]\n', '[fixedfonts]\na:XTEFIX.FON, "XT EGA Fixed", "133,96,72"\n')
    source = once(source, '[oemfonts]\n', '[oemfonts]\na:XTEOEM.FON, "XT EGA Terminal", "133,96,72",1\n')
    return once(source, '        hpxy\n', '        fixed\n')


def computer_source(source, metadata):
    size, crc = len(metadata), zlib.crc32(metadata)
    source = once(source,
                  'if(on!=49840U&&(on!=49848U||current_metadata_crc()!=0x073140f6UL))',
                  'if((on!=49840U||current_metadata_crc()!=0x0cf60179UL)&&\n'
                  '    (on!=49848U||current_metadata_crc()!=0x073140f6UL)&&\n'
                  '    (on!=%dU||current_metadata_crc()!=0x%08xUL))' % (size,crc))
    source = once(source,
                  'if(size!=49848U||on!=49848U||n!=strlen(previous)||memcmp(names,previous,n))\n   die("Foreign/stale Computer completion marker.");',
                  'if((size!=49848U||on!=49848U||n!=strlen(previous)||memcmp(names,previous,n))){\n'
                  '   if(size!=%dU||on!=%dU)die("Foreign/stale Computer completion marker.");\n'
                  '   if(n!=strlen(previous)||memcmp(names,previous,n)){\n'
                  '    marker_text(previous,49848U);\n'
                  '    if(n!=strlen(previous)||memcmp(names,previous,n))die("Foreign/stale Computer completion marker.");\n'
                  '   }\n  }' % (size,size))
    return source


def payload(files):
    files = dict(files)
    bat = files['WINXT/SETUPXT.BAT'].decode('ascii').replace('\r\n', '\n')
    bat = once(bat, 'ECHO Its preset selects HPXY 640x256 desktop, PC/XT Hold and COM1 wheel mouse.',
               'ECHO Its preset selects 320x200 16 colors without panning, PC/XT Hold and COM1 wheel mouse.')
    bat = once(bat, 'ECHO Hardware panning is available through XYCTL after Windows starts.',
               'ECHO HPXY is optional. Select it in Setup or later use MODEXT /XR1.')
    require(bat.count('C:\\WINXT /XR1 %1') == 2, 'Changed forced Setup profile')
    bat = bat.replace('C:\\WINXT /XR1 %1', 'C:\\WINXT %1')
    files['WINXT/SETUPXT.BAT'] = bat.replace('\n', '\r\n').encode('ascii')
    files['WINXT/MODEXT.BAT'] = b'''@ECHO OFF\r
IF "%1"=="/320" GOTO SELECT\r
IF "%1"=="/XR1" GOTO SELECT\r
ECHO Use MODEXT /320 for 320x200 16 colors without panning.\r
ECHO Use MODEXT /XR1 for the optional HPXY panning desktop.\r
GOTO DONE\r
:SELECT\r
C:\\WINXT\\FIXXT.EXE REPAIR C:\\WINDOWS C:\\WINXT %1\r
IF ERRORLEVEL 1 GOTO BAD\r
C:\\WINXT\\CPSET.EXE APPLY C:\\WINDOWS\r
IF ERRORLEVEL 1 GOTO BAD\r
ECHO Display selected. Run C:\\STARTXT from plain DOS.\r
GOTO DONE\r
:BAD\r
ECHO Profile repair stopped. Read the stated error.\r
:DONE\r
'''
    files['WINXT/OEMSETUP.INF'] = ordinary(files['WINXT/OEMSETUP.INF'].decode('ascii').replace('\r\n', '\n')).replace('\n', '\r\n').encode('ascii')
    text = files['README.TXT'].decode('ascii').replace('\r\n', '\n')
    text = once(text, 'Use C:\\STARTXT on every later launch.',
                'The new-install default is 320x200, 16 colors, without panning.\n'
                'HPXY remains an optional display choice in Windows Setup.\n'
                'An update retains the selected display and panning choice.\n'
                'Use C:\\STARTXT on every later launch. From DOS, MODEXT /320\n'
                'selects fixed 320x200; MODEXT /XR1 selects optional HPXY.')
    text = once(text, 'choose Display, Other, enter that folder and select Tandy EX/HX HPXY.',
                'choose Display, Other, enter that folder and select fixed 320x200\n'
                '16 colors or the optional Tandy EX/HX HPXY panning display.')
    files['README.TXT'] = text.replace('\n','\r\n').encode('ascii')
    files['WINXT/PROFILES.TXT'] = (
        'WINDOWS XT DISPLAY\r\n\r\n'
        'New installs default to fixed 320x200, 16 colors, without panning.\r\n'
        'Existing installations keep their selected display.\r\n'
        'From plain DOS use C:\\MODEXT /320 for fixed 320x200, or\r\n'
        'C:\\MODEXT /XR1 for the optional HPXY 640x256 panning desktop.\r\n'
        'Start Windows with C:\\STARTXT. PAN /SETTINGS enables optional\r\n'
        'window-workspace panning on fixed displays when you choose it.\r\n').encode('ascii')
    text = files['WINXT/START.TXT'].decode('ascii').replace('\r\n','\n')
    text = once(text, 'The desktop is 640x256 through a 320x200 sixteen-colour viewport.\nXYCTL starts in Software mode.',
                'The default desktop is fixed 320x200, 16 colors, without panning.\n'
                'MODEXT /XR1 selects optional HPXY; MODEXT /320 returns to fixed.\n'
                'For optional HPXY, XYCTL starts in Software mode.')
    files['WINXT/START.TXT'] = text.replace('\n','\r\n').encode('ascii')
    return files


def aliases(native, files, metadata):
    """Bind staged inputs and all destination counts, including one-copy scripts."""
    pins = (native/'SETPINS.H').read_text('ascii')
    recipe = (native/'SETFILES.H').read_text('ascii')
    crcs = (native/'SETINPUT.H').read_text('ascii')
    for key, body in files.items():
        if not key.startswith('WINXT/') or '/' in key[6:]:
            continue
        name = key[6:]
        row = '{"%s","%s",%dUL,0,0x%08xUL}' % (name, hashlib.sha256(body).hexdigest(), len(body), zlib.crc32(body))
        pattern = r'\{"'+re.escape(name)+r'","[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL\}'
        if re.search(pattern, pins):
            pins, count = re.subn(pattern, lambda _: row, pins)
            require(count == 1, 'Duplicate native input: ' + name)
        else:
            pins = once(pins, '};', row + ',\n};')
        recipe = re.sub(r'(,"'+re.escape(name)+r'",)\d+UL(,0\})',
                        lambda m: m[1] + str(len(body)) + 'UL' + m[2], recipe)
        # Full preparation retains the complete supplied source folder.
        destinations = ['WINXT\\\\'+name]
        if name in APP + (FIXED, 'XTESYS.FON', 'XTEFIX.FON', 'XTEOEM.FON'):
            destinations.append('WINXT\\\\FILES\\\\'+name)
        if name == FIXED:
            destinations.append('W30\\\\'+name)
        for path in destinations:
            if '{"'+path+'",' in recipe:
                continue
            row = '{"%s","%s",%dUL,0},\n' % (path, name, len(body))
            recipe = once(recipe, '};\n#define NFILES', row + '};\n#define NFILES')
            crcs = once(crcs, '};', '0x00000000UL, /* '+path+' */\n};')
    recipe = re.sub(r'(,"SETUP.INF",)\d+UL(,2\})', lambda m: m[1]+str(len(metadata))+'UL'+m[2], recipe)
    recipe = re.sub(r'#define SETUP_OUTPUT_SHA "[0-9a-f]+"', '#define SETUP_OUTPUT_SHA "'+hashlib.sha256(metadata).hexdigest()+'"', recipe)
    recipe = re.sub(r'#define SETUP_OUTPUT_CRC 0x[0-9a-f]+UL', '#define SETUP_OUTPUT_CRC 0x%08xUL' % zlib.crc32(metadata), recipe)
    rows = re.findall(r'\{"([^"\n]+)","[^"\n]+",\d+UL,[0-4]\}', recipe)
    setup = (native/'SETUP.C').read_text('ascii')
    for define, count in [('FRESH_COUNT',len(rows)),('UPDATE_COUNT',sum(not n.startswith('W30\\\\') for n in rows)),('SETUP_BYTES',len(metadata))]:
        setup, n = re.subn(r'(#define '+define+r' )\d+U?', lambda m: m[1]+str(count)+('U' if define=='SETUP_BYTES' else ''), setup)
        require(n == 1, 'Missing native count: ' + define)
    for name, text in [('SETPINS.H',pins),('SETFILES.H',recipe),('SETINPUT.H',crcs),('SETUP.C',setup)]:
        write(native/name,text)
    return len(rows), sum(not n.startswith('W30\\\\') for n in rows)


def stage(repo, baseline, fixed, stock, out, watcom=None, hpxy=None):
    require(not out.exists(), 'Fresh private output directory required')
    loader = importlib.machinery.SourceFileLoader
    q = loader('fixed_default_accepted', str(repo/'tools/HPDIB/PUBLISH.PY')).load_module()
    files = q.verify_core(baseline.read_bytes())
    driver = fixed.read_bytes()
    q.P.native(driver, True)
    require(len(driver)==FIXED_BYTES and hashlib.sha256(driver).hexdigest()==FIXED_SHA256,
            'Fixed input differs from the qualified stock-metric 320x200x16 build')
    files['WINXT/'+FIXED] = driver
    if hpxy is not None:
        hp=hpxy.read_bytes();q.P.native(hp,True)
        require(len(hp)==HPXY_HOTFIX_BYTES and hashlib.sha256(hp).hexdigest()==HPXY_HOTFIX_SHA256,
                'HPXY input differs from the qualified Output/text hotfix')
        files['WINXT/HPXY.DRV']=hp
    files = payload(files)
    out.mkdir(parents=True)
    native = out/'native'
    staging = q.M.S
    # Historical adaptation stages sources and normally compiles immediately.
    # Defer that compile until after the complete fixed-default overlay.
    compile_native = staging.N.compile_native
    staging.N.compile_native = lambda *args, **kwargs: b''
    try:
        staging.stage(native, {n:files['WINXT/'+n] for n in APP}, watcom)
    finally:
        staging.N.compile_native = compile_native
    header = (native/'SETFILES.H').read_text('ascii')
    original = setup_bytes(header, stock.read_bytes())
    require(len(original) == 49848 and zlib.crc32(original) == 0x073140f6, 'Changed current Setup metadata')
    # Also retain the exact preceding pre-grabber metadata migration.
    legacy = original.replace(b'a:TANDYGR.GR2', b'a:CGA.GR2')
    require(len(legacy) == 49840 and zlib.crc32(legacy) == 0x0cf60179, 'Changed prior Setup metadata')
    write(native/'SETFILES.H', adapt_operations(header))
    metadata = setup_bytes((native/'SETFILES.H').read_text('ascii'), stock.read_bytes())
    previous = [(original,zlib.crc32(original)),(legacy,zlib.crc32(legacy))]
    write(native/'DFSETUP.H',migration_header(previous,metadata))
    write(native/'XRPREP.C',adapt_preparer((native/'XRPREP.C').read_text('ascii'),previous))
    write(native/'FIXXT.C',adapt_finisher((native/'FIXXT.C').read_text('ascii'),files,len(metadata)))
    # The retained display-selection skip must also cover shared helper code.
    for name in ('TGINT.H','PANINT.H'):
        source = (native/name).read_text('ascii')
        source = source.replace('mode==KEEP_XRSYNC','(mode==KEEP_XRSYNC||mode==KEEP_DISPLAY)')
        if name == 'PANINT.H':
            source = once(source,
                          'if(automatic && (stricmp(marker,leaf)||pan_present("load")||pan_present("run")))',
                          'if((automatic&&stricmp(marker,leaf))||(!stricmp(marker,leaf)&&(pan_present("load")||pan_present("run"))))')
        write(native/name,source)
    hp = files['WINXT/HPXY.DRV']
    write(native/'HPXYID.H','#define HPXY_FILE "HPXY.DRV"\n#define HPXY_BYTES %dUL\n#define HPXY_CRC 0x%08xUL\n' % (len(hp),zlib.crc32(hp)))
    write(native/'CPSET.C',computer_source((repo/'tools/UPAN/CPSET.C').read_text('ascii'),metadata))
    counts = aliases(native,files,metadata)
    if watcom is None:
        return dict(status='SOURCES_STAGED_NOT_BUILT',out=str(out),setup_bytes=len(metadata),counts=counts)
    files['WINXT/CPSET.EXE'] = compile_native(native,watcom,'CPSET',True)
    # FIXXT checks the exact compiled companion size; then SETUP checks FIXXT.
    aliases_existing(native,'CPSET.EXE',files['WINXT/CPSET.EXE'])
    source=(native/'FIXXT.C').read_text('ascii')
    names=re.findall(r'"([A-Z0-9.]+)"',re.search(r'static const char \*names\[\]=\{(.*?)\};',source)[1])
    match=re.search(r'static unsigned long sizes\[\]=\{(.*?)\};',source)
    sizes=match[1].split(',');sizes[names.index('CPSET.EXE')]=str(len(files['WINXT/CPSET.EXE']))+'UL'
    write(native/'FIXXT.C',source[:match.start(1)]+','.join(sizes)+source[match.end(1):])
    fix = compile_native(native,watcom)
    files['WINXT/FIXXT.EXE'] = fix
    aliases_existing(native,'FIXXT.EXE',fix)
    files['SETUP.EXE'] = compile_native(native,watcom,'SETUP',True)
    # This is a private candidate, not the current producer or accepted package.
    expanded = out/'expanded'
    expanded.mkdir()
    for name,body in files.items():
        p=expanded/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(body)
    (out/'WINXT.ZIP').write_bytes(q.C.archive(files))
    return dict(status='PRIVATE_CANDIDATE_NOT_QUALIFIED',out=str(out),setup_bytes=len(metadata),counts=counts)


def aliases_existing(native,name,body):
    pins=(native/'SETPINS.H').read_text('ascii')
    pins,count=re.subn(r'(\{"'+re.escape(name)+r'",)"[0-9a-f]{64}",\d+UL,0,0x[0-9a-f]+UL',
                      lambda m:m[1]+'"%s",%dUL,0,0x%08xUL' % (hashlib.sha256(body).hexdigest(),len(body),zlib.crc32(body)),pins)
    require(count==1,'Missing compiled native input')
    files=(native/'SETFILES.H').read_text('ascii')
    files,count=re.subn(r'(,"'+re.escape(name)+r'",)\d+UL(,0\})',lambda m:m[1]+str(len(body))+'UL'+m[2],files)
    require(count==2,'Missing compiled native aliases')
    write(native/'SETPINS.H',pins);write(native/'SETFILES.H',files)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo',type=Path,default=ROOT)
    for name in ('baseline','fixed','setup-input','out'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--watcom',type=Path)
    parser.add_argument('--hpxy',type=Path)
    args=parser.parse_args()
    print(stage(args.repo.resolve(),args.baseline,args.fixed,args.setup_input,args.out,args.watcom,args.hpxy))


if __name__=='__main__':
    main()
