using UnityEngine;

namespace PMBrawler
{
    public enum ProjectileEffect { None, Slow, DrainEnergy, ReverseControls }

    /// <summary>Bug reports, meeting invites, budget cuts and memos thrown at the PM.</summary>
    public class Projectile : MonoBehaviour
    {
        Vector2 velocity;
        float gravity, life = 6f, radius;
        DamageInfo damage;
        ProjectileEffect effect;
        Team team;

        public static Projectile Spawn(Vector2 pos, Vector2 velocity, float gravity, string labelKey, Color color,
            DamageInfo damage, ProjectileEffect effect, Team team, GameObject source)
        {
            var go = new GameObject("Projectile");
            go.transform.position = pos;
            var label = Loc.Get(labelKey);
            float w = Mathf.Max(0.6f, label.Length * 0.2f + 0.2f);
            Art.Shape("Paper", go.transform, Vector2.zero, new Vector2(w, 0.4f), color, 60);
            Art.Text(label, go.transform, Vector2.zero, 0.26f, Color.black, 61);
            var p = go.AddComponent<Projectile>();
            p.velocity = velocity;
            p.gravity = gravity;
            p.radius = Mathf.Max(0.3f, w * 0.45f);
            damage.source = source;
            p.damage = damage;
            p.effect = effect;
            p.team = team;
            return p;
        }

        void Update()
        {
            float dt = Time.deltaTime;
            velocity += Vector2.down * gravity * dt;
            transform.position += (Vector3)(velocity * dt);
            transform.Rotate(0, 0, -velocity.x * 20f * dt);

            life -= dt;
            if (life <= 0f) { Destroy(gameObject); return; }

            foreach (var c in Physics2D.OverlapCircleAll(transform.position, radius))
            {
                if (c.TryGetComponent<Solid>(out var solid) && !solid.oneWay)
                {
                    Pop();
                    return;
                }
                var hp = c.GetComponentInParent<Health>();
                if (hp == null || hp.team == team) continue;
                damage.sourcePos = (Vector2)transform.position - velocity.normalized;
                if (hp.TakeDamage(damage) && hp.TryGetComponent<PlayerController>(out var pm))
                    pm.ApplyEffect(effect);
                Pop();
                return;
            }
        }

        void Pop()
        {
            Fx.Burst(transform.position, Color.white, 5);
            Destroy(gameObject);
        }
    }
}
