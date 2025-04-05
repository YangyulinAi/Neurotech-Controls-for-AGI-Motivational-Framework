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
        // Arrow Direction 
        {"Rest",50 },
        {"Up", 80},
        {"Down", 20},
        {"Left Close", 40},
        {"Right Close", 60},
        {"Up Left Close", 70},
        {"Up Right Close", 90},
        {"Left Far", 41},
        {"Right Far", 61},
        {"Up Left Far", 71},
        {"Up Right Far", 91},

        // Number Shown
        {"One", 11},
        {"Two", 22},
        {"Three", 33},
        {"Four", 44},
        {"Five", 55},
        {"Six", 66},
        {"Seven", 77},
        {"Eight", 88},
        {"Nine", 99},

        // User Res
        {"0", 0},//Not press
        {"1", 1},// Pressed

        {"UserRes", 254},
        { "UserNotRes", 255},

        // Epoch
        {"Start", 101},
        {"End", 102},

        // User Res Checker
        {"True", 201},
        {"False", 202},

        // Number Show/Hide
        {"NumberShow", 111},
        {"NumberHide", 112},

        // Bad Epoch
        {"Bad", 222}

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
