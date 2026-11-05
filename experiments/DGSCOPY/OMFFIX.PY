"""Remove only the empty CONST/BSS members from one native C6 object group."""

def repair(data):
    records = []
    segments = []
    at = 0
    while at < len(data):
        if at+3 > len(data):
            raise ValueError('Truncated OMF header')
        kind = data[at]
        size = int.from_bytes(data[at+1:at+3], 'little')
        end = at+3+size
        if size < 1 or end > len(data) or sum(data[at:end]) & 255:
            raise ValueError('Invalid OMF record or checksum')
        payload = data[at+3:end-1]
        records.append((kind, payload, data[at:end]))
        if kind == 0x98:
            segments.append(payload)
        at = end
    if len(segments) != 4 or any(int.from_bytes(segments[n][1:3], 'little') for n in [1, 2, 3]):
        raise ValueError('Expected native C6 text and three empty data segments')
    out = bytearray()
    groups = 0
    for kind, payload, original in records:
        if kind != 0x9a:
            out.extend(original)
            continue
        groups += 1
        if payload != b'\x02\xff\x03\xff\x04\xff\x02':
            raise ValueError('Unexpected native C6 group members')
        payload = b'\x02\xff\x02'
        record = bytearray([kind])+bytearray((len(payload)+1).to_bytes(2, 'little'))+payload
        record.append((-sum(record)) & 255)
        out.extend(record)
    if groups != 1:
        raise ValueError('Expected exactly one native C6 group')
    return bytes(out)
