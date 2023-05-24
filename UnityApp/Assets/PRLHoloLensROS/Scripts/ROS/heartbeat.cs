/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using RosSharp;
using RosSharp.RosBridgeClient;
using RosSharp.RosBridgeClient.MessageTypes.Std;
using UnityEngine;

public class heartbeat : UnitySubscriber<RosSharp.RosBridgeClient.MessageTypes.Std.String>
{
    [SerializeField]
    private int timeOutSecondsThreshold = 2;

    private bool receivedMsg = false;
    private bool reconnectSent = false;
    private float lastTimeClockReceived = -1;
    private RosConnector rosConnector;

    // Start is called before the first frame update
    protected override void Start()
    {
        base.Start();
        rosConnector = GetComponent<RosConnector>();
    }

    void Update()
    {
        if (receivedMsg)
        {
            lastTimeClockReceived = UnityEngine.Time.realtimeSinceStartup;
            receivedMsg = false;
            reconnectSent = false;
        }
        float noMessageSinceSeconds = UnityEngine.Time.realtimeSinceStartup - lastTimeClockReceived;
        if (noMessageSinceSeconds > timeOutSecondsThreshold && reconnectSent == false)
        {
            rosConnector.Reconnecting();
            reconnectSent = true;
        }
    }

    protected override void ReceiveMessage(String message)
    {
        receivedMsg = true;
    }

}
