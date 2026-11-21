#!/usr/bin/env python3
"""Travel poster for VELMORA, a place that isn't there.

Stdlib-only PNG writer (zlib + struct). Draws a vintage-style poster:
gradient dusk sky, sun disc, layered mountain ridges, a calm sea with a
sun path, floating islets and birds. The place name VELMORA is the only
text, rendered with an embedded 5x7 bitmap font.
"""
import math
import os
import struct
import zlib

W, H = 768, 1024
NAME = "VELMORA"

# --- 5x7 bitmap font (rows top->bottom, '#' = ink) ---
FONT = {
    "V": ["#...#", "#...#", "#...#", "#...#", "#...#", ".#.#.", "..#.."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    " ": [".....", ".....", ".....", ".....", ".....", ".....", "....."],
}


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    return (int(lerp(c1[0], c2[0], t)), int(lerp(c1[1], c2[1], t)),
            int(lerp(c1[2], c2[2], t)))


def main():
    px = bytearray(W * H * 3)

    def set_px(x, y, c):
        if 0 <= x < W and 0 <= y < H:
            i = (y * W + x) * 3
            px[i], px[i + 1], px[i + 2] = c[0], c[1], c[2]

    def fill_rect(x0, y0, x1, y1, c):
        for y in range(max(0, y0), min(H, y1)):
            base = y * W * 3
            for x in range(max(0, x0), min(W, x1)):
                i = base + x * 3
                px[i], px[i + 1], px[i + 2] = c[0], c[1], c[2]

    # Palette (vintage poster)
    sky_top = (18, 52, 86)       # deep dusk blue
    sky_mid = (86, 128, 160)     # dusty blue
    sky_low = (242, 177, 92)     # amber horizon
    sun_c = (250, 214, 130)
    sun_core = (253, 238, 190)
    ridge_far = (64, 96, 120)
    ridge_mid = (38, 74, 92)
    ridge_near = (20, 48, 58)
    sea_top = (232, 150, 92)
    sea_bot = (16, 54, 72)
    cream = (246, 236, 214)
    ink = (12, 30, 40)

    horizon = int(H * 0.62)
    sun_x, sun_y, sun_r = W // 2, int(H * 0.40), 150

    # Sky gradient (three-stop)
    for y in range(horizon):
        t = y / horizon
        if t < 0.55:
            c = mix(sky_top, sky_mid, t / 0.55)
        else:
            c = mix(sky_mid, sky_low, (t - 0.55) / 0.45)
        fill_rect(0, y, W, y + 1, c)

    # Stars in the upper sky (deterministic pseudo-random)
    seed = 1234567
    for _ in range(160):
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sx = seed % W
        seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
        sy = seed % int(H * 0.30)
        b = 150 + (seed % 90)
        set_px(sx, sy, (b, b, min(255, b + 20)))
        if seed % 5 == 0:
            set_px(sx + 1, sy, (b, b, min(255, b + 20)))

    # Sun disc with soft rim
    for y in range(sun_y - sun_r - 30, sun_y + sun_r + 30):
        for x in range(sun_x - sun_r - 30, sun_x + sun_r + 30):
            d = math.hypot(x - sun_x, y - sun_y)
            if d < sun_r:
                t = d / sun_r
                set_px(x, y, mix(sun_core, sun_c, t * t))
            elif d < sun_r + 26:
                t = (d - sun_r) / 26.0
                # blend rim toward sky by re-reading current pixel
                if 0 <= x < W and 0 <= y < H:
                    i = (y * W + x) * 3
                    cur = (px[i], px[i + 1], px[i + 2])
                    set_px(x, y, mix(sun_c, cur, t))

    # Mountain ridges (sine-sum silhouettes), back to front
    def ridge(base_y, amp, color, ph1, ph2):
        for x in range(W):
            t = x / W
            ytop = int(base_y - amp * (0.55 * math.sin(t * 9.0 + ph1)
                                       + 0.30 * math.sin(t * 23.0 + ph2)
                                       + 0.15 * math.sin(t * 47.0 + ph1 * 2.0)
                                       + 0.55))
            fill_rect(x, ytop, x + 1, horizon + 2, color)

    ridge(int(H * 0.52), 90, ridge_far, 0.7, 2.1)
    ridge(int(H * 0.58), 70, ridge_mid, 3.9, 0.4)

    # Floating islets (small rock cones with a flat top) in the sky band
    def islet(cx, cy, wdt, col):
        half = wdt // 2
        for dy in range(0, 46):
            shrink = int(half * (dy / 46.0) ** 1.6)
            fill_rect(cx - half + shrink, cy + dy, cx + half - shrink,
                      cy + dy + 1, col)
        fill_rect(cx - half, cy - 5, cx + half, cy, mix(col, cream, 0.35))

    islet(int(W * 0.18), int(H * 0.30), 120, ridge_mid)
    islet(int(W * 0.84), int(H * 0.24), 90, ridge_far)
    islet(int(W * 0.70), int(H * 0.36), 64, ridge_mid)

    # Sea
    for y in range(horizon, H):
        t = (y - horizon) / (H - horizon)
        fill_rect(0, y, W, y + 1, mix(sea_top, sea_bot, t ** 0.8))

    # Near shore ridge overlapping the horizon on both sides
    def shore(side):
        for x in range(W):
            t = x / W
            edge = (t if side < 0 else 1.0 - t)
            if edge > 0.42:
                continue
            ytop = int(H * 0.60 + 120 * edge + 14 * math.sin(t * 31.0))
            fill_rect(x, ytop, x + 1, H, ridge_near)

    shore(-1)
    shore(1)

    # Sun path on the water: bright broken streaks under the sun
    seed = 987654
    for y in range(horizon + 4, H - 130, 3):
        t = (y - horizon) / (H - horizon)
        width = int(40 + 150 * t)
        for x in range(sun_x - width, sun_x + width):
            seed = (seed * 1103515245 + 12345) & 0x7FFFFFFF
            if seed % 100 < 34:
                glow = mix(sun_c, cream, 0.4)
                set_px(x, y, glow)
                set_px(x, y + 1, mix(glow, sea_bot, 0.35))

    # Birds: tiny chevrons
    def bird(cx, cy, s, col):
        for k in range(-s, s + 1):
            yy = cy - abs(k) // 2
            set_px(cx + k, yy, col)
            set_px(cx + k, yy + 1, col)

    bird(int(W * 0.30), int(H * 0.20), 12, ink)
    bird(int(W * 0.36), int(H * 0.23), 9, ink)
    bird(int(W * 0.66), int(H * 0.16), 10, ink)

    # --- Place name: VELMORA, large cream letters with dark offset ---
    scale = 13
    glyph_w, glyph_h, tracking = 5, 7, 2
    text_w = (len(NAME) * (glyph_w + tracking) - tracking) * scale
    tx = (W - text_w) // 2
    ty = int(H * 0.845)

    def draw_text(ox, oy, col):
        cx = tx + ox
        for ch in NAME:
            rows = FONT[ch]
            for gy, row in enumerate(rows):
                for gx, cell in enumerate(row):
                    if cell == "#":
                        fill_rect(cx + gx * scale, ty + oy + gy * scale,
                                  cx + (gx + 1) * scale,
                                  ty + oy + (gy + 1) * scale, col)
            cx += (glyph_w + tracking) * scale

    # thin rules above and below the name
    rule_y1 = ty - 26
    rule_y2 = ty + glyph_h * scale + 22
    fill_rect(tx - 30, rule_y1, tx + text_w + 30, rule_y1 + 3, cream)
    fill_rect(tx - 30, rule_y2, tx + text_w + 30, rule_y2 + 3, cream)

    draw_text(4, 4, ink)     # offset shadow
    draw_text(0, 0, cream)   # face

    # --- PNG encode (filter 0 rows) ---
    raw = bytearray()
    for y in range(H):
        raw.append(0)
        raw.extend(px[y * W * 3:(y + 1) * W * 3])

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")

    os.makedirs("/output", exist_ok=True)
    out = "/output/entry.png"
    with open(out, "wb") as f:
        f.write(png)
    os.chmod(out, 0o644)


if __name__ == "__main__":
    main()
