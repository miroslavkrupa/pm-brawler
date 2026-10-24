"""Hand-drawn cartoon characters (Deponia-like): lanky bodies, big noses and feet, inked outlines.

Poses come from the pixel-art generator (same frames, same timing) scaled to a 100-unit tall
figure: origin between the feet, y up, facing right. Everything is drawn in those units and
mapped to pixels by Figure.P.
"""
import math
import os
import sys
from dataclasses import dataclass, field, replace

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ArtGen'))
from characters import FRAMES, COMMITTEE_FRAMES, Pose, poses as pixel_poses, committee_poses  # noqa: E402

from ink import INK, Ink, ellipse, limb, mix, poly, rrect, shade, smooth, subtract, intersect, union, translated  # noqa: E402

PPU = 128
U = 100 / 58      # pixel-pose units -> figure units


def scaled_pose(p: Pose):
    f = lambda q: (q[0] * U, q[1] * U)
    return replace(p, hip=f(p.hip), sho=f(p.sho), head=f(p.head), fknee=f(p.fknee), ffoot=f(p.ffoot),
                   bknee=f(p.bknee), bfoot=f(p.bfoot), felb=f(p.felb), fhand=f(p.fhand), belb=f(p.belb),
                   bhand=f(p.bhand))


SKIN = {
    'light': '#f0bf98',
    'pale': '#f4d2b8',
    'tan': '#d39a6c',
    'dark': '#93603f',
}


@dataclass
class Spec:
    name: str
    height: float = 2.3            # world units, sole to top of the head
    skin: str = 'light'
    hair: str = '#6a4426'
    hair_style: str = 'messy'      # spiky / messy / slick / bald / hood / bun / curly
    shirt: str = '#f2efe6'
    sleeves: str = None
    rolled: bool = False           # rolled-up sleeves show the forearms
    jacket: str = None
    vest: str = None
    hoodie: bool = False
    pants: str = '#3b4a78'
    shoes: str = '#4a2c1e'
    sneakers: bool = False
    tie: str = None
    loose_tie: bool = False
    belly: float = 0.0
    width: float = 1.0
    eyes: str = 'normal'           # normal / glasses / shades
    stubble: bool = False
    beard: str = None
    mustache: str = None
    freckles: bool = False
    nose: float = 1.0
    chin: float = 1.0
    item: str = None               # clipboard / laptop / magnifier / phone / calculator
    hat: str = None                # crown / visor / headphones
    cigar: bool = False
    lanyard: str = None            # badge text
    pocket_pens: bool = False
    print_: str = None             # text/logo on a hoodie or t-shirt
    stain: bool = False
    watch: bool = False


