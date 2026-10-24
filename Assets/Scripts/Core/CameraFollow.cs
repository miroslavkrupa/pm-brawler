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
        int screenHeight;
        float levelWidth = -1f, levelBottom;
        float pixel;   // one screen pixel in world units when snapping, 0 = no snapping

        void Awake()
        {
            Instance = this;
            cam = GetComponent<Camera>();
            cam.orthographic = true;
            UpdateZoom();
            basePos = transform.position;
        }

        /// <summary>
        /// Zoom so about <see cref="Art.ViewHeight"/> world units are visible. For pixel art, snap to a zoom
        /// where every art pixel covers a whole number of screen pixels so the dithering stays crisp (falling
        /// back to the exact zoom on small windows). Call again after switching art styles.
        /// </summary>
        public void UpdateZoom()
        {
            screenHeight = Screen.height;
            float view = Art.ViewHeight;
            if (!Art.PixelPerfect)
            {
                cam.orthographicSize = view / 2f;
                pixel = 0f;
                if (levelWidth >= 0f) SetBounds(levelWidth, levelBottom);
                return;
            }
            int scale = Mathf.Max(1, Mathf.RoundToInt(screenHeight / (view * Art.PPU)));
            float size = screenHeight / (2f * Art.PPU * scale);
            if (size > view * 0.65f || size < view * 0.4f)
            {
                size = view / 2f;
                pixel = 0f;
            }
            else pixel = 1f / (Art.PPU * scale);
            cam.orthographicSize = size;
            if (levelWidth >= 0f) SetBounds(levelWidth, levelBottom);
        }

        public void SetBounds(float levelWidth, float levelBottom)
        {
            this.levelWidth = levelWidth;
            this.levelBottom = levelBottom;
            float halfW = cam.orthographicSize * cam.aspect;
            minX = halfW - 0.5f;
            maxX = Mathf.Max(minX, levelWidth - halfW - 0.5f);
            minY = levelBottom + cam.orthographicSize + 0.5f; // a little foundation under the floor, not a wall of bricks
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
            if (Screen.height != screenHeight) UpdateZoom();
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
            var pos = basePos + offset;
            if (pixel > 0f)
            {
                // snap to the screen pixel grid so sprites don't shimmer
                pos.x = Mathf.Round(pos.x / pixel) * pixel;
                pos.y = Mathf.Round(pos.y / pixel) * pixel;
            }
            transform.position = pos;
        }
    }
}
