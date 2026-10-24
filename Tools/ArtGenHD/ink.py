"""Hand-drawn cartoon toolkit on top of Skia: smooth outlines, inked strokes, painted shading and grain.

The look aims at modern 2D adventure games (Deponia and friends): thick dark-brown ink lines,
soft gradient shading with a darker band along the lower-right edges, a light rim on the
upper-left, a faint paper texture over everything and slightly muted, warm colours.
"""
import math
import os
import random

import numpy as np
import skia

HERE = os.path.dirname(__file__)
FONT_DIR = os.path.join(HERE, 'fonts')

INK = '#2b1d16'


# ---------------------------------------------------------------- colours

def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def col(h, a=255):
    if isinstance(h, int):
        return h
    r, g, b = rgb(h) if isinstance(h, str) else h
    return skia.Color(r, g, b, a)


def mix(a, b, t):
    a, b = rgb(a) if isinstance(a, str) else a, rgb(b) if isinstance(b, str) else b
    return '#%02x%02x%02x' % tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def shade(h, t):
    """Darker (t<0) toward a warm purple-brown, lighter (t>0) toward a warm cream."""
    return mix(h, '#3a2232', -t) if t < 0 else mix(h, '#fff3d6', t)


# ---------------------------------------------------------------- paths

def smooth(points, closed=True, tension=0.5):
    """Catmull-Rom spline through the points, as a Skia path."""
    p = skia.Path()
    n = len(points)
    if n < 2:
        return p
    pts = [skia.Point(*q) for q in points]
    p.moveTo(pts[0])
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else pts[(i + 1) % n]
        c1 = skia.Point(p1.fX + (p2.fX - p0.fX) * tension / 3, p1.fY + (p2.fY - p0.fY) * tension / 3)
        c2 = skia.Point(p2.fX - (p3.fX - p1.fX) * tension / 3, p2.fY - (p3.fY - p1.fY) * tension / 3)
        p.cubicTo(c1, c2, p2)
    if closed:
        p.close()
    return p


def poly(points):
    p = skia.Path()
    p.moveTo(*points[0])
    for q in points[1:]:
        p.lineTo(*q)
    p.close()
    return p


def ellipse(cx, cy, rx, ry):
    p = skia.Path()
    p.addOval(skia.Rect.MakeLTRB(cx - rx, cy - ry, cx + rx, cy + ry))
    return p


def rrect(x0, y0, x1, y1, r):
    p = skia.Path()
    p.addRRect(skia.RRect.MakeRectXY(skia.Rect.MakeLTRB(x0, y0, x1, y1), r, r))
    return p


def limb(bones, radii, cap=True):
    """Tapered tube along a polyline (joint positions + radius at each joint), smoothed."""
    left, right = [], []
    n = len(bones)
    for i, (x, y) in enumerate(bones):
        if i == 0:
            dx, dy = bones[1][0] - x, bones[1][1] - y
        elif i == n - 1:
            dx, dy = x - bones[i - 1][0], y - bones[i - 1][1]
        else:
            dx, dy = bones[i + 1][0] - bones[i - 1][0], bones[i + 1][1] - bones[i - 1][1]
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        r = radii[i]
        left.append((x + nx * r, y + ny * r))
        right.append((x - nx * r, y - ny * r))
    pts = left[:]
    if cap:
        # round end cap
        x, y = bones[-1]
        dx, dy = bones[-1][0] - bones[-2][0], bones[-1][1] - bones[-2][1]
        L = math.hypot(dx, dy) or 1
        pts.append((x + dx / L * radii[-1] * 0.9, y + dy / L * radii[-1] * 0.9))
    pts += right[::-1]
    if cap:
        x, y = bones[0]
        dx, dy = bones[0][0] - bones[1][0], bones[0][1] - bones[1][1]
        L = math.hypot(dx, dy) or 1
        pts.append((x + dx / L * radii[0] * 0.9, y + dy / L * radii[0] * 0.9))
    return smooth(pts, closed=True, tension=0.6)


def union(*paths):
    out = paths[0]
    for p in paths[1:]:
        out = skia.Op(out, p, skia.PathOp.kUnion_PathOp) or out
    return out


def intersect(a, b):
    return skia.Op(a, b, skia.PathOp.kIntersect_PathOp) or skia.Path()


def subtract(a, b):
    return skia.Op(a, b, skia.PathOp.kDifference_PathOp) or a


def translated(p, dx, dy):
    q = skia.Path(p)
    q.offset(dx, dy)
    return q


# ---------------------------------------------------------------- grain

_grain = None


def grain_shader(scale=1.0):
    """A tiling paper/brush texture (grey noise around 128) to overlay on painted areas."""
    global _grain
    if _grain is None:
        rnd = np.random.default_rng(7)
        n = 256
        base = rnd.normal(0, 1, (n, n))
        # soften into blotches + keep some fine speckle
        f = np.fft.fft2(base)
        fy = np.fft.fftfreq(n)[:, None]
        fx = np.fft.fftfreq(n)[None, :]
        blot = np.real(np.fft.ifft2(f * np.exp(-(fx ** 2 + fy ** 2) * 900)))
        blot = blot / (np.abs(blot).max() + 1e-6)
        fine = rnd.normal(0, 1, (n, n)) * 0.35
        # horizontal brush streaks
        streak = np.real(np.fft.ifft2(np.fft.fft2(rnd.normal(0, 1, (n, n))) * np.exp(-(fx ** 2) * 4000 - (fy ** 2) * 60)))
        streak = streak / (np.abs(streak).max() + 1e-6)
        v = 128 + blot * 40 + fine * 20 + streak * 18
        v = np.clip(v, 0, 255).astype(np.uint8)
        rgba = np.dstack([v, v, v, np.full_like(v, 255)])
        _grain = skia.Image.fromarray(rgba, colorType=skia.ColorType.kRGBA_8888_ColorType)
    m = skia.Matrix.Scale(scale, scale)
    return _grain.makeShader(skia.TileMode.kRepeat, skia.TileMode.kRepeat, skia.SamplingOptions(), m)


