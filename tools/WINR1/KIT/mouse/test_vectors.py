"""Protocol vectors and host-only checks for protocol_model.py."""

import unittest

from protocol_model import Decoder, frame, signed8


def send_frame(decoder, dx=0, dy=0, buttons=0, extension=None):
    result = None
    for byte in frame(dx, dy, buttons):
        result = decoder.feed(byte)
    if extension is not None:
        decoder.feed(extension)
    return result


class DecoderVectors(unittest.TestCase):
    def test_every_signed_coordinate_value(self):
        # Exercise all 256 encodings on both axes, including sign boundaries.
        for raw in range(256):
            expected = signed8(raw)
            d = Decoder()
            result = send_frame(d, dx=raw, dy=0)
            self.assertEqual(result, (1 if expected else 0, expected, 0), raw)
            d = Decoder()
            result = send_frame(d, dx=0, dy=raw)
            self.assertEqual(result, (1 if expected else 0, 0, expected), raw)

    def test_button_edges_and_three_byte_fallback(self):
        d = Decoder()
        self.assertEqual(send_frame(d, buttons=1), (2, 0, 0))
        self.assertEqual(send_frame(d, buttons=1), (0, 0, 0))
        self.assertEqual(send_frame(d, buttons=3), (8, 0, 0))
        self.assertEqual(send_frame(d, buttons=2), (4, 0, 0))
        self.assertEqual(send_frame(d, buttons=0), (16, 0, 0))
        # The event is emitted at byte three; no extension is required.
        self.assertEqual(d.state, 3)

    def test_optional_wheel_nibbles_and_middle_bit(self):
        for wheel in range(-8, 8):
            d = Decoder()
            send_frame(d)
            byte = 0x10 | (wheel & 0x0F)  # middle-button bit is ignored
            d.feed(byte)
            self.assertEqual(d.read(), wheel)
            self.assertEqual(d.read(), 0)

    def test_resynchronization_and_bad_extensions(self):
        d = Decoder()
        d.feed(0x40)          # partial header
        d.feed(0x41)          # a new header replaces it
        d.feed(1)
        self.assertEqual(d.feed(2), (1, 65, 2))
        d.feed(0x40)
        d.feed(0)
        d.feed(0)
        d.feed(0x20)          # malformed extension
        self.assertEqual(d.state, 0)
        d.feed(0x80)          # invalid byte resets parser
        self.assertEqual(d.state, 0)

    def test_lsr_error_drops_partial_frame_and_no_dr_ignores_byte(self):
        d = Decoder()
        d.feed(0x40)
        d.feed(0x01, lsr=0)   # DR clear: do not consume the apparent header
        self.assertEqual(d.state, 1)
        d.feed(0x01, lsr=0x05)  # overrun: drop parser state
        self.assertEqual(d.state, 0)
        self.assertEqual(send_frame(d), (0, 0, 0))
        self.assertEqual(d.state, 3)

    def test_queue_capacity_drop_newest_and_saturating_loss(self):
        d = Decoder()
        for _ in range(40):
            send_frame(d, extension=1)
        self.assertEqual(len(d.queue), 31)
        self.assertEqual(d.lost, 9)
        self.assertEqual([d.read() for _ in range(31)], [1] * 31)
        self.assertEqual(d.read(), 0)
        d.lost = 0xFFFF
        for _ in range(32):
            send_frame(d, extension=1)
        self.assertEqual(d.lost, 0xFFFF)

    def test_uart_error_preserves_button_baseline(self):
        d = Decoder()
        self.assertEqual(send_frame(d, buttons=1), (2, 0, 0))
        d.feed(0x40)
        d.feed(0, lsr=0x08)  # parity error aborts the partial frame
        self.assertEqual(d.buttons, 1)
        self.assertEqual(send_frame(d, buttons=0), (4, 0, 0))


if __name__ == "__main__":
    unittest.main()
