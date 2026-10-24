"""Character sprite sheets: a posable 3/4-view figure with adventure-game proportions
(big head, big nose, expressive eyes), dressed per character.

Coordinates inside a pose are in pixels with the origin between the feet and y pointing up;
the figure faces right (Unity flips it for facing left).
"""
from dataclasses import dataclass, field, replace

from pixel import Ramp, Sprite, blank, capsule, ellipse, polygon, rect, line, hex2rgb, shift

SKINS = {
    # hand-picked ramps: generated ones go muddy or pink on skin
    'light': Ramp('#f2be90', hi='#ffdcb4', mid='#dc9e70', sh='#b8764e', out='#6c3a26'),
    'pale': Ramp('#f6d0b0', hi='#fff0dc', mid='#e2ae8c', sh='#c08466', out='#704436'),
    'tan': Ramp('#d89a66', hi='#f0bc88', mid='#c08050', sh='#9a5e3a', out='#5a3220'),
    'dark': Ramp('#9a6240', hi='#b87c54', mid='#844e32', sh='#683a24', out='#38200f'),
}

FRAMES = ['idle0', 'idle1', 'walk0', 'walk1', 'walk2', 'walk3', 'jump', 'fall', 'atk0', 'atk1', 'hurt']


@dataclass
class Pose:
    hip: tuple = (0, 25)
    sho: tuple = (0, 41)
    head: tuple = (1, 50)
    fknee: tuple = (1, 13)
    ffoot: tuple = (2, 1)
    bknee: tuple = (-2, 13)
    bfoot: tuple = (-3, 1)
    felb: tuple = (3, 32)
    fhand: tuple = (5, 25)
    belb: tuple = (-3, 32)
    bhand: tuple = (-3, 25)
    item_angle: float = 0.0
    face: str = 'normal'   # normal / blink / shout / hurt / grin


def poses():
    """The shared animation, authored for a 58 px tall figure."""
    base = Pose()
    p = {}
    p['idle0'] = base
    p['idle1'] = replace(base, sho=(0, 40), head=(1, 49), felb=(3, 31), fhand=(5, 24), belb=(-3, 31), bhand=(-3, 24))
    p['walk0'] = replace(base, ffoot=(8, 1), fknee=(5, 12), bfoot=(-7, 2), bknee=(-3, 12),
                         felb=(0, 32), fhand=(-3, 26), belb=(2, 32), bhand=(6, 26), hip=(0, 24), sho=(1, 40), head=(2, 49))
    p['walk1'] = replace(base, ffoot=(1, 5), fknee=(4, 14), bfoot=(-1, 1), bknee=(1, 13),
                         felb=(2, 32), fhand=(3, 25), belb=(-1, 32), bhand=(-1, 25), hip=(0, 25), sho=(1, 41), head=(2, 50))
    p['walk2'] = replace(base, ffoot=(-7, 2), fknee=(-3, 12), bfoot=(8, 1), bknee=(5, 12),
                         felb=(3, 32), fhand=(7, 26), belb=(-3, 32), bhand=(-5, 27), hip=(0, 24), sho=(1, 40), head=(2, 49))
    p['walk3'] = replace(base, ffoot=(-1, 1), fknee=(1, 13), bfoot=(1, 5), bknee=(4, 14),
                         felb=(2, 32), fhand=(2, 25), belb=(-2, 32), bhand=(-2, 25), hip=(0, 25), sho=(1, 41), head=(2, 50))
    p['jump'] = replace(base, hip=(0, 26), sho=(1, 42), head=(2, 51), fknee=(6, 19), ffoot=(3, 9), bknee=(0, 17),
                        bfoot=(-5, 9), felb=(6, 40), fhand=(8, 47), belb=(-5, 40), bhand=(-7, 46), face='shout')
    p['fall'] = replace(base, fknee=(3, 12), ffoot=(4, 1), bknee=(-3, 13), bfoot=(-6, 3),
                        felb=(7, 36), fhand=(11, 40), belb=(-6, 36), bhand=(-10, 40))
    p['atk0'] = replace(base, sho=(-2, 41), head=(-1, 50), hip=(-1, 25), fknee=(2, 13), ffoot=(5, 1),
                        bknee=(-3, 13), bfoot=(-5, 1), felb=(-5, 39), fhand=(-7, 46), belb=(2, 33), bhand=(5, 28),
                        item_angle=-40, face='grin')
    p['atk1'] = replace(base, sho=(3, 40), head=(5, 49), hip=(1, 24), fknee=(6, 12), ffoot=(10, 1),
                        bknee=(-3, 12), bfoot=(-7, 1), felb=(10, 37), fhand=(16, 36), belb=(-2, 33), bhand=(-5, 28),
                        item_angle=80, face='shout')
    p['hurt'] = replace(base, sho=(-4, 39), head=(-5, 47), hip=(-1, 24), fknee=(3, 12), ffoot=(5, 2),
                        bknee=(-3, 12), bfoot=(-6, 1), felb=(4, 38), fhand=(10, 43), belb=(-8, 41), bhand=(-11, 46),
                        face='hurt')
    return p


