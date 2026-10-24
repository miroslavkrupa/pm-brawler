using UnityEngine;

namespace PMBrawler
{
    public struct BuiltLevel
    {
        public Vector2 playerStart;
        public float width;
        public ExitDoor exit;
        public Color ceiling;
    }

    /// <summary>Turns a LevelDef's text map into colliders, enemies, pickups and the office around them.</summary>
    public static class LevelBuilder
    {
        static readonly string[] Posters =
        {
            "Q3 OKRs", "SYNERGY\n+200%", "DEADLINE:\nFRIDAY", "AGILE!!!", "BUDGET: 0", "KPI", "ROADMAP\nv17", "SPRINT 47", "ROI?"
        };

        const float Segment = 8f;      // one wall tile = one window, 8 units wide
        const float WallHeight = 14f;
        const float FarParallax = 0.8f;

        public static BuiltLevel Build(LevelDef def, Transform root)
        {
            var result = new BuiltLevel();
            int h = def.map.Length;
            int w = 0;
            foreach (var row in def.map) w = Mathf.Max(w, row.Length);
            result.width = w;

            for (int r = 0; r < h; r++)
            {
                string row = def.map[r];
                int y = h - 1 - r;
                for (int x = 0; x < row.Length; x++)
                {
                    char ch = row[x];
                    if (ch == '#' || ch == '=')
                    {
                        int start = x;
                        while (x + 1 < row.Length && row[x + 1] == ch) x++;
                        BuildSolid(root, def, start, x - start + 1, r, ch == '=');
                        continue;
                    }

                    var feet = new Vector2(x + 0.5f, y + 0.05f);
                    switch (ch)
                    {
                        case 'P': result.playerStart = feet + Vector2.up * 0.95f; break;
                        case 'E': result.exit = ExitDoor.Create(new Vector2(x + 0.5f, y), root); break;
                        case 'D': Enemy.Spawn<Developer>(feet + Vector2.up * 0.9f, root); break;
                        case 'T': Enemy.Spawn<Tester>(feet + Vector2.up * 0.9f, root); break;
                        case 'S': Enemy.Spawn<Stakeholder>(feet + Vector2.up * 0.95f, root); break;
                        case 'F': Enemy.Spawn<Cfo>(feet + Vector2.up * 0.95f, root); break;
                        case 'B': Enemy.Spawn<SteeringCommittee>(feet + Vector2.up * 1.35f, root); break;
                        case 'C': Enemy.Spawn<Ceo>(feet + Vector2.up * 1.2f, root); break;
                        case 'c': Pickup.Spawn(PickupKind.Coffee, feet + Vector2.up * 0.5f, root); break;
                        case 'g': Pickup.Spawn(PickupKind.Gantt, feet + Vector2.up * 0.5f, root); break;
                        case 'f': Pickup.Spawn(PickupKind.ScopeFreeze, feet + Vector2.up * 0.5f, root); break;
                    }
                }
            }

            result.ceiling = BuildDecor(def, root, w);
            return result;
        }

        static void BuildSolid(Transform root, LevelDef def, int x, int len, int r, bool oneWay)
        {
            string level = def.key;
            int y = def.map.Length - 1 - r;
            bool bottomRow = r == def.map.Length - 1;
            var go = new GameObject(oneWay ? "Platform" : "Ground");
            go.transform.SetParent(root, false);
            var solid = go.AddComponent<Solid>();
            solid.oneWay = oneWay;
            var col = go.AddComponent<BoxCollider2D>();

            if (oneWay)
            {
                // a row of desks: the top board is the platform, drawers hang below it
                go.transform.position = new Vector2(x + len / 2f, y + 0.8f);
                col.size = new Vector2(len, 0.4f);
                col.usedByEffector = true;
                var eff = go.AddComponent<PlatformEffector2D>();
                eff.useOneWay = true;
                eff.surfaceArc = 160f;
                var desk = Art.Load($"Levels/{level}/desk", new Vector2(0.5f, 1f));
                for (int i = 0; i < len; i++)
                    Art.Place("Desk", go.transform, desk, new Vector2(i - (len - 1) / 2f, 0.2f), 5);
            }
            else
            {
                go.transform.position = new Vector2(x + len / 2f, y + 0.5f);
                col.size = new Vector2(len, 1f);
                var top = Art.Load($"Levels/{level}/top");
                var fill = Art.Load($"Levels/{level}/fill");
                for (int i = 0; i < len; i++)
                {
                    float lx = i - (len - 1) / 2f;
                    int depth = DepthBelowSurface(def, x + i, r);
                    Art.Place("Tile", go.transform, depth == 0 ? top : fill, new Vector2(lx, 0f), 5).color = Shade(depth);
                    // keep the floor going below the bottom of the map so the camera never sees under it
                    if (bottomRow)
                        for (int d = 1; d <= 3; d++)
                            Art.Place("Tile", go.transform, fill, new Vector2(lx, -d), 5).color = Shade(depth + d);
                }
            }
        }

