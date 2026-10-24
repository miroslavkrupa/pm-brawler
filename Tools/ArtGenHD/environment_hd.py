"""Hand-drawn office environments: the view outside, walls with windows and blinds, floor tiles and
lots of project-management clutter (Kanban boards, Gantt charts, burndowns, risk matrices...).

Room geometry (in world units, relative to the bottom of the wall; the floor is 1 unit up):
  wall tile 8 x 14, window x 1.6..6.4, y 3.4..7.4, wall props centred at x 0 (between windows), y 5.4.
"""
import math
import random

from ink import INK, Ink, ellipse, limb, mix, poly, rrect, shade, smooth, union, subtract, intersect

PPU = 128          # props, tiles
WALL_PPU = 96      # wall tiles
FAR_PPU = 48       # the view through the windows (soft, far away)

WALL = dict(w=8, h=14, win=(1.6, 6.4, 3.4, 7.4), prop_y=5.4, curtain_top=7.95, curtain_x=1.45)

THEMES = {
    'level1': dict(  # dev team open space, night shift
        wall='#5f8a86', wall2='#4e7470', dado='#3c4a52', trim='#d8d0bc', floor='#4a4f5e', carpet='#5c6a8a',
        sky=('#1c2448', '#3a3f78', '#6a5a8c'), city='night',
        floor_props=['desk_dev', 'server', 'plant', 'trash', 'desk_dev', 'cooler', 'chair'],
        wall_props=['kanban', 'poster_works', 'clock', 'burndown', 'kanban', 'calendar'],
    ),
    'level2': dict(  # QA gauntlet, rainy afternoon
        wall='#8a9460', wall2='#76804e', dado='#4a4a36', trim='#e0d8c0', floor='#55503e', carpet='#7a6a48',
        sky=('#7a8c98', '#a0aab0', '#c8c8c0'), city='rain',
        floor_props=['desk_qa', 'printer', 'cabinet', 'plant', 'desk_qa', 'trash', 'cooler'],
        wall_props=['bugboard', 'traffic', 'poster_bugs', 'calendar', 'bugboard', 'clock'],
    ),
    'level3': dict(  # stakeholder alignment workshop, sunset
        wall='#a87a8a', wall2='#946676', dado='#5a3a4a', trim='#ecdcc8', floor='#4e3a44', carpet='#8a4a5a',
        sky=('#3a2a5a', '#c05a6a', '#ffb070'), city='sunset',
        floor_props=['flipchart', 'chair', 'coffee', 'plant', 'flipchart', 'chair', 'trash'],
        wall_props=['whiteboard', 'stickies', 'projector', 'poster_scope', 'stickies', 'clock'],
    ),
    'level4': dict(  # steering committee boardroom, storm
        wall='#7a4a30', wall2='#6a3e26', dado='#3e2414', trim='#d0a848', floor='#3a2418', carpet='#7a1e26', panel=True,
        sky=('#16161e', '#2a2a3a', '#4a4a5a'), city='storm',
        floor_props=['globe', 'binders', 'plant', 'binders'],
        wall_props=['gantt', 'rag', 'portrait', 'risk', 'portrait', 'clock'],
        curtains=True,
    ),
    'level5': dict(  # the C-suite penthouse, above the clouds
        wall='#2c3a5e', wall2='#24304e', dado='#161c30', trim='#d8b448', floor='#1c1c2c', carpet='#a8842a', panel=True,
        sky=('#0a0a24', '#24205a', '#7a4a8a'), city='clouds',
        floor_props=['trophy', 'aquarium', 'plant', 'golf', 'trophy'],
        wall_props=['kpi', 'portrait', 'orgchart', 'poster_synergy', 'portrait', 'clock'],
        curtains=True,
    ),
}


# ---------------------------------------------------------------- the view outside

def far(key):
    th = THEMES[key]
    W, H = 32 * FAR_PPU, 14 * FAR_PPU
    ink = Ink(W, H, scale=0.6)
    rnd = random.Random(key)
    top, mid, low = th['sky']
    ink.gradient(rrect(0, 0, W, H, 0), top, low, angle=90)
    ink.c.drawPaint(__import__('skia').Paint(Shader=__import__('ink').grain_shader(1.5), BlendMode=__import__('skia').BlendMode.kOverlay, Alphaf=0.25))
    horizon = H * 0.62
    city = th['city']
    if city in ('night', 'clouds'):
        for _ in range(260):
            x, y = rnd.uniform(0, W), rnd.uniform(0, horizon * 0.7)
            ink.fill(ellipse(x, y, rnd.uniform(0.6, 1.6), rnd.uniform(0.6, 1.6)), '#fff6d8', rnd.randint(120, 255))
        ink.fill(ellipse(W * 0.72, H * 0.16, 34, 34), '#fff2c8')
        ink.fill(ellipse(W * 0.72, H * 0.16, 60, 60), '#fff2c8', 40)
    if city == 'sunset':
        ink.fill(ellipse(W * 0.35, horizon - 30, 70, 70), '#ffe0a0')
        ink.fill(ellipse(W * 0.35, horizon - 30, 120, 120), '#ffc080', 60)
    # clouds
    for i in range(14 if city != 'storm' else 22):
        cx, cy = rnd.uniform(0, W), rnd.uniform(H * 0.05, horizon * 0.8)
        blobs = None
        for j in range(5):
            e = ellipse(cx + rnd.uniform(-80, 80), cy + rnd.uniform(-10, 10), rnd.uniform(40, 90), rnd.uniform(14, 26))
            blobs = e if blobs is None else union(blobs, e)
        c = mix(mid, '#ffffff', 0.25) if city not in ('storm', 'night') else mix(mid, '#000000', 0.2)
        ink.painted(blobs, c, outline=False, light=0.25, dark=0.2)
    # skyline layers
    layers = [(0.55, mix(mid, top, 0.4), 60, 160), (0.8, mix(top, '#000000', 0.25), 40, 220)]
    if city == 'clouds':
        layers = [(0.6, mix(top, '#000000', 0.2), 20, 80)]
    for depth, color, minh, maxh in layers:
        x = -20
        while x < W:
            bw = rnd.uniform(40, 110)
            bh = rnd.uniform(minh, maxh) * (1.2 if depth > 0.7 else 1)
            b = rrect(x, horizon - bh + depth * 60, x + bw, H, 2)
            ink.fill(b, color)
            ink.stroke(b, mix(color, '#000000', 0.4), width=1.2, alpha=120)
            # windows
            lit = '#ffd890' if city in ('night', 'storm', 'sunset', 'clouds') else '#c8d8e0'
            for wy in range(int(horizon - bh + depth * 60 + 10), int(H), 14):
                for wx in range(int(x + 6), int(x + bw - 8), 11):
                    if rnd.random() < (0.35 if city in ('night', 'storm', 'clouds') else 0.2):
                        ink.fill(rrect(wx, wy, wx + 6, wy + 8, 1), lit, 200)
            # a crane or antenna now and then
            if rnd.random() < 0.15:
                ax = x + bw / 2
                ink.line([(ax, horizon - bh + depth * 60), (ax, horizon - bh + depth * 60 - 40)], color=color, width=3)
                ink.fill(ellipse(ax, horizon - bh + depth * 60 - 40, 3, 3), '#ff4040')
            x += bw + rnd.uniform(0, 16)
    if city == 'clouds':
        # a sea of clouds below the penthouse
        for i in range(40):
            cx = rnd.uniform(0, W)
            ink.painted(ellipse(cx, horizon + rnd.uniform(20, 120), rnd.uniform(60, 140), rnd.uniform(20, 40)),
                        mix(low, '#ffffff', 0.3), outline=False)
    if city in ('rain', 'storm'):
        for _ in range(900):
            x, y = rnd.uniform(0, W), rnd.uniform(0, H)
            ink.line([(x, y), (x - 6, y + 18)], color='#d8e0f0', width=0.9, alpha=90)
    if city == 'storm':
        x, y = W * 0.6, 0
        pts = [(x, y)]
        while y < horizon:
            x += rnd.uniform(-30, 30)
            y += rnd.uniform(20, 50)
            pts.append((x, y))
        ink.line(pts, color='#f0f0ff', width=4)
        ink.line(pts, color='#ffffff', width=1.5)
    return ink.image()


