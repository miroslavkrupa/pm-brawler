using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    public enum GameState { Title, Intro, Playing, Paused, LevelComplete, GameOver, Victory }

    /// <summary>
    /// Runs the whole game: state machine, level loading, lives/score and the HUD.
    /// Bootstraps itself into any scene, so pressing Play in an empty scene just works.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }

        public GameState State { get; private set; } = GameState.Title;
        public int LevelIndex { get; private set; }
        public int Score { get; private set; }
        public int Lives { get; private set; } = 3;
        public float KillY => -4f;

        const int StartLives = 3;
        const string BestKey = "best";

        Transform levelRoot;
        ExitDoor exit;
        float introTimer;
        int scoreAtLevelStart;
        Lang lastLang;

        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            if (FindAnyObjectByType<GameManager>() == null)
                new GameObject("GameManager").AddComponent<GameManager>();
        }

        void Awake()
        {
            if (Instance != null && Instance != this) { Destroy(gameObject); return; }
            Instance = this;
            Application.targetFrameRate = 60;

            var cam = Camera.main;
            if (cam == null)
            {
                cam = new GameObject("Main Camera").AddComponent<Camera>();
                cam.tag = "MainCamera";
            }
            cam.clearFlags = CameraClearFlags.SolidColor;
            if (!cam.TryGetComponent<CameraFollow>(out _)) cam.gameObject.AddComponent<CameraFollow>();
            lastLang = Loc.Current;
        }

        void Start()
        {
            LoadLevel(0);
            State = GameState.Title;
        }

        void Update()
        {
            if (GameInput.LanguagePressed) Loc.Toggle();
            if (Loc.Current != lastLang)
            {
                lastLang = Loc.Current;
                if (exit) exit.Refresh();
            }

            switch (State)
            {
                case GameState.Title:
                    if (GameInput.ConfirmPressed)
                    {
                        Score = 0;
                        Lives = StartLives;
                        LoadLevel(0);
                    }
                    break;

                case GameState.Intro:
                    introTimer -= Time.deltaTime;
                    if (introTimer <= 0f || GameInput.ConfirmPressed) State = GameState.Playing;
                    break;

                case GameState.Playing:
                    if (GameInput.PausePressed) { State = GameState.Paused; Time.timeScale = 0f; break; }
                    if (exit && !exit.IsOpen && RemainingEnemies() == 0)
                    {
                        exit.Open();
                        var pm = PlayerController.Instance;
                        if (pm) Fx.FloatText(Loc.Get("ui.exitOpen"), pm.Center + Vector2.up * 1.6f, Art.Hex("#52b788"), 0.4f, 2.5f);
                    }
                    break;

                case GameState.Paused:
                    if (GameInput.PausePressed) { State = GameState.Playing; Time.timeScale = 1f; }
                    break;

                case GameState.LevelComplete:
                    if (GameInput.ConfirmPressed)
                    {
                        if (LevelIndex + 1 < Levels.All.Length) LoadLevel(LevelIndex + 1);
                        else State = GameState.Victory;
                    }
                    break;

                case GameState.GameOver:
                    if (GameInput.ConfirmPressed)
                    {
                        Lives = StartLives;
                        Score = scoreAtLevelStart;
                        LoadLevel(LevelIndex);
                    }
                    break;

                case GameState.Victory:
                    if (GameInput.ConfirmPressed)
                    {
                        LoadLevel(0);
                        State = GameState.Title;
                    }
                    break;
            }
        }

        public void LoadLevel(int index)
        {
            StopAllCoroutines();
            Fx.ResetHitStop();
            Time.timeScale = 1f;
            if (levelRoot) Destroy(levelRoot.gameObject);
            foreach (var p in FindObjectsByType<Projectile>(FindObjectsSortMode.None)) Destroy(p.gameObject);
            foreach (var t in FindObjectsByType<FloatingText>(FindObjectsSortMode.None)) Destroy(t.gameObject);
            Fighter.All.Clear();

            LevelIndex = index;
            scoreAtLevelStart = Score;
            var def = Levels.All[index];
            levelRoot = new GameObject("Level " + (index + 1)).transform;
            var built = LevelBuilder.Build(def, levelRoot);
            exit = built.exit;

            var player = PlayerController.Create(built.playerStart, levelRoot);
            var cam = CameraFollow.Instance;
            cam.GetComponent<Camera>().backgroundColor = built.ceiling;
            cam.target = player.transform;
            cam.SetBounds(built.width, 0f);
            cam.SnapTo(player.transform.position);

            State = GameState.Intro;
            introTimer = 2.5f;
        }

        public int RemainingEnemies()
        {
            int n = 0;
            foreach (var f in Fighter.All)
                if (f is Enemy e && !e.Hp.IsDead) n++;
            return n;
        }

        Enemy ActiveBoss()
        {
            foreach (var f in Fighter.All)
                if (f is Enemy e && e.IsBoss && e.Aggro && !e.Hp.IsDead) return e;
            return null;
        }

        public void AddScore(int points) => Score += points;

        public int Best => PlayerPrefs.GetInt(BestKey, 0);

        void SaveBest()
        {
            if (Score > Best) { PlayerPrefs.SetInt(BestKey, Score); PlayerPrefs.Save(); }
        }

        public void ReachedExit()
        {
            if (State != GameState.Playing) return;
            var pm = PlayerController.Instance;
            Score += 500 + (pm ? Mathf.RoundToInt(pm.Hp.Current) * 5 : 0);
            SaveBest();
            State = GameState.LevelComplete;
        }

        public void OnPlayerDied()
        {
            Lives--;
            StartCoroutine(AfterDeath());
        }

        IEnumerator AfterDeath()
        {
            yield return new WaitForSeconds(1.5f);
            if (Lives > 0) PlayerController.Instance?.Respawn();
            else
            {
                SaveBest();
                State = GameState.GameOver;
            }
        }

        // ------------------------------------------------------------------ HUD

        GUIStyle big, mid, small;
        const float RefHeight = 720f;

        void EnsureStyles()
        {
            if (big != null) return;
            big = new GUIStyle(GUI.skin.label) { font = Art.Font, fontSize = 54, fontStyle = FontStyle.Bold, alignment = TextAnchor.MiddleCenter, wordWrap = true };
            big.normal.textColor = Color.white; // tinted per label via GUI.color
            mid = new GUIStyle(big) { fontSize = 28 };
            small = new GUIStyle(big) { fontSize = 18, fontStyle = FontStyle.Normal };
        }

        void OnGUI()
        {
            EnsureStyles();
            float s = Screen.height / RefHeight;
            GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, new Vector3(s, s, 1f));
            float W = Screen.width / s, H = RefHeight;

            if (State != GameState.Title) DrawHud(W);

            switch (State)
            {
                case GameState.Title:
                    Dim(W, H, 0.55f);
                    Shadow(new Rect(0, H * 0.22f, W, 80), Loc.Get("ui.title"), big, Art.Hex("#ffd23f"));
                    Shadow(new Rect(0, H * 0.22f + 80, W, 40), Loc.Get("ui.subtitle"), mid, Color.white);
                    if (Mathf.Repeat(Time.unscaledTime, 1f) < 0.7f)
                        Shadow(new Rect(0, H * 0.52f, W, 40), Loc.Get("ui.pressStart"), mid, Color.white);
                    Shadow(new Rect(40, H * 0.66f, W - 80, 60), Loc.Get("ui.controls"), small, Art.Hex("#ced4da"));
                    Shadow(new Rect(0, H * 0.78f, W, 30), Loc.Get("ui.lang"), small, Art.Hex("#90e0ef"));
                    Shadow(new Rect(0, H * 0.84f, W, 30), Loc.Get("ui.best", Best), small, Art.Hex("#ced4da"));
                    break;

                case GameState.Intro:
                    Dim(W, H, 0.35f);
                    var key = Levels.All[LevelIndex].key;
                    Shadow(new Rect(0, H * 0.35f, W, 70), Loc.Get(key + ".title"), big, Color.white);
                    Shadow(new Rect(0, H * 0.35f + 75, W, 40), Loc.Get(key + ".sub"), mid, Art.Hex("#ffd23f"));
                    break;

                case GameState.Paused:
                    Dim(W, H, 0.5f);
                    Shadow(new Rect(0, H * 0.4f, W, 70), Loc.Get("ui.paused"), big, Color.white);
                    Shadow(new Rect(0, H * 0.4f + 75, W, 40), Loc.Get("ui.pausedSub"), small, Color.white);
                    break;

                case GameState.LevelComplete:
                    Dim(W, H, 0.5f);
                    Shadow(new Rect(0, H * 0.38f, W, 70), Loc.Get("ui.levelComplete"), big, Art.Hex("#52b788"));
                    Shadow(new Rect(0, H * 0.38f + 75, W, 40), Loc.Get("ui.score", Score), mid, Color.white);
                    Shadow(new Rect(0, H * 0.38f + 125, W, 40), Loc.Get("ui.continue"), small, Color.white);
                    break;

                case GameState.GameOver:
                    Dim(W, H, 0.6f);
                    Shadow(new Rect(0, H * 0.38f, W, 70), Loc.Get("ui.gameover"), big, Art.Hex("#ff6b6b"));
                    Shadow(new Rect(0, H * 0.38f + 75, W, 40), Loc.Get("ui.score", Score), mid, Color.white);
                    Shadow(new Rect(0, H * 0.38f + 125, W, 40), Loc.Get("ui.gameoverSub"), small, Color.white);
                    break;

                case GameState.Victory:
                    Dim(W, H, 0.6f);
                    Shadow(new Rect(0, H * 0.3f, W, 70), Loc.Get("ui.victory"), big, Art.Hex("#ffd23f"));
                    Shadow(new Rect(0, H * 0.3f + 75, W, 40), Loc.Get("ui.victorySub"), mid, Color.white);
                    Shadow(new Rect(0, H * 0.3f + 130, W, 40), Loc.Get("ui.score", Score) + "    " + Loc.Get("ui.best", Best), mid, Color.white);
                    Shadow(new Rect(0, H * 0.3f + 190, W, 40), Loc.Get("ui.victoryHint"), small, Color.white);
                    break;
            }
        }

        void DrawHud(float W)
        {
            var pm = PlayerController.Instance;
            var left = new GUIStyle(small) { alignment = TextAnchor.MiddleLeft };
            var right = new GUIStyle(small) { alignment = TextAnchor.MiddleRight };

            if (pm)
            {
                Shadow(new Rect(20, 14, 200, 22), Loc.Get("ui.hp"), left, Color.white);
                Bar(new Rect(20, 38, 260, 16), pm.Hp.Current / pm.Hp.max, Art.Hex("#e63946"));
                Shadow(new Rect(20, 58, 200, 22), Loc.Get("ui.energy"), left, Color.white);
                Bar(new Rect(20, 82, 260, 12), pm.Energy / PlayerController.MaxEnergy, Art.Hex("#c08552"));
                // tick at the special-move cost
                Fill(new Rect(20 + 260 * PlayerController.SpecialCost / PlayerController.MaxEnergy - 1, 80, 2, 16), Color.white);

                float y = 100;
                if (pm.GanttTimer > 0f) { Shadow(new Rect(20, y, 400, 22), Loc.Get("ui.status.gantt"), left, Art.Hex("#4ea8de")); y += 22; }
                if (pm.ReverseTimer > 0f) { Shadow(new Rect(20, y, 400, 22), Loc.Get("ui.status.reverse"), left, Art.Hex("#ff6b6b")); y += 22; }
                if (pm.IsSlowed) { Shadow(new Rect(20, y, 400, 22), Loc.Get("ui.status.slow"), left, Art.Hex("#ced4da")); }
            }

            Shadow(new Rect(W - 320, 14, 300, 22), Loc.Get("ui.score", Score), right, Color.white);
            Shadow(new Rect(W - 320, 38, 300, 22), Loc.Get("ui.lives", Lives), right, Color.white);
            int remaining = RemainingEnemies();
            Shadow(new Rect(W - 320, 62, 300, 22),
                remaining > 0 ? Loc.Get("ui.remaining", remaining) : Loc.Get("ui.exitOpen"), right,
                remaining > 0 ? Art.Hex("#ffd23f") : Art.Hex("#52b788"));

            var boss = ActiveBoss();
            if (boss)
            {
                float bw = Mathf.Min(600f, W - 80f);
                var r = new Rect((W - bw) / 2f, RefHeight - 60, bw, 18);
                Shadow(new Rect(r.x, r.y - 26, bw, 24), Loc.Get(boss.NameKey), new GUIStyle(small) { fontStyle = FontStyle.Bold }, Color.white);
                Bar(r, boss.Hp.Current / boss.Hp.max, Art.Hex("#9d0208"));
            }
        }

        static void Fill(Rect r, Color c) =>
            GUI.DrawTexture(r, Texture2D.whiteTexture, ScaleMode.StretchToFill, false, 0f, c, 0f, 0f);

        static void Bar(Rect r, float t, Color c)
        {
            Fill(new Rect(r.x - 2, r.y - 2, r.width + 4, r.height + 4), new Color(0, 0, 0, 0.6f));
            Fill(new Rect(r.x, r.y, r.width * Mathf.Clamp01(t), r.height), c);
        }

        static void Dim(float w, float h, float a) => Fill(new Rect(0, 0, w, h), new Color(0, 0, 0, a));

        static void Shadow(Rect r, string text, GUIStyle style, Color color)
        {
            var prev = GUI.color;
            GUI.color = new Color(0, 0, 0, 0.8f);
            GUI.Label(new Rect(r.x + 2, r.y + 2, r.width, r.height), text, style);
            GUI.color = color;
            GUI.Label(r, text, style);
            GUI.color = prev;
        }
    }
}
