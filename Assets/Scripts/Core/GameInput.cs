using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace PMBrawler
{
    /// <summary>
    /// Keyboard input that works with both the new Input System package and the legacy Input Manager,
    /// whichever the project has enabled.
    /// </summary>
    public static class GameInput
    {
#if ENABLE_INPUT_SYSTEM
        static Keyboard K => Keyboard.current;

        public static float Horizontal
        {
            get
            {
                if (K == null) return 0f;
                float h = 0f;
                if (K.aKey.isPressed || K.leftArrowKey.isPressed) h -= 1f;
                if (K.dKey.isPressed || K.rightArrowKey.isPressed) h += 1f;
                return h;
            }
        }

        public static bool Down => K != null && (K.sKey.isPressed || K.downArrowKey.isPressed);
        public static bool JumpPressed => K != null && (K.spaceKey.wasPressedThisFrame || K.wKey.wasPressedThisFrame || K.upArrowKey.wasPressedThisFrame);
        public static bool JumpHeld => K != null && (K.spaceKey.isPressed || K.wKey.isPressed || K.upArrowKey.isPressed);
        public static bool AttackPressed => K != null && (K.jKey.wasPressedThisFrame || K.xKey.wasPressedThisFrame);
        public static bool HeavyPressed => K != null && (K.kKey.wasPressedThisFrame || K.cKey.wasPressedThisFrame);
        public static bool SpecialPressed => K != null && (K.lKey.wasPressedThisFrame || K.vKey.wasPressedThisFrame);
        public static bool ConfirmPressed => K != null && (K.enterKey.wasPressedThisFrame || K.numpadEnterKey.wasPressedThisFrame);
        public static bool PausePressed => K != null && (K.escapeKey.wasPressedThisFrame || K.pKey.wasPressedThisFrame);
        public static bool LanguagePressed => K != null && K.tabKey.wasPressedThisFrame;
#else
        public static float Horizontal
        {
            get
            {
                float h = 0f;
                if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) h -= 1f;
                if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) h += 1f;
                return h;
            }
        }

        public static bool Down => Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow);
        public static bool JumpPressed => Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow);
        public static bool JumpHeld => Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow);
        public static bool AttackPressed => Input.GetKeyDown(KeyCode.J) || Input.GetKeyDown(KeyCode.X);
        public static bool HeavyPressed => Input.GetKeyDown(KeyCode.K) || Input.GetKeyDown(KeyCode.C);
        public static bool SpecialPressed => Input.GetKeyDown(KeyCode.L) || Input.GetKeyDown(KeyCode.V);
        public static bool ConfirmPressed => Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter);
        public static bool PausePressed => Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P);
        public static bool LanguagePressed => Input.GetKeyDown(KeyCode.Tab);
#endif
    }
}