# ---------------------------------------------------------------- walls

def wall(key):
    th = THEMES[key]
    U = WALL_PPU
    W, H = WALL['w'] * U, WALL['h'] * U
    ink = Ink(W, H, scale=0.9)

    def Y(y):  # wall units (from bottom) to px
        return H - y * U

    import skia
    base = th['wall']
    if th.get('panel'):
        ink.gradient(rrect(0, 0, W, H, 0), shade(base, 0.08), shade(base, -0.15), angle=90)
        for x in range(0, W, U * 2):
            panel = rrect(x + 10, Y(11.6), x + U * 2 - 10, Y(2.6), 6)
            ink.painted(panel, shade(base, 0.04), width=2.2, light=0.15, dark=0.25)
            ink.line([(x + 24, Y(11.2)), (x + 24, Y(3))], color=shade(base, 0.25), width=1.4, alpha=120)
    else:
        ink.gradient(rrect(0, 0, W, H, 0), shade(base, 0.12), shade(base, -0.12), angle=90)
        # subtle painted wallpaper pattern: vertical brush bands
        for x in range(0, W, 48):
            ink.fill(rrect(x, 0, x + 24, H, 0), th['wall2'], 70)
    ink.grain_scale = 1.5   # 384 px grain repeats exactly twice per 768 px tile, so tiles join seamlessly
    ink.c.drawPaint(skia.Paint(Shader=__import__('ink').grain_shader(1.5), BlendMode=skia.BlendMode.kOverlay, Alphaf=0.5))

    # dado rail and lower wall
    ink.painted(rrect(-4, Y(2.2), W + 4, Y(0), 0), th['dado'], width=2.5, light=0.12)
    ink.painted(rrect(-4, Y(2.35), W + 4, Y(2.15), 3), th['trim'], width=2.2)
    # baseboard
    ink.painted(rrect(-4, Y(1.3), W + 4, Y(0.9), 2), shade(th['trim'], -0.25), width=2.2)
    # ceiling molding and dark ceiling above
    ink.fill(rrect(0, 0, W, Y(12.4), 0), shade(base, -0.65))
    for i in range(2):
        lx = W * (0.25 + i * 0.5)
        lamp = rrect(lx - U * 0.9, Y(13.4), lx + U * 0.9, Y(13.15), 6)
        ink.painted(lamp, '#f4f4e8', width=2)
        ink.fill(rrect(lx - U * 1.6, Y(13.15), lx + U * 1.6, Y(12.4), 0), '#fff8d0', 25)
    ink.painted(rrect(-4, Y(12.5), W + 4, Y(12.1), 2), th['trim'], width=2.4)

    # window with frame, sill and blinds; the glass is a hole for the view layer
    x0, x1, y0, y1 = WALL['win']
    fx0, fx1, fy0, fy1 = x0 * U, x1 * U, Y(y1), Y(y0)
    ink.cast_shadow(rrect(fx0 - 16, fy0 - 16, fx1 + 16, fy1 + 20, 6), 6, 8, 90, 8)
    frame = subtract(rrect(fx0 - 14, fy0 - 14, fx1 + 14, fy1 + 10, 6), rrect(fx0, fy0, fx1, fy1, 2))
    ink.painted(frame, th['trim'], width=2.6, light=0.2)
    ink.painted(rrect(fx0 - 26, fy1 + 6, fx1 + 26, fy1 + 22, 4), th['trim'], width=2.6, light=0.25)  # sill
    # mullion
    mx = (fx0 + fx1) / 2
    ink.painted(rrect(mx - 6, fy0, mx + 6, fy1, 1), th['trim'], width=2)
    # half-lowered blinds: slats in the top 40% of the window
    blind_bottom = fy0 + (fy1 - fy0) * 0.42
    for i, y in enumerate(range(int(fy0 + 4), int(blind_bottom), 9)):
        for a, b in ((fx0 + 2, mx - 6), (mx + 6, fx1 - 2)):
            tilt = 2 if i % 2 else 0
            slat = poly([(a, y), (b, y + tilt), (b, y + 6 + tilt), (a, y + 6)])
            ink.fill(slat, '#ece6d6')
            ink.stroke(slat, shade('#ece6d6', -0.45), width=1.0, alpha=200)
    ink.painted(rrect(fx0 - 6, blind_bottom - 2, fx1 + 6, blind_bottom + 8, 3), '#d8d0bc', width=2)
    for xx in (fx0 + (mx - fx0) * 0.5, mx + (fx1 - mx) * 0.5):
        ink.line([(xx, blind_bottom + 8), (xx + 3, blind_bottom + 60)], color='#e8e0cc', width=1.6)
        ink.fill(ellipse(xx + 3, blind_bottom + 62, 4, 5), '#e8e0cc')

    img = ink.image()
    # punch the glass out (below the blinds), leaving a faint reflection
    from PIL import ImageDraw
    import numpy as np
    arr = np.array(img)
    gy0 = int(blind_bottom + 9)
    for (a, b) in ((int(fx0), int(mx - 6)), (int(mx + 7), int(fx1))):
        arr[gy0:int(fy1), a:b, 3] = 0
        # reflection streaks
        for k in range(3):
            for yy in range(gy0, int(fy1)):
                xx = a + 20 + k * 22 + (yy - gy0) // 2
                if a <= xx < b - 6:
                    arr[yy, xx:xx + 6] = [255, 255, 255, 34]
    from PIL import Image
    return Image.fromarray(arr, 'RGBA')


# ---------------------------------------------------------------- floor tiles

def tiles(key):
    th = THEMES[key]
    U = PPU
    import skia
    # fill: dark foundation / concrete
    ink = Ink(U, U, scale=0.9)
    ink.grain_scale = 0.5   # 128 px grain = one tile, seamless
    ink.gradient(rrect(0, 0, U, U, 0), shade(th['floor'], 0.05), shade(th['floor'], -0.1), angle=90)
    ink.c.drawPaint(skia.Paint(Shader=__import__('ink').grain_shader(0.5), BlendMode=skia.BlendMode.kOverlay, Alphaf=0.6))
    ink.line([(0, U * 0.5), (U, U * 0.5)], color=shade(th['floor'], -0.3), width=2, alpha=120)
    ink.line([(U * 0.5, 0), (U * 0.5, U * 0.5)], color=shade(th['floor'], -0.3), width=2, alpha=120)
    fill = ink.image()
    # top: carpet surface with a lip
    ink = Ink(U, U, scale=0.9)
    ink.grain_scale = 0.5   # 128 px grain = one tile, seamless
    ink.gradient(rrect(0, 0, U, U, 0), shade(th['floor'], 0.05), shade(th['floor'], -0.1), angle=90)
    ink.c.drawPaint(skia.Paint(Shader=__import__('ink').grain_shader(0.5), BlendMode=skia.BlendMode.kOverlay, Alphaf=0.6))
    ink.gradient(rrect(-2, 0, U + 2, U * 0.26, 0), shade(th['carpet'], -0.1), shade(th['carpet'], 0.1), angle=90)
    ink.c.drawPaint(skia.Paint(Shader=__import__('ink').grain_shader(0.5), BlendMode=skia.BlendMode.kOverlay, Alphaf=0.0))
    ink.fill(rrect(-2, U * 0.26, U + 2, U * 0.34, 0), shade(th['trim'], -0.2))
    ink.line([(-2, U * 0.26), (U + 2, U * 0.26)], width=2.5)
    ink.line([(-2, U * 0.34), (U + 2, U * 0.34)], width=2.5)
    ink.line([(-2, 1), (U + 2, 1)], color=shade(th['carpet'], 0.3), width=2)
    top = ink.image()
    # desk: a row of office desks seen from the front, 1 unit wide, 0.75 tall
    ink = Ink(U, int(U * 0.75), scale=0.9)
    ink.grain_scale = 0.5
    h = int(U * 0.75)
    ink.painted(rrect(-3, 0, U + 3, 16, 3), '#c8935a', light=0.3, width=2.4)
    ink.painted(rrect(4, 16, U - 4, h - 26, 2), '#a8744a', width=2.2)
    for yy in (16 + (h - 42) * 0.5,):
        ink.line([(4, yy), (U - 4, yy)], width=2)
    for yy in (16 + (h - 42) * 0.25, 16 + (h - 42) * 0.75):
        ink.painted(rrect(U / 2 - 12, yy - 3, U / 2 + 12, yy + 3, 3), '#d8c070', width=1.4, grain=False)
    ink.painted(rrect(10, h - 26, 22, h - 4, 2), '#5a5a62', width=2)
    ink.painted(rrect(U - 22, h - 26, U - 10, h - 4, 2), '#5a5a62', width=2)
    desk = ink.image()
    return fill, top, desk


