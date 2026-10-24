"""Generates every sprite in Assets/Resources/Art. Run from anywhere:

    python3 -m venv .venv && .venv/bin/pip install pillow numpy
    .venv/bin/python Tools/ArtGen/gen_art.py

The game loads these at runtime through Art.cs; the frame layout is written to Art/manifest.json.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from characters import CAST, COMMITTEE_FRAMES, FRAMES, committee_sheet, sheet  # noqa: E402
from environment import THEMES, door, floor_tiles, panorama, paper, pickups, prop, smear, spark, wall_tile  # noqa: E402
from pixel import strip  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'Assets', 'Resources', 'Art'))


def save(img, rel):
    path = os.path.join(ROOT, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)


def main():
    manifest = {'characters': [], 'levels': []}

    for name, spec in CAST.items():
        save(strip(sheet(spec)), f'Characters/{name}.png')
        manifest['characters'].append({'name': name, 'cellW': spec.cell[0], 'cellH': spec.cell[1], 'feet': 2,
                                       'frames': FRAMES})
    save(strip(committee_sheet()), 'Characters/committee.png')
    manifest['characters'].append({'name': 'committee', 'cellW': 128, 'cellH': 96, 'feet': 2,
                                   'frames': COMMITTEE_FRAMES})

    for key, th in THEMES.items():
        save(panorama(key), f'Levels/{key}/far.png')
        save(wall_tile(key), f'Levels/{key}/wall.png')
        fill, top, desk = floor_tiles(key)
        save(fill, f'Levels/{key}/fill.png')
        save(top, f'Levels/{key}/top.png')
        save(desk, f'Levels/{key}/desk.png')
        for p in sorted(set(th['props'])):
            save(prop(p, key), f'Levels/{key}/{p}.png')
        manifest['levels'].append({'key': key, 'props': th['props'], 'ceiling': th['trim']})

    for name, img in pickups().items():
        save(img, f'Items/{name}.png')
    save(door(False), 'Items/door_closed.png')
    save(door(True), 'Items/door_open.png')
    for kind in ('memo', 'bug', 'budget', 'invite'):
        save(paper(kind), f'Items/paper_{kind}.png')
    save(spark(), 'Fx/spark.png')
    save(smear(), 'Fx/smear.png')

    with open(os.path.join(ROOT, 'manifest.json'), 'w') as f:
        json.dump(manifest, f, indent=1)
    print('wrote', ROOT)


if __name__ == '__main__':
    main()
