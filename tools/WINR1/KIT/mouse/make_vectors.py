"""Generate DOS decoder-harness records from the independent protocol model."""

import argparse
import hashlib
import struct
from pathlib import Path

from protocol_model import Decoder, frame

RESET, FEED, READ, LOST = 0, 1, 2, 3
RECORD = struct.Struct("<BBBBHHHH")  # exactly 12 bytes


class Writer:
    def __init__(self, path):
        self.path = Path(path)
        self.file = self.path.open("wb")
        self.decoder = Decoder()
        self.count = 0

    def emit(self, op, byte=0, lsr=1, result=None):
        check_coordinates = 0
        if result is None:
            cf, ax, bx, cx = 0, 0, 0, 0
        elif op == FEED:
            flags, dx, dy = result
            cf, ax, bx, cx = int(flags != 0), flags, dx & 0xFFFF, dy & 0xFFFF
            check_coordinates = 1
        else:
            cf, ax, bx, cx = 0, result & 0xFFFF, 0, 0
        self.file.write(RECORD.pack(op, byte, lsr, cf, ax, bx, cx, check_coordinates))
        self.count += 1

    def reset(self):
        self.decoder.reset()
        self.emit(RESET)

    def feed(self, byte, lsr=1):
        result = self.decoder.feed(byte, lsr)
        self.emit(FEED, byte, lsr, result)

    def send_frame(self, dx=0, dy=0, buttons=0, extension=None):
        for byte in frame(dx, dy, buttons):
            self.feed(byte)
        if extension is not None:
            self.feed(extension)

    def read(self):
        self.emit(READ, result=self.decoder.read())

    def lost(self):
        self.emit(LOST, result=self.decoder.lost)

    def close(self):
        self.file.close()
        digest = hashlib.sha256(self.path.read_bytes()).hexdigest()
        return self.count, self.path.stat().st_size, digest


def generate(path, overflow_events=65570):
    w = Writer(path)
    w.reset()

    # Exhaust all wire encodings on each signed coordinate axis.
    for raw in range(256):
        w.send_frame(dx=raw)
    for raw in range(256):
        w.send_frame(dy=raw)

    # Button transitions, repeated held states, simultaneous changes, and
    # three-byte frames with no optional fourth byte.
    for buttons in (0, 1, 1, 3, 2, 0):
        w.send_frame(dx=0, dy=0, buttons=buttons)

    # All signed wheel nibbles, including zero, with ignored middle bit set.
    for wheel in range(-8, 8):
        w.send_frame(extension=0x10 | (wheel & 0x0F))

    # Resync at a header in a partial packet; malformed extension; bit-7 byte;
    # UART parity/overrun error; DR-clear input that must not advance state.
    w.feed(0x40)
    w.feed(0x41)
    w.feed(0x01)
    w.feed(0x02)
    w.feed(0x40)
    w.feed(0)
    w.feed(0)
    w.feed(0x20)
    w.feed(0x40)
    w.feed(0x80)
    for error_bit in (0x02, 0x04, 0x08, 0x10):
        w.feed(0x40)
        w.feed(0x00, lsr=error_bit)
    w.feed(0x40)
    w.feed(0x01, lsr=0)
    w.feed(0x01, lsr=1)
    w.feed(0x02, lsr=1)
    w.read()
    w.lost()

    # Fill the 31-entry queue, overflow sufficiently to saturate its 16-bit
    # loss counter, then prove it remains saturated and read queued values.
    w.reset()
    for _ in range(overflow_events):
        w.send_frame(extension=1)
    for _ in range(31):
        w.read()
    w.read()  # empty queue returns zero
    w.lost()

    # Reset must clear parser, button baseline, queue, and loss counter.
    w.reset()
    w.read()
    w.lost()
    w.send_frame(buttons=1)
    w.reset()
    w.send_frame(buttons=0)  # no stale button-up event after reset
    return w.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="vectors.bin")
    parser.add_argument("--overflow-events", type=int, default=65540)
    args = parser.parse_args()
    if args.overflow_events < 65566:
        parser.error("overflow-events must be at least 65566 to reach 0xffff loss")
    records, size, digest = generate(args.output, args.overflow_events)
    print(f"records={records} bytes={size} sha256={digest}")


if __name__ == "__main__":
    main()