# ---------------------------------------------------------------- props

def sticky(ink, x, y, s, color, rot=0.0, text=None, seed=0):
    rnd = random.Random(seed)
    ink.c.save()
    ink.c.translate(x, y)
    ink.c.rotate(rot)
    note = poly([(-s / 2, -s / 2), (s / 2, -s / 2), (s / 2, s / 2 - s * 0.12), (s / 2 - s * 0.14, s / 2), (-s / 2, s / 2)])
    ink.cast_shadow(note, 2, 2, 60, 2)
    ink.painted(note, color, width=1.4, light=0.2, dark=0.18)
    if text:
        ink.text(text, 0, -s * 0.1, s * 0.3, color='#3a2a24')
    else:
        for i in range(2):
            ink.line([(-s * 0.32, -s * 0.15 + i * s * 0.25), (s * (0.1 + rnd.random() * 0.2), -s * 0.15 + i * s * 0.25)],
                     color='#5a4a44', width=1.2, alpha=180)
    ink.c.restore()


def board(ink, x0, y0, x1, y1, frame='#9aa0aa', face='#f6f6f0'):
    ink.cast_shadow(rrect(x0, y0, x1, y1, 4), 5, 6, 90, 6)
    ink.painted(rrect(x0, y0, x1, y1, 4), frame, width=2.6, light=0.3)
    ink.painted(rrect(x0 + 8, y0 + 8, x1 - 8, y1 - 8, 2), face, width=1.6, shadow=False, light=0.05)


STICKY = ['#ffe36a', '#ff9ac0', '#9ad8ff', '#a8f0a0', '#ffb870']


