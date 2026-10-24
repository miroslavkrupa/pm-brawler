using UnityEngine;

namespace PMBrawler
{
    public struct BuiltLevel
    {
        public Vector2 playerStart;
        public float width;
        public ExitDoor exit;
    }

    /// <summary>Turns a LevelDef's text map into colliders, enemies, pickups and some office decor.</summary>
    public static class LevelBuilder
    {
        static readonly string[] Posters =
        {
            "Q3 OKRs", "SYNERGY +200%", "DEADLINE: FRIDAY", "AGILE!!!", "BUDGET: 0", "KPI", "ROADMAP v17", "SPRINT 47", "ROI?"
        };

        public static BuiltLevel Build(LevelDef def, Transform root)
        {
            var result = new BuiltLevel();
            int h = def.map.Length;
            int w = 0;
            foreach (var row in def.map) w = Mathf.Max(w, row.Length);
            result.width = w;

            BuildDecor(root, w, def.background);

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
                        bool topRow = r == 0 || def.map[r - 1].Length <= start || def.map[r - 1][start] != '#';
                        BuildSolid(root, start, x - start + 1, y, ch == '=', topRow);
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
            return result;
        }

        static void BuildSolid(Transform root, int x, int len, int y, bool oneWay, bool topRow)
        {
            var go = new GameObject(oneWay ? "Platform" : "Ground");
            go.transform.SetParent(root, false);
            var solid = go.AddComponent<Solid>();
            solid.oneWay = oneWay;
            var col = go.AddComponent<BoxCollider2D>();

            if (oneWay)
            {
                // thin desk-like platform at the top of the tile
                go.transform.position = new Vector2(x + len / 2f, y + 0.8f);
                col.size = new Vector2(len, 0.4f);
                col.usedByEffector = true;
                var eff = go.AddComponent<PlatformEffector2D>();
                eff.useOneWay = true;
                eff.surfaceArc = 160f;
                Art.Shape("Desk", go.transform, Vector2.zero, new Vector2(len, 0.4f), Art.Hex("#bc8a5f"), 5);
                Art.Shape("DeskEdge", go.transform, new Vector2(0, -0.17f), new Vector2(len, 0.06f), Art.Hex("#6f4518"), 6);
            }
            else
            {
                go.transform.position = new Vector2(x + len / 2f, y + 0.5f);
                col.size = new Vector2(len, 1f);
                Art.Shape("Block", go.transform, Vector2.zero, new Vector2(len, 1f), Art.Hex("#4a4e69"), 5);
                if (topRow) Art.Shape("Carpet", go.transform, new Vector2(0, 0.42f), new Vector2(len, 0.16f), Art.Hex("#9a8c98"), 6);
            }
        }

        /// <summary>Cheap office backdrop: windows and motivational posters.</summary>
        static void BuildDecor(Transform root, int width, Color bg)
        {
            var decor = new GameObject("Decor").transform;
            decor.SetParent(root, false);
            var wallTint = Color.Lerp(bg, Color.white, 0.08f);
            var windowTint = Color.Lerp(bg, Art.Hex("#90e0ef"), 0.25f);
            Art.Shape("Wall", decor, new Vector2(width / 2f, 7f), new Vector2(width + 40f, 14f), wallTint, -20);
            for (int x = 6; x < width - 3; x += 9)
            {
                if ((x / 9) % 2 == 0)
                {
                    Art.Shape("Window", decor, new Vector2(x, 8.5f), new Vector2(3f, 2.4f), windowTint, -19);
                    Art.Shape("Mullion", decor, new Vector2(x, 8.5f), new Vector2(0.1f, 2.4f), wallTint, -18);
                }
                else
                {
                    Art.Shape("Poster", decor, new Vector2(x, 7.5f), new Vector2(2.6f, 1.4f), Color.Lerp(bg, Color.white, 0.6f), -19);
                    Art.Text(Posters[Random.Range(0, Posters.Length)], decor, new Vector2(x, 7.5f), 0.35f, Color.Lerp(bg, Color.black, 0.4f), -18);
                }
            }
        }
    }
}
