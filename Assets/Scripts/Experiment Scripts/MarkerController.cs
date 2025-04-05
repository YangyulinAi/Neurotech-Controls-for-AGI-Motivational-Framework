/**
 * Author: Yangyulin Ai
 * Email: Yangyulin-1@student.uts.edu.au
 * Date: 2024-03-18
 */

using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class MarkerController
{
    private byte? marker;
    private LSLSender lslSender;
    private UDPSender udpSender;

    private Dictionary<string, byte> markerValues = new Dictionary<string, byte>
    {
        // Experiment Start/End
        {"Exp Start",100},
        {"Exp End", 109},

        // Rest Stage
        {"Open Start", 110},
        {"Open End", 119},
        {"Close Start", 120},
        {"Close End", 129},

        // Video Stage
        {"Video Start", 200},
        {"Video End", 209},

        // Video Type
        {"Neutral", 201},
        {"Amusement", 202},
        {"Sadness", 203},
        {"Anger", 204},
        {"Fear", 205},
        {"Disgust", 206},

        // Valence Rating Stage
        {"Valence Rating Start", 210},
        {"Valence Rating End", 219},

        // User Res - Valence
        {"Valence 1", 211},
        {"Valence 2", 212},
        {"Valence 3", 213},
        {"Valence 4", 214},
        {"Valence 5", 215},

        // Arousal Rating Stage
        {"Arousal Rating Start", 220},
        {"Arousal Rating End", 229},

        // User Res - Arousal
        {"Arousal 1", 221},
        {"Arousal 2", 222},
        {"Arousal 3", 223},
        {"Arousal 4", 224},
        {"Arousal 5", 225},

        // User Res
        {"Press", 1}

    };

    public MarkerController(string IP, int port)
    {
        lslSender = new LSLSender();

        if (lslSender == null)
        {
            Debug.LogError("<color=red>LSLSender component not found.</color>");
        }

        udpSender = new UDPSender(IP, port);

        if (udpSender == null)
        {
            Debug.LogError("<color=red>UDPSender component not found.</color>");
        }
    }


    public bool SendMarker(string key)
    {
        if(GetMarkerValue(key))
        {
            // Send LSL message
            if (this.marker.HasValue && lslSender != null)
            {
                //return lslSender.SendMarker(this.marker);
            }
            // Send UDP message
            if (this.marker.HasValue && udpSender != null)
            {
                return udpSender.SendUDPMessage(this.marker);
            }

            SetMarker(null);// After sent the marker set it to null for safty
            return true;
        }

        return false;
    }

    private bool GetMarkerValue(string key)
    {
        if (markerValues.TryGetValue(key, out byte value))
        {
            this.marker = value;
            return true;
        }

        this.marker = null; // Returning null means that the corresponding value was not found
        return false;
    }

    private void SetMarker(byte? marker)
    {
        this.marker = marker;
    }
}
