using UnityEngine;

namespace PMBrawler
{
    /// <summary>Moves a background layer along with the camera by <see cref="factor"/> (1 = glued to the camera).</summary>
    [DefaultExecutionOrder(100)] // after CameraFollow
    public class Parallax : MonoBehaviour
    {
        public float factor = 0.8f;

        void LateUpdate()
        {
            var cam = CameraFollow.Instance;
            if (!cam) return;
            var p = transform.localPosition;
            p.x = cam.transform.position.x * factor;
            transform.localPosition = p;
        }
    }
}
