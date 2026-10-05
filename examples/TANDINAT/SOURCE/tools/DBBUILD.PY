#!/usr/bin/env python3
"""Compile the original editable TANDINATOR JSON to the TANDI01 disk format.
Python 3.8+, standard library only. Run --help for usage. See data/FORMAT.TXT.
"""
import argparse
import collections
import textwrap
import json
import os
from pathlib import Path
import re
import struct
import sys

MAGIC = b'TANDI01\0'
VERSION = 1
HEADER = 64
MAX_CHARS = 2000
MAX_QUESTIONS = 256
CODES = {'NO': 0, 'PROBABLY_NO': 1, 'UNKNOWN': 2, 'PROBABLY_YES': 3, 'YES': 4}

class DatabaseError(ValueError):
    pass

def require(condition, message):
    if not condition:
        raise DatabaseError(message)

def unique_json(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, 'Duplicate JSON key: ' + str(key))
        result[key] = value
    return result

def load_source(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f, object_pairs_hook=unique_json)

def ascii_string(value, limit, label):
    require(isinstance(value, str) and bool(value), label + ': expected nonempty string')
    require(all(32 <= ord(c) <= 126 for c in value), label + ': printable ASCII only')
    encoded = value.encode('ascii')
    require(len(encoded) <= limit, label + ': string exceeds ' + str(limit) + ' bytes')
    return encoded + b'\0'

def validate_source(source):
    require(isinstance(source, dict), 'Source must be an object')
    require(source.get('format_version') == 1 and type(source.get('format_version')) is int,
            'Source format_version must be integer 1')
    questions = source.get('questions')
    characters = source.get('characters')
    require(isinstance(questions, list) and 1 <= len(questions) <= MAX_QUESTIONS,
            'Question count must be 1..256')
    require(isinstance(characters, list) and 1 <= len(characters) <= MAX_CHARS,
            'Character count must be 1..2000')
    qids, cids, texts, names = [], [], [], []
    for label, entries, ids, strings, field, limit in (
        ('question', questions, qids, texts, 'text', 79),
        ('character', characters, cids, names, 'name', 39)):
        for entry in entries:
            require(isinstance(entry, dict), label + ': expected object')
            ident = entry.get('id')
            require(isinstance(ident, str) and re.fullmatch(r'[a-z][a-z0-9_]{0,47}', ident),
                    label + ': invalid id ' + repr(ident))
            require(ident not in ids, 'Duplicate ' + label + ' id: ' + ident)
            ids.append(ident)
            strings.append(ascii_string(entry.get(field), limit, label + ' ' + ident))
            words = entry[field].split()
            require(all(len(word) <= 26 for word in words),
                    label + ' ' + ident + ': word exceeds 26-column UI width')
            if label == 'question':
                require(len(textwrap.wrap(entry[field], width=26, break_long_words=False,
                                          break_on_hyphens=False)) <= 3,
                        'question ' + ident + ': exceeds three-line 320-pixel UI')
    require(len(set(texts)) == len(texts), 'Duplicate question text')
    require(len(set(names)) == len(names), 'Duplicate character display name')
    qset = set(qids)
    rows = []
    for char in characters:
        answers = char.get('answers')
        require(isinstance(answers, dict), char['id'] + ': answers must be an object')
        require(set(answers) == qset,
                char['id'] + ': missing answer targets ' + repr(sorted(qset - set(answers))) +
                '; unknown answer targets ' + repr(sorted(set(answers) - qset)))
        row = []
        for qid in qids:
            value = answers[qid]
            require(type(value) is int and 0 <= value <= 4,
                    char['id'] + '/' + qid + ': answer must be integer 0..4')
            row.append(value)
        rows.append(row)
    return texts, names, rows

