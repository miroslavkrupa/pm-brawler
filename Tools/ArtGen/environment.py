"""Backgrounds, tiles, props, pickups and effects in the same 32 px-per-unit pixel style.

Each level has a theme: a far 'view through the windows' panorama (dithered sky, sea, islands),
a tileable office wall with the windows cut out, its own floor and props.
"""
import math
import random

import numpy as np
from PIL import Image

from pixel import BAYER4, Ramp, Sprite, blank, capsule, ellipse, hex2rgb, line, polygon, rect, shift

U = 32          # pixels per world unit
WALL_H = 448    # 14 units


def lerp(a, b, t):
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def C(h):
    return hex2rgb(h) if isinstance(h, str) else h


def gradient_bands(img, y0, y1, stops, x0=0, x1=None, dither=True):
    """Vertical gradient quantised into colour bands with Bayer dithering between neighbours."""
    px = img.load()
    x1 = img.width if x1 is None else x1
    cols = [C(s) for s in stops]
    n = len(cols) - 1
    for y in range(y0, y1):
        t = (y - y0) / max(1, (y1 - y0 - 1)) * n
        i = min(int(t), n - 1)
        f = t - i
        for x in range(x0, x1):
            c = cols[i + 1] if (dither and f > BAYER4[y % 4, x % 4]) or (not dither and f > 0.5) else cols[i]
            px[x, y] = c + (255,)


def fill_mask(img, mask, color, dither_to=None, amount=0.5, ox=0, oy=0):
    px = img.load()
    c0 = C(color)
    c1 = C(dither_to) if dither_to else None
    ys, xs = np.nonzero(mask)
    for y, x in zip(ys, xs):
        xx, yy = x + ox, y + oy
        if 0 <= xx < img.width and 0 <= yy < img.height:
            c = c1 if c1 and amount > BAYER4[yy % 4, xx % 4] else c0
            px[xx, yy] = c + (255,)


def wrap_noise(w, n, amp, seed, octaves=3):
    """1-D periodic noise (wraps at w) for horizon silhouettes."""
    rnd = random.Random(seed)
    out = np.zeros(w)
    for o in range(octaves):
        freq = n * (2 ** o)
        phase = [rnd.random() * math.tau for _ in range(4)]
        for k, ph in enumerate(phase):
            out += np.sin(np.arange(w) / w * math.tau * (freq + k) + ph) * amp / (2 ** o) / 4
    return out


# ---------------------------------------------------------------- themes

THEMES = {
    'level1': dict(  # night harbour, a pirate ship in the bay
        sky=['#0c0a24', '#1a1640', '#2a2260', '#3c3080', '#5a4498'], sea=['#16244e', '#0e1838', '#0a1028'],
        land='#120e26', land2='#1c1838', moon=True, ship=True, stars=True, island='hills',
        wall='#2c4a5a', wall2='#24404e', trim='#5a3a28', wains='#3a2a2a', floor='#3a3448', carpet='#5a4a7a',
        props=['plant', 'cooler', 'cabinet', 'poster', 'server', 'poster', 'whiteboard', 'plant'],
    ),
    'level2': dict(  # tropical island at dusk
        sky=['#2a1a4a', '#6a2a6a', '#c04a5a', '#f08a4a', '#ffd070'], sea=['#3a3a7a', '#2a2a5a', '#1c1c40'],
        land='#2a1630', land2='#3a2040', sun=True, palms=True, island='island',
        wall='#3e6a4a', wall2='#345a3e', trim='#6a4228', wains='#4a3020', floor='#4a3a30', carpet='#7a5a3a',
        props=['bugboard', 'plant', 'poster', 'cabinet', 'cooler', 'poster', 'bugboard', 'plant'],
    ),
    'level3': dict(  # sunset over a city on the coast
        sky=['#1a1440', '#3a1e5e', '#7a2e70', '#d0507a', '#ff9a6a'], sea=['#4a2a6a', '#34204e', '#22163a'],
        land='#1e1232', land2='#2c1a44', sun=True, city=True,
        wall='#5a3a6e', wall2='#4c3060', trim='#3a2a40', wains='#2e2238', floor='#3a2a40', carpet='#8a3a5a',
        props=['whiteboard', 'plant', 'poster', 'flipchart', 'cooler', 'poster', 'whiteboard', 'plant'],
    ),
    'level4': dict(  # stormy night, rain, lightning over the sea
        sky=['#0a0a14', '#14141e', '#1e1e2e', '#2a2a40', '#3a3a50'], sea=['#1a2028', '#12161e', '#0c0e14'],
        land='#08080e', land2='#10101a', storm=True, island='rocks',
        wall='#5a2e1e', wall2='#4a2618', trim='#d0a040', wains='#3a1e12', floor='#2e1a14', carpet='#7a1a22',
        panel=True, props=['portrait', 'curtain', 'portrait', 'clock', 'portrait', 'curtain', 'globe', 'portrait'],
    ),
    'level5': dict(  # penthouse above the clouds, the volcano island glowing
        sky=['#06061a', '#0e0e30', '#1a1650', '#2e1e6a', '#5a2a6a'], sea=['#1a1a40', '#121230', '#0a0a20'],
        land='#140a1a', land2='#22102a', stars=True, volcano=True, moon=True,
        wall='#1e2a4a', wall2='#18223e', trim='#d8b040', wains='#141c32', floor='#1a1a2a', carpet='#a8842a',
        panel=True, props=['statue', 'plant', 'portrait', 'aquarium', 'statue', 'portrait', 'plant', 'globe'],
    ),
}


