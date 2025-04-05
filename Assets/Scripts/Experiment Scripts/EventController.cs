using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using System;
using UnityEngine.Video;
using UnityEngine.UI;

/*
 * Updated by Yangyulin Ai
 * This script controls the experiment workflow with the following stages:
 *   Stage 1: Video playback phase (input disabled)
 *   Stage 2: Valence rating phase
 *   Stage 3: Arousal rating phase
 * After Stage 3 completes, it automatically switches back to Stage 1 to play the next video.
 * Video files are loaded sequentially from the StreamingAssets folder.
 * This version directly controls the RawImage (which displays the video via a Render Texture)
 * and adjusts the hintText position through code.
 */
public class EventController : MonoBehaviour
{
    // LSL related parameters
    //private liblsl.StreamInfo streaminfo;
    //private liblsl.StreamOutlet outlet;
    //string StreamName = "Neuroteach-AGI";
    //string StreamType = "Markers";
    //public int ChannelCount = 1;
    //private double dataRate = liblsl.IRREGULAR_RATE;

    // UI components: Hint text for displaying instructions
    public Text hintText;
    public float hintDisplayTime = 20f;

    // VideoPlayer component (ensure its Render Mode is set to Render Texture)
    public VideoPlayer videoPlayer;

    // RawImage used to display the video (its Texture must be set to the VideoPlayer's Render Texture)
    public RawImage rawImage;

    public string[,] videoData = new string[,] {
    { "49.mp4", "Neutral" },
    { "2.mp4", "Anger" },  
    { "52.mp4", "Sadness" },
    { "44.mp4", "Amusement" },
    { "7.mp4", "Fear" },
    { "10.mp4", "Disgust" },   
    { "24.mp4", "Fear" },
    { "45.mp4", "Neutral" },
    { "5.mp4", "Anger" },
    { "46.mp4", "Sadness" },
    { "17.mp4", "Disgust" },
    { "23.mp4", "Amusement" }};


    // Global stage variable:
    // stage 0: Resting phase (包含睁眼和闭眼)
    // stage 1: Video playback phase
    // stage 2: Valence rating phase
    // stage 3: Arousal rating phase
    private int stage = 0;
    private bool hasRating = false;
    private int orderNum = 0;
    private int clipIndex = 0;

    /// <summary>
    ///  For Merker Controller
    /// </summary>
    private MarkerController markerController;
    public string IP = "192.168.1.11";
    public int port = 9999;

    void Start()
    {
        //SetupLSL();
        hintText.gameObject.SetActive(false);
        // Register the event for when the video playback finishes
        videoPlayer.loopPointReached += OnVideoFinished;
        // Ensure RawImage is active at start so the video is visible
        rawImage.gameObject.SetActive(true);
        // Set initial hint text position (e.g., top center) by adjusting its anchored position.
        // Adjust the Vector2 values as needed.
        SetHintTextPosition(new Vector2(0, 200));
        SetMarkerController();
        SendMarker("Exp Start");
        StartCoroutine(RestingPhase());
    }

