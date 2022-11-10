/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Prl.Scripts.ScriptableObjects.Variables;
using Prl.Scripts.ScriptableObjects.Events;

public class PublishPose : MonoBehaviour
{
    [SerializeField]
    private TransformVariable Pose;
    [SerializeField]
    private GameEvent Event;

    public void SendPose()
    {
        Pose.Position = gameObject.transform.localPosition;
        Pose.Rotation = gameObject.transform.localRotation;
        Event.Raise();
    }
}
