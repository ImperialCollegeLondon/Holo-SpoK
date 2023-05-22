/*
Personal Robotics Lab - Imperial College London, 2023
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Prl.Scripts.ScriptableObjects.Variables;
using Prl.Scripts.ScriptableObjects.Events;
using Microsoft.MixedReality.Toolkit.Utilities;
using Microsoft.MixedReality.Toolkit.Input;

public class ComeHere : MonoBehaviour
{

    [SerializeField]
    private TransformVariable Pose;
    [SerializeField]
    private GameEvent Event;

    public Transform ParentFrame;

    public void SendPose()
    {
        Pose.Position = ParentFrame.InverseTransformPoint(CameraCache.Main.transform.position);
        Pose.Rotation = Quaternion.FromToRotation(ParentFrame.forward, CameraCache.Main.transform.forward);
        Event.Raise();
    }
}