@dataclass
class Spec:
    name: str
    height: int = 58            # pixels from sole to top of head
    cell: tuple = (64, 72)
    skin: str = 'light'
    hair: str = '#7a4a24'
    hair_style: str = 'short'   # guybrush / short / messy / slick / bald / hood / bun
    shirt: str = '#f4f4ec'
    sleeves: str = None        # defaults to shirt
    jacket: str = None         # open jacket over the shirt
    pants: str = '#2f3e74'
    shoes: str = '#3a2418'
    tie: str = None
    belly: float = 0.0          # 0..1 pushes the torso out in front
    width: float = 1.0          # torso width multiplier
    eyes: str = 'normal'        # normal / glasses / shades / visor
    beard: str = None
    mustache: bool = False
    nose: float = 1.0
    item: str = None            # clipboard / laptop / magnifier / phone / calculator / cigar_hand
    hat: str = None             # crown / headphones / visor
    cigar: bool = False
    extras: list = field(default_factory=list)


# ---------------------------------------------------------------- drawing


class Figure:
    def __init__(self, spec: Spec, pose: Pose):
        self.s = spec
        self.p = pose
        self.k = spec.height / 58.0
        w, h = spec.cell
        self.sp = Sprite(w, h)
        self.ox = w / 2 - 1
        self.oy = h - 3   # soles 2px above the bottom so the outline fits
        self.r = {
            'skin': SKINS[spec.skin],
            'hair': Ramp(spec.hair),
            'shirt': Ramp(spec.shirt),
            'sleeve': Ramp(spec.sleeves or spec.jacket or spec.shirt),
            'jacket': Ramp(spec.jacket) if spec.jacket else None,
            'pants': Ramp(spec.pants),
            'shoes': Ramp(spec.shoes),
            'tie': Ramp(spec.tie) if spec.tie else None,
        }

    def P(self, pt):
        """Pose space -> image space."""
        return (self.ox + pt[0] * self.k, self.oy - pt[1] * self.k)

    def m(self):
        return blank(self.sp.w, self.sp.h)

    # --- limbs

    def leg(self, knee, foot, back):
        s, r, k = self.s, self.r, self.k
        hip = self.P((self.p.hip[0] + (-2 if back else 2) * s.width, self.p.hip[1]))
        kn, ft = self.P(knee), self.P(foot)
        pants = r['pants'] if not back else Ramp(r['pants'].mid)
        mk = capsule(self.m(), hip, kn, 3.4 * k * s.width ** 0.5, 3.0 * k)
        capsule(mk, kn, (ft[0], ft[1] - 2.5 * k), 3.0 * k, 2.6 * k)
        self.sp.part(mk, pants)
        # shoe: a rounded wedge pointing forward
        sm = self.m()
        fx, fy = ft
        ellipse(sm, fx + 2.0 * k, fy - 1.0 * k, 4.6 * k, 2.4 * k)
        rect(sm, fx - 2.5 * k, fy - 1 * k, fx + 6 * k, fy + 0.4 * k)
        shoes = r['shoes'] if not back else Ramp(r['shoes'].mid)
        self.sp.part(sm, shoes, band=1)

    def arm(self, elb, hand, back):
        s, r, k = self.s, self.r, self.k
        p = self.p
        sx = p.sho[0] + (-4.5 if back else 3.5) * s.width
        sho = self.P((sx, p.sho[1] - 2))
        el, hd = self.P(elb), self.P(hand)
        sleeve = r['sleeve'] if not back else Ramp(r['sleeve'].mid)
        mk = capsule(self.m(), sho, el, 3.0 * k, 2.6 * k)
        capsule(mk, el, hd, 2.6 * k, 2.2 * k)
        self.sp.part(mk, sleeve)
        # cuff + hand
        hm = ellipse(self.m(), hd[0], hd[1], 2.3 * k, 2.3 * k)
        skin = r['skin'] if not back else Ramp(r['skin'].mid)
        self.sp.part(hm, skin, band=1)

    # --- body

    def torso(self):
        s, r, k, p = self.s, self.r, self.k, self.p
        hx, hy = p.hip
        sx, sy = p.sho
        hw, sw = 6.0 * s.width, 7.0 * s.width
        bel = s.belly * 6
        pts = [(sx - sw, sy), (sx + sw - 1, sy), (sx + sw + bel * 0.4, sy - 6),
               (hx + hw + bel, hy + 7), (hx + hw + bel * 0.6, hy + 2), (hx + hw, hy - 1),
               (hx - hw, hy - 1), (hx - hw - 0.5, hy + 6), (sx - sw - 0.5, sy - 4)]
        tm = polygon(self.m(), [self.P(q) for q in pts])
        # trousers waist
        wm = polygon(self.m(), [self.P(q) for q in [(hx - hw, hy + 2), (hx + hw + bel * 0.6, hy + 2),
                                                    (hx + hw, hy - 3), (hx - hw, hy - 3)]])
        self.sp.part(tm, r['shirt'], band=3)
        if s.jacket:
            # open jacket: the shirt shows as a wedge in front
            jm = tm.copy()
            front = polygon(self.m(), [self.P(q) for q in [(sx + 0.5, sy + 1), (sx + sw + 2, sy + 1),
                                                           (hx + hw + bel + 2, hy + 7), (hx + hw * 0.6 + bel, hy + 2)]])
            jm &= ~front
            self.sp.part(jm, r['jacket'], band=3, cast=False)
            # lapel line
            lm = self.m()
            line(lm, self.P((sx + 1, sy)), self.P((sx + 3 + bel * 0.4, sy - 9)))
            self.sp.pixels(lm & jm, r['jacket'].sh)
        if r['tie']:
            tx = sx + 3.0 + bel * 0.35
            tie = polygon(self.m(), [self.P(q) for q in [(tx - 1, sy), (tx + 1.5, sy), (tx + 2 + bel * 0.2, sy - 11),
                                                         (tx + 0.5 + bel * 0.25, sy - 14), (tx - 1.2 + bel * 0.2, sy - 11)]])
            self.sp.part(tie, r['tie'], band=1)
        cm = polygon(self.m(), [self.P(q) for q in [(sx - 2, sy + 1), (sx + 4, sy + 1), (sx + 3, sy - 2), (sx + 1, sy - 1), (sx - 1, sy - 2)]])
        self.sp.part(cm & tm, Ramp(shift(r['shirt'].base, 0.04)), band=1, cast=False)
        belt = polygon(self.m(), [self.P(q) for q in [(hx - hw, hy + 2), (hx + hw + bel * 0.6, hy + 2),
                                                      (hx + hw + bel * 0.6, hy), (hx - hw, hy)]])
        self.sp.part(wm, r['pants'], cast=False)
        self.sp.part(belt & wm, Ramp('#3a2418'), shade=False, cast=False, hi=False)

    def neck(self):
        k, p = self.k, self.p
        a = self.P((p.sho[0] + 0.5, p.sho[1] - 1))
        b = self.P((p.head[0] - 0.5, p.head[1] - 5))
        self.sp.part(capsule(self.m(), a, b, 2.4 * k), Ramp(self.r['skin'].mid), hi=False)

    def head(self):
        s, r, k, p = self.s, self.r, self.k, self.p
        hx, hy = p.head
        cx, cy = self.P((hx, hy))
        sp = self.sp
        hair = r['hair']
        skin = r['skin']

        # back hair / hood behind the head
        if s.hair_style == 'hood':
            hood = ellipse(self.m(), cx - 1.0 * k, cy - 0.5 * k, 8.6 * k, 9.2 * k)
            sp.part(hood, r['sleeve'], band=2)
        if s.hair_style == 'guybrush':
            tail = capsule(self.m(), (cx - 5 * k, cy - 3 * k), (cx - 9.5 * k, cy + 3 * k), 2.4 * k, 1.6 * k)
            sp.part(tail, hair)
        if s.hair_style == 'bun':
            sp.part(ellipse(self.m(), cx - 5 * k, cy - 6 * k, 3.2 * k, 3.0 * k), hair)

        # skull + jaw
        hm = ellipse(self.m(), cx, cy, 6.6 * k, 7.6 * k)
        ellipse(hm, cx + 1.8 * k, cy + 3.2 * k, 5.2 * k, 4.4 * k)     # jaw pushes forward
        sp.part(hm, skin, band=2)

        # ear
        em = ellipse(self.m(), cx - 1.6 * k, cy + 0.6 * k, 1.6 * k, 2.2 * k)
        sp.part(em & hm, Ramp(skin.mid), hi=False, cast=False)
        sp.dot(int(cx - 1.4 * k), int(cy + 0.6 * k), skin.sh)

        # beard
        if s.beard:
            bm = ellipse(self.m(), cx + 1.5 * k, cy + 4.6 * k, 5.6 * k, 3.8 * k) & hm
            bm &= ~ellipse(self.m(), cx - 2.4 * k, cy, 2.6 * k, 4 * k)
            sp.part(bm, Ramp(s.beard), cast=False)

        # nose: the adventure-game trademark
        nk = s.nose
        nm = ellipse(self.m(), cx + 6.4 * k, cy + 1.2 * k, 2.4 * k * nk, 2.0 * k * nk)
        polygon(nm, [(cx + 4.2 * k, cy - 2.6 * k), (cx + 6.5 * k, cy + 0.5 * k), (cx + 4 * k, cy + 1.5 * k)])
        sp.part(nm, skin, band=1)
        sp.dot(int(cx + 5.8 * k), int(cy + 2.4 * k), skin.out)   # nostril

        # eye
        ex, ey = int(round(cx + 2.4 * k)), int(round(cy - 1.4 * k))
        face = p.face
        white, pupil, brow = (250, 248, 240), (20, 16, 30), hair.out if s.hair_style != 'bald' else skin.out
        if face == 'blink':
            sp.dot(ex, ey + 1, skin.out); sp.dot(ex + 1, ey + 1, skin.out); sp.dot(ex + 2, ey + 1, skin.out)
        elif face == 'hurt':
            for d in (-1, 0, 1):
                sp.dot(ex + 1 + d, ey + 1 + d, pupil); sp.dot(ex + 1 + d, ey + 1 - d, pupil)
        else:
            for yy in range(ey, ey + 3):
                sp.dot(ex, yy, white); sp.dot(ex + 1, yy, white)
            sp.dot(ex + 2, ey + 1, white)
            sp.dot(ex + 1, ey + 1, pupil); sp.dot(ex + 1, ey + 2, pupil)
        # brow
        by = ey - 2 if face != 'shout' else ey - 3
        tilt = 1 if face in ('grin', 'shout') else 0
        sp.dot(ex - 1, by + tilt, brow); sp.dot(ex, by, brow); sp.dot(ex + 1, by, brow); sp.dot(ex + 2, by - tilt * 0 + (1 if tilt else 0), brow)

        # mouth
        mx, my = int(round(cx + 3.2 * k)), int(round(cy + 4.6 * k))
        mouth = (120, 30, 40)
        if face in ('shout', 'hurt'):
            for yy in range(my - 1, my + 2):
                sp.dot(mx, yy, mouth); sp.dot(mx + 1, yy, mouth)
            sp.dot(mx + 1, my - 1, white)
        elif face == 'grin':
            sp.dot(mx - 1, my - 1, skin.out); sp.dot(mx, my, skin.out); sp.dot(mx + 1, my, white); sp.dot(mx + 2, my - 1, skin.out)
        else:
            sp.dot(mx, my, skin.out); sp.dot(mx + 1, my, skin.out)

        if s.mustache:
            mm = ellipse(self.m(), cx + 4.0 * k, cy + 3.4 * k, 2.8 * k, 1.2 * k)
            sp.part(mm, Ramp(s.beard or s.hair), band=1, cast=False)

        # glasses
        if s.eyes == 'glasses':
            gm = self.m()
            for dx in range(-1, 4):
                gm[ey - 1, ex + dx] = True
                gm[ey + 3, ex + dx] = True
            gm[ey:ey + 3, ex - 1] = True
            gm[ey:ey + 3, ex + 3] = True
            line(gm, (ex - 1, ey), (cx - 2 * k, ey))
            sp.pixels(gm, (40, 30, 50))
        elif s.eyes == 'shades':
            gm = rect(self.m(), ex - 1, ey, ex + 3, ey + 2)
            line(gm, (ex - 1, ey), (cx - 2 * k, ey))
            sp.pixels(gm, (20, 18, 28))
            sp.dot(ex, ey, (120, 140, 200))

        # hair on top
        st = s.hair_style
        if st == 'guybrush':
            hm2 = ellipse(self.m(), cx - 0.8 * k, cy - 4.2 * k, 6.8 * k, 4.4 * k)
            polygon(hm2, [(cx - 6.6 * k, cy - 3 * k), (cx - 4 * k, cy + 3 * k), (cx - 1 * k, cy - 2 * k)])
            polygon(hm2, [(cx + 1 * k, cy - 8.8 * k), (cx + 7.6 * k, cy - 6.4 * k), (cx + 4 * k, cy - 4.2 * k)])  # fringe flick
            hm2 &= ~ellipse(self.m(), cx + 4.2 * k, cy - 1.6 * k, 3.4 * k, 2.2 * k)
            sp.part(hm2, hair, band=2, cast=False)
        elif st == 'short':
            hm2 = ellipse(self.m(), cx - 0.6 * k, cy - 4.6 * k, 6.9 * k, 4.0 * k)
            polygon(hm2, [(cx - 6.8 * k, cy - 4 * k), (cx - 6 * k, cy + 2 * k), (cx - 2.6 * k, cy - 1 * k)])
            hm2 &= ~ellipse(self.m(), cx + 4.6 * k, cy - 1.2 * k, 3.6 * k, 2.4 * k)
            sp.part(hm2, hair, band=2, cast=False)
        elif st == 'messy':
            hm2 = ellipse(self.m(), cx - 0.4 * k, cy - 5.0 * k, 7.4 * k, 4.4 * k)
            for i, (dx, dy) in enumerate([(-6, -7), (-3, -10), (0, -10.5), (3, -10), (6, -8)]):
                polygon(hm2, [(cx + (dx - 2) * k, cy - 6 * k), (cx + dx * k, cy + dy * k), (cx + (dx + 2) * k, cy - 6 * k)])
            polygon(hm2, [(cx - 7 * k, cy - 4 * k), (cx - 6.5 * k, cy + 3 * k), (cx - 2.4 * k, cy - 1 * k)])
            hm2 &= ~ellipse(self.m(), cx + 4.6 * k, cy - 1.0 * k, 3.6 * k, 2.4 * k)
            sp.part(hm2, hair, band=2, cast=False)
        elif st == 'slick':
            hm2 = ellipse(self.m(), cx - 1.2 * k, cy - 4.4 * k, 6.6 * k, 3.8 * k)
            polygon(hm2, [(cx - 7 * k, cy - 3 * k), (cx - 6 * k, cy + 1 * k), (cx - 2 * k, cy - 2 * k)])
            hm2 &= ~ellipse(self.m(), cx + 3.6 * k, cy - 1.4 * k, 4.2 * k, 2.6 * k)
            sp.part(hm2, hair, band=1, cast=False)
            # comb lines
            sp.dot(int(cx - 2 * k), int(cy - 6 * k), hair.hi); sp.dot(int(cx), int(cy - 7 * k), hair.hi)
        elif st == 'bald':
            hm2 = ellipse(self.m(), cx - 4.4 * k, cy - 0.6 * k, 2.6 * k, 3.4 * k) & hm
            sp.part(hm2, hair, band=1, cast=False)
            sp.dot(int(cx - 1 * k), int(cy - 6 * k), (255, 255, 255))  # shine
        elif st == 'bun':
            hm2 = ellipse(self.m(), cx - 0.6 * k, cy - 4.6 * k, 6.9 * k, 4.0 * k)
            polygon(hm2, [(cx - 6.8 * k, cy - 4 * k), (cx - 6 * k, cy + 3 * k), (cx - 2.6 * k, cy - 1 * k)])
            hm2 &= ~ellipse(self.m(), cx + 4.6 * k, cy - 1.0 * k, 3.6 * k, 2.4 * k)
            sp.part(hm2, hair, band=2, cast=False)
        elif st == 'hood':
            front = ellipse(self.m(), cx - 1.0 * k, cy - 0.5 * k, 8.6 * k, 9.2 * k)
            front &= ~ellipse(self.m(), cx + 2.4 * k, cy + 0.8 * k, 6.4 * k, 7.6 * k)
            front &= ~rect(self.m(), cx + 5 * k, cy - 2 * k, cx + 12 * k, cy + 12 * k)
            sp.part(front, r['sleeve'], band=2, cast=False)
            # fringe sticking out of the hood
            fm = polygon(self.m(), [(cx - 1 * k, cy - 7 * k), (cx + 6 * k, cy - 5.6 * k), (cx + 3.4 * k, cy - 3.4 * k),
                                    (cx + 1 * k, cy - 4.4 * k)])
            sp.part(fm & ~ellipse(self.m(), cx + 4.6 * k, cy - 1.0 * k, 3 * k, 2 * k), hair, cast=False, band=1)

        # head-wear
        if s.hat == 'crown':
            crm = polygon(self.m(), [(cx - 5 * k, cy - 7 * k), (cx + 5 * k, cy - 7 * k), (cx + 5.5 * k, cy - 12 * k),
                                     (cx + 3 * k, cy - 9.5 * k), (cx + 0.5 * k, cy - 13 * k), (cx - 2 * k, cy - 9.5 * k),
                                     (cx - 4.5 * k, cy - 12 * k)])
            sp.part(crm, Ramp('#f2c230'), band=1)
            sp.dot(int(cx + 0.5 * k), int(cy - 8.5 * k), (200, 30, 50))
            sp.dot(int(cx - 3 * k), int(cy - 8.5 * k), (40, 120, 220))
            sp.dot(int(cx + 3.6 * k), int(cy - 8.5 * k), (40, 170, 90))
        elif s.hat == 'headphones':
            band = capsule(self.m(), (cx - 5.8 * k, cy - 1 * k), (cx - 1 * k, cy - 8.6 * k), 1.1 * k)
            capsule(band, (cx - 1 * k, cy - 8.6 * k), (cx + 3 * k, cy - 7.6 * k), 1.1 * k)
            sp.part(band, Ramp('#2b2b36'), hi=False, cast=False)
            sp.part(ellipse(self.m(), cx - 2.0 * k, cy + 0.6 * k, 2.4 * k, 2.8 * k), Ramp('#e2453c'), band=1)
        elif s.hat == 'visor':
            vm = polygon(self.m(), [(cx - 6.5 * k, cy - 5.4 * k), (cx + 6.5 * k, cy - 5.4 * k), (cx + 10.5 * k, cy - 3.4 * k),
                                    (cx + 5 * k, cy - 3.2 * k), (cx - 6.5 * k, cy - 3.6 * k)])
            sp.part(vm, Ramp('#3fa86b'), band=1)

        if s.cigar or p.face == 'grin' and s.cigar:
            cm = rect(self.m(), mx + 1, my, mx + int(5 * k), my + 1)
            sp.part(cm, Ramp('#7a4422'), shade=False, cast=False)
            sp.dot(mx + int(5 * k) + 1, my, (255, 120, 40))
            sp.dot(mx + int(5 * k) + 1, my + 1, (190, 190, 190))

    # --- props in the front hand

    def item(self):
        s, k, p = self.s, self.k, self.p
        if not s.item:
            return
        hx, hy = self.P(p.fhand)
        sp = self.sp
        import math
        a = math.radians(p.item_angle)

        def rot(dx, dy):
            # rotate around the hand, positive angle = forward/clockwise on screen
            return (hx + (dx * math.cos(a) - dy * math.sin(a)) * k, hy + (dx * math.sin(a) + dy * math.cos(a)) * k)

        if s.item == 'clipboard':
            board = polygon(self.m(), [rot(-1, -11), rot(8, -11), rot(8, 2), rot(-1, 2)])
            sp.part(board, Ramp('#a8743c'), band=1)
            paper = polygon(self.m(), [rot(0.5, -9.5), rot(6.5, -9.5), rot(6.5, 0.5), rot(0.5, 0.5)])
            sp.part(paper, Ramp('#f8f4e4'), band=1, cast=False)
            lm = self.m()
            for ly in (-7.5, -5.5, -3.5, -1.5):
                line(lm, rot(1.5, ly), rot(5.5, ly))
            sp.pixels(lm & paper, (110, 130, 170))
            clip = polygon(self.m(), [rot(2, -12.4), rot(5, -12.4), rot(5, -10), rot(2, -10)])
            sp.part(clip, Ramp('#c8ccd4'), band=1)
        elif s.item == 'laptop':
            # open laptop held up in front, screen towards the viewer
            lid = polygon(self.m(), [rot(-2, -12), rot(9, -12), rot(10, 0), rot(-1, 0)])
            sp.part(lid, Ramp('#5c6474'), band=1)
            scr = polygon(self.m(), [rot(-0.6, -10.8), rot(7.8, -10.8), rot(8.6, -1.2), rot(0.2, -1.2)])
            sp.part(scr & lid, Ramp('#1c2a3c'), shade=False, cast=False)
            cm = self.m()
            for i, (x0, x1) in enumerate([(1, 5), (2, 7), (2, 4), (1, 6), (2, 5)]):
                line(cm, rot(x0, -9.4 + i * 1.8), rot(x1, -9.4 + i * 1.8))
            sp.pixels(cm & scr, (90, 220, 140))
            base = polygon(self.m(), [rot(-1, 0), rot(10, 0), rot(12, 2.2), rot(1, 2.2)])
            sp.part(base, Ramp('#a4acba'), band=1)
        elif s.item == 'magnifier':
            h1, h2 = rot(0, 0), rot(4, -6)
            sp.part(capsule(self.m(), rot(-1, 2), h2, 1.2 * k), Ramp('#6a3c1e'), band=1)
            c = rot(6.5, -9.5)
            ring = ellipse(self.m(), c[0], c[1], 4.6 * k, 4.6 * k)
            glass = ellipse(self.m(), c[0], c[1], 3.2 * k, 3.2 * k)
            sp.part(ring & ~glass, Ramp('#c9a227'), band=1)
            sp.part(glass, Ramp('#bfe6ff'), band=1, cast=False)
            sp.dot(int(c[0] - 1), int(c[1] - 1), (255, 255, 255))
        elif s.item == 'phone':
            ph = polygon(self.m(), [rot(-1, -7), rot(3, -7), rot(3, 0), rot(-1, 0)])
            sp.part(ph, Ramp('#2a2a34'), band=1)
            scr = polygon(self.m(), [rot(-0.2, -6.2), rot(2.2, -6.2), rot(2.2, -1), rot(-0.2, -1)])
            sp.part(scr & ph, Ramp('#7fd4ff'), shade=False, cast=False)
        elif s.item == 'calculator':
            cm = polygon(self.m(), [rot(-1, -8), rot(5, -8), rot(5, 1), rot(-1, 1)])
            sp.part(cm, Ramp('#d8d0b8'), band=1)
            scr = polygon(self.m(), [rot(0, -7), rot(4, -7), rot(4, -5), rot(0, -5)])
            sp.part(scr & cm, Ramp('#8fbf7a'), shade=False, cast=False)
            km = self.m()
            for kx in (0.5, 2.5):
                for ky in (-3.5, -1.5, 0):
                    q = rot(kx + 0.5, ky)
                    if 0 <= int(q[1]) < km.shape[0] and 0 <= int(q[0]) < km.shape[1]:
                        km[int(q[1]), int(q[0])] = True
            sp.pixels(km & cm, (90, 70, 60))
        elif s.item == 'mug':
            mm = polygon(self.m(), [rot(-1, -5), rot(4, -5), rot(4, 1), rot(-1, 1)])
            sp.part(mm, Ramp('#f4f0e8'), band=1)

    # --- assemble

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
        self.sp.outline()
        return self.sp.image()


