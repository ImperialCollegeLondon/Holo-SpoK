/*
© Siemens AG, 2017-2019
Author: Dr. Martin Bischoff (martin.bischoff@siemens.com)

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
*/

using System;
using System.Collections;
using System.Threading;
using RosSharp.RosBridgeClient.Protocols;
using UnityEngine;

namespace RosSharp.RosBridgeClient
{
    public class RosConnector : MonoBehaviour
    {
        public int SecondsTimeout = 10;

        public RosSocket RosSocket { get; private set; }
        public RosSocket.SerializerEnum Serializer;
        public Protocol protocol;
        public string RosBridgeServerUrl = "ws://localhost:9090";

        public ManualResetEvent IsConnected { get; private set; }

        //Added for heartbeat signal logic
        [SerializeField]
        private bool autoReconnectOnConnectionLost = true;
        private bool manualOnCloseTrigger = false;
        private bool startReconnectionCycle = true;

        public bool isConnected = false;

        public event EventHandler OnRosConnectorReConnected;

        public virtual void Awake()
        {
            RosBridgeServerUrl = PlayerPrefs.GetString("server_address");

            if (String.IsNullOrEmpty(RosBridgeServerUrl))
                RosBridgeServerUrl = "ws://10.0.0.145:9090";
#if WINDOWS_UWP
            // overwrite selection
            protocol = Protocol.WebSocketUWP;
#endif
            IsConnected = new ManualResetEvent(false);
#if WINDOWS_UWP
            //Modified for heartbeat logic
            //ConnectAndWait();
            manualOnCloseTrigger = true;
#else
            new Thread(ConnectAndWait).Start();
#endif
        }

        //Added for heartbeat signal
        public void Update()
        {
            if (startReconnectionCycle)
            {
                startReconnectionCycle = false;
                StartCoroutine(Reconnect());
            }
        }

        protected void ConnectAndWait()
        {
            RosSocket = ConnectToRos(protocol, RosBridgeServerUrl, OnConnected, OnClosed, Serializer);

            //Removed for heartbeat logic
            //if (!IsConnected.WaitOne(SecondsTimeout * 1000))
                //Debug.LogWarning("Failed to connect to RosBridge at: " + RosBridgeServerUrl);
        }

        public static RosSocket ConnectToRos(Protocol protocolType, string serverUrl, EventHandler onConnected = null, EventHandler onClosed = null, RosSocket.SerializerEnum serializer = RosSocket.SerializerEnum.Microsoft)
        {
            IProtocol protocol = ProtocolInitializer.GetProtocol(protocolType, serverUrl);
            protocol.OnConnected += onConnected;
            protocol.OnClosed += onClosed;

            return new RosSocket(protocol, serializer);
        }

        private static RosBridgeClient.Protocols.IProtocol GetProtocol(Protocol protocol, string rosBridgeServerUrl)
        {

#if WINDOWS_UWP
            Debug.Log("Defaulted to UWP Protocol");
            return new RosBridgeClient.Protocols.WebSocketUWPProtocol(rosBridgeServerUrl);
#else
            switch (protocol)
            {
                case Protocol.WebSocketNET:
                    return new RosBridgeClient.Protocols.WebSocketNetProtocol(rosBridgeServerUrl);
                case Protocol.WebSocketSharp:
                    return new RosBridgeClient.Protocols.WebSocketSharpProtocol(rosBridgeServerUrl);
                case Protocol.WebSocketUWP:
                    Debug.Log("WebSocketUWP only works when deployed to HoloLens, defaulting to WebSocketNetProtocol");
                    return new RosBridgeClient.Protocols.WebSocketNetProtocol(rosBridgeServerUrl);
                default:
                    return null;
            }
#endif
        }

        private void OnApplicationQuit()
        {
            RosSocket.Close();
        }

        private void OnConnected(object sender, EventArgs e)
        {
            //Added for heartbeat logic
            isConnected = true;
            IsConnected.Set();
            //Removed for heartbeat logic
            //Debug.Log("Connected to RosBridge: " + RosBridgeServerUrl);
            OnRosConnectorReConnected?.Invoke(this, EventArgs.Empty);
        }

        private void OnClosed(object sender, EventArgs e)
        {
            //Added for heartbeat logic
            isConnected = false;
            IsConnected.Reset();
            //Removed for heartbeat logic
            //Debug.Log("Disconnected from RosBridge: " + RosBridgeServerUrl);
        }

        // Added for heartbeat logic
        private IEnumerator Reconnect()
        {
            if (isConnected)
                yield break;

            new Thread(ConnectAndWait).Start();
            yield return new WaitForSeconds(2);

            if (isConnected)
                yield break;

            yield return Reconnect();
        }

        public void Reconnecting()
        {
            if (autoReconnectOnConnectionLost)
            {
                startReconnectionCycle = true;
            }
            if (manualOnCloseTrigger)
            {
                OnClosed(this, EventArgs.Empty);
            }
        }
    }
}