    void Update()
    {
        // Only listen for rating input during Stage 2 (Valence) or Stage 3 (Arousal)
        if (stage == 2 || stage == 3)
        {
            if (stage == 2 && !hasRating)
            {
                SendMarker("Valence Rating Start");
                hasRating = true;
            }
            else
            {
                SendMarker("Arousal Rating Start");
                hasRating = true;
            }

            if (Input.GetKeyDown(KeyCode.Alpha1) || Input.GetKeyDown(KeyCode.Keypad1))
            {
                ProcessUserInput(1);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha2) || Input.GetKeyDown(KeyCode.Keypad2))
            {
                ProcessUserInput(2);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha3) || Input.GetKeyDown(KeyCode.Keypad3))
            {
                ProcessUserInput(3);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha4) || Input.GetKeyDown(KeyCode.Keypad4))
            {
                ProcessUserInput(4);
            }
            else if (Input.GetKeyDown(KeyCode.Alpha5) || Input.GetKeyDown(KeyCode.Keypad5))
            {
                ProcessUserInput(5);
            }
        }
    }

    private IEnumerator RestingPhase()
    {
   
        stage = 0;
        hintText.text = "Rest phase: Keep your eyes open for 60 seconds.";
        hintText.gameObject.SetActive(true);
        SendMarker("Open Start");
        Debug.Log("Resting Phase: Open Start");
        yield return new WaitForSeconds(60f);
        SendMarker("Open End");
        Debug.Log("Resting Phase: Open End");


        hintText.text = "Resting phase: Keep your eyes closed for 60 seconds.";
        SendMarker("Close Start");
        Debug.Log("Resting Phase: Close Start");
        yield return new WaitForSeconds(60f);
        SendMarker("Close End");
        Debug.Log("Resting Phase: Close End");


        hintText.gameObject.SetActive(false);
        stage = 1;
        PlayVideoClip(clipIndex);
    }


    /// <summary>
    /// Plays the video file at the given index and sets stage = 1 (video playback phase).
    /// </summary>
    /// <param name="index">Index of the video in videoFileNames array.</param>
    void PlayVideoClip(int index)
    {
        if (index < videoData.GetLength(0))
        {
            SendMarker("Video Start");

            string videoType = videoData[index, 1];
            SendMarker(videoType);

            stage = 1;
            rawImage.gameObject.SetActive(true);

            string fileName = videoData[index, 0];
            string fullPath = "file://" + Application.streamingAssetsPath + "/" + fileName;
            videoPlayer.url = fullPath;
            videoPlayer.Play();
            hintText.gameObject.SetActive(false);
            Debug.Log("Playing video: " + fileName + " with type: " + videoType);
        }
        else
        {
            Debug.Log("All videos have been played.");
            SendMarker("Exp End");
            StartCoroutine(StopAfterSendingMarker(1f));
        }
    }

    /// <summary>
    /// Called when video playback finishes. Hides the RawImage (thus hiding the video)
    /// and transitions to the rating phase: first Valence (stage = 2).
    /// </summary>
    /// <param name="vp">VideoPlayer instance that finished playing.</param>
    void OnVideoFinished(VideoPlayer vp)
    {
        SendMarker("Video End");
        // Hide the RawImage to hide the video display
        rawImage.gameObject.SetActive(false);
        stage = 2; // Switch to Valence rating phase
        hasRating = false;
        UpdateHintText();
        hintText.gameObject.SetActive(true);
        Debug.Log("Video finished, entering Valence rating stage.");
    }

    /// <summary>
    /// Updates the hintText based on the current stage.
    /// </summary>
    void UpdateHintText()
    {
        if (stage == 2)
        {
            hintText.text = "Please rate your emotional pleasantness (Valence): press keys 1-5";
        }
        else if (stage == 3)
        {
            hintText.text = "Please rate your activation level (Arousal): press keys 1-5";
        }
    }

    /// <summary>
    /// Processes the user input rating, sends marker, and transitions between stages.
    /// </summary>
    /// <param name="rating">User rating (1 to 5).</param>
    void ProcessUserInput(int rating)
    {
        SendMarker("Press");
        String marker_value = "";

        if (stage == 2)
        {
            marker_value += "Valence ";          
            // Send marker for the Valence phase, e.g. 900 + orderNum + 0.1 * rating
            //SendMarkerOnToggleSelection(0.1f * rating);
            Debug.Log("Valence rating: " + rating);
            // Transition to Arousal rating phase
            stage = 3;
            hasRating = false;
            UpdateHintText();
        }
        else if (stage == 3)
        {
            marker_value += "Arousal ";
            // Send marker for the Arousal phase, e.g. 900 + orderNum + 0.2 * rating
            //SendMarkerOnToggleSelection(0.2f * rating);
            Debug.Log("Arousal rating: " + rating);
            // After rating, update state and prepare next video
            orderNum++;
            clipIndex++;
            stage = 1; // Switch back to video playback phase
            hintText.gameObject.SetActive(false);
            // Activate RawImage for the next video display
            rawImage.gameObject.SetActive(true);
            StartCoroutine(WaitAndPlayNextVideo(1f));
        }
        SendMarker(marker_value + rating.ToString());
        SendMarker(marker_value + "Rating End");
    }

    private IEnumerator WaitAndPlayNextVideo(float waitTime)
    {
        yield return new WaitForSeconds(waitTime);
        PlayVideoClip(clipIndex);
    }


    public void SetHintTextPosition(Vector2 newPosition)
    {
        hintText.rectTransform.anchoredPosition = newPosition;
    }

    private void SetMarkerController()
    {
        markerController = new MarkerController(IP, port);
    }

    private void SendMarker(string marker)
    {
        if (markerController.SendMarker(marker))
        {
            //Debug.Log(marker);
        }
        else
        {
            Debug.LogError($"<color=red>Marker {marker} has failed to be sent</color>");
            Application.Quit();
        }
    }

    private IEnumerator StopAfterSendingMarker(float waitTime)
    {
        yield return new WaitForSeconds(waitTime);
        Application.Quit();
    }

}
