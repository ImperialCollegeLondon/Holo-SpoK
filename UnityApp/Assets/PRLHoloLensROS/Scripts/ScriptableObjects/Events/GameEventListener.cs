/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using UnityEngine.Events;

namespace Prl.Scripts.ScriptableObjects.Events
{
    public class GameEventListener : MonoBehaviour
    {

        public GameEvent Event;
        public UnityEvent Response;

        private void OnEnable()
        {
            Debug.Log("GameEventListener::OnEnable");
            Event.RegisterListener(this);
        }

        private void OnDisable()
        {
            Event.UnregisterListener(this);
        }

        public void OnEventRaised()
        {
            Debug.Log("GameEventListener::OnEventRaised");
            Response.Invoke();
        }
    }
}