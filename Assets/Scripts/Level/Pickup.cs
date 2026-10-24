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
            string art = kind switch { PickupKind.Coffee => "coffee", PickupKind.Gantt => "gantt", _ => "freeze" };
            // a soft glow behind so pickups stand out from the busy backgrounds
            Art.Shape("Glow", go.transform, Vector2.zero, Vector2.one * 0.9f, new Color(1f, 0.95f, 0.6f, 0.18f), 29, true);
            Art.Place("Icon", go.transform, Art.Load("Items/" + art), Vector2.zero, 30);
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
