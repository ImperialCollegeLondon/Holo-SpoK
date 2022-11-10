/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using System.Collections.Generic;

namespace Prl.Scripts.ScriptableObjects.Events
{
    [CreateAssetMenu]
    public class GameEvent : ScriptableObject
    {

        private List<GameEventListener> listeners = new List<GameEventListener>();

        public void Raise()
        {
            Debug.LogFormat("GameEvent::Raise - listeners.Count: {0}", listeners.Count);
            for (int i = listeners.Count - 1; i >= 0; i--)
                listeners[i].OnEventRaised();
        }

        public void RegisterListener(GameEventListener listener)
        {
            listeners.Add(listener);
        }

        public void UnregisterListener(GameEventListener listener)
        {
            listeners.Remove(listener);
        }
    }
}