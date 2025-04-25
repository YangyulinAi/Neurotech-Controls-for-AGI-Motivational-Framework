using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Asset
{
    /// <summary>
    /// Manages a character instance: plays expressions and walking,
    /// and keeps the character visible after actions complete.
    /// </summary>
    public class CharacterController : MonoBehaviour
    {
        [Header("Settings")]
        [Tooltip("List of character prefabs to instantiate")]
        public List<GameObject> characterPrefabs;

        [Tooltip("List of effect prefabs corresponding to expressions")]
        public List<GameObject> effectPrefabs;

        [Tooltip("Parent transform under which the character will be instantiated")]
        public Transform characterParent;

        [Tooltip("Transform representing the spawn position for the character")]
        public Transform spawnPos;

        private GameObject currentCharacter;
        private GameObject currentCharacterStyle;

        /// <summary>
        /// Make character show a happy expression for a given duration.
        /// </summary>
        public void Happy(float duration)
        {
            StartCoroutine(Emotion(0, "Front", "happyFront", 0, "happy", duration));
        }

        /// <summary>
        /// Make character show an angry expression for a given duration.
        /// </summary>
        public void Angry(float duration)
        {
            StartCoroutine(Emotion(0, "Front", "angryFront", 1, "angry", duration));
        }

        /// <summary>
        /// Make character show a sad expression for a given duration.
        /// </summary>
        public void Sad(float duration)
        {
            StartCoroutine(Emotion(0, "Front", "sadFront", 2, "sad", duration));
        }

        /// <summary>
        /// Walk the character from spawn position to a destination coordinate.
        /// </summary>
        public void Walk(Vector3 destination)
        {
            StartCoroutine(WalkTo(destination));
        }

        // Internal coroutine that handles emotion animations and effects.
        private IEnumerator Emotion(int characterID, string style, string animation, int effectID, string effectAnimation, float duration)
        {
            DestroyAll();

            // Instantiate and position the character
            currentCharacter = Instantiate(characterPrefabs[characterID], characterParent);
            currentCharacter.transform.position = spawnPos.position;

            // Activate the correct style child and find effect parent
            Transform effectParent = null;
            currentCharacterStyle = null;
            foreach (Transform t in currentCharacter.GetComponentsInChildren<Transform>())
            {
                if (t == currentCharacter.transform) continue;
                bool isStyle = (t.name == style);
                bool isEffect = (t.name == "Effect");
                t.gameObject.SetActive(isStyle || isEffect);
                if (isStyle) currentCharacterStyle = t.gameObject;
                if (isEffect) effectParent = t;
            }

            // Play character animation
            currentCharacterStyle.GetComponent<Animator>().Play(animation);

            // Play effect animation if specified
            GameObject spawnedEffect = null;
            if (effectID >= 0)
            {
                spawnedEffect = Instantiate(effectPrefabs[effectID], effectParent);
                spawnedEffect.GetComponent<Animator>().Play(effectAnimation);
                // Automatically destroy the effect after its clip length
                float effectLength = spawnedEffect.GetComponent<Animator>()
                    .GetCurrentAnimatorStateInfo(0).length;
                Destroy(spawnedEffect, effectLength);
            }

            // Wait for the specified duration
            yield return new WaitForSeconds(duration);

            // Character remains visible; no DestroyAll here
        }

        // Internal coroutine to walk the character to a target point.
        private IEnumerator WalkTo(Vector3 destination)
        {
            DestroyAll();

            // Instantiate character in side view
            currentCharacter = Instantiate(characterPrefabs[0], characterParent);
            currentCharacter.transform.position = spawnPos.position;

            // Activate side-view style only
            currentCharacterStyle = null;
            foreach (Transform t in currentCharacter.GetComponentsInChildren<Transform>())
            {
                if (t == currentCharacter.transform) continue;
                bool isSide = (t.name == "Side");
                t.gameObject.SetActive(isSide);
                if (isSide) currentCharacterStyle = t.gameObject;
            }

            // Play walk animation
            currentCharacterStyle.GetComponent<Animator>().Play("walk");

            // Move character until reaching destination
            while (Vector3.Distance(currentCharacter.transform.position, destination) > 0.1f)
            {
                currentCharacter.transform.position = Vector3.MoveTowards(
                    currentCharacter.transform.position,
                    destination, 2f * Time.deltaTime);
                yield return null;
            }
            // Character remains at destination; no reset
        }

        // Utility to destroy all previous instances under characterParent
        private void DestroyAll()
        {
            for (int i = characterParent.childCount - 1; i >= 0; i--)
            {
                Destroy(characterParent.GetChild(i).gameObject);
            }
        }
    }
}
