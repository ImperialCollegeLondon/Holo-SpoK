/*
Personal Robotics Lab - Imperial College London, 2021
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using System;
using UnityEngine;
using UnityEngine.SceneManagement;

using Microsoft.MixedReality.Toolkit;
using Microsoft.MixedReality.Toolkit.SceneSystem;


namespace com.prl.rosbridge
{

    public class RosBridgeIP : MonoBehaviour
    {
        #region Private Fields
        private Uri unusedUri;
        #endregion

        #region MonoBehaviour Methods
        void Start()
        {
            if (String.IsNullOrEmpty(PlayerPrefs.GetString("server_address")))
            {
                PlayerPrefs.SetString("server_address", "ws://10.0.0.109:9090");
            }

            IpInputHandler ipInput = GetComponentInChildren<IpInputHandler>();

            ipInput.Init(OkButtomPressed, PlayerPrefs.GetString("server_address"));
        }
        #endregion

        #region Public Methods
        public void OkButtomPressed(string serverAddress)
        {
            //Should be a valid websocket address
            if (!serverAddress.StartsWith("ws://"))
            {
                Debug.Log("URI is not valid. The URI must be a websocket starting with ws://");
                return;
            }

            //Should be a valid URI
            if (!Uri.TryCreate(serverAddress, UriKind.Absolute, out unusedUri))
            {
                Debug.Log("URI is not valid. The URI provided could not be converted into a valid absolute URI. The typical IP is ws://192.168.1.X:9090");
                return;
            }

            AcceptInput(serverAddress);
        }
        #endregion

        #region Private Methods
        private async void AcceptInput(string ip)
        {
            PlayerPrefs.SetString("server_address", ip);
            PlayerPrefs.Save();

            IMixedRealitySceneSystem sceneSystem = MixedRealityToolkit.Instance.GetService<IMixedRealitySceneSystem>();
            await sceneSystem.LoadContent("MainScene", LoadSceneMode.Single);
        }
        #endregion
    }
}
