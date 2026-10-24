using System;
using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Base enemy: walks up to the PM and hits them. Subclasses set stats/looks in Configure()
    /// and override Think() / Attack() for their gimmick.
    /// </summary>
    public abstract class Enemy : Fighter
    {
        public static event Action<Enemy> Defeated;

        public string NameKey { get; protected set; }
        public bool IsBoss { get; protected set; }
        public bool Aggro { get; private set; }

        protected string quoteKey;
        protected int score = 100;
        protected float speed = 2.5f, aggroRange = 9f, attackRange = 1.1f, attackCooldown = 1.3f, attackDamage = 10f;
        protected bool superArmor;      // bosses shrug off stun and most knockback
        protected bool busy;            // an attack routine is controlling movement
        protected float cooldown = 0.8f;

        float quoteTimer;

        protected PlayerController P => PlayerController.Instance;
        protected bool PlayerAlive => P != null && !P.Hp.IsDead;
        protected float Dx => P.transform.position.x - transform.position.x;
        protected float Dist => Vector2.Distance(P.Center, Center);
        protected int DirToPlayer => Dx >= 0f ? 1 : -1;

        public static T Spawn<T>(Vector2 pos, Transform parent) where T : Enemy
        {
            var go = new GameObject(typeof(T).Name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var e = go.AddComponent<T>();
            e.Configure();
            e.Face(-1);
            e.quoteTimer = UnityEngine.Random.Range(1f, 6f);
            return e;
        }

        protected abstract void Configure();

        protected override void Update()
        {
            base.Update();
            if (Hp.IsDead) return;
            var gm = GameManager.Instance;
            if (gm == null || gm.State != GameState.Playing || !PlayerAlive)
            {
                if (!IsStunned) Move(0f);
                return;
            }

            if (transform.position.y < gm.KillY) { Hp.Kill(); return; }

            float dt = Time.deltaTime;
            if (!Aggro && Dist < aggroRange) { Aggro = true; OnAggro(); }
            if (!Aggro) { Move(0f); return; }

            if (cooldown > 0f && !IsFrozen) cooldown -= dt;

            quoteTimer -= dt;
            if (quoteTimer <= 0f && quoteKey != null)
            {
                quoteTimer = UnityEngine.Random.Range(6f, 12f);
                Say(Loc.Random(quoteKey));
            }

            if (IsFrozen) { Move(0f); return; }
            if (IsStunned || busy) return;
            Think();
        }

        protected virtual void OnAggro() { }

        /// <summary>Default brain: walk up to the player and swing.</summary>
        protected virtual void Think()
        {
            FaceTowards(P.transform.position);
            if (Mathf.Abs(Dx) > attackRange) WalkTowards(DirToPlayer, speed);
            else
            {
                Move(0f);
                if (cooldown <= 0f) StartCoroutine(Attack());
            }
        }

        protected virtual IEnumerator Attack()
        {
            busy = true;
            yield return Windup(0.35f);
            if (!IsStunned)
            {
                MeleeHit(new Vector2(attackRange * 0.7f, 0f), new Vector2(1.3f, 1.4f), new DamageInfo
                {
                    amount = attackDamage,
                    knockback = new Vector2(5f, 4f),
                    stun = 0.3f
                });
            }
            cooldown = attackCooldown * UnityEngine.Random.Range(0.8f, 1.3f);
            yield return new WaitForSeconds(0.25f);
            busy = false;
        }

        /// <summary>Telegraph: squash the sprite so the player can react.</summary>
        protected IEnumerator Windup(float seconds)
        {
            Move(0f);
            Visual.localScale = new Vector3(Facing * 1.15f, 0.85f, 1f);
            yield return new WaitForSeconds(seconds);
            Visual.localScale = new Vector3(Facing, 1f, 1f);
        }

        /// <summary>Walk, but don't step off a ledge.</summary>
        protected void WalkTowards(int dir, float spd)
        {
            Face(dir);
            var b = Col.bounds;
            var probe = new Vector2(b.center.x + dir * (b.extents.x + 0.3f), b.min.y - 0.4f);
            bool groundAhead = false;
            foreach (var c in Physics2D.OverlapPointAll(probe))
                if (c.TryGetComponent<Solid>(out _)) { groundAhead = true; break; }
            Move(groundAhead || !Grounded ? dir * spd : 0f);
        }

        protected void Say(string text, float duration = 2.2f) => Fx.Say(transform, text, Height * 0.5f + 0.6f, duration);

        protected override void OnDamaged(DamageInfo d)
        {
            if (superArmor)
            {
                d.stun = 0f;
                d.knockback = new Vector2(d.knockback.x * 0.1f, 0f);
                Flash();
                Fx.Burst(Center, Color.white, 6);
                return;
            }
            // getting hit interrupts a windup
            StopAllCoroutines();
            busy = false;
            Visual.localScale = new Vector3(Facing, 1f, 1f);
            base.OnDamaged(d);
            if (!Aggro) { Aggro = true; OnAggro(); }
        }

        protected override void OnDied()
        {
            StopAllCoroutines();
            busy = true;
            GameManager.Instance?.AddScore(score);
            Fx.FloatText(Loc.Get("fx.ko"), Center + Vector2.up * (Height * 0.5f + 0.4f), Art.Hex("#ff6b6b"), 0.28f, 1.4f);
            Defeated?.Invoke(this);

            if (!IsBoss && UnityEngine.Random.value < 0.15f)
                Pickup.Spawn(PickupKind.Coffee, Center, transform.parent);

            // fly off screen, cartoon style
            Col.enabled = false;
            Rb.gravityScale = 3f;
            Rb.freezeRotation = false;
            Rb.linearVelocity = new Vector2(-Facing * 5f, 10f);
            Rb.angularVelocity = 720f * -Facing;
            Destroy(gameObject, 2f);
        }
    }
}
