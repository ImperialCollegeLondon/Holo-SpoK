/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Microsoft.MixedReality.Toolkit.Utilities;

using Prl.Scripts.ScriptableObjects.Variables;

public class Follow : MonoBehaviour
{
    public GameObject TargetObject;
    public GameObject SpotBaseLink;
    public GameObject GoalMarker;

    [SerializeField]
    private BoolVariable FollowMode;

    // Update is called once per frame
    void Update()
    {
        if (FollowMode.value == true)
        {

            TargetObject.transform.position = CameraCache.Main.transform.position;
            TargetObject.transform.rotation = CameraCache.Main.transform.rotation;


            Vector3 worldCoords = TargetObject.transform.TransformPoint(SpotBaseLink.transform.localPosition);
            Vector3 SpotBaseToTargetObject_World = SpotBaseLink.transform.position - worldCoords;
            Vector2 xyTarget_World = new Vector2(SpotBaseToTargetObject_World.x, SpotBaseToTargetObject_World.z);

            float xyDistance = xyTarget_World.magnitude;

            if (xyDistance > 1.75f)
            {
                Vector3 newGoalMarkerPos = new Vector3(TargetObject.transform.position.x, GoalMarker.transform.position.y, TargetObject.transform.position.z);
                Vector3 currentGoalMarkerPos = GoalMarker.transform.position;
                Vector3 new2 = newGoalMarkerPos - (newGoalMarkerPos - currentGoalMarkerPos).normalized * 0.5f;

                GoalMarker.transform.position = new2;
                GoalMarker.transform.LookAt(newGoalMarkerPos);

                GoalMarker.GetComponent<PublishPose>().SendPose();
            }

        }
        else
        {
            return;
        }
    }
}