# ---------------------------------------------------------------- painting

class Ink:
    """Wraps a Skia canvas with the house style."""

    def __init__(self, w, h, scale=1.0):
        self.w, self.h = w, h
        self.surface = skia.Surface(w, h)
        self.c = self.surface.getCanvas()
        self.c.clear(skia.ColorTRANSPARENT)
        self.s = scale            # line widths and shading offsets scale with this
        self.grain_scale = None   # fixed grain size for tiling images (the 256 px texture times this must divide the width)

    # basic fills

    def fill(self, path, color, alpha=255):
        self.c.drawPath(path, skia.Paint(AntiAlias=True, Color=col(color, alpha)))

    def stroke(self, path, color=INK, width=None, alpha=255, cap=skia.Paint.kRound_Cap):
        w = (width if width is not None else 3.2) * self.s
        self.c.drawPath(path, skia.Paint(AntiAlias=True, Color=col(color, alpha), Style=skia.Paint.kStroke_Style,
                                         StrokeWidth=w, StrokeJoin=skia.Paint.kRound_Join, StrokeCap=cap))

    def line(self, pts, color=INK, width=None, alpha=255):
        self.stroke(smooth(pts, closed=False), color, width, alpha)

    def gradient(self, path, top, bottom, angle=110):
        """Fill with a linear gradient across the path's bounds (angle in degrees, 90 = top to bottom)."""
        b = path.computeTightBounds()
        cx, cy = b.centerX(), b.centerY()
        r = max(b.width(), b.height()) / 2
        a = math.radians(angle)
        p0 = skia.Point(cx - math.cos(a) * r, cy - math.sin(a) * r)
        p1 = skia.Point(cx + math.cos(a) * r, cy + math.sin(a) * r)
        sh = skia.GradientShader.MakeLinear([p0, p1], [col(top), col(bottom)])
        self.c.drawPath(path, skia.Paint(AntiAlias=True, Shader=sh))

    def painted(self, path, base, outline=True, width=None, light=0.18, dark=0.30, rim=True, shadow=True,
                grain=True, angle=115):
        """The workhorse: gradient fill, inner shadow on the lower right, rim light upper left, grain, ink line."""
        c, s = self.c, self.s
        self.gradient(path, shade(base, light * 0.6), shade(base, -dark * 0.35), angle)
        c.save()
        c.clipPath(path, skia.ClipOp.kIntersect, True)
        b = path.computeTightBounds()
        big = skia.Rect.MakeLTRB(b.left() - 200, b.top() - 200, b.right() + 200, b.bottom() + 200)
        if shadow:
            # everything outside the path shifted up-left = a band along the lower-right inside edge
            sp = skia.Path()
            sp.addRect(big)
            sp.addPath(translated(path, -7 * s, -6 * s))
            sp.setFillType(skia.PathFillType.kEvenOdd)
            c.drawPath(sp, skia.Paint(AntiAlias=True, Color=col(shade(base, -dark), 200),
                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 3.5 * s)))
        if rim:
            rp = skia.Path()
            rp.addRect(big)
            rp.addPath(translated(path, 4 * s, 4 * s))
            rp.setFillType(skia.PathFillType.kEvenOdd)
            c.drawPath(rp, skia.Paint(AntiAlias=True, Color=col(shade(base, light + 0.12), 150),
                                      MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 2.0 * s)))
        if grain:
            g = self.grain_scale if self.grain_scale is not None else 0.9 * s
            c.drawPaint(skia.Paint(Shader=grain_shader(g), BlendMode=skia.BlendMode.kOverlay, Alphaf=0.35))
        c.restore()
        if outline:
            self.stroke(path, INK, width)

    def cast_shadow(self, path, dx=6, dy=6, alpha=90, blur=4):
        """Soft shadow of a shape onto what's behind it (draw before the shape)."""
        s = self.s
        self.c.drawPath(translated(path, dx * s, dy * s),
                        skia.Paint(AntiAlias=True, Color=col('#1c1018', alpha),
                                   MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, blur * s)))

    def text(self, s_, x, y, size, color=INK, font='Kalam-Bold.ttf', align='center', rotate=0.0, alpha=255):
        tf = skia.Typeface.MakeFromFile(os.path.join(FONT_DIR, font))
        f = skia.Font(tf, size)
        w = f.measureText(s_)
        dx = {'center': -w / 2, 'left': 0, 'right': -w}[align]
        self.c.save()
        self.c.translate(x, y)
        self.c.rotate(rotate)
        self.c.drawString(s_, dx, size * 0.35, f, skia.Paint(AntiAlias=True, Color=col(color, alpha)))
        self.c.restore()

    def image(self):
        img = self.surface.makeImageSnapshot()
        arr = img.toarray(colorType=skia.ColorType.kRGBA_8888_ColorType)
        from PIL import Image
        # Skia works premultiplied; PNG wants straight alpha
        a = arr[..., 3:4].astype(np.float32) / 255.0
        rgbv = np.where(a > 0, arr[..., :3] / np.maximum(a, 1e-6), 0)
        out = np.dstack([np.clip(rgbv, 0, 255), arr[..., 3]]).astype(np.uint8)
        return Image.fromarray(out, 'RGBA')


def jitter(points, amount, seed=1):
    """Wobble points a little so lines look hand-drawn."""
    rnd = random.Random(seed)
    return [(x + rnd.uniform(-amount, amount), y + rnd.uniform(-amount, amount)) for x, y in points]
