using System;
using UnityEngine;

namespace PMBrawler
{
    public enum Team { Player, Enemy }

    public struct DamageInfo
    {
        public float amount;
        public Vector2 knockback;   // x is applied away from the source
        public float stun;          // seconds the victim can't act
        public bool heavy;          // heavy hits break shields
        public Vector2 sourcePos;
        public GameObject source;
    }

    public class Health : MonoBehaviour
    {
        public Team team;
        public float max = 100f;
        public float Current { get; private set; }
        public bool IsDead => Current <= 0f;
        public bool invulnerable;
        public float invulnerableAfterHit = 0f;

        /// <summary>Return true to block the hit (e.g. a developer's "works on my machine" shield).</summary>
        public Func<DamageInfo, bool> blockCheck;

        public event Action<DamageInfo> Damaged;
        public event Action<DamageInfo> Blocked;
        public event Action Died;

        float iFrames;

        public void Init(float maxHp)
        {
            max = maxHp;
            Current = maxHp;
        }

        void Update()
        {
            if (iFrames > 0f) iFrames -= Time.deltaTime;
        }

        public bool TakeDamage(DamageInfo d)
        {
            if (IsDead || invulnerable || iFrames > 0f) return false;
            if (blockCheck != null && blockCheck(d))
            {
                Blocked?.Invoke(d);
                return false;
            }
            Current = Mathf.Max(0f, Current - d.amount);
            iFrames = invulnerableAfterHit;
            Damaged?.Invoke(d);
            if (IsDead) Died?.Invoke();
            return true;
        }

        /// <summary>Instant death that ignores invulnerability (falling into a pit).</summary>
        public void Kill()
        {
            if (IsDead) return;
            Current = 0f;
            Died?.Invoke();
        }

        public void Heal(float amount) => Current = Mathf.Min(max, Current + amount);

        public void Revive()
        {
            Current = max;
            iFrames = 2f;
        }
    }
}
