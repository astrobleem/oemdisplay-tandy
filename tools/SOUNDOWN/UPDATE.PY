"""Refresh the current XR1 consumer bytes from accepted native builds.

Developer integration only. Consumers run the downloaded native Setup.
No historical release/archive, Windows installation or foreign checkout changes.
"""
from pathlib import Path
import argparse
import hashlib
import io
import json
import os
import zipfile
import zlib

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
NAMES = {'TCHIME.EXE': 'chime3', 'XPCHIME.EXE': 'xpchime3',
         'TEXIT.EXE': 'texit3', 'TP.EXE': 'tp3', 'TSHELL.EXE': 'tshell3'}
SOURCE = {'TCHIME.EXE': 'src/win30/CHIME/TCHIME.C',
          'XPCHIME.EXE': 'src/win30/XPCHIME/XPCHIME.C',
          'TEXIT.EXE': 'src/win30/TEXIT/TEXIT.C',
          'TP.EXE': 'tools/WHEEL/WIN16/SOURCE/TP/TP.C + TPSOUND.C',
          'TSHELL.EXE': 'examples/TSHELL/TSHELL.C + TSBOOT.C',
          'FIXXT.EXE': 'tools/SOUNDOWN/FIXXT.C'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def identity(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def encoded(value):
    return (json.dumps(value, indent=2)+'\n').replace('\n', '\r\n').encode('ascii')


def native(directory, name, sound):
    record = json.loads((directory/'BUILD.JSON').read_bytes())
    sourcepins = record.get('source_pins')
    if sourcepins is not None:
        sources = {}
        for label, pin in sourcepins.items():
            prefix, relative = label.split('/', 2)[1:]
            require(prefix in ('oemdisplay-tandy', 'oemsound-tandy'),
                    'Unsupported native source root: '+label)
            path = (REPO if prefix == 'oemdisplay-tandy' else sound)/relative
            require(identity(path.read_bytes()) == pin, 'Stale source: '+label)
            require(identity((directory/path.name).read_bytes()) == pin,
                    'Changed staged source: '+label)
            sources[label] = pin
        pin = record['runtime'][name]
    else:
        sources = record['sources']
        base = sound/'src/win30/DRIVER' if name == 'SOUND.DRV' else HERE
        for label, pin in sources.items():
            require(identity((base/label).read_bytes()) == pin,
                    'Stale finisher source: '+label)
            require(identity((directory/label).read_bytes()) == pin,
                    'Changed staged finisher source: '+label)
        pin = record['runtime']
    binary = (directory/name).read_bytes()
    require(identity(binary) == pin, 'Native binary differs: '+name)
    process = json.loads((directory/'PROCESS.JSON').read_bytes())
    require(process.get('return') == 0 and process.get('owned_child_stopped')
            and process.get('lease_released') and 'error' not in process,
            'Native build did not complete/clean up: '+name)
    return binary, {'runtime': pin, 'sources': sources,
                    'build_record': identity((directory/'BUILD.JSON').read_bytes())}


def sound_source(sound, directory):
    source = sound/'src/win30/DRIVER'
    record = json.loads((directory/'BUILD.JSON').read_bytes())
    entries = {name: (source/name).read_bytes() for name in record['sources']}
    for name in ('BUILD.PY', 'RUNDOS.PY', 'SOUNDID.H', 'SOUNDID.JSON'):
        entries[name] = (source/name).read_bytes()
    entries['LICENSE'] = (sound/'LICENSE').read_bytes()
    entries['BUILD.JSN'] = (directory/'BUILD.JSON').read_bytes()
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in sorted(entries.items()):
            require('/' not in name and '\\' not in name and '..' not in name,
                    'Unsafe corresponding source name')
            info = zipfile.ZipInfo('SOUND/'+name, (1980, 1, 1, 0, 0, 0))
            info.external_attr = 0x20
            info.create_system = 0
            archive.writestr(info, data)
    return output.getvalue()


def integrate(args):
    kit = REPO/'tools/XR1PACK'
    binaries, records = {}, {}
    for name, directory in NAMES.items():
        binaries[name], records[name] = native(args.native/directory, name,
                                               args.sound_repo)
    binaries['FIXXT.EXE'], records['FIXXT.EXE'] = native(args.fixxt, 'FIXXT.EXE',
                                                        args.sound_repo)
    driver = args.native/'driver2'
    binaries['SOUND.DRV'], records['SOUND.DRV'] = native(driver, 'SOUND.DRV',
                                                        args.sound_repo)
    soundid = (args.sound_repo/'src/win30/DRIVER/SOUNDID.JSON').read_bytes()
    soundpin = json.loads(soundid)
    require(identity(binaries['SOUND.DRV']) ==
            {key: soundpin[key] for key in ('bytes', 'sha256')} and
            '%08x' % zlib.crc32(binaries['SOUND.DRV']) == soundpin['crc32'],
            'Canonical generated SOUND identity differs from native driver')
    require((HERE/'SOUNDID.H').read_bytes() ==
            (args.sound_repo/'src/win30/DRIVER/SOUNDID.H').read_bytes(),
            'FIXXT and canonical driver use different generated expectations')
    acceptance = json.loads(args.acceptance.read_bytes())
    require(acceptance.get('runtime_claim') ==
            'completed production-driver native observer',
            'Completed production native acceptance is required')
    for name in ('TCHIME.EXE', 'XPCHIME.EXE', 'TEXIT.EXE', 'TP.EXE'):
        require(acceptance['client_binaries'].get(name) == identity(binaries[name]),
                'Native acceptance covers another consumer: '+name)
    require(acceptance['client_binaries'].get('WINDOWS/TSHELL.EXE') ==
            identity(binaries['TSHELL.EXE']),
            'Native acceptance covers another installed TSHELL')
    require('AllPass' in acceptance['logs']['UNIFYQA.LOG']['checks'],
            'Native acceptance did not complete')
    require(acceptance['driver'] == identity(binaries['SOUND.DRV']),
            'Native acceptance tested another sound driver')
    files = {'PAYLOAD/'+name: data for name, data in binaries.items()}
    owners = json.loads((kit/'PAYLOAD/OWNERS.TXT').read_bytes())
    for row in owners['files']:
        if row['name'] in binaries:
            row.update(identity(binaries[row['name']]))
    if not any(row['name'] == 'SOUND.DRV' for row in owners['files']):
        owners['files'].append({'name': 'SOUND.DRV', 'target': 'SYSTEM',
            **identity(binaries['SOUND.DRV']),
            'policy': 'Canonical source CRC and installed full source comparison'})
    files['PAYLOAD/OWNERS.TXT'] = encoded(owners)
    inputs = json.loads((kit/'INPUTS.JSN').read_bytes())
    present = {row['path'] for row in inputs['files']}
    added = 0
    for destination in ('WINXT/SOUND.DRV', 'WINXT/FILES/SOUND.DRV'):
        if destination not in present:
            inputs['files'].append({'path': destination, 'origin': 'components',
                                   **identity(binaries['SOUND.DRV'])})
            added += 1
    for mode in inputs['output_counts']:
        inputs['output_counts'][mode] += added
    counts = {name: 0 for name in files}
    for row in inputs['files']:
        name = 'PAYLOAD/'+row['path'].rsplit('/', 1)[-1]
        if row['origin'] == 'components' and name in files:
            row.update(identity(files[name])); counts[name] += 1
    require(all(value == (1 if name == 'PAYLOAD/OWNERS.TXT' else 2)
                for name, value in counts.items()),
            'Current XR1 must have root and FILES entries for every consumer/helper')
    files['INPUTS.JSN'] = encoded(inputs)
    source = json.loads((kit/'PROVENANCE.JSN').read_bytes())
    source['files']['SOUND.DRV'] = {**identity(binaries['SOUND.DRV']),
        'source_record': 'SOUNDSRC.ZIP: canonical oemsound-tandy src/win30/DRIVER',
        'classification': 'Project sound driver; included SOUNDLIC.TXT applies'}
    for name, record in source['files'].items():
        if 'PAYLOAD/'+name in files:
            record.update(identity(files['PAYLOAD/'+name]))
            if name in SOURCE:
                record['source_record'] = SOURCE[name]
    files['PROVENANCE.JSN'] = encoded(source)
    files['SOUNDID.JSN'] = soundid
    files['SOUNDSRC.ZIP'] = sound_source(args.sound_repo, driver)
    files['SOUNDLIC.TXT'] = (args.sound_repo/'LICENSE').read_bytes()
    notice = (kit/'NOTICE.TXT').read_bytes()
    sound_note = (b'\r\nCANONICAL SOUND DRIVER\r\n'
        b'SOUND.DRV is the same canonical driver used by Tandy Winamp and desktop\r\n'
        b'alerts. Its corresponding source is SOUNDSRC.ZIP; SOUNDLIC.TXT retains\r\n'
        b'the existing source license. No compiler or Windows implementation is included.\r\n')
    if b'CANONICAL SOUND DRIVER' not in notice:
        notice += sound_note
    files['NOTICE.TXT'] = notice
    public = json.loads((kit/'PUBLIC.JSN').read_bytes())
    for name, data in files.items():
        public['files'][name] = identity(data)
    for name in ('PAYLOAD/SOUND.DRV', 'SOUNDID.JSN', 'SOUNDSRC.ZIP', 'SOUNDLIC.TXT'):
        public['bundles']['WINXT-XR1.ZIP'][name] = name
    files['PUBLIC.JSN'] = encoded(public)
    report = {'scope': 'current XR1 canonical sound driver, five consumers and matching finisher',
              'native_acceptance': identity(args.acceptance.read_bytes()),
              'native_builds': records,
              'installed_targets': {'TSHELL.EXE': 'WINDOWS',
                'TCHIME.EXE': 'WINXT', 'XPCHIME.EXE': 'WINXT',
                'TEXIT.EXE': 'WINXT', 'TP.EXE': 'WINXT',
                'FIXXT.EXE': 'WINXT', 'SOUND.DRV': 'SYSTEM'},
              'source_mirrors': 'WINXT/FILES; all six EXEs and canonical SOUND.DRV',
              'changed_files': {name: identity(data) for name, data in files.items()},
              'qualification_refresh_required':
                'QUALIFY.JSN current INPUTS/runtime pins and separate new native integration evidence',
              'applied': args.apply}
    if args.report:
        require(not args.report.exists(), 'Report output must be new')
    if args.apply:
        for name in files:
            require(not (kit/name).with_name((kit/name).name+'.SNDNEW').exists(),
                    'Integration staging file already exists')
        for name, data in files.items():
            target = kit/name
            temporary = target.with_name(target.name+'.SNDNEW')
            require(not temporary.exists(), 'Integration staging file already exists')
            with temporary.open('xb') as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            require(temporary.read_bytes() == data, 'Integration write/readback failed')
            os.replace(temporary, target)
    if args.report:
        args.report.write_bytes(encoded(report))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', required=True, type=Path)
    parser.add_argument('--fixxt', required=True, type=Path)
    parser.add_argument('--sound-repo', required=True, type=Path)
    parser.add_argument('--acceptance', required=True, type=Path)
    parser.add_argument('--report', type=Path)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    try:
        integrate(args)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, 'Refused: '+str(error)+'\n')
