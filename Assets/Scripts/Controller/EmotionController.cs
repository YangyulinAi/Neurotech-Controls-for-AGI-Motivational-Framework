using UnityEngine;
using System.Collections;

namespace Asset
{
    public class EmotionController : MonoBehaviour
    {
        public BciClientWebSocket bciClient;
        private CharacterController characterController;

        private float prevValence = float.NaN;
        private float prevArousal = float.NaN;

        private bool isCoolingDown = false;
        private const float duration = 2f;

        void Awake()
        {
            characterController = FindObjectOfType<CharacterController>();
            if (bciClient == null)
                bciClient = FindObjectOfType<BciClientWebSocket>();
        }

        void Update()
        {
            if (bciClient == null || isCoolingDown) return;

            float v = bciClient.Valence;
            float a = bciClient.Arousal;

            if (!Mathf.Approximately(v, prevValence) || !Mathf.Approximately(a, prevArousal))
            {
                DecideAction(v, a);
                prevValence = v;
                prevArousal = a;
                StartCoroutine(Cooldown());
            }
        }

        private void DecideAction(float v, float a)
        {
            if (v > 0.5f && a > 0.5f)
                characterController.Happy(duration);
            else if (v <= 0.5f && a > 0.5f)
                characterController.Angry(duration);
            else if (v <= 0.5f && a <= 0.5f)
                characterController.Sad(duration);
            else
                characterController.Happy(duration);
        }

        private IEnumerator Cooldown()
        {
            isCoolingDown = true;
            yield return new WaitForSeconds(duration);
            isCoolingDown = false;
        }
    }
}