def sheet(spec: Spec):
    ps = poses()
    return [Figure(spec, ps[name]).draw() for name in FRAMES]


CAST = {
    'pm': Spec('pm', hair='#e8c050', hair_style='guybrush', shirt='#f4f2ea', pants='#33457e', tie='#d22a2a',
               item='clipboard'),
    'developer': Spec('developer', height=55, skin='pale', hair='#3a2a20', hair_style='hood', shirt='#3d5a80',
                      pants='#2c3550', shoes='#d8d8d0', beard='#4a3220', item='laptop'),
    'tester': Spec('tester', height=53, hair='#c0502a', hair_style='messy', shirt='#4fae7e', pants='#a08e62',
                   shoes='#5a3a22', eyes='glasses', width=0.9, item='magnifier'),
    'stakeholder': Spec('stakeholder', height=58, skin='tan', hair='#2a1a14', hair_style='slick', shirt='#f0e6c8',
                        jacket='#7b3fa8', pants='#4a2470', shoes='#1e1418', tie='#ffd60a', width=1.1, nose=1.2,
                        item='phone'),
    'cfo': Spec('cfo', height=58, hair='#9a9a9a', hair_style='bald', shirt='#e8ecf0', jacket='#4a5260',
                pants='#2a2e34', shoes='#1e1418', tie='#ffd23f', belly=0.6, eyes='glasses', mustache=True,
                beard='#a8a8a8', hat='visor', item='calculator', nose=1.15),
    'ceo': Spec('ceo', height=74, cell=(88, 92), skin='tan', hair='#d0d0d4', hair_style='slick', shirt='#f4f4f4',
                jacket='#1b2a4e', pants='#141a2c', shoes='#0e0a0c', tie='#fca311', belly=1.0, width=1.25,
                eyes='shades', hat='crown', cigar=True, nose=1.3),
}


