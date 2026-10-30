"""Draws the Quick Profile Switch icon (two opposite arrows on a blue tile) without extra libraries.

Writes extension/icons/icon-{48,96,128}.png and host/icon.ico. Run: python tools/make_icons.py
"""
import os
import struct
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BLUE, WHITE = (0, 96, 223), (255, 255, 255)
# Pfeile in Einheitskoordinaten (0..1): Schaft und zwei Spitzenstriche je Pfeil
SEGMENTS = [((0.22, 0.37), (0.78, 0.37)), ((0.62, 0.23), (0.78, 0.37)), ((0.62, 0.51), (0.78, 0.37)),
            ((0.78, 0.63), (0.22, 0.63)), ((0.38, 0.49), (0.22, 0.63)), ((0.38, 0.77), (0.22, 0.63))]
STROKE, RADIUS, SS = 0.085, 0.2, 4  # Strichstärke, Eckenradius, Supersampling


def dist_to_segment(px, py, a, b):
    (ax, ay), (bx, by) = a, b
    dx, dy = bx - ax, by - ay
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
    return ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** 0.5


def in_rounded_square(x, y):
    cx, cy = min(max(x, RADIUS), 1 - RADIUS), min(max(y, RADIUS), 1 - RADIUS)
    return (x - cx) ** 2 + (y - cy) ** 2 <= RADIUS ** 2


def render(size):
    rows = []
    for py in range(size):
        row = bytearray()
        for px in range(size):
            tile = arrow = 0
            for sy in range(SS):
                for sx in range(SS):
                    x, y = (px + (sx + 0.5) / SS) / size, (py + (sy + 0.5) / SS) / size
                    if in_rounded_square(x, y):
                        tile += 1
                        if any(dist_to_segment(x, y, a, b) <= STROKE / 2 for a, b in SEGMENTS):
                            arrow += 1
            n = SS * SS
            if tile == 0:
                row += bytes((0, 0, 0, 0))
                continue
            w = arrow / tile
            row += bytes(round(BLUE[i] * (1 - w) + WHITE[i] * w) for i in range(3)) + bytes((round(255 * tile / n),))
        rows.append(bytes(row))
    return rows


def png(size):
    raw = b"".join(b"\x00" + r for r in render(size))
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))


def ico(sizes):
    images = [png(s) for s in sizes]
    header = struct.pack("<HHH", 0, 1, len(images))
    offset = 6 + 16 * len(images)
    entries = b""
    for s, data in zip(sizes, images):
        entries += struct.pack("<BBBBHHII", s % 256, s % 256, 0, 0, 1, 32, len(data), offset)
        offset += len(data)
    return header + entries + b"".join(images)


if __name__ == "__main__":
    icons = os.path.join(ROOT, "extension", "icons")
    os.makedirs(icons, exist_ok=True)
    for s in (48, 96, 128):
        with open(os.path.join(icons, f"icon-{s}.png"), "wb") as f:
            f.write(png(s))
    with open(os.path.join(ROOT, "host", "icon.ico"), "wb") as f:
        f.write(ico([16, 24, 32, 48, 64, 256]))
    print("Icons geschrieben")
