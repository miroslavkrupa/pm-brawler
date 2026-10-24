using UnityEngine;

namespace PMBrawler
{
    /// <summary>The level exit. Locked until every blocker in the level has been dealt with (the "sign-off").</summary>
    public class ExitDoor : MonoBehaviour
    {
        public bool IsOpen { get; private set; }

        SpriteRenderer door;
        TextMesh label;

        public static ExitDoor Create(Vector2 bottomCenter, Transform parent)
        {
            var go = new GameObject("Exit");
            go.transform.SetParent(parent, false);
            go.transform.position = bottomCenter;
            Art.Shape("Frame", go.transform, new Vector2(0, 1.25f), new Vector2(1.6f, 2.6f), Art.Hex("#495057"), -2);
            var e = go.AddComponent<ExitDoor>();
            e.door = Art.Shape("Door", go.transform, new Vector2(0, 1.2f), new Vector2(1.3f, 2.4f), Art.Hex("#c1121f"), -1);
            e.label = Art.Text("", go.transform, new Vector2(0, 3.1f), 0.32f, Color.white, 40);
            e.Refresh();
            return e;
        }

        public void Open()
        {
            if (IsOpen) return;
            IsOpen = true;
            Refresh();
            Fx.Burst((Vector2)transform.position + Vector2.up * 1.2f, Art.Hex("#52b788"), 20);
        }

        public void Refresh()
        {
            door.color = IsOpen ? Art.Hex("#52b788") : Art.Hex("#c1121f");
            label.text = IsOpen ? Loc.Get("ui.exit") : Loc.Get("ui.exitLocked");
        }

        void Update()
        {
            if (!IsOpen) return;
            var pm = PlayerController.Instance;
            if (pm == null || pm.Hp.IsDead || GameManager.Instance.State != GameState.Playing) return;
            var d = pm.Center - ((Vector2)transform.position + Vector2.up * 1.2f);
            if (Mathf.Abs(d.x) < 0.8f && Mathf.Abs(d.y) < 1.5f) GameManager.Instance.ReachedExit();
        }
    }
}
