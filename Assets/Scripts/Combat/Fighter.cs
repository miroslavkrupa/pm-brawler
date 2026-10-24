using System.Collections.Generic;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>
    /// Shared body for the player and enemies: physics, ground check, facing, knockback, stun,
    /// slow, hit-flash and melee hitboxes.
    /// </summary>
    [RequireComponent(typeof(Rigidbody2D), typeof(BoxCollider2D), typeof(Health))]
    public abstract class Fighter : MonoBehaviour
    {
        public static readonly List<Fighter> All = new();

        public Rigidbody2D Rb { get; private set; }
        public BoxCollider2D Col { get; private set; }
        public Health Hp { get; private set; }
        public Transform Visual { get; private set; }
        public int Facing { get; private set; } = 1;
        public bool Grounded { get; private set; }
        public bool IsStunned => stunTimer > 0f;
        public bool IsSlowed => slowTimer > 0f;
        public float SpeedMultiplier => (IsSlowed ? 0.5f : 1f) * (frozenTimer > 0f ? 0f : 1f);
        public bool IsFrozen => frozenTimer > 0f;

        protected float stunTimer, slowTimer, frozenTimer;
        SpriteRenderer[] renderers;
        Color[] baseColors;
        float flashTimer;
        Vector2 size;

        /// <summary>Call right after AddComponent to build the body.</summary>
        protected void SetupBody(Art.Look look, float maxHp, Team team)
        {
            size = look.size;
            Rb = GetComponent<Rigidbody2D>();
            Col = GetComponent<BoxCollider2D>();
            Hp = GetComponent<Health>();

            Rb.freezeRotation = true;
            Rb.gravityScale = 3.2f;
            Rb.interpolation = RigidbodyInterpolation2D.Interpolate;
            Rb.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
            Col.size = look.size;
            var slippery = new PhysicsMaterial2D("NoFriction") { friction = 0f, bounciness = 0f };
            Col.sharedMaterial = slippery;

            Hp.team = team;
            Hp.Init(maxHp);
            Hp.Damaged += OnDamaged;
            Hp.Died += OnDied;

            Visual = new GameObject("Visual").transform;
            Visual.SetParent(transform, false);
            renderers = Art.BuildCharacter(Visual, look);
            baseColors = new Color[renderers.Length];
            for (int i = 0; i < renderers.Length; i++) baseColors[i] = renderers[i].color;

            IgnoreOtherFighters();
            All.Add(this);
        }

        /// <summary>Fighters pass through each other; only hitboxes connect. Must be redone after re-enabling the collider.</summary>
        protected void IgnoreOtherFighters()
        {
            foreach (var other in All)
                if (other && other != this && other.Col) Physics2D.IgnoreCollision(Col, other.Col);
        }

        protected virtual void OnDestroy() => All.Remove(this);

        public float Height => size.y;
        public Vector2 Center => Col ? (Vector2)Col.bounds.center : (Vector2)transform.position;

        public void Face(int dir)
        {
            if (dir == 0 || dir == Facing) return;
            Facing = dir > 0 ? 1 : -1;
            var s = Visual.localScale;
            s.x = Facing;
            Visual.localScale = s;
        }

        public void FaceTowards(Vector2 p) => Face(p.x > transform.position.x ? 1 : -1);

        protected virtual void FixedUpdate()
        {
            Grounded = CheckGround();
        }

        protected virtual void Update()
        {
            float dt = Time.deltaTime;
            if (stunTimer > 0f) stunTimer -= dt;
            if (slowTimer > 0f) slowTimer -= dt;
            if (frozenTimer > 0f) frozenTimer -= dt;

            if (flashTimer > 0f)
            {
                flashTimer -= dt;
                if (flashTimer <= 0f) RestoreColors();
            }
            else if (IsFrozen) Tint(new Color(0.6f, 0.85f, 1f));
            else if (Hp.invulnerable || IsStunned) Blink();
            else RestoreColors();
        }

        bool CheckGround()
        {
            if (Rb.linearVelocity.y > 0.05f) return false;
            var b = Col.bounds;
            var hits = Physics2D.OverlapBoxAll(new Vector2(b.center.x, b.min.y - 0.04f), new Vector2(b.size.x * 0.9f, 0.08f), 0f);
            foreach (var h in hits)
                if (h.TryGetComponent<Solid>(out _)) return true;
            return false;
        }

        protected void Move(float speed)
        {
            Rb.linearVelocity = new Vector2(speed * SpeedMultiplier, Rb.linearVelocity.y);
        }

        public void Stun(float seconds) => stunTimer = Mathf.Max(stunTimer, seconds);
        public void Slow(float seconds) => slowTimer = Mathf.Max(slowTimer, seconds);
        public void Freeze(float seconds) => frozenTimer = Mathf.Max(frozenTimer, seconds);

        protected virtual void OnDamaged(DamageInfo d)
        {
            stunTimer = Mathf.Max(stunTimer, d.stun);
            float dir = Mathf.Sign(transform.position.x - d.sourcePos.x);
            if (dir == 0f) dir = -Facing;
            Rb.linearVelocity = new Vector2(d.knockback.x * dir, d.knockback.y);
            Flash();
            Fx.Burst(Center, Color.white, d.heavy ? 12 : 6);
        }

        protected abstract void OnDied();

        /// <summary>Damage every opponent overlapping a box in front of this fighter. Returns number of hits.</summary>
        public int MeleeHit(Vector2 offset, Vector2 boxSize, DamageInfo d)
        {
            var center = (Vector2)transform.position + new Vector2(offset.x * Facing, offset.y);
            d.sourcePos = transform.position;
            d.source = gameObject;
            int hits = 0;
            var seen = new HashSet<Health>();
            foreach (var c in Physics2D.OverlapBoxAll(center, boxSize, 0f))
            {
                var hp = c.GetComponentInParent<Health>();
                if (hp == null || hp.team == Hp.team || !seen.Add(hp)) continue;
                if (hp.TakeDamage(d))
                {
                    hits++;
                    Fx.HitWord(c.bounds.center);
                }
            }
#if UNITY_EDITOR
            Debug.DrawLine(center - boxSize / 2f, center + boxSize / 2f, Color.red, 0.2f);
#endif
            return hits;
        }

        public void Flash(float time = 0.1f)
        {
            flashTimer = time;
            Tint(Color.white);
        }

        void Tint(Color c)
        {
            foreach (var r in renderers) if (r) r.color = c;
        }

        void Blink()
        {
            bool on = Mathf.Repeat(Time.time * 12f, 1f) > 0.5f;
            for (int i = 0; i < renderers.Length; i++)
                if (renderers[i]) { var c = baseColors[i]; c.a = on ? 0.35f : 1f; renderers[i].color = c; }
        }

        void RestoreColors()
        {
            for (int i = 0; i < renderers.Length; i++)
                if (renderers[i]) renderers[i].color = baseColors[i];
        }
    }
}