# ---------------------------------------------------------------- far layer: the view

def panorama(key, w=1024, h=WALL_H):
    th = THEMES[key]
    rnd = random.Random(key)
    img = Image.new('RGBA', (w, h), (0, 0, 0, 255))
    horizon = int(h * 0.53)   # about two thirds down the windows
    gradient_bands(img, 0, horizon, th['sky'])
    px = img.load()

    if th.get('stars'):
        for _ in range(w * h // 900):
            x, y = rnd.randrange(w), rnd.randrange(int(horizon * 0.8))
            b = rnd.choice([(200, 200, 230), (255, 255, 255), (150, 150, 200)])
            px[x, y] = b + (255,)
            if rnd.random() < 0.08:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    px[(x + dx) % w, max(0, y + dy)] = (140, 140, 190, 255)

    def disc(cx, cy, r, col, glow=None, glow_r=0):
        if glow:
            gm = ellipse(blank(w, h), cx, cy, glow_r, glow_r) & ~ellipse(blank(w, h), cx, cy, r + 1, r + 1)
            ys, xs = np.nonzero(gm)
            for y, x in zip(ys, xs):
                d = math.hypot(x - cx, y - cy)
                t = 1 - (d - r) / (glow_r - r)
                if t * 0.7 > BAYER4[y % 4, x % 4]:
                    base = px[x, y][:3]
                    px[x, y] = lerp(base, C(glow), 0.35) + (255,)
        fill_mask(img, ellipse(blank(w, h), cx, cy, r, r), col)

    if th.get('moon'):
        mx, my = int(w * 0.7), int(h * 0.18)
        disc(mx, my, 18, '#f4ecc8', glow='#8a80c0', glow_r=46)
        # craters
        for dx, dy, r in ((-5, -4, 3), (6, 3, 4), (-2, 8, 2)):
            fill_mask(img, ellipse(blank(w, h), mx + dx, my + dy, r, r), '#d8ceac')
    if th.get('sun'):
        sx, sy = int(w * 0.35), int(horizon - 26)
        disc(sx, sy, 30, '#ffe8a0', glow='#ffb070', glow_r=80)
        # sun bands like in old VGA sunsets
        for i, yy in enumerate(range(sy + 6, sy + 30, 6)):
            rect_m = rect(blank(w, h), sx - 32, yy, sx + 32, yy + 1 + i // 2)
            fill_mask(img, rect_m & ellipse(blank(w, h), sx, sy, 31, 31), th['sky'][-2])

    # clouds: flat lens shapes with a lighter top edge
    ncl = 7 if not th.get('storm') else 14
    for i in range(ncl):
        cx, cy = rnd.randrange(w), rnd.randrange(int(horizon * 0.15), int(horizon * 0.75))
        cw, ch = rnd.randrange(60, 160), rnd.randrange(6, 14)
        cm = blank(w, h)
        for j in range(5):
            ellipse(cm, (cx + rnd.randrange(-cw // 2, cw // 2)) % w, cy + rnd.randrange(-ch // 2, ch // 2),
                    rnd.randrange(cw // 5, cw // 3), ch)
        # wrap horizontally
        cm2 = cm.copy()
        if th.get('storm'):
            col, top = '#262636', '#3e3e58'
        else:
            col = lerp(C(th['sky'][min(len(th['sky']) - 1, int(cy / horizon * len(th['sky'])))]), C(th['sky'][-1]), 0.45)
            top = lerp(col, (255, 255, 255), 0.25)
        fill_mask(img, cm2, col)
        edge = cm2 & ~np.roll(cm2, 2, axis=0)
        fill_mask(img, edge, top)

    if th.get('storm'):
        for _ in range(3):
            x, y = rnd.randrange(60, w - 60), 10
            lm = blank(w, h)
            while y < horizon - 10:
                nx, ny = x + rnd.randrange(-12, 13), y + rnd.randrange(10, 24)
                line(lm, (x, y), (nx, ny))
                line(lm, (x + 1, y), (nx + 1, ny))
                x, y = nx, ny
            fill_mask(img, lm, '#f0f0ff')

    # sea
    gradient_bands(img, horizon, h, th['sea'])
    # glitter of the moon / sun on the water
    gx = int(w * 0.7) if th.get('moon') else int(w * 0.35)
    if th.get('moon') or th.get('sun'):
        glint = C('#f4ecc8') if th.get('moon') else C('#ffd890')
        for y in range(horizon + 2, h, 3):
            spread = 6 + (y - horizon) * 0.5
            for _ in range(3):
                x0 = int(gx + rnd.uniform(-spread, spread))
                ln = rnd.randrange(3, 10)
                for x in range(x0, x0 + ln):
                    px[x % w, y] = glint + (255,)
    # wave strokes
    for _ in range(w * 2):
        x, y = rnd.randrange(w), rnd.randrange(horizon + 4, h)
        ln = rnd.randrange(2, 7)
        c = lerp(C(th['sea'][0]), (255, 255, 255), 0.18)
        for xx in range(x, x + ln):
            px[xx % w, y] = c + (255,)

    # far land: wrap-around silhouettes on the horizon
    def ridge(base_y, amp, n, col, seed, crop=None):
        nz = wrap_noise(w, n, amp, seed)
        for x in range(w):
            top = int(base_y - abs(nz[x]) - amp * 0.2)
            if crop and not crop(x):
                continue
            for y in range(top, base_y + 2):
                px[x, y] = C(col) + (255,)

    isl = th.get('island')
    if th.get('city'):
        x = 0
        while x < w:
            bw, bh = rnd.randrange(12, 34), rnd.randrange(20, 110)
            for xx in range(x, min(w, x + bw)):
                for yy in range(horizon - bh, horizon + 1):
                    px[xx, yy] = C(th['land2']) + (255,)
            # lit windows
            for yy in range(horizon - bh + 4, horizon - 2, 5):
                for xx in range(x + 2, min(w, x + bw - 2), 4):
                    if rnd.random() < 0.35:
                        px[xx, yy] = (255, 210, 120, 255)
                        px[xx + 1 if xx + 1 < w else xx, yy] = (240, 180, 100, 255)
            x += bw + rnd.randrange(0, 6)
    if isl == 'hills':
        ridge(horizon, 26, 2, th['land2'], 1)
        ridge(horizon, 12, 4, th['land'], 2)
    elif isl == 'rocks':
        ridge(horizon, 40, 3, th['land2'], 3)
        ridge(horizon, 16, 6, th['land'], 4)
    elif isl == 'island':
        # one big island with palms, plus a far small one
        cx = int(w * 0.62)
        im = ellipse(blank(w, h), cx, horizon + 6, 150, 34)
        im &= rect(blank(w, h), 0, 0, w, horizon)
        fill_mask(img, im, th['land'])
        im2 = ellipse(blank(w, h), int(w * 0.12), horizon + 3, 60, 14) & rect(blank(w, h), 0, 0, w, horizon)
        fill_mask(img, im2, th['land2'])
    if th.get('palms'):
        for px0, lean in ((int(w * 0.55), -1), (int(w * 0.6), 1), (int(w * 0.68), 1), (int(w * 0.1), 1)):
            base = horizon - (24 if px0 > w * 0.3 else 8)
            pm = blank(w, h)
            top = (px0 + lean * 10, base - 46)
            capsule(pm, (px0, base), top, 2, 1.2)
            for ang in (-160, -130, -100, -60, -20, 10):
                a = math.radians(ang)
                tip = (top[0] + math.cos(a) * 22, top[1] + math.sin(a) * 10 + 8)
                mid = (top[0] + math.cos(a) * 12, top[1] + math.sin(a) * 8)
                capsule(pm, top, mid, 2.4, 2)
                capsule(pm, mid, tip, 2, 0.8)
            fill_mask(img, pm, th['land'])
    if th.get('volcano'):
        cx = int(w * 0.3)
        vm = polygon(blank(w, h), [(cx - 130, horizon + 1), (cx - 22, horizon - 70), (cx + 20, horizon - 72),
                                   (cx + 120, horizon + 1)])
        fill_mask(img, vm, th['land2'])
        # glowing crater and lava trickles
        fill_mask(img, ellipse(blank(w, h), cx - 1, horizon - 70, 20, 3), '#ff6a20')
        lm = blank(w, h)
        for dx in (-12, 3, 14):
            x, y = cx + dx, horizon - 69
            while y < horizon - 14:
                nx, ny = x + rnd.randrange(-3, 4) + (dx // 8), y + rnd.randrange(5, 10)
                line(lm, (x, y), (nx, ny))
                x, y = nx, ny
        fill_mask(img, lm, '#e8401a')
        # smoke
        for i in range(8):
            fill_mask(img, ellipse(blank(w, h), cx + i * 9 + rnd.randrange(-4, 4), horizon - 80 - i * 10,
                                   10 + i * 3, 6 + i), '#2a1e3e', dither_to=th['sky'][1], amount=0.4)
        # the skull rock, of course
        sx = int(w * 0.78)
        sm = ellipse(blank(w, h), sx, horizon - 18, 26, 22) | rect(blank(w, h), sx - 16, horizon - 10, sx + 16, horizon)
        fill_mask(img, sm, th['land'])
        for ex in (-9, 9):
            fill_mask(img, ellipse(blank(w, h), sx + ex, horizon - 20, 5, 6), '#ff8a2a')
        fill_mask(img, polygon(blank(w, h), [(sx - 3, horizon - 8), (sx + 3, horizon - 8), (sx, horizon - 13)]), '#ff8a2a')

    if th.get('ship'):
        sx, sy = int(w * 0.32), horizon + 10
        hull = polygon(blank(w, h), [(sx - 40, sy - 10), (sx + 44, sy - 12), (sx + 30, sy + 4), (sx - 30, sy + 4)])
        fill_mask(img, hull, '#0c0a18')
        for mx, mh in ((sx - 16, 60), (sx + 10, 74), (sx + 32, 46)):
            fill_mask(img, rect(blank(w, h), mx, sy - 10 - mh, mx + 1, sy - 10), '#0c0a18')
            for k in range(3):
                sw = 26 - k * 5
                sail = polygon(blank(w, h), [(mx - sw // 2, sy - 16 - mh + k * 18 + 6), (mx + sw // 2, sy - 16 - mh + k * 18 + 6),
                                             (mx + sw // 2 + 2, sy - mh + k * 18 + 4), (mx - sw // 2 + 2, sy - mh + k * 18 + 4)])
                fill_mask(img, sail, '#2c2850', dither_to='#3c3668', amount=0.3)
        fill_mask(img, rect(blank(w, h), sx + 9, sy - 92, sx + 18, sy - 86), '#0c0a18')   # jolly roger
        px[sx + 13, sy - 90] = (230, 230, 230, 255)
        # lantern lights
        for lx in (sx - 20, sx, sx + 22):
            px[lx, sy - 6] = (255, 200, 90, 255)

    if th.get('storm'):
        # rain streaks
        for _ in range(w * h // 120):
            x, y = rnd.randrange(w), rnd.randrange(h)
            for k in range(4):
                xx, yy = (x - k) % w, y + k * 2
                if yy < h:
                    px[xx, yy] = lerp(px[xx, yy][:3], (160, 170, 200), 0.5) + (255,)
    return img


# ---------------------------------------------------------------- wall layer (windows are holes)

def wall_tile(key, w=256, h=WALL_H):
    """One 8-unit wall segment with a big window. The camera sees units 0..14 of the wall."""
    th = THEMES[key]
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    px = img.load()
    wall, wall2 = C(th['wall']), C(th['wall2'])
    # wallpaper: soft vertical stripes with dithered seams
    for y in range(h):
        for x in range(w):
            stripe = (x // 8) % 2 == 0
            c = wall if stripe else wall2
            if x % 8 == 0 and BAYER4[y % 4, x % 4] > 0.5:
                c = lerp(wall, wall2, 0.5)
            px[x, y] = c + (255,)
    if th.get('panel'):
        # boardroom wood panelling
        for y in range(h):
            for x in range(w):
                g = (math.sin(x * 0.7 + math.sin(y * 0.05 + x) * 2) + 1) / 2
                c = lerp(wall, wall2, g * 0.8)
                if x % 64 in (0, 1):
                    c = C(th['wains'])
                elif x % 64 == 2:
                    c = lerp(wall, (255, 255, 255), 0.12)
                px[x, y] = c + (255,)

    floor_y = h - 2 * U          # world y=2 is where the main floor sits on most levels (only decorative)
    # wainscoting band at the bottom and a cornice at the top
    wains_top = h - 3 * U
    for y in range(wains_top, h):
        for x in range(w):
            c = C(th['wains'])
            if (x % 32) in (0, 31):
                c = shift(c, -0.05)
            if (x % 32) == 1:
                c = shift(c, 0.04)
            px[x, y] = c + (255,)
    for y in range(wains_top - 6, wains_top):
        for x in range(w):
            t = (y - (wains_top - 6)) / 6
            px[x, y] = (lerp(C(th['trim']), shift(C(th['trim']), -0.2), t) if y < wains_top - 1 else shift(C(th['trim']), -0.25)) + (255,)
    for y in range(0, 14):
        for x in range(w):
            c = C(th['trim']) if y < 10 else shift(C(th['trim']), -0.18)
            if y in (3, 7):
                c = shift(C(th['trim']), 0.1)
            px[x, y] = c + (255,)

    # window: 5..10.2 units above the bottom of the wall
    wx0, wx1 = 40, w - 40
    wy0, wy1 = h - int(10.2 * U), h - int(5.0 * U)
    frame = C('#e8e0d0') if not th.get('panel') else C(th['trim'])
    fr2 = shift(frame, -0.2)
    for y in range(wy0 - 6, wy1 + 10):
        for x in range(wx0 - 6, wx1 + 6):
            px[x, y] = (frame if (y < wy0 - 2 or x < wx0 - 2) else fr2) + (255,)
    # sill
    for y in range(wy1 + 4, wy1 + 12):
        for x in range(wx0 - 12, wx1 + 12):
            px[x, y] = (frame if y < wy1 + 7 else fr2) + (255,)
    # glass hole with mullions
    for y in range(wy0, wy1):
        for x in range(wx0, wx1):
            mull = abs(x - (wx0 + wx1) // 2) <= 2 or abs(y - (wy0 + int((wy1 - wy0) * 0.4))) <= 1
            if mull:
                px[x, y] = fr2 + (255,)
            else:
                px[x, y] = (0, 0, 0, 0)
    # a few glass reflection streaks, half transparent
    for i in range(18):
        for y in range(wy0 + 4 + i, wy0 + 4 + i + 1):
            for x in range(wx0 + 6 + i, wx0 + 10 + i):
                if px[x, y][3] == 0:
                    px[x, y] = (255, 255, 255, 40)
    # window shadow on the wall below the sill
    for y in range(wy1 + 12, wy1 + 16):
        for x in range(wx0 - 10, wx1 + 12):
            if BAYER4[y % 4, x % 4] < 0.5:
                c = px[x, y]
                px[x, y] = shift(c[:3], -0.06) + (255,)
    # moody lighting: the wall gets darker towards the ceiling (dithered steps, like VGA rooms)
    for y in range(14, 150):
        t = 1 - (y - 14) / 136
        for x in range(w):
            c = px[x, y]
            if c[3] == 255:
                steps = (0.0, 0.05, 0.10, 0.15)
                k = t * 3
                i = min(int(k), 2)
                d = steps[i + 1] if (k - i) > BAYER4[y % 4, x % 4] else steps[i]
                px[x, y] = shift(c[:3], -d) + (255,)
    if th.get('panel'):
        # curtains are props; add a dark pelmet over the window
        for y in range(wy0 - 18, wy0 - 6):
            for x in range(wx0 - 14, wx1 + 14):
                px[x, y] = (shift(C(th['carpet']), -0.05) if y < wy0 - 9 else shift(C(th['carpet']), -0.2)) + (255,)
    return img


# ---------------------------------------------------------------- floor tiles

def floor_tiles(key):
    """Returns (fill 32x32 tileable, top 32x32 with carpet edge, desk 32x24 tileable)."""
    th = THEMES[key]
    rnd = random.Random(key + 'f')
    base = C(th['floor'])
    dark, darker = shift(base, -0.06), shift(base, -0.12)
    fill = Image.new('RGBA', (U, U))
    p = fill.load()
    # bricks / concrete blocks
    for y in range(U):
        for x in range(U):
            row = y // 8
            off = 8 if row % 2 else 0
            mortar = y % 8 == 7 or (x + off) % 16 == 15
            c = darker if mortar else (base if BAYER4[y % 4, x % 4] > 0.15 else dark)
            if (x + off) % 16 == 0 and not mortar:
                c = shift(base, 0.04)
            p[x, y] = c + (255,)
    for _ in range(10):
        x, y = rnd.randrange(U), rnd.randrange(U)
        p[x, y] = darker + (255,)

    # top tile: a strip of floor seen slightly from above, then a lip, then the darker foundation
    top = fill.copy()
    tp = top.load()
    carpet = C(th['carpet'])
    far_c, near_c = shift(carpet, -0.06), shift(carpet, 0.03)
    for y in range(0, 14):
        for x in range(U):
            if y == 0:
                c = shift(carpet, 0.12)
            else:
                t = y / 13
                c = near_c if t > BAYER4[y % 4, x % 4] else far_c
                # a faint woven pattern
                if (x + y * 3) % 11 == 0 and y > 2:
                    c = shift(c, -0.04)
            tp[x, y] = c + (255,)
    trim = C(th['trim'])
    for y in range(14, 19):
        for x in range(U):
            c = shift(trim, 0.08) if y == 14 else (trim if y < 17 else shift(trim, -0.2))
            tp[x, y] = c + (255,)
    for x in range(U):
        tp[x, 19] = shift(base, -0.25) + (255,)
        tp[x, 20] = shift(base, -0.15) + (255,)

    desk = Image.new('RGBA', (U, 24), (0, 0, 0, 0))
    dp = desk.load()
    wood, woodl, woodd = C('#b07a48'), C('#cc965c'), C('#7a4a28')
    for y in range(24):
        for x in range(U):
            if y < 2:
                c = woodl
            elif y < 6:
                g = (math.sin(x * 0.4 + y) + 1) / 2
                c = wood if g > 0.3 else shift(wood, -0.04)
            elif y == 6:
                c = woodd
            elif y < 20:
                # drawer fronts hanging under the desk top
                c = shift(wood, -0.08)
                if x % 16 in (0, 15) or y in (7, 19):
                    c = woodd
                if x % 16 in (7, 8) and y in (11, 12):
                    c = C('#e0c060')   # brass handle
            else:
                c = (0, 0, 0, 0)
            dp[x, y] = c if len(c) == 4 else c + (255,)
    # dark outline at the bottom of the drawers
    for x in range(U):
        dp[x, 20] = C('#2a1a10') + (255,)
    return fill, top, desk


# ---------------------------------------------------------------- props

def prop(name, key):
    th = THEMES[key]
    if name == 'plant':
        s = Sprite(32, 56)
        s.part(polygon(blank(32, 56), [(9, 40), (23, 40), (21, 54), (11, 54)]), Ramp('#c0603a'), band=2)
        s.part(rect(blank(32, 56), 8, 38, 24, 41), Ramp('#d8784a'), band=1)
        leaves = blank(32, 56)
        for a, l in ((-150, 15), (-120, 18), (-90, 20), (-60, 18), (-30, 15), (-105, 12), (-75, 13)):
            r = math.radians(a)
            capsule(leaves, (16, 38), (16 + math.cos(r) * l, 38 + math.sin(r) * l * 1.4), 2.4, 1)
        s.part(leaves, Ramp('#3e8a3a'), band=1)
        s.outline()
        return s.image()
    if name == 'cooler':
        s = Sprite(24, 64)
        s.part(rect(blank(24, 64), 4, 26, 19, 62), Ramp('#dcdcdc'), band=2)
        s.part(ellipse(blank(24, 64), 12, 15, 8, 12) & rect(blank(24, 64), 0, 3, 24, 26), Ramp('#7ac0f0'), band=2)
        s.part(rect(blank(24, 64), 6, 34, 9, 37), Ramp('#3a7ad0'), band=0, cast=False)
        s.part(rect(blank(24, 64), 14, 34, 17, 37), Ramp('#d03a3a'), band=0, cast=False)
        s.dot(9, 9, (255, 255, 255)); s.dot(9, 10, (255, 255, 255))
        s.outline()
        return s.image()
    if name == 'cabinet':
        s = Sprite(32, 64)
        s.part(rect(blank(32, 64), 3, 6, 28, 62), Ramp('#8a92a0'), band=2)
        for y0 in (9, 27, 45):
            s.part(rect(blank(32, 64), 6, y0, 25, y0 + 14), Ramp('#9aa2b0'), band=1, cast=False)
            s.part(rect(blank(32, 64), 13, y0 + 4, 18, y0 + 5), Ramp('#3a3a44'), shade=False, cast=False)
        # files sticking out + a mug on top
        s.part(rect(blank(32, 64), 8, 2, 14, 6), Ramp('#f0e8c8'), band=1)
        s.part(rect(blank(32, 64), 19, 0, 24, 6), Ramp('#e04a4a'), band=1)
        s.outline()
        return s.image()
    if name == 'server':
        s = Sprite(32, 80)
        s.part(rect(blank(32, 80), 2, 2, 29, 78), Ramp('#2a2e3a'), band=2)
        rnd = random.Random(7)
        for y0 in range(6, 74, 8):
            s.part(rect(blank(32, 80), 5, y0, 26, y0 + 5), Ramp('#3a404e'), band=1, cast=False)
            for x0 in range(7, 24, 3):
                s.dot(x0, y0 + 2, rnd.choice([(80, 240, 120), (80, 240, 120), (250, 180, 60), (60, 60, 70)]))
        s.outline()
        return s.image()
    if name == 'whiteboard':
        s = Sprite(64, 52)
        s.part(rect(blank(64, 52), 2, 2, 61, 44), Ramp('#b8bcc4'), band=1)
        s.part(rect(blank(64, 52), 5, 5, 58, 41), Ramp('#f8f8f4'), shade=False, hi=False, cast=False)
        rnd = random.Random(key)
        for i in range(7):
            x, y = rnd.randrange(8, 50), rnd.randrange(8, 32)
            s.part(rect(blank(64, 52), x, y, x + 6, y + 6), Ramp(rnd.choice(['#ffe066', '#ff9ac0', '#9ad8ff', '#a8f0a0'])),
                   band=1, cast=True)
        lm = blank(64, 52)
        line(lm, (9, 36), (24, 20)); line(lm, (24, 20), (36, 28)); line(lm, (36, 28), (54, 11))
        s.pixels(lm, (200, 40, 40))
        s.part(rect(blank(64, 52), 8, 44, 55, 46), Ramp('#8a8e96'), band=1)
        s.outline()
        return s.image()
    if name == 'flipchart':
        s = Sprite(40, 72)
        lm = blank(40, 72)
        capsule(lm, (20, 50), (8, 70), 1.2); capsule(lm, (20, 50), (32, 70), 1.2); capsule(lm, (20, 50), (20, 70), 1.2)
        s.part(lm, Ramp('#6a6a72'), band=0)
        s.part(rect(blank(40, 72), 4, 4, 35, 50), Ramp('#f8f6ee'), band=2)
        dm = blank(40, 72)
        for i, hgt in enumerate((10, 18, 26, 34)):
            rect(dm, 8 + i * 7, 46 - hgt, 12 + i * 7, 46)
        s.part(dm, Ramp('#4a9ad8'), band=1, cast=False)
        al = blank(40, 72)
        line(al, (8, 30), (34, 8))
        s.pixels(al, (210, 50, 50))
        s.part(rect(blank(40, 72), 2, 2, 37, 5), Ramp('#3a3a44'), band=1)
        s.outline()
        return s.image()
    if name == 'bugboard':
        s = Sprite(64, 48)
        s.part(rect(blank(64, 48), 2, 2, 61, 45), Ramp('#b07a48'), band=1)
        s.part(rect(blank(64, 48), 5, 5, 58, 42), Ramp('#c8a070'), shade=False, cast=False)
        rnd = random.Random(3)
        for i in range(10):
            x, y = rnd.randrange(8, 50), rnd.randrange(8, 34)
            s.part(rect(blank(64, 48), x, y, x + 7, y + 5), Ramp('#f8f4e4'), band=1)
            # a little red bug drawn on each card
            s.dot(x + 3, y + 2, (200, 40, 40)); s.dot(x + 4, y + 2, (200, 40, 40)); s.dot(x + 3, y + 3, (60, 20, 20))
        s.outline()
        return s.image()
    if name == 'poster':
        s = Sprite(64, 44)
        frame = Ramp(th['trim'])
        s.part(rect(blank(64, 44), 1, 1, 62, 42), frame, band=1)
        s.part(rect(blank(64, 44), 4, 4, 59, 39), Ramp('#f4ecd8'), shade=False, hi=False, cast=False)
        s.outline()
        return s.image()
    if name == 'portrait':
        s = Sprite(48, 60)
        s.part(rect(blank(48, 60), 1, 1, 46, 58), Ramp('#d0a040', hi='#f8d870'), band=2)
        s.part(rect(blank(48, 60), 6, 6, 41, 53), Ramp('#2a2236'), shade=False, hi=False, cast=False)
        # a stern executive: head + suit
        s.part(ellipse(blank(48, 60), 24, 26, 9, 11), Ramp('#e0b088'), band=2)
        s.part(polygon(blank(48, 60), [(10, 53), (38, 53), (34, 40), (14, 40)]), Ramp('#1e2438'), band=2)
        s.part(polygon(blank(48, 60), [(22, 40), (26, 40), (25, 50), (23, 50)]), Ramp('#b02030'), band=1)
        s.part(ellipse(blank(48, 60), 24, 18, 9, 4), Ramp('#9a9aa2'), band=1, cast=False)
        s.dot(21, 26, (20, 16, 30)); s.dot(27, 26, (20, 16, 30)); s.dot(22, 32, (90, 40, 30)); s.dot(26, 32, (90, 40, 30))
        s.outline()
        return s.image()
    if name == 'curtain':
        s = Sprite(32, 200)
        cm = blank(32, 200)
        polygon(cm, [(2, 0), (30, 0), (24, 120), (28, 196), (4, 196), (10, 120)])
        s.part(cm, Ramp(th['carpet']), band=3)
        fm = blank(32, 200)
        for x0 in (9, 16, 23):
            line(fm, (x0, 4), (x0 - 2, 120)); line(fm, (x0 - 2, 120), (x0, 194))
        s.pixels(fm & cm, shift(C(th['carpet']), -0.16))
        s.part(rect(blank(32, 200), 6, 112, 26, 118), Ramp('#d8b040'), band=1)
        s.outline()
        return s.image()
    if name == 'clock':
        s = Sprite(28, 28)
        s.part(ellipse(blank(28, 28), 14, 14, 12, 12), Ramp('#d0a040'), band=1)
        s.part(ellipse(blank(28, 28), 14, 14, 9, 9), Ramp('#f6f0e0'), shade=False, cast=False)
        lm = blank(28, 28)
        line(lm, (14, 14), (14, 7)); line(lm, (14, 14), (19, 16))
        s.pixels(lm, (30, 20, 30))
        s.outline()
        return s.image()
    if name == 'globe':
        s = Sprite(32, 56)
        s.part(polygon(blank(32, 56), [(10, 54), (22, 54), (18, 46), (14, 46)]), Ramp('#7a4a28'), band=1)
        s.part(capsule(blank(32, 56), (16, 46), (16, 34), 1.5), Ramp('#7a4a28'), band=0)
        s.part(ellipse(blank(32, 56), 16, 22, 12, 12), Ramp('#3a7ac0'), band=2)
        lm = ellipse(blank(32, 56), 12, 18, 5, 4) | ellipse(blank(32, 56), 20, 27, 4, 3)
        s.part(lm & ellipse(blank(32, 56), 16, 22, 11, 11), Ramp('#5aa04a'), band=1, cast=False)
        s.outline()
        return s.image()
    if name == 'statue':
        s = Sprite(32, 72)
        s.part(rect(blank(32, 72), 6, 52, 25, 70), Ramp('#3a2a4a'), band=2)
        gold = Ramp('#e8b830', hi='#fff0a0')
        fm = blank(32, 72)
        ellipse(fm, 16, 14, 5, 6)
        polygon(fm, [(9, 22), (23, 22), (21, 50), (11, 50)])
        capsule(fm, (21, 24), (27, 10), 2)
        s.part(fm, gold, band=2)
        s.part(polygon(blank(32, 72), [(24, 9), (30, 9), (31, 4), (28, 6), (27, 2), (25, 6), (23, 4)]), gold, band=1)
        s.outline()
        return s.image()
    if name == 'aquarium':
        s = Sprite(64, 72)
        s.part(rect(blank(64, 72), 4, 46, 59, 70), Ramp('#2a2236'), band=2)
        s.part(rect(blank(64, 72), 2, 8, 61, 46), Ramp('#3aa0c8'), band=2)
        s.part(rect(blank(64, 72), 2, 4, 61, 8), Ramp('#1e1e2a'), band=1)
        for fx, fy, col in ((18, 22, '#ff8a2a'), (40, 30, '#ffd040'), (30, 16, '#ff5a8a')):
            fm = ellipse(blank(64, 72), fx, fy, 4, 2)
            polygon(fm, [(fx - 3, fy), (fx - 7, fy - 3), (fx - 7, fy + 3)])
            s.part(fm, Ramp(col), band=1, cast=False)
        s.part(polygon(blank(64, 72), [(4, 44), (20, 38), (36, 42), (60, 37), (60, 45), (4, 45)]), Ramp('#e0c890'), band=1, cast=False)
        s.outline()
        return s.image()
    raise KeyError(name)


# ---------------------------------------------------------------- pickups, door, projectiles, fx

def pickups():
    out = {}
    # coffee: a steaming mug
    s = Sprite(24, 28)
    s.part(rect(blank(24, 28), 4, 10, 16, 25), Ramp('#f4f0e8'), band=2)
    s.part(ellipse(blank(24, 28), 18, 17, 4, 5) & ~ellipse(blank(24, 28), 18, 17, 2, 3), Ramp('#f4f0e8'), band=1)
    s.part(rect(blank(24, 28), 5, 10, 15, 11), Ramp('#5a3418'), shade=False, cast=False)
    s.part(rect(blank(24, 28), 6, 15, 14, 19), Ramp('#d03a3a'), band=1, cast=False)   # a heart logo strip
    sm = blank(24, 28)
    for x0 in (7, 12):
        line(sm, (x0, 8), (x0 + 1, 5)); line(sm, (x0 + 1, 5), (x0, 2))
    s.pixels(sm, (230, 230, 240))
    s.outline()
    out['coffee'] = s.image()
    # Gantt chart: a treasure-map style scroll with bars
    s = Sprite(32, 28)
    s.part(rect(blank(32, 28), 4, 4, 27, 23), Ramp('#ecd8a0', hi='#fff0c0'), band=2)
    s.part(capsule(blank(32, 28), (3, 4), (3, 23), 2.5), Ramp('#c8a868'), band=1)
    s.part(capsule(blank(32, 28), (28, 4), (28, 23), 2.5), Ramp('#c8a868'), band=1)
    for i, (x0, x1, col) in enumerate([(8, 16, '#3a7ad0'), (12, 22, '#d03a3a'), (15, 25, '#3aa05a'), (9, 14, '#d0a030')]):
        s.part(rect(blank(32, 28), x0, 7 + i * 4, x1, 8 + i * 4), Ramp(col), shade=False, cast=False)
    xm = blank(32, 28)
    line(xm, (22, 19), (25, 22)); line(xm, (25, 19), (22, 22))
    s.pixels(xm, (200, 30, 30))
    s.outline()
    out['gantt'] = s.image()
    # scope freeze: an ice block with a frozen document inside
    s = Sprite(28, 28)
    s.part(rect(blank(28, 28), 3, 3, 24, 24), Ramp('#a8e0ff', hi='#e8f8ff'), band=3)
    s.part(rect(blank(28, 28), 9, 7, 18, 19), Ramp('#f8f4e4'), band=1)
    lm = blank(28, 28)
    for y in (10, 13, 16):
        line(lm, (11, y), (16, y))
    s.pixels(lm, (90, 110, 160))
    s.pixels(line(blank(28, 28), (5, 6), (9, 4)) | line(blank(28, 28), (5, 9), (12, 4)), (255, 255, 255))
    s.outline()
    out['freeze'] = s.image()
    return out


def door(open_):
    s = Sprite(56, 96)
    s.part(rect(blank(56, 96), 2, 2, 53, 95), Ramp('#6a4a32'), band=2)            # frame
    inner = rect(blank(56, 96), 8, 8, 47, 95)
    if open_:
        s.part(inner, Ramp('#fff4c0', hi='#ffffff'), shade=False, hi=False)
        s.part(polygon(blank(56, 96), [(8, 8), (20, 14), (20, 95), (8, 95)]), Ramp('#3a7a4a'), band=1)
    else:
        s.part(inner, Ramp('#a83a2a'), band=2)
        for y0 in (14, 52):
            s.part(rect(blank(56, 96), 13, y0, 42, y0 + 30), Ramp('#b84a3a'), band=1, cast=False)
        s.part(ellipse(blank(56, 96), 41, 58, 2.5, 2.5), Ramp('#e8c040'), band=0)
    # EXIT sign above
    s.part(rect(blank(56, 96), 14, 0, 41, 7), Ramp('#3aa05a' if open_ else '#c03030'), band=1)
    s.outline()
    return s.image()


def paper(kind):
    s = Sprite(40, 16)
    col = {'memo': '#fce8a0', 'bug': '#f8f4e4', 'budget': '#f4f0e0', 'invite': '#e8eef8'}[kind]
    s.part(rect(blank(40, 16), 1, 1, 38, 14), Ramp(col), band=1)
    if kind == 'invite':
        lm = blank(40, 16)
        line(lm, (1, 1), (20, 9)); line(lm, (20, 9), (38, 1))
        s.pixels(lm, (150, 160, 190))
    if kind == 'bug':
        s.part(ellipse(blank(40, 16), 33, 8, 3, 3), Ramp('#d02a2a'), band=0)
    if kind == 'budget':
        s.part(rect(blank(40, 16), 2, 2, 6, 13), Ramp('#3aa05a'), band=0, cast=False)
    s.outline()
    return s.image()


def spark():
    s = Sprite(9, 9)
    m = blank(9, 9)
    line(m, (4, 0), (4, 8)); line(m, (0, 4), (8, 4))
    rect(m, 3, 3, 5, 5)
    s.pixels(m, (255, 255, 255))
    return s.image()


def smear(w=48, h=48):
    """A crescent swing trail, white; tinted at runtime."""
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    p = img.load()
    cx, cy = w * 0.2, h * 0.5
    for y in range(h):
        for x in range(w):
            d = math.hypot(x + 0.5 - cx, (y + 0.5 - cy) * 0.9)
            ang = math.atan2(y + 0.5 - cy, x + 0.5 - cx)
            if w * 0.48 < d < w * 0.72 and abs(ang) < 1.25:
                t = 1 - abs(ang) / 1.25
                inner = (d - w * 0.48) / (w * 0.24)
                if t * (1.2 - inner) > BAYER4[y % 4, x % 4] * 0.9:
                    p[x, y] = (255, 255, 255, 255 if inner > 0.45 else 200)
    return img
