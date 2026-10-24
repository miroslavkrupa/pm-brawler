"""Tiny pixel-art toolkit: hue-shifted colour ramps, part masks, pillow shading and sel-out outlines.

Everything works on numpy arrays at 1:1 pixel scale (no anti-aliasing), y grows downwards like
images do. A sprite is built from parts drawn back to front; each part is shaded from its own
mask and the finished silhouette gets a coloured outline, which is what gives the late-80s /
early-90s adventure game look.
"""
import colorsys
import math

import numpy as np
from PIL import Image


# ---------------------------------------------------------------- colours

def hex2rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def shift(rgb, dl=0.0, ds=0.0, dh=0.0):
    """Shift lightness / saturation / hue (hue in degrees)."""
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    h = (h + dh / 360) % 1
    l = min(1, max(0, l + dl))
    s = min(1, max(0, s + ds))
    r, g, b = colorsys.hls_to_rgb(h, l, s)
    return (round(r * 255), round(g * 255), round(b * 255))


def toward_hue(rgb, target_deg, amount, dl, ds=0.0):
    """Shift lightness and pull the hue toward a target (warm highlights, cool shadows)."""
    r, g, b = (c / 255 for c in rgb)
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    hd = h * 360
    diff = ((target_deg - hd + 540) % 360) - 180
    hd += max(-14.0, min(14.0, diff * amount))  # capped so skin never turns pink and blues never go cyan
    l = min(1, max(0, l + dl))
    s = min(1, max(0, s + ds))
    r, g, b = colorsys.hls_to_rgb((hd / 360) % 1, l, s)
    return (round(r * 255), round(g * 255), round(b * 255))


class Ramp:
    """Five tones: hi, base, mid-shadow, shadow, outline. Highlights lean yellow, shadows lean purple-blue."""

    def __init__(self, base, hi=None, mid=None, sh=None, out=None):
        def c(v):
            return hex2rgb(v) if isinstance(v, str) else v
        b = c(base)
        self.base = b
        self.hi = c(hi) or toward_hue(b, 55, 0.15, 0.10, 0.0)
        self.mid = c(mid) or toward_hue(b, 250, 0.10, -0.08, -0.04)
        self.sh = c(sh) or toward_hue(b, 255, 0.22, -0.17, -0.08)
        self.out = c(out) or toward_hue(b, 260, 0.30, -0.33, -0.12)

    def dark(self):
        return self.out


# ---------------------------------------------------------------- shapes into masks

def blank(w, h):
    return np.zeros((h, w), dtype=bool)


def ellipse(m, cx, cy, rx, ry):
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    m |= ((xs + 0.5 - cx) / max(rx, 0.01)) ** 2 + ((ys + 0.5 - cy) / max(ry, 0.01)) ** 2 <= 1.0
    return m


def rect(m, x0, y0, x1, y1):
    """Inclusive pixel rect."""
    h, w = m.shape
    x0, x1 = sorted((int(round(x0)), int(round(x1))))
    y0, y1 = sorted((int(round(y0)), int(round(y1))))
    m[max(0, y0):min(h, y1 + 1), max(0, x0):min(w, x1 + 1)] = True
    return m


def polygon(m, pts):
    """Even-odd scanline fill of a polygon sampled at pixel centres."""
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    px, py = xs + 0.5, ys + 0.5
    inside = np.zeros_like(m)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        if y1 == y2:
            continue
        cond = ((y1 > py) != (y2 > py))
        xint = (x2 - x1) * (py - y1) / (y2 - y1) + x1
        inside ^= cond & (px < xint)
    m |= inside
    return m


def capsule(m, a, b, r0, r1=None):
    """Thick line from a to b with (optionally tapering) radius."""
    if r1 is None:
        r1 = r0
    h, w = m.shape
    ys, xs = np.mgrid[0:h, 0:w]
    px, py = xs + 0.5, ys + 0.5
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    L2 = dx * dx + dy * dy
    if L2 == 0:
        t = np.zeros_like(px)
    else:
        t = np.clip(((px - ax) * dx + (py - ay) * dy) / L2, 0, 1)
    cx, cy = ax + t * dx, ay + t * dy
    r = r0 + (r1 - r0) * t
    m |= (px - cx) ** 2 + (py - cy) ** 2 <= r * r
    return m


def line(m, a, b):
    """1px Bresenham line."""
    x0, y0 = int(round(a[0])), int(round(a[1]))
    x1, y1 = int(round(b[0])), int(round(b[1]))
    dx, dy = abs(x1 - x0), -abs(y1 - y0)
    sx, sy = (1 if x0 < x1 else -1), (1 if y0 < y1 else -1)
    err = dx + dy
    h, w = m.shape
    while True:
        if 0 <= x0 < w and 0 <= y0 < h:
            m[y0, x0] = True
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy
    return m


