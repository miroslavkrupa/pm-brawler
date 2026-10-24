using UnityEngine;

namespace PMBrawler
{
    /// <summary>Drifts, fades and destroys itself. Used for hit words, quotes and sparks.</summary>
    public class FloatingText : MonoBehaviour
    {
        float life, age;
        Vector2 velocity;
        bool gravity;
        Renderer[] renderers;

        public void Init(float life, Vector2 velocity, bool rising = true)
        {
            this.life = life;
            this.velocity = velocity;
            gravity = !rising;
            renderers = GetComponentsInChildren<Renderer>();
        }

        void Update()
        {
            age += Time.deltaTime;
            if (gravity) velocity += Physics2D.gravity * Time.deltaTime;
            else velocity *= 1f - 2f * Time.deltaTime;
            transform.position += (Vector3)(velocity * Time.deltaTime);
            float a = 1f - age / life;
            foreach (var r in renderers)
            {
                if (r is SpriteRenderer sr) { var c = sr.color; c.a = a; sr.color = c; }
                else if (r.TryGetComponent<TextMesh>(out var tm)) { var c = tm.color; c.a = a; tm.color = c; }
            }
            if (age >= life) Destroy(gameObject);
        }
    }
}
