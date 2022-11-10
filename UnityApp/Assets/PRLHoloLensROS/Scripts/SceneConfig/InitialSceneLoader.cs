/*
Personal Robotics Lab - Imperial College London, 2021
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using UnityEngine.SceneManagement;

using Microsoft.MixedReality.Toolkit;
using Microsoft.MixedReality.Toolkit.SceneSystem;

namespace com.prl.mrtk
{
    public class InitialSceneLoader : MonoBehaviour
    {
        #region Private Serializable Fields
        [SerializeField]
        private string StartSceneName = "";
        #endregion

        #region MonoBehaviour Methods
        void Start()
        {
            if (!string.IsNullOrEmpty(StartSceneName))
            {
                LoadScene();
            }
        }
        #endregion

        #region Private Methods
        private async void LoadScene()
        {
            IMixedRealitySceneSystem sceneSystem = MixedRealityToolkit.Instance.GetService<IMixedRealitySceneSystem>();
            if (!sceneSystem.IsContentLoaded(StartSceneName))
                await sceneSystem.LoadContent(StartSceneName, LoadSceneMode.Single);
        }
        #endregion
    }
}