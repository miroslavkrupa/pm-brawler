using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>Announces "just one small change" and charges across the room: scope creep in human form.</summary>
    public class Stakeholder : Enemy
    {
        protected override void Configure()
        {
            SetupBody(new Art.Look
            {
                size = new Vector2(1f, 1.8f),
                sheet = "stakeholder",
                speech = Art.Hex("#e0aaff")
            }, 60f, Team.Enemy);
            NameKey = "enemy.stake";
            quoteKey = "quote.stake";
            speed = 2.2f;
            attackDamage = 14f;
            attackCooldown = 2.2f;
            score = 150;
        }

        protected override void Think()
        {
            FaceTowards(P.transform.position);
            bool sameFloor = Mathf.Abs(P.transform.position.y - transform.position.y) < 1.2f;
            if (cooldown <= 0f && sameFloor && Mathf.Abs(Dx) < 8f)
            {
                StartCoroutine(Attack());
                return;
            }
            if (Mathf.Abs(Dx) > 2.5f) WalkTowards(DirToPlayer, speed);
            else Move(0f);
        }

        protected override IEnumerator Attack()
        {
            busy = true;
            Say(Loc.Get("quote.stake.charge"), 1.2f);
            yield return Windup(0.6f);
            if (IsStunned) { busy = false; yield break; }

            bool hit = false;
            float t = 0f;
            while (t < 0.6f && !IsStunned && !hit)
            {
                Move(Facing * 11f);
                hit = MeleeHit(new Vector2(0.5f, 0f), new Vector2(1.1f, 1.6f), new DamageInfo
                {
                    amount = attackDamage,
                    knockback = new Vector2(9f, 6f),
                    stun = 0.5f
                }) > 0;
                t += Time.deltaTime;
                yield return null;
            }
            Move(0f);
            cooldown = attackCooldown * Random.Range(0.8f, 1.3f);
            yield return new WaitForSeconds(0.5f); // catching their breath: punish window
            busy = false;
        }
    }
}
