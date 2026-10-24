using System.Collections.Generic;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// On-screen buttons for phones and tablets: a d-pad on the left, action buttons on the right and
    /// pause / fullscreen / language at the top. Shows up on mobile browsers or as soon as the screen is
    /// touched; <see cref="GameInput"/> merges it with the keyboard.
    /// </summary>
    [DefaultExecutionOrder(-100)] // read the touches before anything asks GameInput
    public class TouchControls : MonoBehaviour
    {
        enum B { Left, Right, Down, Jump, Attack, Heavy, Special, Pause, Fullscreen, Lang, Style }

        public static bool Active { get; private set; }

        public static float Horizontal => (Held(B.Right) ? 1f : 0f) - (Held(B.Left) ? 1f : 0f);
        public static bool Down => Held(B.Down);
        public static bool JumpPressed => Pressed(B.Jump);
        public static bool JumpHeld => Held(B.Jump);
        public static bool AttackPressed => Pressed(B.Attack);
        public static bool HeavyPressed => Pressed(B.Heavy);
        public static bool SpecialPressed => Pressed(B.Special);
        public static bool PausePressed => Pressed(B.Pause);
        public static bool FullscreenPressed => Pressed(B.Fullscreen);
        public static bool LanguagePressed => Pressed(B.Lang);
        public static bool StylePressed => Pressed(B.Style);
        /// <summary>A tap anywhere that isn't on a button: "press Enter" on menus.</summary>
        public static bool TapPressed { get; private set; }

        /// <summary>Phone held upright: the game wants landscape.</summary>
        public static bool Portrait => Active && Screen.height > Screen.width;

        const float RefHeight = 720f; // same GUI space as the HUD

        static readonly HashSet<B> held = new(), wasHeld = new();
        static readonly Dictionary<B, Rect> rects = new();
        static Texture2D circle, triangle;

        static bool Held(B b) => held.Contains(b);
        static bool Pressed(B b) => held.Contains(b) && !wasHeld.Contains(b);

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (FindAnyObjectByType<TouchControls>() == null)
                DontDestroyOnLoad(new GameObject("TouchControls").AddComponent<TouchControls>().gameObject);
        }

        void Awake()
        {
            Active = Application.isMobilePlatform;
            Input.multiTouchEnabled = true;
        }

        float Scale => Screen.height / RefHeight;

        void Layout()
        {
            rects.Clear();
            float W = Screen.width / Scale, H = RefHeight;
            float big = 120f, mid = 96f, gap = 14f, edge = 28f;

            // d-pad: left / right side by side, down tucked between and below
            rects[B.Left] = new Rect(edge, H - edge - big - 40f, big, big);
            rects[B.Right] = new Rect(edge + big + gap + 10f, H - edge - big - 40f, big, big);
            rects[B.Down] = new Rect(edge + (big + gap + 10f) / 2f + (big - mid * 0.7f) / 2f, H - edge - mid * 0.7f + 6f, mid * 0.7f, mid * 0.7f);

            // actions: jump is the big one in the corner, the others around it
            float jx = W - edge - big, jy = H - edge - big;
            rects[B.Jump] = new Rect(jx, jy, big, big);
            rects[B.Attack] = new Rect(jx - mid - gap, jy + big - mid, mid, mid);
            rects[B.Heavy] = new Rect(jx + big - mid, jy - mid - gap, mid, mid);
            rects[B.Special] = new Rect(jx - mid - gap, jy - mid - gap, mid, mid);

            // small buttons along the top centre, clear of the HUD in the corners
            float s = 64f;
            float x0 = W / 2f - (s * 4f + gap * 3f) / 2f;
            rects[B.Pause] = new Rect(x0, 12f, s, s);
            rects[B.Fullscreen] = new Rect(x0 + s + gap, 12f, s, s);
            rects[B.Lang] = new Rect(x0 + 2f * (s + gap), 12f, s, s);
            rects[B.Style] = new Rect(x0 + 3f * (s + gap), 12f, s, s);
        }

        void Update()
        {
            wasHeld.Clear();
            wasHeld.UnionWith(held);
            held.Clear();
            TapPressed = false;

            if (Input.touchCount > 0) Active = true;
            if (!Active) return;

            Layout();
            float sc = Scale;
            for (int i = 0; i < Input.touchCount; i++)
            {
                var t = Input.GetTouch(i);
                if (t.phase == TouchPhase.Ended || t.phase == TouchPhase.Canceled) continue;
                // screen space has y up, GUI space y down
                var p = new Vector2(t.position.x / sc, (Screen.height - t.position.y) / sc);
                bool onButton = false;
                foreach (var kv in rects)
                {
                    if (!Visible(kv.Key)) continue;
                    // a little slack around each button so thumbs don't slip off
                    var r = kv.Value;
                    var grown = new Rect(r.x - 12f, r.y - 12f, r.width + 24f, r.height + 24f);
                    if (!grown.Contains(p)) continue;
                    held.Add(kv.Key);
                    onButton = true;
                }
                if (!onButton && t.phase == TouchPhase.Began) TapPressed = true;
            }
        }

        /// <summary>Gameplay buttons only show while playing; menus are a tap anywhere.</summary>
        static bool Visible(B b)
        {
            if (b == B.Fullscreen || b == B.Lang || b == B.Style) return true;
            var gm = GameManager.Instance;
            return gm != null && (gm.State == GameState.Playing || gm.State == GameState.Paused);
        }

        void OnGUI()
        {
            if (!Active) return;
            GUI.depth = -10; // above the HUD
            var sc = Scale;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(sc, sc, 1f));
            float W = Screen.width / sc;

            if (Portrait)
            {
                GUI.DrawTexture(new Rect(0, 0, W, RefHeight), Texture2D.whiteTexture, ScaleMode.StretchToFill, false, 0f,
                    new Color(0.05f, 0.03f, 0.1f, 0.92f), 0f, 0f);
                Label(new Rect(0, RefHeight * 0.4f, W, 120), Loc.Get("ui.rotate"), 40, Color.white);
                return;
            }

            Layout();
            var gm = GameManager.Instance;
            var pm = PlayerController.Instance;

            if (Visible(B.Jump))
            {
                Button(B.Left, rects[B.Left], 180f);
                Button(B.Right, rects[B.Right], 0f);
                Button(B.Down, rects[B.Down], 90f);
                Button(B.Jump, rects[B.Jump], -90f);
                Button(B.Attack, rects[B.Attack], null, Loc.Get("touch.attack"));
                Button(B.Heavy, rects[B.Heavy], null, null, Art.Load("Items/gantt")?.texture);
                // the special costs caffeine: dim the button until there's enough
                bool ready = pm == null || pm.Energy >= PlayerController.SpecialCost;
                Button(B.Special, rects[B.Special], null, null, Art.Load("Items/coffee")?.texture, ready ? 1f : 0.35f);
                Button(B.Pause, rects[B.Pause], null, gm.State == GameState.Paused ? ">" : "II");
            }
            Button(B.Fullscreen, rects[B.Fullscreen], null, "[ ]");
            Button(B.Lang, rects[B.Lang], null, Loc.Current == Lang.CS ? "EN" : "CZ");
            Button(B.Style, rects[B.Style], null, "ART");
        }

        // ------------------------------------------------------------------ drawing

        static void Button(B b, Rect r, float? arrow, string text = null, Texture icon = null, float alpha = 1f)
        {
            bool down = Held(b);
            var bg = down ? new Color(1f, 0.85f, 0.4f, 0.55f) : new Color(0.1f, 0.08f, 0.16f, 0.45f);
            bg.a *= alpha;
            GUI.DrawTexture(r, Circle, ScaleMode.StretchToFill, true, 0f, bg, 0f, 0f);
            var fg = new Color(1f, 1f, 1f, (down ? 1f : 0.8f) * alpha);
            var inner = new Rect(r.x + r.width * 0.3f, r.y + r.height * 0.3f, r.width * 0.4f, r.height * 0.4f);
            if (arrow.HasValue)
            {
                var m = GUI.matrix;
                // the pivot is in screen pixels, so undo the GUI scaling
                GUIUtility.RotateAroundPivot(arrow.Value, inner.center * (Screen.height / RefHeight));
                GUI.DrawTexture(inner, Triangle, ScaleMode.StretchToFill, true, 0f, fg, 0f, 0f);
                GUI.matrix = m;
            }
            if (icon)
            {
                var ir = new Rect(r.x + r.width * 0.22f, r.y + r.height * 0.22f, r.width * 0.56f, r.height * 0.56f);
                GUI.DrawTexture(ir, icon, ScaleMode.ScaleToFit, true, 0f, new Color(1f, 1f, 1f, alpha), 0f, 0f);
            }
            if (text != null) Label(r, text, r.height * 0.28f, fg);
        }

        static GUIStyle style;

        static void Label(Rect r, string text, float size, Color color)
        {
            style ??= new GUIStyle(GUI.skin.label) { alignment = TextAnchor.MiddleCenter, fontStyle = FontStyle.Bold, wordWrap = true };
            style.font = Art.Font; // follows the art style
            style.fontSize = Mathf.RoundToInt(size);
            var prev = GUI.color;
            GUI.color = new Color(0f, 0f, 0f, color.a * 0.7f);
            GUI.Label(new Rect(r.x + 2f, r.y + 2f, r.width, r.height), text, style);
            GUI.color = color;
            GUI.Label(r, text, style);
            GUI.color = prev;
        }

        static Texture2D Circle => circle ? circle : circle = MakeTexture(64, (x, y, s) =>
        {
            float d = new Vector2(x + 0.5f - s / 2f, y + 0.5f - s / 2f).magnitude;
            float a = Mathf.Clamp01(s / 2f - d);                      // soft edge
            float ring = d > s / 2f - 3f ? 1f : 0.75f;                 // brighter rim
            return new Color(ring, ring, ring, a);
        });

        static Texture2D Triangle => triangle ? triangle : triangle = MakeTexture(64, (x, y, s) =>
        {
            // pointing right
            float u = (x + 0.5f) / s, v = Mathf.Abs((y + 0.5f) / s - 0.5f) * 2f;
            return new Color(1f, 1f, 1f, u > 0.12f && v < 1f - u + 0.12f && u < 0.92f ? 1f : 0f);
        });

        static Texture2D MakeTexture(int s, System.Func<int, int, int, Color> f)
        {
            var tex = new Texture2D(s, s, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp };
            for (int y = 0; y < s; y++)
                for (int x = 0; x < s; x++)
                    tex.SetPixel(x, y, f(x, y, s));
            tex.Apply();
            return tex;
        }
    }
}