class Figure:
    def __init__(self, spec: Spec, pose: Pose, cell=None, ink=None, origin=None):
        self.s = spec
        self.p = scaled_pose(pose)
        hpx = spec.height * PPU
        self.k = hpx / 100.0                       # px per figure unit
        if cell is None:
            cell = (int(104 * self.k), int(118 * self.k))
        self.cell = cell
        self.ink = ink or Ink(cell[0], cell[1], scale=hpx / 300.0)
        self.ox, self.oy = origin or (cell[0] * 0.5, cell[1] - 0.025 * cell[1] - 4)
        self.skin = SKIN.get(spec.skin, spec.skin)

    def P(self, x, y=None):
        if y is None:
            x, y = x
        return (self.ox + x * self.k, self.oy - y * self.k)

    def Ps(self, pts):
        return [self.P(q) for q in pts]

    def R(self, r):
        return r * self.k

    # ------------------------------------------------------------ limbs

    def leg(self, knee, foot, back):
        s, p, ink = self.s, self.p, self.ink
        hx = p.hip[0] + (-4 if back else 4) * s.width
        hip = (hx, p.hip[1] + 2)
        ankle = (foot[0] - 1, foot[1] + 5)
        pants = shade(s.pants, -0.18) if back else s.pants
        path = limb(self.Ps([hip, knee, ankle]), [self.R(7.2 * s.width ** 0.5), self.R(5.8), self.R(5.0)])
        ink.painted(path, pants)
        # trouser creases at the knee and the hem
        kx, ky = self.P(knee)
        ink.line([(kx - self.R(3), ky - self.R(1)), (kx + self.R(1), ky + self.R(2)), (kx + self.R(3.5), ky + self.R(1))],
                 width=1.6, alpha=170)
        self.shoe(foot, back)

    def shoe(self, foot, back):
        s, ink = self.s, self.ink
        fx, fy = foot
        color = s.shoes if not back else shade(s.shoes, -0.15)
        if s.sneakers:
            pts = [(fx - 6, fy + 6), (fx + 3, fy + 7), (fx + 11, fy + 4), (fx + 13.5, fy + 1.5), (fx + 12, fy - 0.5),
                   (fx - 6.5, fy - 0.5), (fx - 7.5, fy + 2)]
        else:
            pts = [(fx - 5.5, fy + 6.5), (fx + 2, fy + 6.5), (fx + 9, fy + 4.5), (fx + 13, fy + 2), (fx + 12.5, fy - 0.5),
                   (fx - 6, fy - 0.5), (fx - 7, fy + 2.5)]
        path = smooth(self.Ps(pts), tension=0.55)
        ink.cast_shadow(path, 2, 3, 60, 3)
        ink.painted(path, color, light=0.25)
        # sole
        sole = self.Ps([(fx - 6.5, fy + 1.4), (fx + 12.8, fy + 1.4)])
        ink.line(sole, color=mix(INK, color, 0.2), width=2.0)
        if s.sneakers:
            ink.line(self.Ps([(fx - 1, fy + 5), (fx + 4, fy + 5.5)]), width=1.4)
            ink.line(self.Ps([(fx + 0, fy + 3.6), (fx + 5, fy + 4.2)]), width=1.4)

    def arm(self, elb, hand, back):
        s, p, ink = self.s, self.p, self.ink
        sx = p.sho[0] + (-7 if back else 6) * s.width
        sho = (sx, p.sho[1] - 3)
        sleeve_col = s.sleeves or s.jacket or s.shirt
        if back:
            sleeve_col = shade(sleeve_col, -0.18)
        if s.rolled:
            # sleeve to just below the elbow, then bare forearm
            ex, ey = elb
            hx, hy = hand
            cuff = (ex + (hx - ex) * 0.25, ey + (hy - ey) * 0.25)
            fore = limb(self.Ps([cuff, hand]), [self.R(3.9), self.R(3.3)])
            ink.painted(fore, self.skin if not back else shade(self.skin, -0.15))
            up = limb(self.Ps([sho, elb, cuff]), [self.R(5.6), self.R(4.9), self.R(5.0)])
            ink.painted(up, sleeve_col)
            cx, cy = self.P(cuff)
            ink.stroke(ellipse(cx, cy, self.R(4.6), self.R(2.2)), width=2.2)
        else:
            path = limb(self.Ps([sho, elb, hand]), [self.R(5.8), self.R(5.0), self.R(4.2)])
            ink.painted(path, sleeve_col)
            if s.watch and not back:
                wx, wy = self.P((elb[0] + (hand[0] - elb[0]) * 0.8, elb[1] + (hand[1] - elb[1]) * 0.8))
                ink.painted(ellipse(wx, wy, self.R(3.2), self.R(2.0)), '#e8c048', width=2)
        self.hand(hand, back)

    def hand(self, hand, back):
        ink = self.ink
        hx, hy = self.P(hand)
        skin = self.skin if not back else shade(self.skin, -0.15)
        palm = ellipse(hx, hy, self.R(4.4), self.R(4.0))
        thumb = ellipse(hx + self.R(3.6), hy - self.R(2.2), self.R(1.9), self.R(1.5))
        ink.painted(union(palm, thumb), skin, light=0.15)
        ink.line([(hx - self.R(1.5), hy + self.R(1.2)), (hx + self.R(1.8), hy + self.R(1.6))], width=1.4, alpha=160)

    # ------------------------------------------------------------ body

    def torso(self):
        s, p, ink = self.s, self.p, self.ink
        hx, hy = p.hip
        sx, sy = p.sho
        sw, hw = 10.5 * s.width, 9.0 * s.width
        bel = s.belly * 9
        pts = [(sx - sw + 1, sy + 1), (sx + sw - 2, sy + 1.5), (sx + sw + 1 + bel * 0.3, sy - 6),
               (hx + hw + bel * 0.9, hy + 12), (hx + hw + bel * 0.5, hy + 3), (hx + hw - 1, hy - 1),
               (hx - hw, hy - 1), (hx - hw - 1, hy + 10), (sx - sw - 1.5, sy - 6)]
        body = smooth(self.Ps(pts), tension=0.45)
        self.body_path = body
        shirt = s.shirt
        ink.painted(body, shirt, light=0.2)

        # shirt details: placket, buttons, pocket, collar
        px0 = sx + 4 + bel * 0.25
        if not s.hoodie:
            ink.line(self.Ps([(px0, sy - 2), (px0 + 0.5 + bel * 0.2, hy + 6), (px0 + bel * 0.35, hy + 1)]), width=1.6, alpha=170)
            for i in range(4):
                t = (i + 1) / 5
                bx, by = self.P(px0 + 1.4 + bel * 0.3 * t, sy - 2 - (sy - hy - 4) * t)
                ink.fill(ellipse(bx, by, self.R(0.8), self.R(0.8)), shade(shirt, -0.4))
            if s.pocket_pens:
                pk = smooth(self.Ps([(sx - 4, sy - 6), (sx + 2, sy - 6), (sx + 1.7, sy - 13), (sx - 3.7, sy - 13)]), tension=0.2)
                for i, c in enumerate(['#2d5bd0', '#d03a2a', '#222222']):
                    pen = rrect(*self.P(sx - 3 + i * 1.8, sy - 2.5), *self.P(sx - 2.1 + i * 1.8, sy - 8), self.R(0.5))
                    ink.painted(pen, c, width=1.2, grain=False)
                ink.painted(pk, shade(shirt, -0.05), width=1.8)
            if s.stain:
                st = smooth(self.Ps([(px0 - 6, hy + 13), (px0 - 3, hy + 14), (px0 - 2, hy + 11), (px0 - 5, hy + 10)]))
                ink.fill(st, '#a0703c', 150)

        if s.hoodie:
            # kangaroo pocket, drawstrings, print
            pocket = smooth(self.Ps([(hx - 6, hy + 11), (hx + 7, hy + 11), (hx + 9, hy + 3), (hx - 7, hy + 3)]), tension=0.3)
            ink.painted(pocket, shade(shirt, -0.08), width=2)
            for dx in (1.5, 5.5):
                ink.line(self.Ps([(sx + dx, sy - 1), (sx + dx + 0.5, sy - 10)]), color='#e8e4dc', width=2.2)
            if s.print_:
                cx, cy = self.P(sx + 2, sy - 15)
                ink.text(s.print_, cx, cy, self.R(5.5), color='#9fe0b0', font='Bangers-Regular.ttf')

        if s.vest:
            vest = subtract(body, smooth(self.Ps([(px0 - 3, sy + 2), (px0 + 6, sy + 2), (px0 + 4 + bel * 0.4, hy + 4),
                                                  (px0 - 1, hy + 9)]), tension=0.3))
            vest = intersect(vest, smooth(self.Ps([(sx - sw - 4, sy - 4), (sx + sw + 6 + bel, sy - 4),
                                                   (hx + hw + bel + 4, hy - 3), (hx - hw - 4, hy - 3)]), tension=0.1))
            ink.painted(vest, s.vest)
            for i in range(3):
                bx, by = self.P(px0 + 3 + bel * 0.4, sy - 10 - i * 5)
                ink.fill(ellipse(bx, by, self.R(0.9), self.R(0.9)), '#d8c070')

        if s.jacket:
            opening = smooth(self.Ps([(sx + 0.5, sy + 2), (sx + sw + 3, sy + 2), (hx + hw + bel + 3, hy + 13),
                                      (hx + hw * 0.4 + bel * 0.7, hy - 2), (px0 + 0.5, hy + 10)]), tension=0.25)
            jacket = subtract(body, opening)
            ink.painted(jacket, s.jacket)
            # lapel
            lap = smooth(self.Ps([(sx + 0.5, sy + 1), (sx + 3.5, sy - 2), (px0 + 0.5, sy - 12), (sx + 1.5, sy - 9)]), tension=0.2)
            ink.painted(lap, shade(s.jacket, 0.08), width=2)
            # pocket square and buttons
            sqx, sqy = self.P(sx - 5, sy - 9)
            ink.painted(poly([(sqx, sqy), (sqx + self.R(4), sqy), (sqx + self.R(3), sqy - self.R(2.5)), (sqx + self.R(1), sqy - self.R(3))]),
                        s.tie or '#ffffff', width=1.4, grain=False)
            for i in range(2):
                bx, by = self.P(px0 - 0.5 + bel * 0.5, hy + 12 - i * 6)
                ink.fill(ellipse(bx, by, self.R(1.0), self.R(1.0)), shade(s.jacket, -0.45))

        if s.tie:
            tx = px0 + 0.5 + (2 if s.loose_tie else 0)
            ty = sy - (3 if s.loose_tie else 0)
            knot = smooth(self.Ps([(tx - 2, ty + 1), (tx + 2.2, ty + 1), (tx + 1.4, ty - 2.5), (tx - 1.2, ty - 2.5)]), tension=0.2)
            blade = smooth(self.Ps([(tx - 1.4, ty - 2.4), (tx + 1.6, ty - 2.4), (tx + 3.6 + bel * 0.35, ty - 19),
                                    (tx + 1.5 + bel * 0.35, ty - 23), (tx - 0.8 + bel * 0.3, ty - 19)]), tension=0.25)
            ink.painted(blade, s.tie, width=2.2)
            ink.painted(knot, shade(s.tie, -0.05), width=2.2)
            # diagonal stripes
            for i in range(3):
                y0 = ty - 7 - i * 4.5
                ink.line(self.Ps([(tx - 0.5 + bel * 0.1, y0 + 1), (tx + 2.8 + bel * 0.2, y0 - 1)]),
                         color=shade(s.tie, 0.35), width=1.4, alpha=190)

        if not s.hoodie:
            # collar
            cl = smooth(self.Ps([(sx - 3, sy + 2.5), (sx + 1, sy - 3), (sx + 2.5, sy + 1.5)]), tension=0.2)
            cr = smooth(self.Ps([(sx + 2.5, sy + 1.5), (sx + 7.5, sy - 3.5), (sx + 7, sy + 2.5)]), tension=0.2)
            ink.painted(cl, shade(s.shirt, 0.05), width=2)
            ink.painted(cr, shade(s.shirt, 0.05), width=2)

        if s.lanyard:
            a = self.P(sx - 1, sy + 1)
            b = self.P(sx + 8, sy + 1)
            badge_c = (sx + 4.5 + bel * 0.3, sy - 17)
            bc = self.P(badge_c)
            ink.line([a, (bc[0] - self.R(1), bc[1] - self.R(3))], color='#2d6bd0', width=2.4)
            ink.line([b, (bc[0] + self.R(1), bc[1] - self.R(3))], color='#2d6bd0', width=2.4)
            card = rrect(bc[0] - self.R(3.5), bc[1] - self.R(2.5), bc[0] + self.R(3.5), bc[1] + self.R(4.8), self.R(0.8))
            ink.painted(card, '#fbfbf6', width=1.8, grain=False)
            ink.fill(rrect(bc[0] - self.R(3.5), bc[1] - self.R(2.5), bc[0] + self.R(3.5), bc[1] - self.R(0.6), self.R(0.6)), '#2d6bd0')
            ink.text(s.lanyard, bc[0], bc[1] + self.R(1.8), self.R(3.2), font='Bangers-Regular.ttf')

        # belt
        belt = smooth(self.Ps([(hx - hw - 0.5, hy + 3.5), (hx + hw + bel * 0.5, hy + 3.5), (hx + hw + bel * 0.4, hy),
                               (hx - hw - 0.5, hy)]), tension=0.1)
        if not s.hoodie and not s.jacket:
            ink.painted(belt, '#3a2418', width=2)
            bx, by = self.P(px0 + bel * 0.4, hy + 1.8)
            ink.stroke(rrect(bx - self.R(1.6), by - self.R(1.5), bx + self.R(1.6), by + self.R(1.5), self.R(0.4)), '#d8b850', width=1.8)

    def neck(self):
        p, ink = self.p, self.ink
        a = (p.sho[0] + 2, p.sho[1] - 1)
        b = (p.head[0] - 1, p.head[1] - 8)
        ink.painted(limb(self.Ps([a, b]), [self.R(4.2), self.R(4.0)]), shade(self.skin, -0.12), width=2.4)

    # ------------------------------------------------------------ head

    def head(self):
        s, p, ink = self.s, self.p, self.ink
        hx, hy = p.head
        face = p.face
        P, R = self.P, self.R
        hair = s.hair

        # behind the head
        if s.hair_style == 'hood':
            hood = smooth(self.Ps([(hx - 14, hy - 4), (hx - 12, hy + 9), (hx - 2, hy + 15), (hx + 9, hy + 12), (hx + 11, hy + 2),
                                   (hx + 6, hy - 10), (hx - 6, hy - 14)]), tension=0.55)
            ink.painted(hood, s.shirt)
        if s.hair_style == 'bun':
            ink.painted(ellipse(*P(hx - 9, hy + 9), R(5), R(4.6)), hair)
        if s.hat == 'headphones':
            pass

        # skull, jaw and chin as one shape, slightly egg-shaped and leaning forward
        ch = s.chin
        skull = smooth(self.Ps([(hx - 9.5, hy + 3), (hx - 7, hy + 10.5), (hx + 1, hy + 12.5), (hx + 8, hy + 9), (hx + 10, hy + 2),
                                (hx + 10.5, hy - 5), (hx + 8 * ch, hy - 10 * ch), (hx + 2, hy - 12 * ch), (hx - 5, hy - 10),
                                (hx - 9, hy - 4)]), tension=0.6)
        ink.painted(skull, self.skin, light=0.2)
        self.skull = skull

        # stubble / beard
        if s.stubble or s.beard:
            jaw = smooth(self.Ps([(hx - 3, hy - 3), (hx + 10.5, hy - 4), (hx + 8 * ch, hy - 10.5 * ch), (hx + 1, hy - 12.5 * ch),
                                  (hx - 5, hy - 10), (hx - 6, hy - 5)]), tension=0.5)
            jaw = intersect(jaw, skull)
            if s.beard:
                ink.painted(jaw, s.beard, outline=False)
                ink.stroke(jaw, width=1.8)
            else:
                ink.fill(jaw, '#5a4038', 60)
                import random
                rnd = random.Random(hash(s.name) & 0xffff)
                b = jaw.computeTightBounds()
                for _ in range(70):
                    x, y = rnd.uniform(b.left(), b.right()), rnd.uniform(b.top(), b.bottom())
                    if jaw.contains(x, y):
                        ink.fill(ellipse(x, y, R(0.35), R(0.35)), '#3a2820', 160)

        # ear
        ex, ey = P(hx - 3.5, hy + 0.5)
        ear = ellipse(ex, ey, R(2.8), R(3.8))
        ink.painted(ear, shade(self.skin, -0.05), width=2.2)
        ink.line([(ex + R(0.6), ey - R(2)), (ex - R(0.8), ey), (ex + R(0.4), ey + R(1.8))], width=1.5, alpha=180)

        # far eye (3/4 view): small, peeking past the nose
        # near eye: big, droopy lids
        eyx, eyy = P(hx + 4.5, hy + 2.2)
        far_x, far_y = P(hx + 10.2, hy + 2.6)
        white = '#fbf8f0'
        if face == 'blink':
            ink.line([(eyx - R(3), eyy), (eyx + R(3), eyy + R(0.4))], width=2.4)
        elif face == 'hurt':
            for d in (-1, 1):
                ink.line([(eyx - R(2.2), eyy - R(2.2) * d), (eyx + R(2.2), eyy + R(2.2) * d)], width=2.4)
        else:
            ry = 3.8 if face == 'shout' else 3.4
            eye = ellipse(eyx, eyy, R(3.0), R(ry))
            ink.fill(eye, white)
            px_ = eyx + R(1.2)
            ink.fill(ellipse(px_, eyy + R(0.4), R(1.25), R(1.5)), '#2a1a14')
            ink.fill(ellipse(px_ - R(0.4), eyy - R(0.2), R(0.4), R(0.4)), '#ffffff')
            # heavy upper lid
            lid = smooth([(eyx - R(3.3), eyy - R(0.2)), (eyx, eyy - R(ry + 0.4)), (eyx + R(3.3), eyy - R(0.8)),
                          (eyx + R(3.2), eyy - R(1.6)), (eyx, eyy - R(ry - 1.2)), (eyx - R(3.1), eyy - R(1.0))], tension=0.5)
            if face not in ('shout',):
                ink.fill(lid, shade(self.skin, -0.12))
            ink.stroke(eye, width=2.0)
            # far eye
            if face != 'blink':
                fe = ellipse(far_x, far_y, R(1.6), R(2.8))
                ink.fill(fe, white)
                ink.fill(ellipse(far_x + R(0.5), far_y + R(0.4), R(0.8), R(1.1)), '#2a1a14')
                ink.stroke(fe, width=1.6)

        # eyebrows
        bcol = shade(hair, -0.25) if s.hair_style != 'bald' else '#6a6a6a'
        tilt = {'shout': -2.0, 'grin': -1.2, 'hurt': 1.8}.get(face, 0.0)
        ink.line([(eyx - R(3.6), eyy - R(5.2) + R(tilt * 0.4)), (eyx, eyy - R(6.2)), (eyx + R(3.4), eyy - R(5.4) - R(tilt))],
                 color=bcol, width=3.4)
        ink.line([(far_x - R(1.2), far_y - R(4.3)), (far_x + R(1.4), far_y - R(4.6) - R(tilt * 0.5))], color=bcol, width=2.6)

        # nose: long, droopy, with a bulb
        nk = s.nose
        nose = smooth(self.Ps([(hx + 6.5, hy + 3.5), (hx + 10 + 3 * nk, hy - 0.5), (hx + 12 + 4.5 * nk, hy - 4.5 * nk),
                               (hx + 10 + 3 * nk, hy - 7 * nk), (hx + 6.5, hy - 6), (hx + 5.8, hy - 2)]), tension=0.6)
        ink.painted(nose, shade(self.skin, 0.02), light=0.25)
        nx, ny = P(hx + 8.5 + 2 * nk, hy - 5.3 * nk)
        ink.line([(nx - R(1), ny), (nx + R(0.6), ny + R(0.6))], width=1.6, alpha=200)
        # cheek blush
        ink.fill(ellipse(*P(hx + 1.5, hy - 4), R(3), R(2)), '#e07a6a', 50)

        # mouth
        mx, my = P(hx + 6.2, hy - 8.4 * s.chin)
        if face in ('shout', 'hurt'):
            mouth = smooth([(mx - R(3.2), my - R(0.8)), (mx + R(2.5), my - R(1.2)), (mx + R(2), my + R(3)), (mx - R(2.5), my + R(2.4))],
                           tension=0.6)
            ink.fill(mouth, '#5a1a1e')
            ink.fill(intersect(mouth, ellipse(mx, my + R(2.8), R(2.2), R(1.2))), '#c85060')
            ink.fill(intersect(mouth, rrect(mx - R(2.8), my - R(1.6), mx + R(2.4), my - R(0.2), R(0.3))), '#fbf8f0')
            ink.stroke(mouth, width=2.0)
        elif face == 'grin':
            ink.line([(mx - R(3.5), my - R(0.8)), (mx - R(0.5), my + R(1.2)), (mx + R(2.6), my - R(0.4))], width=2.4)
            ink.fill(smooth([(mx - R(2.4), my + R(0.1)), (mx + R(1.8), my - R(0.1)), (mx - R(0.4), my + R(1.0))]), '#fbf8f0')
        else:
            ink.line([(mx - R(3), my - R(0.3)), (mx, my + R(0.4)), (mx + R(2.2), my - R(0.5))], width=2.2)

        if s.mustache:
            m = smooth(self.Ps([(hx + 2.5, hy - 6.8), (hx + 6, hy - 5.6), (hx + 10.5, hy - 6.5), (hx + 11, hy - 8.6),
                                (hx + 7, hy - 7.6), (hx + 3, hy - 8.8)]), tension=0.5)
            ink.painted(m, s.mustache, width=2)
        if s.freckles:
            for dx, dy in ((0, -2.5), (1.8, -3.4), (-1, -4), (2.6, -1.8), (0.8, -5)):
                ink.fill(ellipse(*P(hx + 1 + dx, hy + dy), R(0.45), R(0.45)), '#b06a40', 200)

        # glasses
        if s.eyes == 'glasses':
            fr = '#3a2a24'
            ink.stroke(rrect(eyx - R(4), eyy - R(3.8), eyx + R(4), eyy + R(3.6), R(1.5)), fr, width=2.4)
            ink.stroke(rrect(far_x - R(2), far_y - R(3.4), far_x + R(2), far_y + R(3.2), R(1)), fr, width=2.0)
            ink.line([(eyx + R(4), eyy - R(0.5)), (far_x - R(2), far_y - R(0.5))], color=fr, width=2.0)
            ink.line([(eyx - R(4), eyy - R(1)), (ex + R(2), ey - R(0.8))], color=fr, width=2.0)
            ink.fill(rrect(eyx - R(3.6), eyy - R(3.4), eyx + R(3.6), eyy + R(3.2), R(1.3)), '#cfe8ff', 50)
        elif s.eyes == 'shades':
            g = smooth([(eyx - R(4.4), eyy - R(3)), (eyx + R(4.2), eyy - R(3)), (eyx + R(3.6), eyy + R(2.6)), (eyx - R(3.6), eyy + R(2.2))], tension=0.35)
            ink.painted(g, '#1c1c28', width=2.2, light=0.3)
            g2 = smooth([(far_x - R(2), far_y - R(2.8)), (far_x + R(2.2), far_y - R(2.8)), (far_x + R(1.8), far_y + R(2.2)),
                         (far_x - R(1.8), far_y + R(2))], tension=0.35)
            ink.painted(g2, '#1c1c28', width=1.8)
            ink.line([(eyx + R(4), eyy - R(1.8)), (far_x - R(2), far_y - R(1.8))], width=2.2)
            ink.line([(eyx - R(4.2), eyy - R(1.8)), (ex + R(2), ey - R(0.8))], width=2.2)
            ink.line([(eyx - R(2.5), eyy - R(1.6)), (eyx - R(0.6), eyy - R(2.2))], color='#9ab0e0', width=1.6)

        # hair on top
        st = s.hair_style
        if st == 'spiky':
            pts = [(hx - 10, hy - 1), (hx - 12, hy + 5), (hx - 9, hy + 8), (hx - 13, hy + 12), (hx - 6, hy + 12.5), (hx - 7, hy + 17),
                   (hx - 1, hy + 14), (hx + 1, hy + 19), (hx + 5, hy + 14.5), (hx + 10, hy + 17), (hx + 10, hy + 12),
                   (hx + 14.5, hy + 11), (hx + 10.5, hy + 7.5), (hx + 6, hy + 9.5), (hx + 1, hy + 8.5), (hx - 4, hy + 6),
                   (hx - 6.5, hy + 1)]
            hp = smooth(self.Ps(pts), tension=0.35)
            ink.painted(hp, hair, light=0.3)
            for a, b in (((hx - 4, hy + 11), (hx - 1, hy + 9)), ((hx + 3, hy + 13), (hx + 5, hy + 10.5))):
                ink.line(self.Ps([a, b]), width=1.6, alpha=170)
        elif st == 'messy':
            pts = [(hx - 9.5, hy - 2), (hx - 11.5, hy + 5), (hx - 9.5, hy + 11), (hx - 3, hy + 15), (hx + 4, hy + 15), (hx + 10, hy + 12.5),
                   (hx + 12, hy + 8), (hx + 8, hy + 8.5), (hx + 6, hy + 6.5), (hx + 2, hy + 8), (hx - 2, hy + 6), (hx - 6, hy + 5),
                   (hx - 6.5, hy)]
            ink.painted(smooth(self.Ps(pts), tension=0.5), hair, light=0.28)
            for a, b in (((hx - 6, hy + 12), (hx - 2, hy + 10)), ((hx + 1, hy + 13.5), (hx + 4, hy + 11)), ((hx + 7, hy + 12), (hx + 9, hy + 9.5))):
                ink.line(self.Ps([a, b]), width=1.6, alpha=170)
        elif st == 'curly':
            hp = None
            for cx, cy, r in ((-9, 4, 4.2), (-8, 9.5, 4.2), (-3, 13, 4.4), (3, 13.5, 4.2), (8.5, 11.5, 4), (11, 7, 3.2), (-10.5, -1, 3.2)):
                e = ellipse(*P(hx + cx, hy + cy), R(r), R(r))
                hp = e if hp is None else union(hp, e)
            hp = subtract(hp, ellipse(*P(hx + 5, hy + 3), R(5.5), R(4)))
            ink.painted(hp, hair, light=0.3)
        elif st == 'slick':
            pts = [(hx - 9.5, hy - 1), (hx - 11, hy + 6), (hx - 7, hy + 12), (hx + 1, hy + 14), (hx + 8, hy + 12.5), (hx + 12, hy + 9),
                   (hx + 9, hy + 7.8), (hx + 2, hy + 8.5), (hx - 4, hy + 6.5), (hx - 6.5, hy + 1)]
            ink.painted(smooth(self.Ps(pts), tension=0.5), hair, light=0.4)
            for i in range(3):
                ink.line(self.Ps([(hx - 7 + i * 3, hy + 9 + i * 0.6), (hx - 1 + i * 3.5, hy + 12.2 - i * 0.3)]),
                         color=shade(hair, 0.4), width=1.6, alpha=200)
        elif st == 'bald':
            side = smooth(self.Ps([(hx - 9.5, hy - 2), (hx - 10.5, hy + 4), (hx - 8, hy + 7), (hx - 5.5, hy + 4), (hx - 6.5, hy - 1)]), tension=0.5)
            ink.painted(side, hair)
            # comb-over strands
            for i in range(3):
                ink.line(self.Ps([(hx - 8, hy + 7.5 + i), (hx - 1, hy + 11.8 + i * 0.3), (hx + 6, hy + 10.5 + i * 0.4)]),
                         color=hair, width=1.8)
            ink.fill(ellipse(*P(hx - 1, hy + 9.5), R(2.4), R(1.2)), '#ffffff', 120)
        elif st == 'bun':
            pts = [(hx - 9.5, hy - 2), (hx - 11, hy + 6), (hx - 6, hy + 12.5), (hx + 2, hy + 13.5), (hx + 9, hy + 11), (hx + 11.5, hy + 6),
                   (hx + 6, hy + 7.5), (hx, hy + 8.5), (hx - 5, hy + 5.5), (hx - 6.5, hy)]
            ink.painted(smooth(self.Ps(pts), tension=0.5), hair, light=0.3)
        elif st == 'hood':
            rim = smooth(self.Ps([(hx - 12, hy - 6), (hx - 11, hy + 8), (hx - 2, hy + 14.5), (hx + 8, hy + 12), (hx + 10.5, hy + 4),
                                  (hx + 7, hy + 9), (hx - 1, hy + 10.5), (hx - 7, hy + 6), (hx - 8, hy - 5)]), tension=0.5)
            ink.painted(rim, s.shirt)
            fringe = smooth(self.Ps([(hx - 3, hy + 10), (hx + 7, hy + 9.5), (hx + 9.5, hy + 5.5), (hx + 4, hy + 7), (hx - 1, hy + 6.5)]), tension=0.5)
            ink.painted(fringe, hair)

        # head-wear
        if s.hat == 'crown':
            cr = poly(self.Ps([(hx - 7, hy + 11), (hx + 8, hy + 11.5), (hx + 9.5, hy + 20), (hx + 5, hy + 15.5), (hx + 1.5, hy + 21.5),
                               (hx - 2, hy + 15.5), (hx - 7.5, hy + 19.5)]))
            ink.painted(cr, '#f0c030', light=0.35)
            for (cx, cy, c) in ((1.5, 13.5, '#d02a3a'), (-4, 13.2, '#2a6ad0'), (6, 13.7, '#2aa05a')):
                ink.painted(ellipse(*P(hx + cx, hy + cy), R(1.3), R(1.3)), c, width=1.4, grain=False)
        elif s.hat == 'visor':
            band = smooth(self.Ps([(hx - 10, hy + 6), (hx + 8, hy + 7.5), (hx + 8, hy + 5.5), (hx - 10, hy + 3.8)]), tension=0.2)
            brim = smooth(self.Ps([(hx + 4, hy + 7.4), (hx + 17, hy + 5.5), (hx + 16, hy + 3.2), (hx + 5, hy + 4.6)]), tension=0.4)
            ink.painted(band, '#2f8a5a', width=2)
            ink.painted(brim, '#4fc08a', width=2)
            ink.fill(brim, '#80ffb0', 40)
        elif s.hat == 'headphones':
            pass

        if s.cigar:
            cx, cy = P(hx + 7, hy - 8.8)
            cg = limb([(cx, cy), (cx + R(9), cy + R(1.5))], [R(1.3), R(1.2)])
            ink.painted(cg, '#7a4422', width=1.8)
            ink.fill(ellipse(cx + R(9.6), cy + R(1.6), R(1.2), R(1.1)), '#ff8a30')
            for i in range(3):
                ink.stroke(ellipse(cx + R(11 + i * 1.5), cy - R(2 + i * 3), R(1.5 + i), R(1 + i * 0.6)), '#c8c0c0', width=1.4, alpha=150 - i * 40)

    # ------------------------------------------------------------ props

    def item(self):
        s, p, ink = self.s, self.p, self.ink
        if not s.item:
            return
        hx, hy = self.P(p.fhand)
        a = math.radians(p.item_angle)
        R = self.R

        def rot(dx, dy):
            return (hx + (dx * math.cos(a) - dy * math.sin(a)) * self.k, hy + (dx * math.sin(a) + dy * math.cos(a)) * self.k)

        def quad(x0, y0, x1, y1):
            return poly([rot(x0, y0), rot(x1, y0), rot(x1, y1), rot(x0, y1)])

        if s.item == 'clipboard':
            board = quad(-2, -19, 14, 3)
            ink.cast_shadow(board, 3, 3, 70, 3)
            ink.painted(board, '#b07a40', width=2.4)
            paper = quad(0, -16, 12, 1)
            ink.painted(paper, '#fbf7ea', width=1.6, shadow=False)
            for i in range(4):
                y = -13 + i * 3.2
                ink.line([rot(2.5, y), rot(3.5, y + 1), rot(5, y - 1)], color='#2aa05a' if i < 2 else '#c03030', width=1.6)
                ink.line([rot(6, y), rot(10.5, y)], color='#7a8ab0', width=1.3)
            ink.c.save()
            cx, cy = rot(7, -4)
            ink.c.translate(cx, cy)
            ink.c.rotate(p.item_angle - 14)
            ink.stroke(rrect(-R(5), -R(2), R(5), R(2), R(0.6)), '#d02a2a', width=1.8, alpha=200)
            ink.text('LATE', 0, 0, R(3.2), color='#d02a2a', font='Bangers-Regular.ttf', alpha=210)
            ink.c.restore()
            ink.painted(quad(3, -21, 9, -17), '#c8ccd4', width=1.8, light=0.4)
        elif s.item == 'laptop':
            lid = quad(-3, -17, 15, 0)
            ink.cast_shadow(lid, 3, 3, 70, 3)
            ink.painted(lid, '#5c6474', width=2.4)
            scr = quad(-1, -15, 13, -2)
            ink.fill(scr, '#14202e')
            colors = ['#7fd8a0', '#ffd070', '#7fb8ff', '#ff8a8a', '#7fd8a0']
            for i, (x0, x1) in enumerate([(1, 7), (2, 10), (2, 6), (1, 9), (3, 8)]):
                ink.line([rot(x0, -13 + i * 2.2), rot(x1, -13 + i * 2.2)], color=colors[i], width=1.5)
            # stickers on the back are hidden; one on the bezel
            ink.painted(ellipse(*rot(11.5, -1), R(1.3), R(1.3)), '#ff5a8a', width=1, grain=False)
            ink.painted(quad(-2, 0, 17, 2.8), '#a4acba', width=2.2)
        elif s.item == 'magnifier':
            ink.painted(limb([rot(-1, 3), rot(5, -7)], [R(1.6), R(1.4)]), '#6a3c1e', width=2)
            cx, cy = rot(9, -12)
            ring = ellipse(cx, cy, R(6.5), R(6.5))
            ink.fill(ellipse(cx, cy, R(5.2), R(5.2)), '#cfeaff', 140)
            ink.c.save()
            ink.c.clipPath(ellipse(cx, cy, R(5.2), R(5.2)), skia_op(), True)
            ink.fill(ellipse(cx + R(1.2), cy + R(1), R(2.5), R(1.6)), '#d03030', 200)   # a bug, magnified
            ink.line([(cx - R(1), cy), (cx + R(3.5), cy + R(2))], width=1.4)
            ink.c.restore()
            ink.stroke(ring, '#c9a227', width=4)
            ink.stroke(ring, INK, width=1.4)
            ink.line([(cx - R(3), cy - R(2.5)), (cx - R(1), cy - R(4))], color='#ffffff', width=2)
        elif s.item == 'phone':
            ph = quad(-2, -11, 5, 1)
            ink.painted(ph, '#26262e', width=2.2)
            scr = quad(-1, -10, 4, -1)
            ink.fill(scr, '#5ab8f0')
            ink.line([rot(0, -8), rot(3, -8)], color='#ffffff', width=1.2)
            ink.line([rot(0, -6), rot(2.5, -6)], color='#ffffff', width=1.2)
        elif s.item == 'calculator':
            cal = quad(-2, -13, 9, 2)
            ink.painted(cal, '#dcd4bc', width=2.2)
            ink.fill(quad(-0.5, -11.5, 7.5, -7.5), '#9cc48a')
            ink.text('-99.9', *rot(3.5, -9.4), R(2.6), color='#2a3a20')
            for kx in range(3):
                for ky in range(3):
                    ink.fill(rrect(*rot(0 + kx * 2.6, -5.5 + ky * 2.4), *rot(1.8 + kx * 2.6, -4 + ky * 2.4), R(0.3)), '#7a6a5a')
            # paper tape spilling out
            ink.painted(smooth([rot(1, -13), rot(3, -18), rot(0, -22), rot(4, -26), rot(6, -24), rot(4, -19), rot(5, -13)]),
                        '#fbf7ea', width=1.4, shadow=False)

    # ------------------------------------------------------------ assemble

    def draw(self):
        p = self.p
        self.arm(p.belb, p.bhand, back=True)
        self.leg(p.bknee, p.bfoot, back=True)
        self.leg(p.fknee, p.ffoot, back=False)
        self.torso()
        self.neck()
        self.head()
        self.arm(p.felb, p.fhand, back=False)
        self.item()
        return self.ink


