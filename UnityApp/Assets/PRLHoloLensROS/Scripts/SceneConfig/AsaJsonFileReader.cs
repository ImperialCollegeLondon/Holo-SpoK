/*
Personal Robotics Lab - Imperial College London, 2022
Author: Rodrigo Chacon Quesada (rac17@ic.ac.uk)

Licensed under Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International
(https://creativecommons.org/licenses/by-nc-sa/4.0/legalcode)
*/

using UnityEngine;
using Microsoft.Azure.SpatialAnchors.Unity;

[RequireComponent(typeof(SpatialAnchorManager))]
public class AsaJsonFileReader : MonoBehaviour
{
    // Start is called before the first frame update
    void Start()
    {
        //Load text from  JSON file (Assets/Resources/azure_asa_account_config.json)
        var jsonTextFile = Resources.Load<TextAsset>("azure_asa_account_config");
        //Then use JsonUtility.FromJson<T>() to deserialize jsonTextFile into an object
        AzureConfig config = AzureConfig.CreateFromJSON(jsonTextFile.ToString());

        //Load credentials into script
        SpatialAnchorManager anchorManager = gameObject.GetComponent<SpatialAnchorManager>();
        anchorManager.SpatialAnchorsAccountId = config.AccountId;
        anchorManager.SpatialAnchorsAccountKey = config.AccountKey;
        anchorManager.SpatialAnchorsAccountDomain = config.AccountDomain;
    }

}

[System.Serializable]
public class AzureConfig
{
    public string AccountId;
    public string AccountKey;
    public string AccountDomain;

    public static AzureConfig CreateFromJSON(string jsonString)
    {
        return JsonUtility.FromJson<AzureConfig>(jsonString);
    }

}
