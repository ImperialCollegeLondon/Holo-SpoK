/*
Personal Robotics Lab - Imperial College London, 2021
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using System;
using TMPro;
using UnityEngine;

namespace com.prl.rosbridge
{

    /// <summary>
    /// Handles the IP configuration of the RosBridgeIPScene.
    /// </summary>
    public class IpInputHandler : MonoBehaviour
    {
        #region Public Fields
        public TMP_InputField Input;
        #endregion

        #region Private Fields
        private string prefill;
        private Action<string> _confirmClick;
        #endregion

        #region Public Methods
        public void Init(Action<string> confirmClick, string ip)
        {
            Input.text = ip;
            prefill = ip;
            _confirmClick = confirmClick;
        }

        public void OnEditClicked()
        {
            OpenSystemKeyboard();
        }

        public void OnConfirmButtomClicked()
        {
            _confirmClick?.Invoke(Input.text);
        }
        #endregion

        #region Private Methods
        private void OpenSystemKeyboard()
        {
            TouchScreenKeyboard.Open(prefill, TouchScreenKeyboardType.URL, false, false, false, false);
            Input.ActivateInputField();
        }
        #endregion
    }
}
