using UnityEngine;

namespace PMBrawler
{
    [RequireComponent(typeof(Camera))]
    public class CameraFollow : MonoBehaviour
    {
        public static CameraFollow Instance { get; private set; }

        public Transform target;
        public float minX = -999f, maxX = 999f, minY = -999f;
        public float lookAhead = 2f, smooth = 6f;

        Camera cam;
        float shakeTime, shakeStrength;
        Vector3 basePos;

        void Awake()
        {
            Instance = this;
            cam = GetComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = 6.5f;
            basePos = transform.position;
        }

        public void SetBounds(float levelWidth, float levelBottom)
        {
            float halfW = cam.orthographicSize * cam.aspect;
            minX = halfW - 0.5f;
            maxX = Mathf.Max(minX, levelWidth - halfW - 0.5f);
            minY = levelBottom + cam.orthographicSize - 1f;
        }

        public void SnapTo(Vector2 p)
        {
            basePos = Clamp(new Vector3(p.x, p.y + 1.5f, -10f));
            transform.position = basePos;
        }

        public void Shake(float strength, float time)
        {
            shakeStrength = Mathf.Max(shakeStrength, strength);
            shakeTime = Mathf.Max(shakeTime, time);
        }

        Vector3 Clamp(Vector3 p)
        {
            // recompute horizontally in case the window (and aspect) changed
            p.x = Mathf.Clamp(p.x, minX, maxX);
            p.y = Mathf.Max(p.y, minY);
            return p;
        }

        void LateUpdate()
        {
            if (target)
            {
                float facing = target.TryGetComponent<Fighter>(out var f) ? f.Facing : 1f;
                var desired = Clamp(new Vector3(target.position.x + facing * lookAhead, target.position.y + 1.5f, -10f));
                basePos = Vector3.Lerp(basePos, desired, 1f - Mathf.Exp(-smooth * Time.unscaledDeltaTime));
            }

            var offset = Vector3.zero;
            if (shakeTime > 0f)
            {
                shakeTime -= Time.unscaledDeltaTime;
                offset = (Vector3)(Random.insideUnitCircle * shakeStrength);
                if (shakeTime <= 0f) shakeStrength = 0f;
            }
            transform.position = basePos + offset;
        }
    }
}
