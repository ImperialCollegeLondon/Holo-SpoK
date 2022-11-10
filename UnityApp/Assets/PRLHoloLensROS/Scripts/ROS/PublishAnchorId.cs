/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)
Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using System.IO;
using UnityEngine;
using Prl.Scripts.ScriptableObjects.Variables;
using Prl.Scripts.ScriptableObjects.Events;

#if WINDOWS_UWP
using Windows.Storage;
#endif

public class PublishAnchorId : MonoBehaviour
{
    [SerializeField]
    private StringVariable String;
    [SerializeField]
    private GameEvent Event;

    public void SendAnchorId()
    {
        string filename = "SavedAzureAnchorID.txt";
        string path = Application.persistentDataPath;

#if WINDOWS_UWP
        StorageFolder storageFolder = ApplicationData.Current.LocalFolder;
        path = storageFolder.Path.Replace('\\', '/') + "/";
#endif

        string filePath = Path.Combine(path, filename);
        String.value = File.ReadAllText(filePath);

        Event.Raise();
    }
}
