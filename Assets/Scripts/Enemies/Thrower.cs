using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>Keeps their distance and lobs things at the PM.</summary>
    public abstract class Thrower : Enemy
    {
        protected string projectileKey = "proj.bug";
        protected Color projectileColor = Color.white;
        protected ProjectileEffect projectileEffect = ProjectileEffect.None;
        protected float minDistance = 3f, maxDistance = 7f;
        protected int volley = 1;

        protected override void Think()
        {
            FaceTowards(P.transform.position);
            float adx = Mathf.Abs(Dx);
            if (adx < minDistance) WalkTowards(-DirToPlayer, speed);
            else if (adx > maxDistance) WalkTowards(DirToPlayer, speed);
            else Move(0f);
            FaceTowards(P.transform.position);

            if (cooldown <= 0f && adx < maxDistance + 3f) StartCoroutine(Attack());
        }

        protected override IEnumerator Attack()
        {
            busy = true;
            for (int i = 0; i < volley; i++)
            {
                yield return Windup(0.3f);
                if (IsStunned || !PlayerAlive) break;
                FaceTowards(P.transform.position);
                Throw(P.Center);
                yield return new WaitForSeconds(0.2f);
            }
            cooldown = attackCooldown * Random.Range(0.8f, 1.3f);
            busy = false;
        }

        protected void Throw(Vector2 target)
        {
            var from = Center + new Vector2(Facing * 0.5f, 0.4f);
            const float g = 12f, vx = 7f;
            float dx = target.x - from.x;
            float t = Mathf.Clamp(Mathf.Abs(dx) / vx, 0.3f, 1.4f);
            float vy = Mathf.Clamp((target.y - from.y + 0.5f * g * t * t) / t, 1f, 14f);
            Projectile.Spawn(from, new Vector2(Mathf.Sign(dx) * Mathf.Abs(dx) / t, vy), g, projectileKey, projectileColor,
                new DamageInfo { amount = attackDamage, knockback = new Vector2(3f, 3f), stun = 0.2f },
                projectileEffect, Team.Enemy, gameObject);
        }
    }
}
