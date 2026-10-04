PRIMARY HARDWARE BASIS (brief paraphrase)
Tandy 1000 EX Technical Reference Manual, Tandy Corporation, 1986.
https://ia803107.us.archive.org/5/items/tandy1000extechnicalreferencemanual/Tandy_1000EX_Technical_Reference_Manual.pdf
Alternative mirror:
https://manuals.plus/m/a5450fe6dcd66bb4902629b9e4200258fee5acfaffa08a96b2eea50c07d828c2.pdf

Printed p35: writing 0200/0201h resets a common ramp; its nominal full-scale
rise takes 1.12 ms. Printed pp55-56 document trigger/read operation.
Printed p56 assigns 0201h bits 0..3 to right X,Y then left X,Y; bits 4..7
are right buttons 1,2 then left buttons 1,2, with zero meaning pressed.
GAME.SCH sheet 6/9 (PDF page81) connects position to LM339 (+), ramp to (-),
with non-inverting readback: axis timing is high, then low. Minimum may
already be low at the first read. No separate presence contact exists.

Caveat: connector naming in printed p5 and schematic routing appears
inconsistent. The software follows p56; confirm physical labels by moving
one stick at a time. Disconnected inputs have no verified unique signature.

BIOS BOUNDARY
EX INT15h/AH84h support was not established. This program does not call it.
The following disassembly project lists the EX ROM as missing, so its
other Tandy ROM listings are not proof for the EX:
https://github.com/ricardoquesada/bios-8088

The original copyrighted manual/ROM is not included in this package.
