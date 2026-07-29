"""Correct PNG encoder wrapper for the report diagrams."""
import os
import struct
import zlib
import generate_png_diagrams as diagrams

def save(self, path):
    rows = []
    for y in range(self.h):
        r, g, b = self.p[y * 3], self.p[y * 3 + 1], self.p[y * 3 + 2]
        row = bytearray()
        for x in range(self.w):
            row.extend((r[x], g[x], b[x]))
        rows.append(b"\0" + bytes(row))
    raw = b"".join(rows)
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff))
    png = (b"\x89PNG\r\n\x1a\n" +
           chunk(b"IHDR", struct.pack(">IIBBBBB", self.w, self.h, 8, 2, 0, 0, 0)) +
           chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    with open(path, "wb") as handle:
        handle.write(png)

diagrams.Canvas.save = save
diagrams.class_diagram()
diagrams.object_diagram()
diagrams.state_diagram()
diagrams.sequence_diagram()
diagrams.activity_diagram()
print("PNG diagrams rendered successfully")
