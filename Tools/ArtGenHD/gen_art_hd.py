"""Generates the hand-drawn art style into Assets/Resources/ArtHD. Run from anywhere:

    python3 -m venv Tools/ArtGen/.venv && Tools/ArtGen/.venv/bin/pip install pillow numpy skia-python
    Tools/ArtGen/.venv/bin/python Tools/ArtGenHD/gen_art_hd.py

The layout matches the pixel style (Tools/ArtGen) so the game can switch between them; the manifest
tells the game the scale, camera zoom, font and room geometry of this style.
"""
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from PIL import Image  # noqa: E402

import characters_hd as ch  # noqa: E402
import environment_hd as env  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, '..', '..', 'Assets', 'Resources', 'ArtHD'))
FONTS = os.path.abspath(os.path.join(HERE, '..', '..', 'Assets', 'Resources', 'Fonts'))
COLUMNS = 6   # frames per row in the character sheets (keeps textures under 4096 px wide)


def save(img, rel):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path, optimize=True)


def grid(frames, cell, columns):
    rows = (len(frames) + columns - 1) // columns
    out = Image.new('RGBA', (cell[0] * min(columns, len(frames)), cell[1] * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, ((i % columns) * cell[0], (i // columns) * cell[1]))
    return out


def main():
    manifest = {
        'style': 'hd', 'ppu': ch.PPU, 'wallPpu': env.WALL_PPU, 'farPpu': env.FAR_PPU,
        'viewHeight': 7.0, 'pixelPerfect': False, 'propScale': 1.2,
        'wallPropY': env.WALL['prop_y'], 'curtainTop': env.WALL['curtain_top'], 'curtainX': env.WALL['curtain_x'], 'font': 'Kalam-Bold',
        'characters': [], 'levels': [],
    }

    for name, spec in ch.CAST.items():
        frames, cell = ch.sheet(spec)
        save(grid(frames, cell, COLUMNS), f'Characters/{name}.png')
        fig = ch.Figure(spec, ch.pixel_poses()['idle0'])
        feet = int(round(cell[1] - fig.oy))
        manifest['characters'].append({'name': name, 'cellW': cell[0], 'cellH': cell[1], 'feet': feet,
                                       'columns': COLUMNS, 'frames': ch.FRAMES})
        print('character', name, cell)
    frames, cell = ch.committee_sheet()
    save(grid(frames, cell, 3), 'Characters/committee.png')
    manifest['characters'].append({'name': 'committee', 'cellW': cell[0], 'cellH': cell[1], 'feet': 6,
                                   'columns': 3, 'frames': ch.COMMITTEE_FRAMES})

    for key, th in env.THEMES.items():
        save(env.far(key), f'Levels/{key}/far.png')
        save(env.wall(key), f'Levels/{key}/wall.png')
        fill, top, desk = env.tiles(key)
        save(fill, f'Levels/{key}/fill.png')
        save(top, f'Levels/{key}/top.png')
        save(desk, f'Levels/{key}/desk.png')
        for p in sorted(set(th['floor_props'] + th['wall_props'])):
            save(env.prop(p, key), f'Levels/{key}/{p}.png')
        if th.get('curtains'):
            save(env.curtain(key), f'Levels/{key}/curtain.png')
        manifest['levels'].append({'key': key, 'floorProps': th['floor_props'], 'wallProps': th['wall_props'],
                                   'curtains': bool(th.get('curtains')), 'ceiling': th['trim']})
        print('level', key)

    for name, img in env.items().items():
        folder = 'Fx' if name in ('spark', 'smear') else 'Items'
        save(img, f'{folder}/{name}.png')

    os.makedirs(FONTS, exist_ok=True)
    for f in ('Kalam-Bold.ttf', 'Kalam-OFL.txt'):
        shutil.copy(os.path.join(HERE, 'fonts', f), os.path.join(FONTS, f))

    with open(os.path.join(ROOT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print('wrote', ROOT)


if __name__ == '__main__':
    main()