        /// <summary>
        /// The room: a parallax view of the outside, a wall with windows, props and posters.
        /// Returns the colour for the camera background (the dark ceiling above the wall).
        /// </summary>
        static Color BuildDecor(LevelDef def, Transform root, int width)
        {
            var decor = new GameObject("Decor").transform;
            decor.SetParent(root, false);
            var info = Art.Level(def.key);
            float floorY = MainFloor(def);
            float wallBottom = floorY - 1f;

            // far layer: a panorama that scrolls slower than the room
            var far = new GameObject("Far").transform;
            far.SetParent(decor, false);
            far.gameObject.AddComponent<Parallax>().factor = FarParallax;
            var farSprite = Art.Load($"Levels/{def.key}/far", Vector2.zero);
            if (farSprite)
            {
                float fw = farSprite.bounds.size.x;
                for (float x = -48f; x < width * (1f - FarParallax) + 48f; x += fw)
                    Art.Place("View", far, farSprite, new Vector2(x, wallBottom), -40);
            }

            var wall = Art.Load($"Levels/{def.key}/wall", Vector2.zero);
            var rnd = new System.Random(def.key.GetHashCode());
            string[] wallProps = info?.wallProps ?? new string[0];
            string[] floorProps = info?.floorProps ?? new string[0];
            int wallIndex = 0, floorIndex = 0;
            for (int k = -3; k * Segment < width + 24f; k++)
            {
                float x0 = k * Segment;
                if (wall) Art.Place("Wall", decor, wall, new Vector2(x0, wallBottom), -30);
                if (k < 0 || x0 + Segment > width + 4) continue;

                // curtains frame every window in the posh rooms
                if (info != null && info.curtains)
                {
                    var curtain = Art.Load($"Levels/{def.key}/curtain", new Vector2(0.5f, 1f));
                    float cx = Art.CurtainX, top = wallBottom + Art.CurtainTop;
                    Art.Place("Curtain", decor, curtain, new Vector2(x0 + cx, top), -18);
                    Art.Place("Curtain", decor, curtain, new Vector2(x0 + Segment - cx, top), -18).flipX = true;
                }

                // one prop on the wall between the windows...
                if (k > 0 && wallProps.Length > 0)
                {
                    string p = wallProps[wallIndex++ % wallProps.Length];
                    var sr = Art.Place(p, decor, Art.Load($"Levels/{def.key}/{p}"), new Vector2(x0, wallBottom + Art.WallPropY), -20);
                    if (p == "poster") // the pixel posters are blank; the hand-drawn ones have their own text
                        Art.Text(Posters[rnd.Next(Posters.Length)], sr.transform, new Vector2(0, -0.02f), 0.26f,
                            Art.Hex("#3a2a30"), -19);
                }

                // ...and usually one standing on the floor under the window
                if (floorProps.Length > 0)
                {
                    string p = floorProps[floorIndex++ % floorProps.Length];
                    float px = x0 + Segment * 0.5f + (float)(rnd.NextDouble() - 0.5) * 3f;
                    float ground = SurfaceAt(def, Mathf.FloorToInt(px));
                    if (ground >= 0f && rnd.NextDouble() >= 0.3)
                    {
                        var sr = Art.Place(p, decor, Art.Load($"Levels/{def.key}/{p}", new Vector2(0.5f, 0f)), new Vector2(px, ground - 0.06f), -10);
                        sr.transform.localScale = Vector3.one * Art.PropScale;
                    }
                }
            }

            var trim = info != null ? Art.Hex(info.ceiling) : def.background;
            return Color.Lerp(trim, Color.black, 0.8f);
        }

        /// <summary>Solid tiles get darker the deeper they are under the walkable surface.</summary>
        static Color Shade(int depth) => Color.Lerp(Color.white, Color.black, Mathf.Min(0.75f, depth * 0.2f));

        static int DepthBelowSurface(LevelDef def, int x, int r)
        {
            int d = 0;
            while (r - d - 1 >= 0 && x < def.map[r - d - 1].Length && def.map[r - d - 1][x] == '#') d++;
            return d;
        }

        /// <summary>The height of the ground in a column (top of the solid stack from the bottom row), or -1 over a pit.</summary>
        static float SurfaceAt(LevelDef def, int x)
        {
            int h = def.map.Length;
            int n = 0;
            for (int r = h - 1; r >= 0; r--)
            {
                string row = def.map[r];
                if (x < 0 || x >= row.Length || row[x] != '#') break;
                n++;
            }
            return n == 0 ? -1f : n;
        }

        static float MainFloor(LevelDef def)
        {
            var counts = new System.Collections.Generic.Dictionary<float, int>();
            int w = def.map[def.map.Length - 1].Length;
            for (int x = 1; x < w - 1; x++)
            {
                float s = SurfaceAt(def, x);
                if (s < 0f) continue;
                counts[s] = counts.TryGetValue(s, out var c) ? c + 1 : 1;
            }
            float best = 3f;
            int most = 0;
            foreach (var kv in counts)
                if (kv.Value > most) { most = kv.Value; best = kv.Key; }
            return best;
        }
    }
}