def pack_values(values):
    result = bytearray((3 * len(values) + 7) // 8)
    for index, value in enumerate(values):
        require(type(value) is int and 0 <= value <= 4, 'Invalid value for packing')
        bit = index * 3
        byte, shift = divmod(bit, 8)
        result[byte] |= (value << shift) & 255
        if shift > 5:
            result[byte + 1] |= value >> (8 - shift)
    return bytes(result)

def unpack_values(data, count):
    require(len(data) == (3 * count + 7) // 8, 'Packed record has wrong size')
    result = []
    for index in range(count):
        byte, shift = divmod(index * 3, 8)
        value = data[byte] >> shift
        if shift > 5:
            value |= data[byte + 1] << (8 - shift)
        value &= 7
        require(value <= 4, 'Packed answer outside 0..4')
        result.append(value)
    remaining = count * 3 % 8
    require(not remaining or data[-1] >> remaining == 0, 'Nonzero matrix padding bits')
    return result

def compile_source(source):
    questions, names, rows = validate_source(source)
    nq, nc = len(questions), len(names)
    rb, cb = (nq * 3 + 7) // 8, (nc * 3 + 7) // 8
    qo = HEADER
    no = qo + 4 * nq
    ro = no + 4 * nc
    co = ro + nc * rb
    so = co + nq * cb
    blob = bytearray(so)
    string_offset = so
    for offset, strings in ((qo, questions), (no, names)):
        for index, string in enumerate(strings):
            struct.pack_into('<I', blob, offset + 4 * index, string_offset)
            blob.extend(string)
            string_offset += len(string)
    for index, row in enumerate(rows):
        blob[ro + index * rb:ro + (index + 1) * rb] = pack_values(row)
    for index in range(nq):
        blob[co + index * cb:co + (index + 1) * cb] = pack_values([r[index] for r in rows])
    blob[:8] = MAGIC
    struct.pack_into('<6H', blob, 8, VERSION, nc, nq, rb, cb, 0)
    struct.pack_into('<7I', blob, 20, qo, no, ro, co, so, len(blob), sum(blob[64:]) & 0xffffffff)
    result = bytes(blob)
    parsed = validate_binary(result)
    require(parsed['rows'] == rows, 'Compiler round-trip mismatch')
    return result

def validate_binary(blob):
    require(isinstance(blob, (bytes, bytearray)), 'Binary input required')
    require(len(blob) >= HEADER, 'Truncated header')
    require(blob[:8] == MAGIC, 'Invalid magic')
    version, nc, nq, rb, cb, reserved = struct.unpack_from('<6H', blob, 8)
    require(version == VERSION, 'Unsupported version')
    require(1 <= nc <= MAX_CHARS and 1 <= nq <= MAX_QUESTIONS, 'Invalid counts')
    require(rb == (nq * 3 + 7) // 8 and cb == (nc * 3 + 7) // 8, 'Invalid matrix record size')
    require(reserved == 0 and not any(blob[48:64]), 'Nonzero reserved header bytes')
    qo, no, ro, co, so, size, checksum = struct.unpack_from('<7I', blob, 20)
    require(size == len(blob), 'File size mismatch')
    require(qo == HEADER and no == qo + nq * 4 and ro == no + nc * 4 and
            co == ro + nc * rb and so == co + nq * cb and so < size,
            'Invalid or overlapping section offsets')
    require(checksum == (sum(blob[64:]) & 0xffffffff), 'Checksum mismatch')
    strings = []
    cursor = so
    for offset, count, limit in ((qo, nq, 79), (no, nc, 39)):
        group = []
        for index in range(count):
            pointer = struct.unpack_from('<I', blob, offset + index * 4)[0]
            require(pointer == cursor and so <= pointer < size, 'Invalid string offset or ordering')
            end = blob.find(b'\0', pointer, min(size, pointer + limit + 1))
            require(end > pointer, 'Invalid or unterminated string')
            raw = blob[pointer:end]
            require(all(32 <= b <= 126 for b in raw), 'Non-ASCII/control byte in string')
            group.append(raw.decode('ascii'))
            cursor = end + 1
        strings.append(group)
    require(cursor == size, 'Trailing bytes after strings')
    rows = [unpack_values(blob[ro + c * rb:ro + (c + 1) * rb], nq) for c in range(nc)]
    for q in range(nq):
        column = unpack_values(blob[co + q * cb:co + (q + 1) * cb], nc)
        require(column == [row[q] for row in rows], 'Row/column matrices disagree')
    return {'version': version, 'nchars': nc, 'nquestions': nq, 'rowbytes': rb, 'colbytes': cb,
            'qoffset': qo, 'nameoffset': no, 'rowoffset': ro, 'coloffset': co,
            'stringsoffset': so, 'filesize': size, 'checksum': checksum,
            'questions': strings[0], 'names': strings[1], 'rows': rows}

def report_for(source, blob):
    info = validate_binary(blob)
    profiles = collections.defaultdict(list)
    for char, row in zip(source['characters'], info['rows']):
        profiles[tuple(row)].append(char['id'])
    histogram = collections.Counter(value for row in info['rows'] for value in row)
    duplicates = [names for names in profiles.values() if len(names) > 1]
    constant_questions = [source['questions'][q]['id'] for q in range(info['nquestions'])
                          if len(set(row[q] for row in info['rows'])) == 1]
    report = {k: v for k, v in info.items() if k not in ('questions', 'names', 'rows')}
    report.update({'answer_histogram': {name: histogram[code] for name, code in CODES.items()},
                   'unknown_percent': round(100 * histogram[2] / (info['nchars'] * info['nquestions']), 4),
                   'duplicate_profiles': duplicates, 'constant_questions': constant_questions,
                   'validation': 'passed', 'orientation_round_trip': 'passed'})
    return report

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument('source', nargs='?', type=Path, default=root / 'data' / 'STARTER.JSON')
    parser.add_argument('output', nargs='?', type=Path, default=root / 'build' / 'TANDY.DAT')
    parser.add_argument('--report', type=Path, default=root / 'build' / 'DBREPORT.JSON')
    parser.add_argument('--check', type=Path, help='Validate an existing TANDY.DAT only')
    parser.add_argument('--strict-unique', action='store_true', help='Reject identical answer profiles')
    args = parser.parse_args(argv)
    try:
        if args.check:
            info = validate_binary(args.check.read_bytes())
            print(json.dumps({k: v for k, v in info.items() if k not in ('questions', 'names', 'rows')}, indent=2))
            return 0
        source = load_source(args.source)
        blob = compile_source(source)
        report = report_for(source, blob)
        require(not args.strict_unique or not report['duplicate_profiles'], 'Identical answer profiles: ' + repr(report['duplicate_profiles']))
        args.output.parent.mkdir(parents=True, exist_ok=True)
        temporary = args.output.with_suffix(args.output.suffix + '.tmp')
        temporary.write_bytes(blob)
        validate_binary(temporary.read_bytes())
        os.replace(temporary, args.output)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(report, indent=2))
        return 0
    except (DatabaseError, OSError, json.JSONDecodeError, UnicodeError) as exc:
        print('DBBUILD: ' + str(exc), file=sys.stderr)
        return 1

if __name__ == '__main__':
    sys.exit(main())
