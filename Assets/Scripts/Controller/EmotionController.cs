using UnityEngine;

namespace Asset
{
    /// <summary>
    /// Listens for key presses (1, 2, 3) to simulate emotion classification
    /// by assigning preset valence/arousal values and triggering
    /// corresponding CharacterController actions.
    /// 1 → Happy (high valence, high arousal)
    /// 2 → Angry (low valence, high arousal)
    /// 3 → Sad   (low valence, low arousal)
    /// </summary>
    public class EmotionController : MonoBehaviour
    {
        private float valence;
        private float arousal;
        private CharacterController characterController;

        void Awake()
        {
            // Cache CharacterController instance from scene
            characterController = FindObjectOfType<CharacterController>();
        }

        void Update()
        {
            // Press 1: Happy
            if (Input.GetKeyDown(KeyCode.Alpha1))
            {
                valence = 0.8f;
                arousal = 0.8f;
                DecideAction(valence, arousal);
            }
            // Press 2: Angry
            else if (Input.GetKeyDown(KeyCode.Alpha2))
            {
                valence = 0.2f;
                arousal = 0.8f;
                DecideAction(valence, arousal);
            }
            // Press 3: Sad
            else if (Input.GetKeyDown(KeyCode.Alpha3))
            {
                valence = 0.2f;
                arousal = 0.2f;
                DecideAction(valence, arousal);
            }
        }

        /// <summary>
        /// Triggers the appropriate CharacterController method
        /// based on given valence/arousal values.
        /// </summary>
        private void DecideAction(float v, float a)
        {
            if (v > 0.5f && a > 0.5f)
            {
                characterController.Happy(2f);
            }
            else if (v <= 0.5f && a > 0.5f)
            {
                characterController.Angry(2f);
            }
            else if (v <= 0.5f && a <= 0.5f)
            {
                characterController.Sad(2f);
            }
            else
            {
                // Fallback to Happy for high valence, low arousal
                characterController.Happy(2f);
            }
        }
    }
}