def shifted(m, dx, dy):
    """m moved by (dx, dy); vacated cells are False."""
    out = np.zeros_like(m)
    h, w = m.shape
    xs0, xs1 = max(0, dx), min(w, w + dx)
    ys0, ys1 = max(0, dy), min(h, h + dy)
    out[ys0:ys1, xs0:xs1] = m[ys0 - dy:ys1 - dy, xs0 - dx:xs1 - dx]
    return out


# ---------------------------------------------------------------- sprite composition

class Sprite:
    """Parts are painted back to front. Each part = mask + ramp, shaded as a soft 'pillow' lit from top-left."""

    def __init__(self, w, h):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), dtype=np.uint8)
        self.alpha = np.zeros((h, w), dtype=bool)
        self.owner = np.full((h, w), -1, dtype=int)
        self.parts = []

    def part(self, mask, ramp, shade=True, hi=True, cast=True, flat=False, band=2):
        """Paint a part. band = width of the shadow band on the lower-right edge."""
        mask = mask.copy()
        idx = len(self.parts)
        self.parts.append(ramp)
        if cast:
            # the new part throws a 1px contact shadow onto what's already there, below and to the right
            under = shifted(mask, 1, 1) & ~mask & self.alpha
            self._darken(under)
        col = np.zeros((self.h, self.w, 3), dtype=np.uint8)
        col[...] = ramp.base
        if not flat:
            if shade:
                deep = mask & ~shifted(mask, -band, -band - 1)
                col[deep] = ramp.mid
                edge = mask & ~shifted(mask, -1, -1)
                col[edge] = ramp.sh
                bottom = mask & ~shifted(mask, 0, -1)
                col[bottom] = ramp.sh
            if hi:
                top = mask & ~shifted(mask, 1, 1) & ~(mask & ~shifted(mask, 0, -1))
                col[top] = ramp.hi
        self.rgb[mask] = col[mask]
        self.alpha |= mask
        self.owner[mask] = idx
        return mask

    def pixels(self, mask, color):
        """Paint flat detail pixels (eyes, buttons...)."""
        c = hex2rgb(color) if isinstance(color, str) else color
        self.rgb[mask] = c
        self.alpha |= mask

    def dot(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            c = hex2rgb(color) if isinstance(color, str) else color
            self.rgb[y, x] = c
            self.alpha[y, x] = True

    def _darken(self, m):
        for y, x in zip(*np.nonzero(m)):
            o = self.owner[y, x]
            if o >= 0:
                r = self.parts[o]
                c = tuple(self.rgb[y, x])
                # step one tone down the owner's ramp
                if c == r.hi:
                    nc = r.base
                elif c == r.base:
                    nc = r.mid
                elif c == r.mid:
                    nc = r.sh
                else:
                    nc = r.out
                self.rgb[y, x] = nc

    def outline(self, color=None):
        """Sel-out: each outline pixel takes the darkest tone of the part it borders."""
        a = self.alpha
        ring = np.zeros_like(a)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            ring |= shifted(a, dx, dy)
        ring &= ~a
        for y, x in zip(*np.nonzero(ring)):
            if color is not None:
                c = hex2rgb(color) if isinstance(color, str) else color
            else:
                c = None
                for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < self.h and 0 <= xx < self.w and a[yy, xx] and self.owner[yy, xx] >= 0:
                        c = self.parts[self.owner[yy, xx]].out
                        break
                if c is None:
                    c = (24, 14, 30)
            self.rgb[y, x] = c
            self.alpha[y, x] = True

    def image(self):
        out = np.zeros((self.h, self.w, 4), dtype=np.uint8)
        out[..., :3] = self.rgb
        out[..., 3] = np.where(self.alpha, 255, 0)
        return Image.fromarray(out, 'RGBA')


# ---------------------------------------------------------------- image helpers

def strip(images):
    w = sum(i.width for i in images)
    h = max(i.height for i in images)
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    x = 0
    for i in images:
        out.paste(i, (x, h - i.height))
        x += i.width
    return out


def preview(img, scale=4, bg=(70, 60, 90)):
    big = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    back = Image.new('RGBA', big.size, bg + (255,))
    back.alpha_composite(big)
    return back


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def dither_mix(c0, c1, t, x, y):
    """Ordered-dither pick between two colours, t in 0..1."""
    return c1 if t > BAYER4[y % 4, x % 4] else c0


def rotate_point(p, center, deg):
    a = math.radians(deg)
    x, y = p[0] - center[0], p[1] - center[1]
    return (center[0] + x * math.cos(a) - y * math.sin(a), center[1] + x * math.sin(a) + y * math.cos(a))
