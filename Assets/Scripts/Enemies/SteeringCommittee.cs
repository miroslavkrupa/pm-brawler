using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Boss of level 4: three people and one table. Sends meeting invites, escalates
    /// (summons stakeholders) and slams the table for a status report.
    /// </summary>
    public class SteeringCommittee : Enemy
    {
        int pattern;
        readonly System.Collections.Generic.List<Enemy> minions = new();

        protected override void Configure()
        {
            SetupBody(new Art.Look
            {
                size = new Vector2(3.6f, 2.6f),
                body = Art.Hex("#6c757d"),
                legs = Art.Hex("#343a40"),
                head = Art.Skin,
                accent = Art.Hex("#c1121f"),
                accessory = "table"
            }, 450f, Team.Enemy);
            NameKey = "enemy.committee";
            quoteKey = "quote.committee";
            IsBoss = true;
            superArmor = true;
            speed = 1.3f;
            aggroRange = 11f;
            attackCooldown = 1.6f;
            attackDamage = 12f;
            score = 2000;
        }

        protected override void OnAggro() => Say(Loc.Random("quote.committee"), 2.5f);

        protected override void Think()
        {
            FaceTowards(P.transform.position);
            if (Mathf.Abs(Dx) > 5f) WalkTowards(DirToPlayer, speed);
            else Move(0f);
            if (cooldown > 0f) return;

            minions.RemoveAll(m => m == null || m.Hp.IsDead);
            pattern = (pattern + 1) % 3;
            if (pattern == 1 && minions.Count >= 2) pattern = 2;
            StartCoroutine(pattern switch { 0 => Invites(), 1 => Escalate(), _ => StatusReportSlam() });
        }

        IEnumerator Invites()
        {
            busy = true;
            yield return Windup(0.5f);
            for (int i = 0; i < 3; i++)
            {
                var from = Center + new Vector2(Facing * 1.5f, 0.8f);
                Projectile.Spawn(from, new Vector2(Facing * 6f, 2f + i * 2.5f), 6f, "proj.invite", Art.Hex("#e9ecef"),
                    new DamageInfo { amount = 8f, knockback = new Vector2(3f, 3f), stun = 0.2f },
                    ProjectileEffect.Slow, Team.Enemy, gameObject);
                yield return new WaitForSeconds(0.15f);
            }
            Done();
        }

        IEnumerator Escalate()
        {
            busy = true;
            Say(Loc.Get("quote.committee.summon"), 1.5f);
            yield return Windup(0.6f);
            for (int i = 0; i < 2; i++)
            {
                var pos = (Vector2)transform.position + new Vector2((i == 0 ? -1 : 1) * 2.5f, 2f);
                var s = Spawn<Stakeholder>(pos, transform.parent);
                minions.Add(s);
                Fx.Burst(pos, Art.Hex("#9d4edd"), 12);
            }
            Done();
        }

        IEnumerator StatusReportSlam()
        {
            busy = true;
            Say(Loc.Get("quote.committee.slam"), 1.5f);
            yield return Windup(0.4f);
            // leap toward the player
            float dx = Mathf.Clamp(Dx, -7f, 7f);
            Rb.linearVelocity = new Vector2(dx / 1.1f, 13f);
            yield return new WaitForSeconds(0.3f);
            float t = 0f;
            while (!Grounded && t < 2f) { t += Time.deltaTime; yield return null; }
            Rb.linearVelocity = Vector2.zero;
            Fx.Shake(0.4f, 0.3f);
            Fx.Burst((Vector2)transform.position + Vector2.down * Height * 0.5f, Art.Hex("#adb5bd"), 20);
            var savedFacing = Facing;
            Face(1);
            MeleeHit(new Vector2(0f, -Height * 0.3f), new Vector2(7f, 1.6f), new DamageInfo
            {
                amount = 22f,
                knockback = new Vector2(10f, 9f),
                stun = 0.6f
            });
            Face(savedFacing);
            Done();
        }

        void Done()
        {
            cooldown = attackCooldown * Random.Range(0.9f, 1.2f);
            busy = false;
        }

        protected override void OnDied()
        {
            // meeting adjourned: everyone they summoned goes home too
            foreach (var m in minions)
                if (m != null && !m.Hp.IsDead) m.Hp.Kill();
            Fx.Shake(0.5f, 0.6f);
            base.OnDied();
        }
    }
}
