/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Prl.Scripts.ScriptableObjects.Variables;
using Prl.Scripts.ScriptableObjects.Events;

public class ToggleFollowMode : MonoBehaviour
{
    [SerializeField]
    private BoolVariable FollowMode;
    [SerializeField]
    private GameEvent Event;

    public void Toggle()
    {
        FollowMode.value = !FollowMode.value;
        Event.Raise();
    }
}