def prop(name, key):
    th = THEMES[key]
    U = PPU
    rnd = random.Random(name + key)

    def canvas(w, h):
        return Ink(int(w * U), int(h * U), scale=1.0), int(w * U), int(h * U)

    # ---- wall props (centred, hung on the wall)
    if name == 'kanban':
        ink, W, H = canvas(2.8, 1.9)
        board(ink, 6, 6, W - 10, H - 12)
        cols = ['TO DO', 'DOING', 'DONE']
        cw = (W - 40) / 3
        for i, c in enumerate(cols):
            cx = 20 + cw * i + cw / 2
            ink.text(c, cx, 30, 18, font='Bangers-Regular.ttf')
            if i:
                ink.line([(20 + cw * i, 22), (20 + cw * i, H - 30)], color='#8a8a90', width=1.6)
            n = [6, 2, 1][i]
            for j in range(n):
                sticky(ink, 20 + cw * i + 24 + (j % 2) * 44 + rnd.uniform(-3, 3), 66 + (j // 2) * 44 + rnd.uniform(-3, 3),
                       36, rnd.choice(STICKY), rnd.uniform(-8, 8), seed=j + i * 10)
        ink.text('WIP LIMIT: 2 (lol)', W - 90, H - 26, 12, color='#c03030', rotate=-3)
        return ink.image()
    if name in ('poster_works', 'poster_bugs', 'poster_scope', 'poster_synergy'):
        ink, W, H = canvas(1.5, 1.9)
        title, sub, bg, art = {
            'poster_works': ('IT WORKS', 'on my machine', '#2a3a5a', 'laptop'),
            'poster_bugs': ('ZERO BUGS', 'since 0 days', '#5a2a2a', 'bug'),
            'poster_scope': ('SCOPE?', 'what scope', '#3a2a5a', 'creep'),
            'poster_synergy': ('SYNERGY', 'leverage the paradigm', '#5a4a1a', 'eagle'),
        }[name]
        ink.cast_shadow(rrect(8, 8, W - 8, H - 8, 3), 5, 6, 90, 6)
        ink.painted(rrect(8, 8, W - 8, H - 8, 3), '#2a2420', width=2.6)
        ink.gradient(rrect(18, 18, W - 18, H - 18, 2), shade(bg, 0.25), shade(bg, -0.25), angle=90)
        cx, cy = W / 2, H * 0.42
        if art == 'laptop':
            ink.painted(rrect(cx - 40, cy - 26, cx + 40, cy + 22, 4), '#8a92a2', width=2.2)
            ink.fill(rrect(cx - 32, cy - 19, cx + 32, cy + 15, 2), '#14202e')
            ink.text('OK', cx, cy - 2, 22, color='#7fd8a0', font='Bangers-Regular.ttf')
            ink.painted(rrect(cx - 50, cy + 22, cx + 50, cy + 30, 3), '#a4acba', width=2)
        elif art == 'bug':
            body = ellipse(cx, cy, 30, 38)
            ink.painted(body, '#d03a2a', width=2.4)
            ink.line([(cx, cy - 38), (cx, cy + 38)], width=2)
            for d in (-1, 1):
                for k in range(3):
                    ink.line([(cx + d * 26, cy - 18 + k * 18), (cx + d * 44, cy - 26 + k * 22)], width=3)
            ink.painted(ellipse(cx, cy - 44, 16, 12), '#3a2a24', width=2)
        elif art == 'creep':
            for i in range(5):
                ink.painted(rrect(cx - 40 + i * 14, cy + 30 - i * 16 - 10, cx - 30 + i * 14, cy + 30, 2), STICKY[i], width=1.6)
            ink.line([(cx - 44, cy + 34), (cx + 40, cy - 40)], color='#ffffff', width=3)
        else:
            wing = smooth([(cx - 60, cy - 10), (cx - 20, cy - 34), (cx, cy - 10), (cx + 20, cy - 34), (cx + 60, cy - 10), (cx, cy + 10)])
            ink.painted(wing, '#6a4a2a', width=2.2)
            ink.painted(ellipse(cx, cy - 18, 10, 9), '#f6f6f0', width=2)
        ink.text(title, W / 2, H * 0.74, 30, color='#fff6d8', font='Bangers-Regular.ttf')
        ink.text(sub, W / 2, H * 0.84, 14, color='#e8dcc0')
        return ink.image()
    if name == 'clock':
        ink, W, H = canvas(0.75, 0.75)
        c = ellipse(W / 2, H / 2, W / 2 - 6, H / 2 - 6)
        ink.cast_shadow(c, 3, 4, 90, 4)
        ink.painted(c, th['trim'], width=2.6)
        ink.painted(ellipse(W / 2, H / 2, W / 2 - 14, H / 2 - 14), '#fbf8ee', width=1.8, shadow=False)
        for i in range(12):
            a = i / 12 * math.tau
            ink.line([(W / 2 + math.cos(a) * (W / 2 - 20), H / 2 + math.sin(a) * (H / 2 - 20)),
                      (W / 2 + math.cos(a) * (W / 2 - 25), H / 2 + math.sin(a) * (H / 2 - 25))], width=1.6)
        ink.line([(W / 2, H / 2), (W / 2 + 14, H / 2 - 18)], width=3)    # five to... deadline
        ink.line([(W / 2, H / 2), (W / 2 - 3, H / 2 - 28)], width=2)
        ink.text('DEADLINE', W / 2, H / 2 + 16, 8, color='#c03030', font='Bangers-Regular.ttf')
        return ink.image()
    if name == 'burndown':
        ink, W, H = canvas(2.0, 1.5)
        board(ink, 6, 6, W - 10, H - 12)
        ink.text('SPRINT BURNDOWN', W / 2, 28, 16, font='Bangers-Regular.ttf')
        ox, oy, gw, gh = 34, H - 40, W - 70, H - 90
        ink.line([(ox, oy - gh), (ox, oy), (ox + gw, oy)], width=2)
        ink.line([(ox, oy - gh), (ox + gw, oy)], color='#5a9a5a', width=2, alpha=180)   # ideal
        pts = [(ox, oy - gh)]
        y = oy - gh
        for i in range(1, 8):
            y += rnd.uniform(-gh * 0.15, gh * 0.06)   # goes UP, of course
            pts.append((ox + gw * i / 7, max(oy - gh * 1.1, min(oy, y))))
        ink.line(pts, color='#d03030', width=3)
        ink.text('ideal', ox + gw * 0.7, oy - gh * 0.2, 11, color='#5a9a5a')
        ink.text('reality', ox + gw * 0.8, pts[-1][1] - 12, 11, color='#d03030')
        return ink.image()
    if name == 'calendar':
        ink, W, H = canvas(1.1, 1.2)
        ink.cast_shadow(rrect(8, 14, W - 8, H - 8, 3), 4, 5, 90, 5)
        ink.painted(rrect(8, 14, W - 8, H - 8, 3), '#fbf8ee', width=2.4, light=0.05)
        ink.painted(rrect(8, 14, W - 8, 40, 3), '#c03030', width=2.4)
        ink.text('OCTOBER', W / 2, 27, 13, color='#ffffff', font='Bangers-Regular.ttf')
        cw, ch = (W - 26) / 7, (H - 60) / 5
        for d in range(31):
            cx, cy = 14 + (d % 7) * cw + cw / 2, 50 + (d // 7) * ch + ch / 2
            ink.text(str(d + 1), cx, cy, 8, color='#5a4a44')
            if d < 23:
                ink.line([(cx - 5, cy - 5), (cx + 5, cy + 5)], color='#c03030', width=1.4)
                ink.line([(cx + 5, cy - 5), (cx - 5, cy + 5)], color='#c03030', width=1.4)
            if d == 24:
                ink.stroke(ellipse(cx, cy, 10, 8), '#c03030', width=2.2)
        ink.text('DEADLINE!!', W / 2 + 10, H - 16, 11, color='#c03030', rotate=-6)
        for x in (W * 0.3, W * 0.7):
            ink.painted(ellipse(x, 14, 4, 6), '#8a8a90', width=1.4)
        return ink.image()
    if name == 'bugboard':
        ink, W, H = canvas(2.6, 1.8)
        board(ink, 6, 6, W - 10, H - 12, frame='#8a6a4a', face='#c8a87a')
        ink.text('BUG TRACKER', W / 2, 30, 18, font='Bangers-Regular.ttf')
        for i in range(14):
            x, y = 40 + (i % 7) * 44 + rnd.uniform(-4, 4), 70 + (i // 7) * 60 + rnd.uniform(-4, 4)
            sticky(ink, x, y, 38, '#ff8a7a' if i % 3 else '#fbf7ea', rnd.uniform(-10, 10), text='#%d' % rnd.randint(1000, 9999), seed=i)
            ink.painted(ellipse(x, y - 17, 3, 3), '#2a6ad0', width=1, grain=False)
        ink.text('CRITICAL: ALL OF THEM', W / 2, H - 28, 13, color='#c03030', rotate=-2)
        return ink.image()
    if name == 'traffic':
        ink, W, H = canvas(0.6, 1.5)
        body = rrect(W / 2 - 24, 10, W / 2 + 24, H - 40, 10)
        ink.cast_shadow(body, 4, 5, 90, 5)
        ink.painted(body, '#2a2a30', width=2.4)
        for i, (c, on) in enumerate((('#ff3a2a', True), ('#ffb020', False), ('#3ad05a', False))):
            e = ellipse(W / 2, 36 + i * 42, 15, 15)
            if on:
                ink.fill(ellipse(W / 2, 36 + i * 42, 26, 26), c, 70)
            ink.painted(e, c if on else shade(c, -0.6), width=1.8)
        ink.text('BUILD', W / 2, H - 24, 14, color='#fbf8ee', font='Bangers-Regular.ttf')
        return ink.image()
    if name == 'whiteboard':
        ink, W, H = canvas(2.8, 1.8)
        board(ink, 6, 6, W - 10, H - 18)
        ink.text('REQUIREMENTS v12 FINAL (2)', W / 2, 32, 16, color='#2a4ad0')
        for i, t in enumerate(['must be fast', 'must be cheap', 'must be done yesterday', 'blockchain?', 'make logo bigger']):
            ink.text('- ' + t, 40, 62 + i * 22, 14, color='#2a2a2a' if i != 3 else '#c03030', align='left')
            if i in (0, 1):
                ink.line([(40, 62 + i * 22), (60 + len(t) * 7, 60 + i * 22)], color='#c03030', width=2)
        sticky(ink, W - 60, 90, 44, '#ffe36a', 8, text='NO!', seed=3)
        ink.painted(rrect(40, H - 22, W - 40, H - 12, 3), '#8a8e96', width=2)
        for i, c in enumerate(['#2a4ad0', '#c03030', '#2a9a4a']):
            ink.painted(rrect(60 + i * 30, H - 28, 84 + i * 30, H - 20, 3), c, width=1.4)
        return ink.image()
    if name == 'stickies':
        ink, W, H = canvas(2.4, 1.8)
        texts = ['ASAP', 'v2?', 'MVP', 'ROI', '!!!', 'nice to have', 'KPI', 'pivot', 'later', 'URGENT', 'why?', 'sync']
        for i in range(22):
            x, y = rnd.uniform(30, W - 30), rnd.uniform(30, H - 30)
            sticky(ink, x, y, 40, rnd.choice(STICKY), rnd.uniform(-14, 14), text=rnd.choice(texts) if rnd.random() < 0.5 else None, seed=i)
        return ink.image()
    if name == 'projector':
        ink, W, H = canvas(2.6, 2.0)
        ink.painted(rrect(10, 4, W - 10, 18, 6), '#6a6a72', width=2.2)
        scr = rrect(20, 18, W - 20, H - 30, 2)
        ink.painted(scr, '#f6f6f2', width=2.2, light=0.05)
        ink.fill(ellipse(W / 2, H / 2, W * 0.42, H * 0.38), '#fff8d0', 60)
        cx, cy, r = W * 0.36, H * 0.5, 64
        import skia
        start = -90
        for frac, c, label in ((0.55, '#d03a2a', 'scope creep'), (0.3, '#ffb020', 'meetings'), (0.15, '#3a9a5a', 'work')):
            path = skia.Path()
            path.moveTo(cx, cy)
            path.arcTo(skia.Rect.MakeLTRB(cx - r, cy - r, cx + r, cy + r), start, frac * 360, False)
            path.close()
            ink.painted(path, c, width=2)
            start += frac * 360
        for i, (c, label) in enumerate((('#d03a2a', 'scope creep'), ('#ffb020', 'meetings'), ('#3a9a5a', 'actual work'))):
            ink.fill(rrect(W * 0.62, H * 0.36 + i * 28, W * 0.62 + 16, H * 0.36 + i * 28 + 16, 2), c)
            ink.text(label, W * 0.62 + 26, H * 0.36 + i * 28 + 8, 14, align='left')
        ink.painted(rrect(W / 2 - 4, H - 30, W / 2 + 4, H - 6, 2), '#6a6a72', width=1.6)
        return ink.image()
    if name == 'gantt':
        ink, W, H = canvas(3.0, 1.9)
        board(ink, 6, 6, W - 10, H - 12, face='#fbf8ee')
        ink.text('PROJECT PLAN (BASELINE 14)', W / 2, 28, 16, font='Bangers-Regular.ttf')
        tasks = ['Kickoff', 'Requirements', 'Design', 'Build', 'Test', 'Go-live']
        for i, t in enumerate(tasks):
            y = 56 + i * 26
            ink.text(t, 24, y, 12, align='left')
            x0 = 110 + i * 32 + rnd.uniform(-6, 6)
            w = rnd.uniform(60, 120)
            bar = rrect(x0, y - 8, x0 + w, y + 8, 3)
            ink.painted(bar, ['#4a8ad0', '#4a8ad0', '#ffb020', '#d03a2a', '#d03a2a', '#8a8a90'][i], width=1.6)
            if i in (3, 4):
                ink.painted(rrect(x0 + w, y - 5, x0 + w + 60, y + 5, 3), '#ff8a7a', width=1.2)   # the slip
        tx = W * 0.62
        ink.line([(tx, 44), (tx, H - 24)], color='#d03030', width=2.4)
        ink.text('TODAY', tx, H - 18, 11, color='#d03030', font='Bangers-Regular.ttf')
        diamond = poly([(W - 50, 190), (W - 42, 198), (W - 50, 206), (W - 58, 198)])
        ink.painted(diamond, '#2a2a2a', width=1.4)
        return ink.image()
    if name == 'rag':
        ink, W, H = canvas(1.6, 1.6)
        board(ink, 6, 6, W - 10, H - 12, frame='#3a3a42')
        ink.text('PROJECT STATUS', W / 2, 28, 14, font='Bangers-Regular.ttf')
        rows = [('Budget', '#d03a2a'), ('Scope', '#d03a2a'), ('Time', '#d03a2a'), ('Morale', '#ffb020'), ('Report', '#3ad05a')]
        for i, (t, c) in enumerate(rows):
            y = 56 + i * 26
            ink.text(t, 30, y, 13, align='left')
            ink.painted(ellipse(W - 44, y, 9, 9), c, width=1.6)
        ink.text('(watermelon: green outside, red inside)', W / 2, H - 26, 8, color='#5a4a44')
        return ink.image()
    if name == 'risk':
        ink, W, H = canvas(1.6, 1.6)
        board(ink, 6, 6, W - 10, H - 12)
        ink.text('RISK MATRIX', W / 2, 26, 14, font='Bangers-Regular.ttf')
        n = 5
        cs = (W - 60) / n
        for i in range(n):
            for j in range(n):
                v = (i + (n - 1 - j)) / (2 * n - 2)
                c = mix(mix('#5ac05a', '#ffd040', min(1, v * 2)), '#e04030', max(0, v * 2 - 1))
                ink.fill(rrect(32 + i * cs, 44 + j * cs, 32 + (i + 1) * cs - 2, 44 + (j + 1) * cs - 2, 2), c)
        ink.painted(ellipse(32 + 4.5 * cs, 44 + 0.5 * cs, 8, 8), '#2a2a2a', width=1.4)
        ink.text('us', 32 + 4.5 * cs, 44 + 0.5 * cs + 14, 10, color='#fbf8ee')
        return ink.image()
    if name == 'portrait':
        ink, W, H = canvas(1.2, 1.5)
        ink.cast_shadow(rrect(6, 6, W - 6, H - 6, 4), 5, 6, 90, 6)
        ink.painted(rrect(6, 6, W - 6, H - 6, 4), '#d4a838', width=2.8, light=0.4)
        ink.gradient(rrect(20, 20, W - 20, H - 20, 2), '#4a3a4a', '#1e1620', angle=90)
        cx = W / 2
        ink.painted(smooth([(cx - 40, H - 20), (cx - 30, H - 70), (cx + 30, H - 70), (cx + 40, H - 20)]), '#1e2438', width=2)
        ink.painted(ellipse(cx, H * 0.42, 24, 30), '#e0b088', width=2)
        ink.painted(ellipse(cx + 18, H * 0.44, 9, 7), '#e0b088', width=1.8)
        ink.painted(smooth([(cx - 24, H * 0.36), (cx - 16, H * 0.22), (cx + 16, H * 0.22), (cx + 22, H * 0.34), (cx, H * 0.28)]), '#9a9aa2', width=1.8)
        ink.fill(ellipse(cx + 6, H * 0.4, 3, 3), '#2a1a14')
        ink.line([(cx, H * 0.53), (cx + 14, H * 0.52)], width=1.8)
        ink.painted(rrect(cx - 30, H - 34, cx + 30, H - 24, 2), '#d4a838', width=1.4)
        return ink.image()
    if name == 'kpi':
        ink, W, H = canvas(2.6, 1.6)
        tv = rrect(6, 6, W - 6, H - 12, 6)
        ink.cast_shadow(tv, 5, 6, 90, 6)
        ink.painted(tv, '#1a1a20', width=2.6)
        scr = rrect(18, 18, W - 18, H - 24, 3)
        ink.gradient(scr, '#14304a', '#0a1828', angle=90)
        ink.text('KPI DASHBOARD', W / 2, 36, 15, color='#9ad8ff', font='Bangers-Regular.ttf')
        for i, (t, v) in enumerate((('Synergy', '+412%'), ('Buzzwords', '+999%'), ('Profit', '+0.3%'))):
            x = 50 + i * (W - 100) / 3 + 30
            ink.text(t, x, 70, 12, color='#c8e0f0')
            ink.text(v, x, 96, 20, color='#7fe0a0', font='Bangers-Regular.ttf')
        pts = [(40 + i * (W - 80) / 9, H - 46 - (i ** 1.7) * 3 - rnd.uniform(0, 6)) for i in range(10)]
        ink.line(pts, color='#7fe0a0', width=3)
        ink.line([pts[-1], (pts[-1][0] - 10, pts[-1][1] + 2)], color='#7fe0a0', width=3)
        return ink.image()
    if name == 'orgchart':
        ink, W, H = canvas(2.2, 1.6)
        board(ink, 6, 6, W - 10, H - 12)
        ink.text('ORG CHART', W / 2, 26, 14, font='Bangers-Regular.ttf')
        boxes = [(W / 2, 54, 'CEO')] + [(W * (0.2 + i * 0.3), 104, t) for i, t in enumerate(['VP', 'VP', 'VP'])]
        boxes += [(W * (0.1 + i * 0.2), 152, t) for i, t in enumerate(['PM', 'dev', 'dev', 'QA', 'you'])]
        for x, y, t in boxes[1:4]:
            ink.line([(W / 2, 64), (x, y - 10)], width=1.6)
        for i, (x, y, t) in enumerate(boxes[4:]):
            ink.line([(W * (0.2 + (i // 2) * 0.3), 114), (x, y - 10)], width=1.4)
        for x, y, t in boxes:
            ink.painted(rrect(x - 28, y - 10, x + 28, y + 10, 3), '#ffd060' if t == 'CEO' else '#cfe0f0', width=1.6)
            ink.text(t, x, y, 11)
        return ink.image()

    # ---- floor props (pivot at the bottom)
    if name in ('desk_dev', 'desk_qa'):
        ink, W, H = canvas(2.4, 2.0)
        floor = H - 6
        top = floor - 0.82 * U
        # chair behind the desk
        ink.painted(rrect(W * 0.58, top - 70, W * 0.82, top + 6, 14), '#3a3a44', width=2.4)
        ink.painted(rrect(14, top, W - 14, top + 16, 3), '#c8935a', light=0.3, width=2.4)
        ink.painted(rrect(22, top + 16, 34, floor, 2), '#5a5a62', width=2)
        ink.painted(rrect(W - 34, top + 16, W - 22, floor, 2), '#5a5a62', width=2)
        ink.painted(rrect(W - 120, top + 16, W - 40, floor - 4, 3), '#a8744a', width=2.2)
        for yy in (top + 50, top + 80):
            ink.line([(W - 116, yy), (W - 44, yy)], width=1.6)
        # monitors
        for i, mx in enumerate((W * 0.32, W * 0.62)):
            mon = rrect(mx - 50, top - 92, mx + 50, top - 22, 4)
            ink.painted(rrect(mx - 6, top - 24, mx + 6, top - 4, 2), '#2a2a30', width=1.8)
            ink.painted(rrect(mx - 22, top - 6, mx + 22, top + 1, 2), '#2a2a30', width=1.8)
            ink.painted(mon, '#2a2a30', width=2.4)
            sc = rrect(mx - 43, top - 85, mx + 43, top - 29, 2)
            ink.fill(sc, '#102030' if name == 'desk_dev' else '#181818')
            if name == 'desk_dev':
                for k in range(6):
                    ink.line([(mx - 38 + (k % 3) * 6, top - 78 + k * 8), (mx - 38 + (k % 3) * 6 + rnd.uniform(20, 60), top - 78 + k * 8)],
                             color=rnd.choice(['#7fd8a0', '#ffd070', '#7fb8ff', '#ff8a8a']), width=1.6)
            else:
                for k in range(6):
                    ok = rnd.random() < 0.3
                    ink.text(('PASS' if ok else 'FAIL'), mx - 20, top - 78 + k * 8, 7, color='#5ad05a' if ok else '#ff4a3a', align='left')
        # keyboard, mug, rubber duck / bug spray
        ink.painted(rrect(W * 0.38, top - 6, W * 0.62, top + 1, 2), '#d8d8d0', width=1.6)
        mug = rrect(W * 0.15, top - 26, W * 0.15 + 22, top, 3)
        ink.painted(mug, '#f6f2ea', width=2)
        ink.text('#1 PM', W * 0.15 + 11, top - 13, 6, color='#c03030')
        if name == 'desk_dev':
            ink.painted(ellipse(W * 0.82, top - 12, 12, 11), '#ffd030', width=2)
            ink.painted(ellipse(W * 0.82 + 8, top - 24, 8, 7), '#ffd030', width=2)
            ink.painted(ellipse(W * 0.82 + 15, top - 22, 5, 2.5), '#ff8a20', width=1.4)
            for i in range(3):
                ink.painted(rrect(W * 0.07 + i * 4, top - 30 - i * 3, W * 0.07 + 30 + i * 4, top - 24 - i * 3, 2), '#e8b060', width=1.4)
        else:
            ink.painted(rrect(W * 0.8, top - 36, W * 0.8 + 16, top, 4), '#3aa05a', width=2)
            ink.text('BUG', W * 0.8 + 8, top - 18, 6, color='#ffffff', font='Bangers-Regular.ttf', rotate=-90)
        return ink.image()
    if name == 'chair':
        ink, W, H = canvas(1.0, 1.5)
        f = H - 6
        ink.painted(rrect(W * 0.25, f - 140, W * 0.75, f - 60, 14), '#3a3a44', width=2.4)
        ink.painted(rrect(W * 0.18, f - 66, W * 0.82, f - 48, 8), '#4a4a54', width=2.4)
        ink.painted(rrect(W / 2 - 5, f - 48, W / 2 + 5, f - 18, 2), '#7a7a82', width=1.8)
        ink.line([(W * 0.15, f - 8), (W / 2, f - 18), (W * 0.85, f - 8)], width=4)
        for x in (W * 0.15, W * 0.85, W / 2):
            ink.painted(ellipse(x, f - 5, 6, 5), '#2a2a2a', width=1.4)
        return ink.image()
    if name == 'server':
        ink, W, H = canvas(1.0, 2.3)
        f = H - 6
        rack = rrect(12, 20, W - 12, f, 4)
        ink.cast_shadow(rack, 5, 4, 80, 5)
        ink.painted(rack, '#2a2e3a', width=2.6)
        for y in range(36, f - 20, 22):
            ink.painted(rrect(22, y, W - 22, y + 16, 2), '#3a404e', width=1.4, grain=False)
            for x in range(30, W - 40, 9):
                c = rnd.choice(['#5af07a', '#5af07a', '#ffb030', '#3a3a44'])
                ink.fill(ellipse(x, y + 8, 2.4, 2.4), c)
        ink.painted(rrect(W * 0.3, 4, W * 0.7, 22, 3), '#f6f2ea', width=1.6)
        ink.text('DO NOT TOUCH', W / 2, 13, 8, color='#c03030', font='Bangers-Regular.ttf')
        return ink.image()
    if name == 'plant':
        ink, W, H = canvas(1.0, 1.7)
        f = H - 6
        for i in range(9):
            a = math.radians(-160 + i * 17 + rnd.uniform(-6, 6))
            L = rnd.uniform(70, 120)
            tip = (W / 2 + math.cos(a) * L * 0.6, f - 70 + math.sin(a) * L)
            mid = (W / 2 + math.cos(a) * L * 0.3, f - 70 + math.sin(a) * L * 0.55)
            leaf = limb([(W / 2, f - 66), mid, tip], [3, 9, 1.5])
            ink.painted(leaf, rnd.choice(['#4a8a3a', '#5a9a40', '#3a7a34']), width=2)
        pot = smooth([(W * 0.28, f - 74), (W * 0.72, f - 74), (W * 0.64, f), (W * 0.36, f)], tension=0.2)
        ink.cast_shadow(pot, 4, 3, 80, 4)
        ink.painted(pot, '#c0663a', width=2.4)
        ink.painted(rrect(W * 0.24, f - 82, W * 0.76, f - 68, 4), '#d47a4a', width=2.2)
        ink.painted(rrect(W * 0.4, f - 40, W * 0.6, f - 26, 2), '#fbf8ee', width=1.4, shadow=False)
        ink.text('Kevin', W / 2, f - 33, 8)
        return ink.image()
    if name == 'trash':
        ink, W, H = canvas(0.7, 0.9)
        f = H - 6
        for i in range(5):
            ink.painted(ellipse(W / 2 + rnd.uniform(-20, 20), f - 70 + rnd.uniform(-10, 4), 14, 12), '#f4f0e4', width=1.6)
        can = smooth([(W * 0.2, f - 70), (W * 0.8, f - 70), (W * 0.72, f), (W * 0.28, f)], tension=0.1)
        ink.painted(can, '#7a8a9a', width=2.4)
        for x in (W * 0.35, W * 0.5, W * 0.65):
            ink.line([(x, f - 64), (x, f - 6)], width=1.4, alpha=150)
        ink.painted(rrect(W * 0.6, f - 20, W * 0.6 + 26, f - 4, 2), '#fbf8ee', width=1.4)
        ink.text('plan v1', W * 0.6 + 13, f - 12, 6)
        return ink.image()
    if name == 'cooler':
        ink, W, H = canvas(0.8, 1.9)
        f = H - 6
        body = rrect(W * 0.2, f - 130, W * 0.8, f, 6)
        ink.cast_shadow(body, 4, 3, 80, 4)
        ink.painted(body, '#e8e8e4', width=2.4)
        bottle = smooth([(W * 0.26, f - 134), (W * 0.74, f - 134), (W * 0.76, f - 190), (W * 0.62, f - 214), (W * 0.38, f - 214),
                         (W * 0.24, f - 190)], tension=0.4)
        ink.painted(bottle, '#8ac8f0', width=2.2, light=0.35)
        ink.fill(ellipse(W * 0.38, f - 190, 5, 14), '#ffffff', 120)
        ink.painted(ellipse(W * 0.38, f - 96, 6, 6), '#3a7ad0', width=1.6)
        ink.painted(ellipse(W * 0.62, f - 96, 6, 6), '#d03a3a', width=1.6)
        ink.painted(rrect(W * 0.6, f - 76, W * 0.6 + 14, f - 58, 2), '#f6f2ea', width=1.4)
        return ink.image()
    if name == 'printer':
        ink, W, H = canvas(1.3, 1.3)
        f = H - 6
        ink.painted(rrect(14, f - 60, W - 14, f, 4), '#8a8a92', width=2.4)
        body = rrect(10, f - 128, W - 10, f - 60, 6)
        ink.painted(body, '#d8d8d0', width=2.4)
        ink.fill(rrect(30, f - 112, 110, f - 88, 3), '#1a2a1a')
        ink.text('PC LOAD LETTER', 70, f - 100, 8, color='#7aff7a')
        for i in range(4):
            ink.painted(poly([(W - 80 + i * 6, f - 128 - i * 4), (W - 30 + i * 6, f - 130 - i * 6), (W - 26 + i * 6, f - 160 - i * 10),
                              (W - 76 + i * 6, f - 156 - i * 8)]), '#fbf8ee', width=1.4, shadow=False)
        ink.painted(rrect(W - 70, f - 90, W - 30, f - 80, 2), '#3a3a40', width=1.4)
        return ink.image()
    if name == 'cabinet':
        ink, W, H = canvas(0.9, 1.7)
        f = H - 6
        cab = rrect(10, 26, W - 10, f, 4)
        ink.cast_shadow(cab, 5, 4, 80, 5)
        ink.painted(cab, '#8a929e', width=2.4)
        for i in range(4):
            y = 36 + i * ((f - 46) / 4)
            ink.painted(rrect(18, y, W - 18, y + (f - 46) / 4 - 8, 3), '#9aa2ae', width=1.8)
            ink.painted(rrect(W / 2 - 14, y + 10, W / 2 + 14, y + 16, 2), '#3a3a44', width=1.2, grain=False)
            ink.painted(rrect(W / 2 - 16, y + 22, W / 2 + 16, y + 32, 1), '#fbf8ee', width=1, shadow=False)
            ink.text(['2019', 'LOST', 'TPS', '???'][i], W / 2, y + 27, 7)
        ink.painted(rrect(20, 8, 48, 28, 2), '#fbf8ee', width=1.6)
        ink.painted(rrect(56, 0, 80, 28, 3), '#d03a3a', width=1.6)
        return ink.image()
    if name == 'flipchart':
        ink, W, H = canvas(1.2, 2.0)
        f = H - 6
        for a, b in (((W / 2, f - 120), (W * 0.15, f)), ((W / 2, f - 120), (W * 0.85, f)), ((W / 2, f - 120), (W / 2, f))):
            ink.line([a, b], color='#6a6a72', width=4)
        sheet_ = rrect(16, 20, W - 16, f - 90, 3)
        ink.painted(sheet_, '#fbf8ee', width=2.4, light=0.05)
        ink.painted(rrect(10, 12, W - 10, 26, 4), '#3a3a44', width=2)
        ink.text('Q4 PRIORITIES', W / 2, 44, 13, color='#2a4ad0')
        for i, t in enumerate(['1. everything', '2. also everything', '3. ???']):
            ink.text(t, 26, 70 + i * 20, 11, align='left', color='#2a2a2a')
        ink.text('PROFIT', W / 2, f - 112, 16, color='#2a9a4a', rotate=-4)
        return ink.image()
    if name == 'coffee':
        ink, W, H = canvas(1.0, 1.7)
        f = H - 6
        ink.painted(rrect(8, f - 70, W - 8, f, 4), '#6a4a3a', width=2.4)
        mach = rrect(16, f - 190, W - 16, f - 70, 8)
        ink.painted(mach, '#2a2a30', width=2.4)
        ink.fill(rrect(30, f - 170, W - 30, f - 140, 3), '#5a7a9a')
        ink.painted(rrect(W / 2 - 18, f - 120, W / 2 + 18, f - 84, 2), '#141418', width=1.8)
        ink.painted(rrect(W / 2 - 32, f - 206, W / 2 + 32, f - 180, 3), '#fbf8ee', width=1.6, shadow=False)
        ink.text('OUT OF ORDER', W / 2, f - 193, 8, color='#c03030', font='Bangers-Regular.ttf', rotate=-5)
        return ink.image()
    if name == 'globe':
        ink, W, H = canvas(0.9, 1.6)
        f = H - 6
        ink.painted(smooth([(W * 0.3, f), (W * 0.7, f), (W * 0.56, f - 30), (W * 0.44, f - 30)]), '#7a4a28', width=2.2)
        ink.line([(W / 2, f - 30), (W / 2, f - 70)], color='#7a4a28', width=5)
        g = ellipse(W / 2, f - 120, 46, 46)
        ink.painted(g, '#3a7ac0', width=2.4, light=0.3)
        for (cx, cy, rx, ry) in ((-14, -14, 16, 12), (14, 10, 12, 16), (-4, 20, 8, 6)):
            ink.painted(intersect(ellipse(W / 2 + cx, f - 120 + cy, rx, ry), g), '#5aa04a', width=1.6, shadow=False)
        ink.stroke(smooth([(W / 2 - 52, f - 128), (W / 2, f - 176), (W / 2 + 52, f - 112)], closed=False), '#c9a227', width=3)
        return ink.image()
    if name == 'binders':
        ink, W, H = canvas(1.1, 1.8)
        f = H - 6
        shelf = rrect(8, 10, W - 8, f, 4)
        ink.cast_shadow(shelf, 5, 4, 80, 5)
        ink.painted(shelf, '#5a3420', width=2.4)
        for row in range(3):
            y0, y1 = 22 + row * ((f - 34) / 3), 22 + (row + 1) * ((f - 34) / 3) - 10
            x = 18
            while x < W - 30:
                bw = rnd.uniform(14, 20)
                c = rnd.choice(['#2a4a8a', '#8a2a2a', '#2a6a3a', '#c8a030', '#5a5a62'])
                ink.painted(rrect(x, y0 + rnd.uniform(0, 8), x + bw, y1, 2), c, width=1.6)
                ink.painted(ellipse(x + bw / 2, y1 - 16, 4, 4), '#fbf8ee', width=1, grain=False)
                x += bw + 2
            ink.painted(rrect(12, y1, W - 12, y1 + 8, 1), '#7a4a2a', width=1.6)
        ink.painted(rrect(W * 0.2, 22, W * 0.8, 40, 2), '#fbf8ee', width=1.4, shadow=False)
        ink.text('RISK REGISTER', W / 2, 31, 8, color='#c03030', font='Bangers-Regular.ttf')
        return ink.image()
    if name == 'trophy':
        ink, W, H = canvas(0.8, 1.6)
        f = H - 6
        ink.painted(rrect(10, f - 80, W - 10, f, 4), '#2a2236', width=2.4)
        cup = smooth([(W * 0.22, f - 170), (W * 0.78, f - 170), (W * 0.66, f - 120), (W * 0.34, f - 120)], tension=0.4)
        for d in (-1, 1):
            ink.stroke(ellipse(W / 2 + d * W * 0.34, f - 150, 12, 16), '#e8b830', width=5)
        ink.painted(cup, '#f0c030', width=2.4, light=0.45)
        ink.painted(rrect(W / 2 - 6, f - 122, W / 2 + 6, f - 96, 2), '#e8b830', width=2)
        ink.painted(rrect(W * 0.3, f - 98, W * 0.7, f - 84, 2), '#e8b830', width=2)
        ink.painted(rrect(W * 0.2, f - 60, W * 0.8, f - 40, 2), '#d8b448', width=1.6)
        ink.text('SYNERGY 2026', W / 2, f - 50, 7, font='Bangers-Regular.ttf')
        return ink.image()
    if name == 'aquarium':
        ink, W, H = canvas(1.8, 1.7)
        f = H - 6
        ink.painted(rrect(14, f - 90, W - 14, f, 4), '#2a2236', width=2.4)
        tank = rrect(8, f - 200, W - 8, f - 90, 4)
        ink.gradient(tank, '#5ac0e0', '#2a6a9a', angle=90)
        for i in range(3):
            fx, fy = rnd.uniform(40, W - 50), rnd.uniform(f - 180, f - 120)
            fish = union(ellipse(fx, fy, 16, 9), poly([(fx - 12, fy), (fx - 28, fy - 10), (fx - 28, fy + 10)]))
            ink.painted(fish, rnd.choice(['#ff8a2a', '#ffd040', '#ff5a8a']), width=1.8)
            ink.fill(ellipse(fx + 8, fy - 2, 2, 2), '#1a1a1a')
        ink.painted(smooth([(10, f - 98), (W * 0.3, f - 112), (W * 0.6, f - 104), (W - 10, f - 114), (W - 10, f - 92), (10, f - 92)], tension=0.4),
                    '#e0c890', width=1.4, shadow=False)
        ink.painted(rrect(W * 0.6, f - 130, W * 0.6 + 40, f - 104, 2), '#8a6a4a', width=1.6)
        ink.text('ROI', W * 0.6 + 20, f - 117, 9, color='#fbf8ee')
        ink.stroke(tank, width=2.6)
        ink.fill(rrect(16, f - 196, 30, f - 96, 3), '#ffffff', 50)
        return ink.image()
    if name == 'golf':
        ink, W, H = canvas(1.6, 0.8)
        f = H - 6
        ink.painted(smooth([(10, f), (W - 10, f), (W - 20, f - 18), (20, f - 20)], tension=0.4), '#4aa04a', width=2.2)
        ink.fill(ellipse(W - 50, f - 12, 10, 4), '#1a1a1a')
        ink.line([(W - 50, f - 12), (W - 50, f - 70)], width=2)
        ink.painted(poly([(W - 50, f - 70), (W - 20, f - 62), (W - 50, f - 54)]), '#d03030', width=1.6)
        ink.painted(ellipse(40, f - 22, 6, 6), '#fbf8ee', width=1.4)
        ink.text('BOARD MEETING', W / 2 - 10, f - 40, 9, color='#2a2a2a', font='Bangers-Regular.ttf')
        return ink.image()
    raise KeyError(name)


def curtain(key):
    th = THEMES[key]
    U = PPU
    W, H = int(0.9 * U), int(5.6 * U)
    ink = Ink(W, H, scale=1.0)
    body = smooth([(4, 0), (W - 4, 0), (W - 20, H * 0.45), (W - 6, H - 4), (8, H - 4), (22, H * 0.45)], tension=0.3)
    ink.painted(body, th['carpet'], width=2.6, light=0.25)
    for x in (W * 0.3, W * 0.5, W * 0.7):
        ink.line([(x, 6), (x - 6, H * 0.45), (x, H - 10)], color=shade(th['carpet'], -0.35), width=2, alpha=200)
    ink.painted(rrect(14, H * 0.43, W - 14, H * 0.47, 6), th['trim'], width=2)
    return ink.image()


# ---------------------------------------------------------------- pickups, door, papers, fx

def items():
    out = {}
    U = PPU
    ink = Ink(int(0.7 * U), int(0.8 * U))
    W, H = int(0.7 * U), int(0.8 * U)
    mug = rrect(14, 30, W - 26, H - 6, 6)
    ink.stroke(ellipse(W - 24, H * 0.6, 14, 16), INK, width=9)
    ink.stroke(ellipse(W - 24, H * 0.6, 14, 16), '#f6f2ea', width=5)
    ink.painted(mug, '#f6f2ea', width=2.4)
    ink.fill(ellipse((14 + W - 26) / 2, 32, (W - 40) / 2, 5), '#5a3418')
    ink.text('I <3 GANTT', (14 + W - 26) / 2, H * 0.62, 9, color='#c03030', font='Bangers-Regular.ttf')
    for x in (W * 0.35, W * 0.55):
        ink.line([(x, 24), (x + 5, 14), (x - 2, 4)], color='#ffffff', width=2.2, alpha=200)
    out['coffee'] = ink.image()

    W, H = int(0.95 * U), int(0.75 * U)
    ink = Ink(W, H)
    paper = smooth([(10, 12), (W - 10, 8), (W - 6, H - 10), (8, H - 6)], tension=0.1)
    ink.painted(paper, '#f2e2b0', width=2.4, light=0.2)
    for i, c in enumerate(['#4a8ad0', '#ffb020', '#d03a2a', '#3a9a5a']):
        x0 = 20 + i * 12
        ink.painted(rrect(x0, 20 + i * 12, x0 + 40, 28 + i * 12, 2), c, width=1.4)
    ink.text('GANTT', W / 2, H - 16, 14, font='Bangers-Regular.ttf', color='#c03030')
    out['gantt'] = ink.image()

    W, H = int(0.85 * U), int(0.85 * U)
    ink = Ink(W, H)
    cube = rrect(8, 8, W - 8, H - 8, 10)
    ink.painted(cube, '#bfe8ff', width=2.4, light=0.35)
    ink.painted(rrect(W * 0.3, H * 0.25, W * 0.7, H * 0.75, 2), '#fbf8ee', width=1.6, shadow=False)
    ink.text('SCOPE', W / 2, H * 0.42, 10, font='Bangers-Regular.ttf', color='#2a4a8a')
    ink.text('LOCKED', W / 2, H * 0.58, 10, font='Bangers-Regular.ttf', color='#2a4a8a')
    ink.fill(rrect(14, 14, 24, H - 30, 4), '#ffffff', 120)
    out['freeze'] = ink.image()

    for open_ in (False, True):
        W, H = int(1.6 * U), int(2.9 * U)
        ink = Ink(W, H)
        frame = rrect(6, 36, W - 6, H - 2, 4)
        ink.painted(frame, '#6a4a32', width=2.6)
        inner = rrect(20, 50, W - 20, H - 2, 2)
        if open_:
            ink.gradient(inner, '#fff8d8', '#ffe8a0', angle=90)
            ink.painted(smooth([(20, 50), (64, 62), (64, H - 2), (20, H - 2)], tension=0.05), '#5a8a5a', width=2.2)
        else:
            ink.painted(inner, '#8a5a3a', width=2.2)
            ink.painted(rrect(W * 0.3, 90, W * 0.7, 150, 3), '#fbf8ee', width=1.6, shadow=False)
            ink.text('MEETING', W / 2, 108, 13, font='Bangers-Regular.ttf', color='#c03030')
            ink.text('IN PROGRESS', W / 2, 130, 11, font='Bangers-Regular.ttf', color='#c03030')
            ink.painted(ellipse(W - 40, H * 0.6, 7, 7), '#e8c040', width=1.6)
        sign = rrect(W * 0.2, 4, W * 0.8, 32, 4)
        ink.painted(sign, '#3ac05a' if open_ else '#d03a2a', width=2.2)
        ink.text('EXIT', W / 2, 18, 18, font='Bangers-Regular.ttf', color='#ffffff')
        out['door_open' if open_ else 'door_closed'] = ink.image()

    for kind, c in (('memo', '#fce8a0'), ('bug', '#fbf7ea'), ('budget', '#f4f0e0'), ('invite', '#e8eef8')):
        W, H = int(1.0 * U), int(0.4 * U)
        ink = Ink(W, H)
        ink.painted(rrect(4, 4, W - 4, H - 4, 3), c, width=2.4, light=0.15)
        if kind == 'invite':
            ink.line([(4, 4), (W / 2, H * 0.6), (W - 4, 4)], color='#7a8ab0', width=1.8)
        if kind == 'bug':
            ink.painted(ellipse(W - 16, H / 2, 7, 8), '#d03a2a', width=1.4)
        if kind == 'budget':
            ink.painted(rrect(8, 8, 18, H - 8, 2), '#3aa05a', width=1.2)
        out['paper_' + kind] = ink.image()

    W = H = 40
    ink = Ink(W, H)
    star = poly([(20, 0), (25, 15), (40, 20), (25, 25), (20, 40), (15, 25), (0, 20), (15, 15)])
    ink.fill(star, '#ffffff')
    out['spark'] = ink.image()

    W, H = 160, 160
    ink = Ink(W, H)
    import skia
    arc = skia.Path()
    arc.addArc(skia.Rect.MakeLTRB(-60, 10, W - 20, H - 10), -70, 140)
    ink.c.drawPath(arc, skia.Paint(AntiAlias=True, Color=skia.ColorWHITE, Style=skia.Paint.kStroke_Style, StrokeWidth=26,
                                   StrokeCap=skia.Paint.kRound_Cap, MaskFilter=skia.MaskFilter.MakeBlur(skia.kNormal_BlurStyle, 4)))
    out['smear'] = ink.image()
    return out