# ---------------------------------------------------------------- the Steering Committee boss

COMMITTEE = [
    Spec('chair', height=58, cell=(48, 72), skin='pale', hair='#6a3a2a', hair_style='bun', shirt='#f2e6e0',
         jacket='#8a2232', tie=None, nose=0.9),
    Spec('member_l', height=56, cell=(48, 72), hair='#888890', hair_style='bald', shirt='#e8ecf0', jacket='#56606e',
         tie='#c1121f', mustache=True, beard='#9a9aa0', eyes='glasses'),
    Spec('member_r', height=56, cell=(48, 72), skin='dark', hair='#1a1414', hair_style='short', shirt='#f4f4f4',
         jacket='#3e4a3a', tie='#2a7ab8', beard='#1a1414'),
]

COMMITTEE_FRAMES = ['idle0', 'idle1', 'atk0', 'atk1', 'hurt']


def committee_poses():
    sit = Pose(felb=(6, 30), fhand=(10, 27), belb=(-1, 30), bhand=(4, 27))   # forearms resting on the table
    return {
        'idle0': sit,
        'idle1': replace(sit, sho=(0, 40), head=(1, 49), face='blink'),
        'atk0': replace(sit, felb=(5, 42), fhand=(8, 49), belb=(-2, 41), bhand=(2, 48), face='shout',
                        sho=(-1, 41), head=(0, 51)),
        'atk1': replace(sit, felb=(8, 32), fhand=(12, 28), belb=(2, 32), bhand=(7, 28), face='shout',
                        sho=(2, 39), head=(4, 47)),
        'hurt': replace(sit, sho=(-3, 40), head=(-4, 48), felb=(3, 42), fhand=(7, 47), face='hurt'),
    }


