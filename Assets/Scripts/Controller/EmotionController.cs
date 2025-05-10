using UnityEngine;

namespace Asset
{
    /// <summary>
    /// Listens to real-time BCI predictions via WebSocket,
    /// reads valence/arousal from the BciWebSocketClient,
    /// and triggers CharacterController actions accordingly.
    /// </summary>
    public class EmotionController : MonoBehaviour
    {
        [Tooltip("Reference to the WebSocket client that provides real-time BCI data")]
        public BciClientWebSocket bciClient;

        private float prevValence = float.NaN;
        private float prevArousal = float.NaN;
        private CharacterController characterController;

        void Awake()
        {
            // Cache CharacterController instance
            characterController = FindObjectOfType<CharacterController>();

            // If not assigned in Inspector, auto-find the BCI client
            if (bciClient == null)
            {
                bciClient = FindObjectOfType<BciClientWebSocket>();
            }
        }

        void Update()
        {
            if (bciClient == null) return;

            float v = bciClient.Valence;
            float a = bciClient.Arousal;

            // Only trigger when values actually change
            if (!Mathf.Approximately(v, prevValence) || !Mathf.Approximately(a, prevArousal))
            {
                DecideAction(v, a);
                prevValence = v;
                prevArousal = a;
            }
        }

        /// <summary>
        /// Triggers the appropriate CharacterController method
        /// based on given valence/arousal values.
        /// </summary>
        private void DecideAction(float v, float a)
        {
            const float duration = 2f;

            if (v > 0.5f && a > 0.5f)
            {
                characterController.Happy(duration);
            }
            else if (v <= 0.5f && a > 0.5f)
            {
                characterController.Angry(duration);
            }
            else if (v <= 0.5f && a <= 0.5f)
            {
                characterController.Sad(duration);
            }
            else
            {
                // Fallback for high valence, low arousal
                characterController.Happy(duration);
            }
        }
    }
}
