using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>The hero: a project manager armed with a clipboard, a Gantt chart and too much coffee.</summary>
    public class PlayerController : Fighter
    {
        public static PlayerController Instance { get; private set; }

        public const float MaxEnergy = 100f;
        public const float SpecialCost = 50f;

        public float Energy { get; private set; } = 50f;
        public float GanttTimer { get; private set; }
        public float ReverseTimer { get; private set; }
        public Vector2 SpawnPoint { get; set; }

        const float RunSpeed = 7f, JumpVelocity = 14.5f, CoyoteTime = 0.1f, JumpBufferTime = 0.12f;
        const float BaseGravity = 3.2f;

        float coyote, jumpBuffer, attackLock, comboWindow;
        int comboStep;
        bool dead;

        public static PlayerController Create(Vector2 pos, Transform parent)
        {
            var go = new GameObject("ProjectManager");
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            var p = go.AddComponent<PlayerController>();
            p.SetupBody(new Art.Look
            {
                size = new Vector2(0.8f, 1.8f),
                sheet = "pm",
                speech = Art.Hex("#ffffff")
            }, 100f, Team.Player);
            p.Hp.invulnerableAfterHit = 0.8f;
            p.SpawnPoint = pos;
            Instance = p;
            return p;
        }

        protected override void OnDestroy()
        {
            base.OnDestroy();
            if (Instance == this) Instance = null;
        }

        protected override void Update()
        {
            base.Update();
            var gm = GameManager.Instance;
            if (dead) return;
            if (gm == null || gm.State != GameState.Playing)
            {
                Move(0f);
                return;
            }

            if (transform.position.y < gm.KillY) { Hp.Kill(); return; }

            float dt = Time.deltaTime;
            if (GanttTimer > 0f) GanttTimer -= dt;
            if (ReverseTimer > 0f) ReverseTimer -= dt;
            if (attackLock > 0f) attackLock -= dt;
            if (comboWindow > 0f) comboWindow -= dt; else comboStep = 0;
            Energy = Mathf.Min(MaxEnergy, Energy + 3f * dt);

            coyote = Grounded ? CoyoteTime : coyote - dt;
            jumpBuffer = GameInput.JumpPressed ? JumpBufferTime : jumpBuffer - dt;

            // longer jump while the button is held, snappier fall
            float vy = Rb.linearVelocity.y;
            Rb.gravityScale = vy > 0f && !GameInput.JumpHeld ? BaseGravity * 2f : vy < 0f ? BaseGravity * 1.3f : BaseGravity;

            if (IsStunned || IsFrozen) return; // knockback carries us

            float h = GameInput.Horizontal * (ReverseTimer > 0f ? -1f : 1f);
            if (attackLock > 0f) Move(h * RunSpeed * 0.2f);
            else
            {
                Move(h * RunSpeed);
                Face(System.Math.Sign(h));
            }

            if (jumpBuffer > 0f && attackLock <= 0f)
            {
                if (GameInput.Down && TryDropThrough()) jumpBuffer = 0f;
                else if (coyote > 0f)
                {
                    Rb.linearVelocity = new Vector2(Rb.linearVelocity.x, JumpVelocity);
                    jumpBuffer = 0f;
                    coyote = 0f;
                }
            }

            if (attackLock > 0f) return;
            if (GameInput.AttackPressed) { if (Grounded) ComboAttack(); else AirAttack(); }
            else if (GameInput.HeavyPressed) StartCoroutine(GanttSlam());
            else if (GameInput.SpecialPressed) TakeItOffline();
        }

        float DamageMult => GanttTimer > 0f ? 2f : 1f;

        void ComboAttack()
        {
            comboStep = comboStep % 3 + 1;
            comboWindow = 0.45f;
            bool finisher = comboStep == 3;
            attackLock = finisher ? 0.35f : 0.18f;
            Rb.linearVelocity = new Vector2(Facing * (finisher ? 4f : 2f), Rb.linearVelocity.y); // small lunge
            Pose(comboStep == 2 ? "atk0" : "atk1", attackLock + 0.06f);
            Swing(new Vector2(0.9f, 0.1f), new Vector2(1.3f, finisher ? 1.2f : 0.5f), finisher ? Art.Hex("#ffd23f") : Art.Hex("#a0784a"));
            Landed(MeleeHit(new Vector2(0.95f, 0f), new Vector2(1.4f, 1.4f), new DamageInfo
            {
                amount = (finisher ? 22f : 11f) * DamageMult,
                knockback = finisher ? new Vector2(7f, 5f) : new Vector2(2f, 1f),
                stun = finisher ? 0.6f : 0.35f
            }));
        }

        void AirAttack()
        {
            attackLock = 0.25f;
            Pose("atk1", attackLock);
            Swing(new Vector2(0.6f, -0.5f), new Vector2(1.2f, 0.9f), Art.Hex("#a0784a"));
            Landed(MeleeHit(new Vector2(0.6f, -0.4f), new Vector2(1.5f, 1.5f), new DamageInfo
            {
                amount = 14f * DamageMult,
                knockback = new Vector2(4f, -2f),
                stun = 0.4f
            }));
        }

        IEnumerator GanttSlam()
        {
            attackLock = 0.7f;
            Fx.Say(transform, Loc.Get("pm.heavy"), Height * 0.5f + 0.7f, 1f);
            Visual.localScale = new Vector3(Facing * 1.1f, 0.9f, 1f); // wind up
            Pose("atk0", 0.25f);
            yield return new WaitForSeconds(0.25f);
            if (dead) yield break;
            Visual.localScale = new Vector3(Facing, 1f, 1f);
            if (IsStunned) yield break;
            Pose("atk1", 0.4f);
            Swing(new Vector2(1.1f, 0f), new Vector2(2f, 1.6f), Art.Hex("#4ea8de"));
            Fx.Shake(0.2f, 0.15f);
            Landed(MeleeHit(new Vector2(1.1f, 0f), new Vector2(2.2f, 1.8f), new DamageInfo
            {
                amount = 35f * DamageMult,
                knockback = new Vector2(10f, 7f),
                stun = 0.9f,
                heavy = true
            }));
        }

        void TakeItOffline()
        {
            if (Energy < SpecialCost)
            {
                Fx.FloatText(Loc.Get("pm.noEnergy"), Center + Vector2.up, Color.gray, 0.3f);
                return;
            }
            Energy -= SpecialCost;
            attackLock = 0.4f;
            Pose("jump", 0.5f); // arms in the air
            Fx.Say(transform, Loc.Get("pm.special"), Height * 0.5f + 0.7f, 1.8f);
            Fx.Shake(0.25f, 0.25f);
            Fx.Burst(Center, Art.Hex("#4ea8de"), 24);
            foreach (var f in Fighter.All.ToArray())
            {
                if (f is not Enemy e || e.Hp.IsDead) continue;
                if (Vector2.Distance(e.Center, Center) > 6f) continue;
                e.Hp.TakeDamage(new DamageInfo { amount = 10f * DamageMult, knockback = new Vector2(3f, 4f), stun = 3f, sourcePos = transform.position, source = gameObject });
                e.Stun(e.IsBoss ? 1f : 3f);
                Fx.FloatText("zZz", e.Center + Vector2.up * (e.Height * 0.5f + 0.3f), Art.Hex("#4ea8de"), 0.4f, 2f);
            }
        }

        void Landed(int hits)
        {
            if (hits <= 0) return;
            Energy = Mathf.Min(MaxEnergy, Energy + 5f * hits);
            Fx.HitStop(0.045f);
            Fx.Shake(0.08f, 0.08f);
        }

        /// <summary>A crescent smear in front of the PM, sized to the hitbox.</summary>
        void Swing(Vector2 offset, Vector2 size, Color color)
        {
            var smear = Art.Load("Fx/smear");
            var sr = Art.Place("Swing", transform, smear, new Vector2(offset.x * Facing, offset.y), 20);
            float w = smear ? smear.bounds.size.x : 1f;
            sr.transform.localScale = new Vector3(Facing * size.x / w * 1.1f, size.y / w * 1.3f, 1f);
            sr.color = Color.Lerp(color, Color.white, 0.5f);
            Destroy(sr.gameObject, 0.09f);
        }

        bool TryDropThrough()
        {
            if (!Grounded) return false;
            var b = Col.bounds;
            foreach (var h in Physics2D.OverlapBoxAll(new Vector2(b.center.x, b.min.y - 0.1f), new Vector2(b.size.x, 0.2f), 0f))
                if (h.TryGetComponent<Solid>(out var s) && s.oneWay)
                {
                    StartCoroutine(IgnoreFor(h, 0.4f));
                    return true;
                }
            return false;
        }

        IEnumerator IgnoreFor(Collider2D platform, float seconds)
        {
            Physics2D.IgnoreCollision(Col, platform, true);
            yield return new WaitForSeconds(seconds);
            if (platform) Physics2D.IgnoreCollision(Col, platform, false);
        }

        // --- Effects from pickups and enemy projectiles ---

        public void ApplyEffect(ProjectileEffect effect)
        {
            switch (effect)
            {
                case ProjectileEffect.Slow:
                    Slow(2.5f);
                    break;
                case ProjectileEffect.DrainEnergy:
                    Energy = Mathf.Max(0f, Energy - 35f);
                    Fx.FloatText(Loc.Get("proj.budget"), Center + Vector2.up, Art.Hex("#ffd23f"), 0.5f);
                    break;
                case ProjectileEffect.ReverseControls:
                    ReverseTimer = 3.5f;
                    break;
            }
        }

        public void AddEnergy(float amount) => Energy = Mathf.Min(MaxEnergy, Energy + amount);
        public void StartGantt(float seconds) => GanttTimer = seconds;
        public void Reverse(float seconds) => ReverseTimer = Mathf.Max(ReverseTimer, seconds);

        // --- Death & respawn ---

        protected override void OnDied()
        {
            dead = true;
            Hp.invulnerable = true;
            StopAllCoroutines();
            Visual.localScale = new Vector3(Facing, 1f, 1f);
            Rb.linearVelocity = new Vector2(-Facing * 3f, 8f);
            Col.enabled = false;
            Fx.Shake(0.3f, 0.3f);
            GameManager.Instance.OnPlayerDied();
        }

        public void Respawn()
        {
            dead = false;
            transform.position = SpawnPoint;
            Rb.linearVelocity = Vector2.zero;
            Col.enabled = true;
            IgnoreOtherFighters();
            Hp.invulnerable = false;
            Hp.Revive();
            ReverseTimer = 0f;
            slowTimer = stunTimer = frozenTimer = 0f;
            Energy = Mathf.Max(Energy, 50f);
            Fx.Say(transform, Loc.Get("pm.respawn"), Height * 0.5f + 0.7f, 1.8f);
        }
    }
}
