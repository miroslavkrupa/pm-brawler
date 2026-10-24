using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Final boss. Phase 1: synergy dash and memos. Below 50%: pivots (reverses your controls),
    /// launches strategic initiatives (summons developers) and leaps for a shockwave slam.
    /// Below 25% everything gets faster.
    /// </summary>
    public class Ceo : Enemy
    {
        int phase = 1, pattern;
        readonly List<Enemy> minions = new();

        protected override void Configure()
        {
            SetupBody(new Art.Look
            {
                size = new Vector2(1.2f, 2.3f),
                body = Art.Hex("#14213d"),
                legs = Art.Hex("#000000"),
                head = Art.Skin,
                accent = Art.Hex("#fca311"),
                accessory = "crown"
            }, 650f, Team.Enemy);
            NameKey = "enemy.ceo";
            quoteKey = "quote.ceo";
            IsBoss = true;
            superArmor = true;
            speed = 3f;
            aggroRange = 11f;
            attackCooldown = 1.5f;
            attackDamage = 16f;
            score = 5000;
        }

        protected override void OnAggro() => Say(Loc.Random("quote.ceo"), 2.5f);

        protected override void Update()
        {
            if (!Hp.IsDead)
            {
                float ratio = Hp.Current / Hp.max;
                if (phase == 1 && ratio <= 0.5f)
                {
                    phase = 2;
                    Say(Loc.Get("quote.ceo.phase2"), 2.5f);
                    Fx.Shake(0.4f, 0.5f);
                    cooldown = 0.5f;
                }
                else if (phase == 2 && ratio <= 0.25f)
                {
                    phase = 3;
                    speed *= 1.4f;
                    attackCooldown *= 0.65f;
                    Fx.Shake(0.4f, 0.5f);
                }
            }
            base.Update();
        }

        protected override void Think()
        {
            FaceTowards(P.transform.position);
            if (Mathf.Abs(Dx) > 4f) WalkTowards(DirToPlayer, speed);
            else Move(0f);
            if (cooldown > 0f) return;

            minions.RemoveAll(m => m == null || m.Hp.IsDead);
            if (phase == 1)
            {
                pattern = (pattern + 1) % 2;
                StartCoroutine(pattern == 0 ? SynergyDash() : Memos());
            }
            else
            {
                pattern = (pattern + 1) % 4;
                if (pattern == 2 && minions.Count >= 2) pattern = 3;
                StartCoroutine(pattern switch { 0 => Pivot(), 1 => SynergyDash(), 2 => Initiative(), _ => ShockwaveSlam() });
            }
        }

        IEnumerator SynergyDash()
        {
            busy = true;
            Say(Loc.Get("quote.ceo").Split('|')[0], 1f); // "Synergy!"
            yield return Windup(0.5f);
            bool hit = false;
            float t = 0f;
            while (t < 0.55f && !hit)
            {
                Move(Facing * 13f);
                hit = MeleeHit(new Vector2(0.6f, 0f), new Vector2(1.3f, 2f), new DamageInfo
                {
                    amount = attackDamage,
                    knockback = new Vector2(10f, 7f),
                    stun = 0.5f
                }) > 0;
                t += Time.deltaTime;
                yield return null;
            }
            Move(0f);
            yield return new WaitForSeconds(0.4f);
            Done();
        }

        IEnumerator Memos()
        {
            busy = true;
            yield return Windup(0.4f);
            for (int i = 0; i < 3; i++)
            {
                FaceTowards(P.transform.position);
                Projectile.Spawn(Center + new Vector2(Facing * 0.7f, 0.6f), new Vector2(Facing * 9f, 1.5f), 2f, "proj.memo",
                    Color.white, new DamageInfo { amount = 9f, knockback = new Vector2(4f, 3f), stun = 0.2f },
                    ProjectileEffect.None, Team.Enemy, gameObject);
                yield return new WaitForSeconds(0.25f);
            }
            Done();
        }

        IEnumerator Pivot()
        {
            busy = true;
            Say(Loc.Get("quote.ceo.pivot"), 1.5f);
            yield return Windup(0.5f);
            Fx.Shake(0.3f, 0.3f);
            P.Reverse(3.5f);
            Fx.FloatText(Loc.Get("ui.status.reverse"), P.Center + Vector2.up * 1.4f, Art.Hex("#ff6b6b"), 0.4f, 1.5f);
            Done();
        }

        IEnumerator Initiative()
        {
            busy = true;
            Say(Loc.Get("quote.ceo.summon"), 1.5f);
            yield return Windup(0.6f);
            for (int i = 0; i < 2; i++)
            {
                var pos = (Vector2)transform.position + new Vector2((i == 0 ? -1 : 1) * 3f, 2f);
                minions.Add(Spawn<Developer>(pos, transform.parent));
                Fx.Burst(pos, Art.Hex("#3d5a80"), 12);
            }
            Done();
        }

        IEnumerator ShockwaveSlam()
        {
            busy = true;
            yield return Windup(0.4f);
            Rb.linearVelocity = new Vector2(Mathf.Clamp(Dx, -6f, 6f), 15f);
            yield return new WaitForSeconds(0.3f);
            float t = 0f;
            while (!Grounded && t < 2f) { t += Time.deltaTime; yield return null; }
            Rb.linearVelocity = Vector2.zero;
            Fx.Shake(0.45f, 0.3f);
            var feet = (Vector2)transform.position + Vector2.down * (Height * 0.5f - 0.6f);
            foreach (int dir in new[] { -1, 1 })
                Projectile.Spawn(feet + Vector2.right * dir, new Vector2(dir * 8f, 0f), 0f, "proj.memo", Art.Hex("#fca311"),
                    new DamageInfo { amount = 14f, knockback = new Vector2(6f, 8f), stun = 0.4f },
                    ProjectileEffect.None, Team.Enemy, gameObject);
            Done();
        }

        void Done()
        {
            cooldown = attackCooldown * Random.Range(0.9f, 1.2f);
            busy = false;
        }

        protected override void OnDied()
        {
            foreach (var m in minions)
                if (m != null && !m.Hp.IsDead) m.Hp.Kill();
            Fx.Shake(0.6f, 0.8f);
            base.OnDied();
        }
    }
}
