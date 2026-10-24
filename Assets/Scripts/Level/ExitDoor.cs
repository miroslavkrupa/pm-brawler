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
            var e = go.AddComponent<ExitDoor>();
            e.door = Art.Place("Door", go.transform, null, Vector2.zero, -1);
            e.label = Art.OutlinedText("", go.transform, new Vector2(0, 3.4f), 0.32f, Color.white, 40);
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
            door.sprite = Art.Load(IsOpen ? "Items/door_open" : "Items/door_closed", new Vector2(0.5f, 0f));
            label.color = IsOpen ? Art.Hex("#8ef0b0") : Art.Hex("#ffb0a0");
            Fx.SetText(label, IsOpen ? Loc.Get("ui.exit") : Loc.Get("ui.exitLocked"));
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
