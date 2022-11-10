/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;

namespace Prl.Scripts.ScriptableObjects.Variables
{
    [CreateAssetMenu]
    public class TransformVariable : ScriptableObject
    {
        /// <summary>
        /// This makes it possible to create an ScriptableObject consisting from a single "Transform".
        /// Use the Assets/Create submenu to create and store an TransformVariable in the project as a ".asset" file.
        /// </summary>
        public Vector3 Position;
        public Quaternion Rotation;
    }
}
