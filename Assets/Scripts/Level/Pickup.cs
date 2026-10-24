using UnityEngine;

namespace PMBrawler
{
    public enum PickupKind { Coffee, Gantt, ScopeFreeze }

    public class Pickup : MonoBehaviour
    {
        PickupKind kind;
        Vector3 basePos;
        float phase;

        public static Pickup Spawn(PickupKind kind, Vector2 pos, Transform parent)
        {
            var go = new GameObject("Pickup_" + kind);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            switch (kind)
            {
                case PickupKind.Coffee:
                    Art.Shape("Cup", go.transform, Vector2.zero, new Vector2(0.45f, 0.55f), Color.white, 30);
                    Art.Shape("Coffee", go.transform, new Vector2(0, 0.2f), new Vector2(0.38f, 0.1f), Art.Hex("#6f4518"), 31);
                    Art.Shape("Handle", go.transform, new Vector2(0.28f, 0), new Vector2(0.15f, 0.25f), Color.white, 29, true);
                    break;
                case PickupKind.Gantt:
                    Art.Shape("Sheet", go.transform, Vector2.zero, new Vector2(0.8f, 0.6f), Color.white, 30);
                    for (int i = 0; i < 3; i++)
                        Art.Shape("Bar", go.transform, new Vector2(-0.15f + i * 0.12f, 0.17f - i * 0.17f), new Vector2(0.35f, 0.1f), Art.Hex("#4ea8de"), 31);
                    break;
                case PickupKind.ScopeFreeze:
                    Art.Shape("Ice", go.transform, Vector2.zero, new Vector2(0.65f, 0.65f), new Color(0.6f, 0.85f, 1f), 30, true);
                    Art.Text("SCOPE\nFREEZE", go.transform, Vector2.zero, 0.15f, Art.Hex("#1d3557"), 32);
                    break;
            }
            var p = go.AddComponent<Pickup>();
            p.kind = kind;
            p.basePos = pos;
            p.phase = Random.value * 6f;
            return p;
        }

        void Update()
        {
            phase += Time.deltaTime * 3f;
            transform.position = basePos + Vector3.up * Mathf.Sin(phase) * 0.12f;

            var pm = PlayerController.Instance;
            if (pm == null || pm.Hp.IsDead) return;
            if (Vector2.Distance(pm.Center, transform.position) > 0.9f) return;

            switch (kind)
            {
                case PickupKind.Coffee:
                    pm.Hp.Heal(25f);
                    pm.AddEnergy(40f);
                    Fx.FloatText(Loc.Get("pickup.coffee"), transform.position + Vector3.up * 0.6f, Art.Hex("#c08552"), 0.32f, 1.2f);
                    break;
                case PickupKind.Gantt:
                    pm.StartGantt(12f);
                    Fx.FloatText(Loc.Get("pickup.gantt"), transform.position + Vector3.up * 0.6f, Art.Hex("#4ea8de"), 0.32f, 1.4f);
                    break;
                case PickupKind.ScopeFreeze:
                    foreach (var f in Fighter.All)
                        if (f is Enemy e && !e.Hp.IsDead) e.Freeze(e.IsBoss ? 2f : 5f);
                    Fx.FloatText(Loc.Get("pickup.freeze"), transform.position + Vector3.up * 0.6f, Art.Hex("#90e0ef"), 0.45f, 1.4f);
                    Fx.Shake(0.2f, 0.2f);
                    break;
            }
            Fx.Burst(transform.position, Color.white, 10);
            Destroy(gameObject);
        }
    }
}
