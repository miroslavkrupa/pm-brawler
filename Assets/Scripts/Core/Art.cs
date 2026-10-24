using System.Collections.Generic;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Loads the game's art and builds sprites, character figures and world-space text. There are two
    /// styles with the same layout: pixel art in Resources/Art (Tools/ArtGen) and hand-drawn cartoon art in
    /// Resources/ArtHD (Tools/ArtGenHD). Each style's manifest.json gives its scale, camera zoom, font and
    /// room geometry. Plain coloured boxes and circles are still available for effects.
    /// </summary>
    public static class Art
    {
        public enum ArtStyle { HandDrawn, Pixel }

        const string StyleKey = "artStyle";

        static Sprite square, circle;
        static Font font;
        static Material flashMaterial;
        static Manifest manifest;
        static ArtStyle? style;
        static readonly Dictionary<string, Sprite> sprites = new();
        static readonly Dictionary<string, CharacterSheet> sheets = new();

        public static Sprite Square => square ? square : square = MakeSprite(false);
        public static Sprite Circle => circle ? circle : circle = MakeSprite(true);

        /// <summary>The style's font from Resources/Fonts (SIL OFL), falling back to Unity's built-in font.</summary>
        public static Font Font => font ? font : font = Resources.Load<Font>("Fonts/" + Info.font) ?? Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");

        /// <summary>Draws a sprite as a solid white silhouette (vertex colour × texture alpha) for hit flashes.</summary>
        public static Material FlashMaterial => flashMaterial ? flashMaterial : flashMaterial = new Material(Shader.Find("GUI/Text Shader"));

        // ------------------------------------------------------------------ style

        public static ArtStyle Style
        {
            get
            {
                // loaded lazily: PlayerPrefs must not be touched from a static initializer
                style ??= (ArtStyle)PlayerPrefs.GetInt(StyleKey, (int)ArtStyle.HandDrawn);
                return style.Value;
            }
            set
            {
                if (style == value) return;
                style = value;
                PlayerPrefs.SetInt(StyleKey, (int)value);
                // everything cached belongs to the old style
                manifest = null;
                font = null;
                sprites.Clear();
                sheets.Clear();
            }
        }

        public static void ToggleStyle() => Style = Style == ArtStyle.Pixel ? ArtStyle.HandDrawn : ArtStyle.Pixel;

        static string Root => Style == ArtStyle.Pixel ? "Art/" : "ArtHD/";

        /// <summary>Art pixels per world unit for characters, props and tiles.</summary>
        public static float PPU => Info.ppu > 0 ? Info.ppu : 32f;
        /// <summary>Visible world height the camera aims for.</summary>
        public static float ViewHeight => Info.viewHeight > 0 ? Info.viewHeight : 9.5f;
        /// <summary>Pixel art wants whole-pixel zoom and point filtering; hand-drawn art is smooth.</summary>
        public static bool PixelPerfect => Info.pixelPerfect;
        public static float PropScale => Info.propScale > 0 ? Info.propScale : 1f;
        /// <summary>Height of wall props and the top of curtains above the bottom of the wall.</summary>
        public static float WallPropY => Info.wallPropY;
        public static float CurtainTop => Info.curtainTop;
        public static float CurtainX => Info.curtainX;

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

        // ------------------------------------------------------------------ manifest

        [System.Serializable]
        class Manifest
        {
            public string style, font = "PixelifySans";
            public float ppu, wallPpu, farPpu, viewHeight, propScale, wallPropY = 7.6f, curtainTop = 10.75f, curtainX = 1.05f;
            public bool pixelPerfect;
            public CharacterInfo[] characters;
            public LevelInfo[] levels;
        }

        [System.Serializable]
        internal class CharacterInfo
        {
            public string name;
            public int cellW, cellH, feet, columns;
            public string[] frames;
        }

        [System.Serializable]
        public class LevelInfo
        {
            public string key;
            public string[] floorProps, wallProps;
            public bool curtains;
            public string ceiling;
        }

        /// <summary>Animation frames of one character, sliced from its sheet (rows of cells), pivot at the feet.</summary>
        public class CharacterSheet
        {
            readonly Dictionary<string, Sprite> frames = new();

            internal CharacterSheet(Texture2D tex, CharacterInfo info, float ppu)
            {
                var pivot = new Vector2(0.5f, (float)info.feet / info.cellH);
                int columns = info.columns > 0 ? info.columns : info.frames.Length;
                for (int i = 0; i < info.frames.Length; i++)
                {
                    // texture rows count from the bottom, sheet rows from the top
                    int col = i % columns, row = i / columns;
                    var rect = new Rect(col * info.cellW, tex.height - (row + 1) * info.cellH, info.cellW, info.cellH);
                    frames[info.frames[i]] = Sprite.Create(tex, rect, pivot, ppu, 0, SpriteMeshType.FullRect);
                }
            }

            public bool Has(string frame) => frames.ContainsKey(frame);

            public bool Valid
            {
                get
                {
                    foreach (var s in frames.Values) return s;
                    return false;
                }
            }

            /// <summary>The frame, or the closest stand-in when this character doesn't have it (e.g. the committee can't walk).</summary>
            public Sprite Get(string frame)
            {
                if (frames.TryGetValue(frame, out var s)) return s;
                return frames.TryGetValue("idle0", out s) ? s : null;
            }
        }

        static Manifest Info
        {
            get
            {
                if (manifest == null)
                {
                    var json = Resources.Load<TextAsset>(Root + "manifest");
                    manifest = json ? JsonUtility.FromJson<Manifest>(json.text) : new Manifest();
                }
                return manifest;
            }
        }

        static Texture2D Texture(string path)
        {
            var tex = Resources.Load<Texture2D>(Root + path);
            if (tex && PixelPerfect) tex.filterMode = FilterMode.Point;
            return tex;
        }

        /// <summary>The far view and the walls are painted at lower resolutions than the rest.</summary>
        static float PpuFor(string path)
        {
            if (path.EndsWith("/far") && Info.farPpu > 0) return Info.farPpu;
            if (path.EndsWith("/wall") && Info.wallPpu > 0) return Info.wallPpu;
            return PPU;
        }

        /// <summary>
        /// Loads {style root}/{path}.png as a sprite. FullRect sprites can be tiled or 9-sliced; the border is
        /// in world units so it means the same in both styles.
        /// </summary>
        public static Sprite Load(string path, Vector2 pivot, bool fullRect = false, float border = 0f)
        {
            string key = $"{path}|{pivot}|{fullRect}|{border}";
            // cached sprites can be destroyed when Unity unloads unused assets, so check before reusing
            if (sprites.TryGetValue(key, out var s) && s) return s;
            var tex = Texture(path);
            if (tex == null)
            {
                Debug.LogWarning("PM Brawler: missing art " + Root + path + " (run the generator in Tools/)");
                return sprites[key] = null;
            }
            float ppu = PpuFor(path);
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), pivot, ppu, 0,
                fullRect || border > 0f ? SpriteMeshType.FullRect : SpriteMeshType.Tight, Vector4.one * border * ppu);
            return sprites[key] = s;
        }

        public static Sprite Load(string path) => Load(path, new Vector2(0.5f, 0.5f));

        public static CharacterSheet Sheet(string name)
        {
            if (sheets.TryGetValue(name, out var sheet) && sheet != null && sheet.Valid) return sheet;
            sheet = null;
            if (Info.characters != null)
                foreach (var c in Info.characters)
                    if (c.name == name)
                    {
                        var tex = Texture("Characters/" + name);
                        if (tex) sheet = new CharacterSheet(tex, c, PPU);
                    }
            if (sheet == null) Debug.LogWarning("PM Brawler: missing character sheet " + name);
            return sheets[name] = sheet;
        }

        public static LevelInfo Level(string key)
        {
            if (Info.levels != null)
                foreach (var l in Info.levels)
                    if (l.key == key) return l;
            return null;
        }

        /// <summary>A sprite object. Use drawMode Tiled/Sliced with a FullRect sprite and set <paramref name="size"/>.</summary>
        public static SpriteRenderer Place(string name, Transform parent, Sprite sprite, Vector2 localPos, int order,
            SpriteDrawMode mode = SpriteDrawMode.Simple, Vector2 size = default)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPos;
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = sprite;
            sr.sortingOrder = order;
            if (mode != SpriteDrawMode.Simple)
            {
                sr.drawMode = mode;
                sr.size = size;
            }
            return sr;
        }

        // ------------------------------------------------------------------ primitives

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

        /// <summary>Adventure-game style talk text: coloured, with a hard dark outline and no bubble.</summary>
        public static TextMesh OutlinedText(string text, Transform parent, Vector2 localPos, float height, Color color, int order = 50)
        {
            var main = Text(text, parent, localPos, height, color, order + 1);
            float o = height * 0.07f;
            var dark = new Color(0.06f, 0.04f, 0.1f, color.a);
            foreach (var d in new[] { new Vector2(o, 0), new Vector2(-o, 0), new Vector2(0, o), new Vector2(0, -o), new Vector2(o, -o) })
                Text(text, main.transform, d, height, dark, order).transform.localScale = Vector3.one;
            return main;
        }

        public static Color Hex(string hex) => ColorUtility.TryParseHtmlString(hex, out var c) ? c : Color.magenta;

        /// <summary>Visual recipe for a character.</summary>
        public struct Look
        {
            public Vector2 size;    // collider size
            public string sheet;    // sprite strip in Resources/Art/Characters
            public Color speech;    // colour of their talk text
        }

        /// <summary>
        /// Builds a character figure under <paramref name="visual"/> (which sits at the fighter's feet).
        /// Returns all renderers for hit-flash.
        /// </summary>
        public static SpriteRenderer[] BuildCharacter(Transform visual, Look look, out CharacterSheet sheet)
        {
            sheet = Sheet(look.sheet);
            var sr = Place("Body", visual, sheet?.Get("idle0"), Vector2.zero, 2);
            if (sheet == null)
            {
                // art missing: fall back to a box so the game stays playable
                sr.sprite = Square;
                sr.transform.localPosition = new Vector2(0, look.size.y / 2f);
                sr.transform.localScale = look.size;
                sr.color = Color.gray;
            }
            return visual.GetComponentsInChildren<SpriteRenderer>();
        }
    }
}
