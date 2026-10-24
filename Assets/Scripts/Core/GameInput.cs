using UnityEngine;
#if ENABLE_INPUT_SYSTEM
using UnityEngine.InputSystem;
#endif

namespace PMBrawler
{
    /// <summary>
    /// Keyboard input that works with both the new Input System package and the legacy Input Manager,
    /// whichever the project has enabled, merged with the on-screen <see cref="TouchControls"/>.
    /// </summary>
    public static class GameInput
    {
        public static float Horizontal => Mathf.Clamp(KeyHorizontal + TouchControls.Horizontal, -1f, 1f);
        public static bool Down => KeyDown || TouchControls.Down;
        public static bool JumpPressed => KeyJumpPressed || TouchControls.JumpPressed;
        public static bool JumpHeld => KeyJumpHeld || TouchControls.JumpHeld;
        public static bool AttackPressed => KeyAttackPressed || TouchControls.AttackPressed;
        public static bool HeavyPressed => KeyHeavyPressed || TouchControls.HeavyPressed;
        public static bool SpecialPressed => KeySpecialPressed || TouchControls.SpecialPressed;
        public static bool ConfirmPressed => KeyConfirmPressed || TouchControls.TapPressed;
        public static bool PausePressed => KeyPausePressed || TouchControls.PausePressed;
        public static bool LanguagePressed => KeyLanguagePressed || TouchControls.LanguagePressed;
        public static bool FullscreenPressed => KeyFullscreenPressed || TouchControls.FullscreenPressed;

#if ENABLE_INPUT_SYSTEM
        static Keyboard K => Keyboard.current;

        static float KeyHorizontal
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

        static bool KeyDown => K != null && (K.sKey.isPressed || K.downArrowKey.isPressed);
        static bool KeyJumpPressed => K != null && (K.spaceKey.wasPressedThisFrame || K.wKey.wasPressedThisFrame || K.upArrowKey.wasPressedThisFrame);
        static bool KeyJumpHeld => K != null && (K.spaceKey.isPressed || K.wKey.isPressed || K.upArrowKey.isPressed);
        static bool KeyAttackPressed => K != null && (K.jKey.wasPressedThisFrame || K.xKey.wasPressedThisFrame);
        static bool KeyHeavyPressed => K != null && (K.kKey.wasPressedThisFrame || K.cKey.wasPressedThisFrame);
        static bool KeySpecialPressed => K != null && (K.lKey.wasPressedThisFrame || K.vKey.wasPressedThisFrame);
        static bool KeyConfirmPressed => K != null && (K.enterKey.wasPressedThisFrame || K.numpadEnterKey.wasPressedThisFrame);
        static bool KeyPausePressed => K != null && (K.escapeKey.wasPressedThisFrame || K.pKey.wasPressedThisFrame);
        static bool KeyLanguagePressed => K != null && K.tabKey.wasPressedThisFrame;
        static bool KeyFullscreenPressed => K != null && K.fKey.wasPressedThisFrame;
#else
        static float KeyHorizontal
        {
            get
            {
                float h = 0f;
                if (Input.GetKey(KeyCode.A) || Input.GetKey(KeyCode.LeftArrow)) h -= 1f;
                if (Input.GetKey(KeyCode.D) || Input.GetKey(KeyCode.RightArrow)) h += 1f;
                return h;
            }
        }

        static bool KeyDown => Input.GetKey(KeyCode.S) || Input.GetKey(KeyCode.DownArrow);
        static bool KeyJumpPressed => Input.GetKeyDown(KeyCode.Space) || Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow);
        static bool KeyJumpHeld => Input.GetKey(KeyCode.Space) || Input.GetKey(KeyCode.W) || Input.GetKey(KeyCode.UpArrow);
        static bool KeyAttackPressed => Input.GetKeyDown(KeyCode.J) || Input.GetKeyDown(KeyCode.X);
        static bool KeyHeavyPressed => Input.GetKeyDown(KeyCode.K) || Input.GetKeyDown(KeyCode.C);
        static bool KeySpecialPressed => Input.GetKeyDown(KeyCode.L) || Input.GetKeyDown(KeyCode.V);
        static bool KeyConfirmPressed => Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter);
        static bool KeyPausePressed => Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.P);
        static bool KeyLanguagePressed => Input.GetKeyDown(KeyCode.Tab);
        static bool KeyFullscreenPressed => Input.GetKeyDown(KeyCode.F);
#endif
    }
}