def skia_op():
    import skia
    return skia.ClipOp.kIntersect


CAST = {
    'pm': Spec('pm', height=2.35, hair='#d8a848', hair_style='spiky', shirt='#f4f1e8', rolled=True, pants='#34477a',
               shoes='#5a3420', tie='#c8302a', loose_tie=True, stubble=True, item='clipboard', lanyard='PM',
               pocket_pens=True, stain=True, nose=1.0),
    'developer': Spec('developer', height=2.3, skin='pale', hair='#3a2a20', hair_style='hood', shirt='#3d5a80', hoodie=True,
                      pants='#2c3550', shoes='#e8e6de', sneakers=True, beard='#4a3220', item='laptop', print_='</>',
                      nose=1.1),
    'tester': Spec('tester', height=2.2, hair='#c4552a', hair_style='curly', shirt='#4fae7e', pants='#a89468',
                   shoes='#5a3a22', eyes='glasses', width=0.9, item='magnifier', freckles=True, lanyard='QA', nose=0.9),
    'stakeholder': Spec('stakeholder', height=2.4, skin='tan', hair='#2a1a14', hair_style='slick', shirt='#f0e6c8',
                        jacket='#7b3fa8', pants='#4a2470', shoes='#1e1418', tie='#f2c618', width=1.1, nose=1.25,
                        chin=1.15, item='phone', watch=True),
    'cfo': Spec('cfo', height=2.3, hair='#9a9a9a', hair_style='bald', shirt='#eef0f2', vest='#4a5260', pants='#2a2e34',
                shoes='#1e1418', tie='#d8b030', belly=0.6, eyes='glasses', mustache='#a8a8a8', hat='visor',
                item='calculator', nose=1.2, pocket_pens=True),
    'ceo': Spec('ceo', height=2.95, skin='tan', hair='#d4d4d8', hair_style='slick', shirt='#f6f6f6', jacket='#1b2a4e',
                pants='#141a2c', shoes='#0e0a0c', tie='#f0a020', belly=1.0, width=1.25, eyes='shades', hat='crown',
                cigar=True, nose=1.35, chin=1.2, watch=True),
}

