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

    public class StringPublisher : UnityPublisher<MessageTypes.Std.String>
    {
        [SerializeField]
        private StringVariable anchorID;

        private MessageTypes.Std.String message;

        // Start is called before the first frame update
        protected override void Start()
        {
            base.Start();
            InitializeMessage();
        }

        public void PublishString()
        {
            UpdateMessage();
            Publish(message);
        }

        private void InitializeMessage()
        {
            message = new MessageTypes.Std.String();
        }

        private void UpdateMessage()
        {
            message.data = anchorID.value;
        }

    }
}
