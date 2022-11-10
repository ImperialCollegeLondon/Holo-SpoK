/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Prl.Scripts.ScriptableObjects.Variables;

public class ToggleRenderers : MonoBehaviour
{
    [SerializeField]
    private BoolVariable toggle;
    public void Toggle()
    {
        Renderer[] rs = GetComponentsInChildren<Renderer>();
        foreach (Renderer r in rs)
        {
            r.enabled = !toggle.value;
        }
    }
}
