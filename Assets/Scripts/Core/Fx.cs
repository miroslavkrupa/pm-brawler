using System.Collections;
using UnityEngine;

namespace PMBrawler
{
    /// <summary>Juice: floating text, speech bubbles, camera shake and hit-stop.</summary>
    public static class Fx
    {
        public static void FloatText(string text, Vector2 pos, Color color, float height = 0.45f, float life = 0.9f)
        {
            var root = new GameObject("FloatText").transform;
            root.position = pos;
            Art.Text(text, root, Vector2.zero, height, color, 200);
            root.gameObject.AddComponent<FloatingText>().Init(life, new Vector2(Random.Range(-0.6f, 0.6f), 2.2f));
        }

        public static void HitWord(Vector2 pos) =>
            FloatText(Loc.Random("fx.hit"), pos + Vector2.up * 0.6f, Art.Hex("#ffd23f"), 0.55f, 0.6f);

        /// <summary>
        /// A short quote that follows the speaker for a few seconds, adventure-game style: text in the
        /// speaker's colour floating over their head, no bubble.
        /// </summary>
        public static void Say(Transform speaker, string text, float height, float duration = 2.2f)
        {
            var old = speaker.Find("Speech");
            if (old) Object.Destroy(old.gameObject);
            var root = new GameObject("Speech").transform;
            root.SetParent(speaker, false);
            root.localPosition = new Vector3(0, height, 0);
            var color = speaker.TryGetComponent<Fighter>(out var f) ? f.SpeechColor : Color.white;
            Art.OutlinedText(text, root, Vector2.zero, 0.34f, color, 210);
            Object.Destroy(root.gameObject, duration);
        }

        /// <summary>Change the text of an <see cref="Art.OutlinedText"/> and its outline copies.</summary>
        public static void SetText(TextMesh main, string text)
        {
            foreach (var tm in main.GetComponentsInChildren<TextMesh>()) tm.text = text;
        }

        public static void Burst(Vector2 pos, Color color, int count = 8)
        {
            var spark = Art.Load("Fx/spark");
            for (int i = 0; i < count; i++)
            {
                var sr = Art.Place("Spark", null, spark, pos, 150);
                sr.color = color;
                sr.transform.localScale = Vector3.one * Random.Range(0.6f, 1.3f);
                sr.gameObject.AddComponent<FloatingText>().Init(0.4f, Random.insideUnitCircle.normalized * Random.Range(3f, 7f), false);
            }
        }

        public static void Shake(float strength = 0.15f, float time = 0.15f)
        {
            if (CameraFollow.Instance) CameraFollow.Instance.Shake(strength, time);
        }

        static bool stopping;

        public static void ResetHitStop() => stopping = false;

        /// <summary>Freeze the game for a split second so hits feel heavy.</summary>
        public static void HitStop(float seconds = 0.05f)
        {
            if (stopping || GameManager.Instance == null || Time.timeScale == 0f) return;
            GameManager.Instance.StartCoroutine(HitStopRoutine(seconds));
        }

        static IEnumerator HitStopRoutine(float seconds)
        {
            stopping = true;
            Time.timeScale = 0.05f;
            yield return new WaitForSecondsRealtime(seconds);
            if (Time.timeScale > 0f) Time.timeScale = 1f; // don't un-pause if the game was paused meanwhile
            stopping = false;
        }
    }
}
