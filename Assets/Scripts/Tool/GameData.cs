using System.Collections;
using System.Collections.Generic;
using UnityEngine;

/*
 * Author: Yangyulin Ai
 * University of Technology Sydney (UTS)
 * Sydney, 10th October, 2022
 * Email: Yangyulin.ai-1@student.uts.edu.au
 */


/* All the cross script parameters should be passed in this class */
public class GameData : MonoBehaviour
{
    //Cross scripts parameters
    public int param = 1;//current running time
    public int random;   //situation seed: 0-49 repersent situation 1, and 50-100 repersent situation 2

    void Start()
    {
        GetRandomSeed();
    }

    void Awake()
    { 
        DontDestroyOnLoad(transform.gameObject);//keep the object to pass the parameter
    }

    void GetRandomSeed()
    {
        System.Random ran = new System.Random();//Using random funtion to get a random number from 0 - 100
        random = ran.Next(100);
    }
}
