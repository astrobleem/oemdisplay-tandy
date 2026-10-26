"""Host-independent executable model of decoder.asm's documented wire contract.

This model uses only the Python standard library and deliberately has no
hardware, Windows, DOS, or existing-driver dependencies.
"""


class Decoder:
    def reset(self):
        self.state = 0
        self.buttons = 0
        self.header = self.xlow = self.ylow = 0
        self.queue = []
        self.lost = 0

    def __init__(self):
        self.reset()

    def feed(self, byte, lsr=1):
        """Return (flags, dx, dy), or None when this byte emits no pointer event."""
        if lsr & 0x1E:
            self.state = 0
            return None
        if not (lsr & 1):
            return None
        if byte & 0x80:
            self.state = 0
            return None
        if byte & 0x40:
            self.header = byte
            self.state = 1
            return None
        if self.state == 0:
            return None
        if self.state == 1:
            self.xlow = byte & 0x3F
            self.state = 2
            return None
        if self.state == 2:
            self.ylow = byte & 0x3F
            self.state = 3
            dx = signed8(((self.header & 3) << 6) | self.xlow)
            dy = signed8((((self.header >> 2) & 3) << 6) | self.ylow)
            buttons = ((self.header >> 5) & 1) | (((self.header >> 4) & 1) << 1)
            flags = 1 if dx or dy else 0
            if buttons & 1 and not self.buttons & 1:
                flags |= 2
            if not buttons & 1 and self.buttons & 1:
                flags |= 4
            if buttons & 2 and not self.buttons & 2:
                flags |= 8
            if not buttons & 2 and self.buttons & 2:
                flags |= 16
            self.buttons = buttons
            return (flags, dx, dy)
        if byte & 0xE0:
            self.state = 0
            return None
        self.state = 0
        wheel = byte & 0x0F
        if wheel & 8:
            wheel -= 16
        if wheel:
            if len(self.queue) < 31:
                self.queue.append(wheel)
            else:
                self.lost = min(0xFFFF, self.lost + 1)
        return None

    def read(self):
        return self.queue.pop(0) if self.queue else 0


def signed8(value):
    return value - 256 if value & 0x80 else value


def frame(dx=0, dy=0, buttons=0):
    """Encode one standard three-byte frame; buttons uses bit0=L, bit1=R."""
    dx &= 0xFF
    dy &= 0xFF
    header = 0x40 | ((buttons & 1) << 5) | ((buttons & 2) << 3)
    header |= (dx >> 6) & 3
    header |= ((dy >> 6) & 3) << 2
    return [header, dx & 0x3F, dy & 0x3F]
