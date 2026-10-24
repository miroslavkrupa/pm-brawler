using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Smashes you with a laptop. Raises a "works on my machine" shield that blocks light hits
    /// from the front — break it with the Gantt slam or hit them from behind.
    /// </summary>
    public class Developer : Enemy
    {
        float shieldTimer, shieldCooldown = 2f;
        GameObject shield;

        protected override void Configure()
        {
            SetupBody(new Art.Look
            {
                size = new Vector2(0.8f, 1.7f),
                body = Art.Hex("#3d5a80"),
                legs = Art.Hex("#293241"),
                head = Art.Skin,
                accent = Art.Hex("#1d2d44"),
                accessory = "hoodie"
            }, 45f, Team.Enemy);
            NameKey = "enemy.dev";
            quoteKey = "quote.dev";
            speed = 2.6f;
            attackDamage = 10f;
            score = 100;
            Hp.blockCheck = d => shieldTimer > 0f && !d.heavy && Mathf.Sign(d.sourcePos.x - transform.position.x) == Facing;
            Hp.Blocked += _ =>
            {
                Fx.FloatText(Loc.Get("pm.blocked"), Center + Vector2.up, Art.Hex("#98c1d9"), 0.35f, 0.6f);
                Flash(0.05f);
            };
        }

        protected override void Update()
        {
            float dt = Time.deltaTime;
            if (shieldCooldown > 0f) shieldCooldown -= dt;
            if (shieldTimer > 0f)
            {
                shieldTimer -= dt;
                if (shieldTimer <= 0f || IsStunned) DropShield();
            }
            base.Update();
        }

        protected override void Think()
        {
            if (shieldTimer > 0f)
            {
                FaceTowards(P.transform.position);
                Move(0f);
                return;
            }
            if (shieldCooldown <= 0f && Mathf.Abs(Dx) < 3.5f && Random.value < 0.02f)
            {
                RaiseShield();
                return;
            }
            base.Think();
        }

        void RaiseShield()
        {
            shieldTimer = 1.6f;
            shieldCooldown = 5f;
            Move(0f);
            FaceTowards(P.transform.position);
            Say(Loc.Get("quote.dev.shield"), 1.6f);
            shield = Art.Shape("Shield", Visual, new Vector2(0.6f, 0.1f), new Vector2(0.18f, 1.6f), new Color(0.6f, 0.85f, 1f, 0.8f), 10).gameObject;
        }

        void DropShield()
        {
            shieldTimer = 0f;
            if (shield) Destroy(shield);
        }

        protected override void OnDamaged(DamageInfo d)
        {
            DropShield(); // a heavy hit (or one from behind) breaks it
            base.OnDamaged(d);
        }
    }
}
