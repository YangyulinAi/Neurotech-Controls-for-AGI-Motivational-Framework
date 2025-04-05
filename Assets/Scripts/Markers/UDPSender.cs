/**
 * Author: Yangyulin Ai
 * Email: Yangyulin-1@student.uts.edu.au
 * Date: 2024-03-18
 */

using UnityEngine;
using System.Net;
using System.Net.Sockets;
using System.Text;

public class UDPSender
{
    public string IP = "192.168.1.11";
    public int port = 9999;

    private UdpClient udpClient;

    public UDPSender(string IP, int port)
    {
        this.IP = IP;
        this.port = port;
        udpClient = new UdpClient();
    }


    public bool SendUDPMessage(byte? value)
    {
        try
        {
            string message = value.ToString();
            byte[] bytesToSend = Encoding.ASCII.GetBytes(message);  // Convert the string to an ASCII byte array
            udpClient.Send(bytesToSend, bytesToSend.Length, IP, port);  // Send UDP message
            Debug.Log($"<color=blue>Sent UDP marker: {value}</color>");
            return true;
        }
        catch (System.Exception ex)
        {
            Debug.LogError($"<color=red>Error sending UDP marker: {ex.Message}</color>");
            return false;
        }
    }

    void OnDestroy()
    {
        udpClient.Close();
    }
}
