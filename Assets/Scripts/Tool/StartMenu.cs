using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

/*
 * Author: Yangyulin Ai
 * University of Technology Sydney (UTS)
 * Sydney, 10th October, 2022
 * Email: Yangyulin.ai-1@student.uts.edu.au
 */

public class StartMenu : MonoBehaviour
{
    public void PlayGame()
    {
        SceneManager.LoadScene(1);//load the scene 1 - Asserts/Scenes/Timer
    }

    public void Tutorial()
    {
        SceneManager.LoadScene(3);//load the scene 3 - Assets/Scenes/Tutorial
    }
}
