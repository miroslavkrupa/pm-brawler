using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Placeholder art generated at runtime: coloured boxes, circles and world-space text.
    /// Swap these for real sprites later without touching gameplay code.
    /// </summary>
    public static class Art
    {
        static Sprite square, circle;
        static Font font;

        public static Sprite Square => square ? square : square = MakeSprite(false);
        public static Sprite Circle => circle ? circle : circle = MakeSprite(true);
        public static Font Font => font ? font : font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        static Sprite MakeSprite(bool round)
        {
            const int s = 32;
            var tex = new Texture2D(s, s, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Bilinear,
                wrapMode = TextureWrapMode.Clamp
            };
            var px = new Color32[s * s];
            float r = s / 2f;
            for (int y = 0; y < s; y++)
                for (int x = 0; x < s; x++)
                {
                    bool inside = !round || new Vector2(x + 0.5f - r, y + 0.5f - r).sqrMagnitude <= r * r;
                    px[y * s + x] = inside ? new Color32(255, 255, 255, 255) : new Color32(255, 255, 255, 0);
                }
            tex.SetPixels32(px);
            tex.Apply();
            return Sprite.Create(tex, new Rect(0, 0, s, s), new Vector2(0.5f, 0.5f), s); // 1 sprite = 1 world unit
        }

        public static SpriteRenderer Shape(string name, Transform parent, Vector2 localPos, Vector2 size, Color color,
            int order = 0, bool round = false)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            go.transform.localScale = new Vector3(size.x, size.y, 1f);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = round ? Circle : Square;
            sr.color = color;
            sr.sortingOrder = order;
            return sr;
        }

        public static TextMesh Text(string text, Transform parent, Vector2 localPos, float height, Color color, int order = 50)
        {
            var go = new GameObject("Text");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var tm = go.AddComponent<TextMesh>();
            tm.font = Font;
            tm.fontSize = 64;
            tm.characterSize = height * 10f / tm.fontSize; // roughly `height` world units per line
            tm.anchor = TextAnchor.MiddleCenter;
            tm.alignment = TextAlignment.Center;
            tm.color = color;
            tm.text = text;
            var mr = go.GetComponent<MeshRenderer>();
            mr.sharedMaterial = Font.material;
            mr.sortingOrder = order;
            return tm;
        }

        public static Color Hex(string hex) => ColorUtility.TryParseHtmlString(hex, out var c) ? c : Color.magenta;

        /// <summary>Visual recipe for a character: body, head, and a small identifying accessory.</summary>
        public struct Look
        {
            public Color body, legs, head, accent;
            public Vector2 size;          // collider size
            public string accessory;     // "tie", "hoodie", "glasses", "suit", "table", "crown"
        }

        public static readonly Color Skin = Hex("#f2c9a0");

        /// <summary>Builds a character figure under <paramref name="visual"/>. Returns all renderers for hit-flash.</summary>
        public static SpriteRenderer[] BuildCharacter(Transform visual, Look look)
        {
            float w = look.size.x, h = look.size.y;
            float legH = h * 0.3f, bodyH = h * 0.42f, headD = h * 0.28f;
            float bottom = -h / 2f;

            if (look.accessory == "table")
            {
                // the Steering Committee: three members behind one long table
                for (int i = -1; i <= 1; i++)
                {
                    float x = i * w * 0.3f;
                    Shape("Member", visual, new Vector2(x, bottom + h * 0.55f), new Vector2(w * 0.24f, h * 0.4f), i == 0 ? look.accent : look.body, 2);
                    Shape("Head", visual, new Vector2(x, bottom + h * 0.85f), new Vector2(w * 0.18f, w * 0.18f), look.head, 3, true);
                    Shape("Eye", visual, new Vector2(x + w * 0.04f, bottom + h * 0.87f), new Vector2(w * 0.03f, w * 0.03f), Color.black, 4, true);
                }
                Shape("Table", visual, new Vector2(0, bottom + h * 0.3f), new Vector2(w, h * 0.12f), Hex("#5a3d2b"), 6);
                Shape("TableLegL", visual, new Vector2(-w * 0.4f, bottom + h * 0.12f), new Vector2(w * 0.06f, h * 0.24f), Hex("#3e2a1d"), 5);
                Shape("TableLegR", visual, new Vector2(w * 0.4f, bottom + h * 0.12f), new Vector2(w * 0.06f, h * 0.24f), Hex("#3e2a1d"), 5);
                Shape("Papers", visual, new Vector2(w * 0.15f, bottom + h * 0.38f), new Vector2(w * 0.2f, h * 0.05f), Color.white, 7);
                return visual.GetComponentsInChildren<SpriteRenderer>();
            }

            Shape("LegL", visual, new Vector2(-w * 0.2f, bottom + legH / 2f), new Vector2(w * 0.3f, legH), look.legs, 1);
            Shape("LegR", visual, new Vector2(w * 0.2f, bottom + legH / 2f), new Vector2(w * 0.3f, legH), look.legs, 1);
            Shape("Body", visual, new Vector2(0, bottom + legH + bodyH / 2f), new Vector2(w, bodyH), look.body, 2);
            var headY = bottom + legH + bodyH + headD / 2f;
            Shape("Head", visual, new Vector2(0, headY), new Vector2(headD, headD), look.head, 3, true);
            // eye on the facing side so you can tell direction
            Shape("Eye", visual, new Vector2(headD * 0.22f, headY + headD * 0.08f), new Vector2(headD * 0.14f, headD * 0.14f), Color.black, 4, true);

            float bodyY = bottom + legH + bodyH / 2f;
            switch (look.accessory)
            {
                case "tie":
                    Shape("Tie", visual, new Vector2(0, bodyY + bodyH * 0.05f), new Vector2(w * 0.14f, bodyH * 0.8f), look.accent, 3);
                    Shape("Clipboard", visual, new Vector2(w * 0.55f, bodyY), new Vector2(w * 0.35f, bodyH * 0.6f), Hex("#a0784a"), 4);
                    break;
                case "hoodie":
                    Shape("Hood", visual, new Vector2(-headD * 0.1f, headY), new Vector2(headD * 1.15f, headD * 1.1f), look.accent, 2, true);
                    Shape("Laptop", visual, new Vector2(w * 0.5f, bodyY - bodyH * 0.1f), new Vector2(w * 0.45f, bodyH * 0.12f), Hex("#9aa3ad"), 4);
                    break;
                case "glasses":
                    Shape("Glasses", visual, new Vector2(headD * 0.2f, headY + headD * 0.08f), new Vector2(headD * 0.55f, headD * 0.2f), look.accent, 5);
                    Shape("Magnifier", visual, new Vector2(w * 0.6f, bodyY + bodyH * 0.2f), new Vector2(w * 0.3f, w * 0.3f), Hex("#bfe3ff"), 4, true);
                    break;
                case "suit":
                    Shape("Lapel", visual, new Vector2(0, bodyY + bodyH * 0.2f), new Vector2(w * 0.3f, bodyH * 0.5f), Color.white, 3);
                    Shape("Tie", visual, new Vector2(0, bodyY + bodyH * 0.1f), new Vector2(w * 0.1f, bodyH * 0.6f), look.accent, 4);
                    break;
                case "crown":
                    Shape("Lapel", visual, new Vector2(0, bodyY + bodyH * 0.2f), new Vector2(w * 0.3f, bodyH * 0.5f), Color.white, 3);
                    Shape("Tie", visual, new Vector2(0, bodyY + bodyH * 0.1f), new Vector2(w * 0.1f, bodyH * 0.6f), look.accent, 4);
                    Shape("Crown", visual, new Vector2(0, headY + headD * 0.6f), new Vector2(headD * 0.8f, headD * 0.35f), Hex("#ffd23f"), 5);
                    Shape("Cigar", visual, new Vector2(headD * 0.55f, headY - headD * 0.15f), new Vector2(headD * 0.4f, headD * 0.1f), Hex("#6b3b1f"), 5);
                    break;
            }
            return visual.GetComponentsInChildren<SpriteRenderer>();
        }
    }
}
