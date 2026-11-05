"""Generate the small code-owned PulseDeck Windows icon (stdlib only)."""
from pathlib import Path
import struct


def bitmap(size):
    pixels = bytearray()
    points = [(0.13, 0.57), (0.32, 0.57), (0.44, 0.27), (0.57, 0.76), (0.70, 0.43), (0.87, 0.43)]
    for y in reversed(range(size)):
        for x in range(size):
            px, py = (x + .5) / size, (y + .5) / size
            corner_x, corner_y = max(.15 - px, 0, px - .85), max(.15 - py, 0, py - .85)
            inside = corner_x * corner_x + corner_y * corner_y <= .15 ** 2
            distance = 1.0
            for (ax, ay), (bx, by) in zip(points, points[1:]):
                dx, dy = bx - ax, by - ay
                t = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)))
                distance = min(distance, ((px - ax - t * dx) ** 2 + (py - ay - t * dy) ** 2) ** .5)
            red, green, blue = (70, 211, 184) if distance < .035 else (11, 24, 23)
            pixels.extend((blue, green, red, 255 if inside else 0))
    mask = bytes(((size + 31) // 32) * 4 * size)
    header = struct.pack("<IIIHHIIIIII", 40, size, size * 2, 1, 32, 0, len(pixels), 0, 0, 0, 0)
    return header + pixels + mask


if __name__ == "__main__":
    sizes = (16, 32, 48, 64)
    blocks = [bitmap(size) for size in sizes]
    output = bytearray(struct.pack("<HHH", 0, 1, len(sizes)))
    offset = 6 + 16 * len(sizes)
    for size, block in zip(sizes, blocks):
        output.extend(struct.pack("<BBBBHHII", size, size, 0, 0, 1, 32, len(block), offset))
        offset += len(block)
    output.extend(b"".join(blocks))
    path = Path(__file__).resolve().parent.parent / "assets/pulsedeck.ico"
    path.parent.mkdir(exist_ok=True)
    path.write_bytes(output)
