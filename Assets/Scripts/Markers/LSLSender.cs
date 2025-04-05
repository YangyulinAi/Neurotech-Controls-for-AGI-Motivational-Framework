/**
 * Author: Yangyulin Ai
 * Email: Yangyulin-1@student.uts.edu.au
 * Date: 2024-03-18
 */



using System.Collections;
using UnityEngine;
using LSL;
using Assets.LSL4Unity.Scripts;

public class LSLSender
{
    private liblsl.StreamInfo streaminfo;
    private liblsl.StreamOutlet outlet;

    public string StreamName = "Hybrid Attention";
    public string StreamType = "Markers";
    public int ChannelCount = 1;
    private double dataRate = liblsl.IRREGULAR_RATE;

    public LSLSender()
    {
        SetupLSL();
    }

    public bool SendMarker(byte? eventMarker)
    {
        string[] markerData = { eventMarker.ToString() };
        if (outlet != null)
        {
            outlet.push_sample(markerData, liblsl.local_clock());
            Debug.Log($"<color=blue>Sent LSL marker: {markerData[0]}</color>");
            return true;
        }
        Debug.LogError($"<color=red>Error sending LSL marker: {markerData[0]}</color>");
        return false;
    }

    void SetupLSL()
    {
        var hash128 = new Hash128();
        hash128.Append(StreamName);
        hash128.Append(StreamType);

        streaminfo = new liblsl.StreamInfo(StreamName, StreamType, ChannelCount, dataRate, liblsl.channel_format_t.cf_string, hash128.ToString());
        outlet = new liblsl.StreamOutlet(streaminfo);
    }
}
