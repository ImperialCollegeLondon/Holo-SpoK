/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Prl.Scripts.ScriptableObjects.Variables;

namespace RosSharp.RosBridgeClient
{
    public class StampedPosePublisher : UnityPublisher<MessageTypes.Geometry.PoseStamped>
    {
        public TransformVariable PublishedTransform;
        public string FrameId = "HoloLens";

        private MessageTypes.Geometry.PoseStamped message;

        // Start is called before the first frame update
        protected override void Start()
        {
            base.Start();
            InitializeMessage();
        }

        public void PublishPose()
        {
            UpdateMessage();
            Publish(message);
        }

        private void InitializeMessage()
        {
            message = new MessageTypes.Geometry.PoseStamped();
            message.header = new MessageTypes.Std.Header();
            message.header.frame_id = FrameId;
        }

        private void UpdateMessage()
        {
            message.header.Update();
            GetGeometryPoint(PublishedTransform.Position.Unity2Ros(), message.pose.position);
            GetGeometryQuaternion(PublishedTransform.Rotation.Unity2Ros(), message.pose.orientation);
        }

        private static void GetGeometryPoint(Vector3 position, MessageTypes.Geometry.Point geometryPoint)
        {
            geometryPoint.x = position.x;
            geometryPoint.y = position.y;
            geometryPoint.z = position.z;
        }

        private static void GetGeometryQuaternion(Quaternion quaternion, MessageTypes.Geometry.Quaternion geometryQuaternion)
        {
            geometryQuaternion.x = quaternion.x;
            geometryQuaternion.y = quaternion.y;
            geometryQuaternion.z = quaternion.z;
            geometryQuaternion.w = quaternion.w;
        }
    }
}