COMMITTEE = [
    Spec('chair', height=2.25, skin='pale', hair='#7a3a2a', hair_style='bun', shirt='#f2e6e0', jacket='#8a2232', nose=0.9),
    Spec('member_l', height=2.2, hair='#8a8a92', hair_style='bald', shirt='#e8ecf0', jacket='#56606e', tie='#c1121f',
         mustache='#9a9aa0', eyes='glasses', nose=1.2),
    Spec('member_r', height=2.2, skin='dark', hair='#1a1414', hair_style='curly', shirt='#f4f4f4', jacket='#3e4a3a',
         tie='#2a7ab8', beard='#1a1414'),
]


def sheet(spec: Spec):
    ps = pixel_poses()
    imgs = [Figure(spec, ps[name]).draw().image() for name in FRAMES]
    return imgs, Figure(spec, ps['idle0']).cell


def committee_sheet():
    """Three members behind one long table; 4.4 x 3.3 world units per cell, feet at the bottom."""
    from ink import Ink, rrect as rr
    W, H = int(4.4 * PPU), int(3.3 * PPU)
    ps = committee_poses()
    frames = []
    for name in COMMITTEE_FRAMES:
        ink = Ink(W, H, scale=2.2 * PPU / 300.0)
        lift = 6 if name == 'atk1' else 0
        floor = H - 6
        for spec, x in ((COMMITTEE[1], 0.2), (COMMITTEE[2], 0.8), (COMMITTEE[0], 0.5)):
            Figure(spec, ps[name], cell=(W, H), ink=ink, origin=(W * x, floor - 0.42 * PPU)).draw()
        top = H - 1.25 * PPU + lift
        k = PPU / 100.0
        # table top, front panel, legs, papers, water jug, gavel, name plate
        ink.cast_shadow(rr(10, top, W - 10, floor, 8), 0, 8, 80, 8)
        legs = [rr(24, top + 60, 46, floor, 4), rr(W - 46, top + 60, W - 24, floor, 4)]
        for l in legs:
            ink.painted(l, '#5a301a')
        front = rr(14, top + 16, W - 14, top + 66 * k * 1.1, 6)
        ink.painted(front, '#6e3c1e', light=0.2)
        for i in range(3):
            x0 = 34 + i * (W - 68) / 3
            ink.painted(rr(x0, top + 26, x0 + (W - 68) / 3 - 18, top + 60 * k * 1.05, 4), '#7e4826', width=2)
        ink.painted(rr(4, top, W - 4, top + 18, 6), '#a0623a', light=0.3)
        plate = rr(W / 2 - 70, top + 30, W / 2 + 70, top + 52, 4)
        ink.painted(plate, '#e0b848', light=0.35, width=2)
        ink.text('STEERING COMMITTEE', W / 2, top + 41, 13, font='Bangers-Regular.ttf')
        ink.painted(rr(110, top - 6 - lift, 168, top + 2, 2), '#fbf7ea', width=1.8, shadow=False)
        ink.painted(rr(320, top - 9 - lift * 2, 372, top + 1, 2), '#fbf7ea', width=1.8, shadow=False)
        ink.text('Q3 RISKS', 346, top - 4 - lift * 2, 8, color='#c03030', font='Bangers-Regular.ttf')
        from ink import ellipse as el
        ink.painted(el(225, top - 16, 11, 16), '#cde8f4', light=0.4, width=2)
        ink.painted(rr(410, top - 10 - lift * 2, 448, top - 2 - lift * 2, 3), '#7a4422', width=2)
        frames.append(ink.image())
    return frames, (W, H)
