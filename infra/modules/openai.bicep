@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the Azure OpenAI workspace')
param openAiName string

@description('Subnet ID for the Private Endpoint')
param subnetId string

resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Disabled' // Required zero-trust network policy
  }
}

resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-04-01' = {
  name: 'pe-${openAiName}'
  location: location
  properties: {
    subnet: {
      id: subnetId
    }
    privateLinkServiceConnections: [
      {
        name: 'plsc-${openAiName}'
        properties: {
          privateLinkServiceId: openAi.id
          groupIds: [
            'account'
          ]
        }
      }
    ]
  }
}