def committee_sheet():
    """Three members behind one long table. 128x96 cells, the table front is the bottom 30 px."""
    from PIL import Image
    from pixel import Sprite as _S
    ps = committee_poses()
    frames = []
    for name in COMMITTEE_FRAMES:
        W, H = 128, 96
        img = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        lift = 2 if name == 'atk1' else 0
        for spec, x in ((COMMITTEE[1], 22), (COMMITTEE[2], 106), (COMMITTEE[0], 64)):
            fig = Figure(spec, ps[name]).draw()
            img.alpha_composite(fig, (x - fig.width // 2, H - fig.height - 16))
        # the table, drawn as its own sprite on top
        t = _S(W, H)
        ty = H - 36 + lift
        top = polygon(blank(W, H), [(4, ty), (W - 4, ty), (W - 1, ty + 5), (1, ty + 5)])
        t.part(top, Ramp('#9a5a30', hi='#c07a44'), band=1)
        front = rect(blank(W, H), 3, ty + 6, W - 4, ty + 22)
        t.part(front, Ramp('#6e3c1e'), band=2)
        # carved panels
        pm = blank(W, H)
        for x0 in range(8, W - 20, 30):
            rect(pm, x0, ty + 9, x0 + 24, ty + 19)
        t.part(pm & front, Ramp('#7e4826'), band=1, cast=False)
        # legs
        legs = rect(blank(W, H), 6, ty + 23, 12, H - 3)
        rect(legs, W - 13, ty + 23, W - 7, H - 3)
        t.part(legs, Ramp('#5a301a'), band=1)
        # papers, a jug and the gavel on the table top
        t.part(rect(blank(W, H), 30, ty - 1 - lift, 42, ty + 1), Ramp('#f6f2e6'), band=1)
        t.part(rect(blank(W, H), 78, ty - 2 - lift * 2, 88, ty), Ramp('#f6f2e6'), band=1)
        jug = ellipse(blank(W, H), 52, ty - 4, 3, 4)
        t.part(jug, Ramp('#bfe0f0'), band=1)
        gav = rect(blank(W, H), 92, ty - 3 - lift * 2, 99, ty - 1 - lift * 2)
        t.part(gav, Ramp('#7a4422'), band=1)
        # name plate in the middle
        t.part(rect(blank(W, H), 52, ty + 11, 76, ty + 17), Ramp('#d8b040'), band=1)
        t.outline()
        img.alpha_composite(t.image())
        frames.append(img)
    return frames
