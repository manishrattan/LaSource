@description('Location for all resources.')
param location string = resourceGroup().location

@description('Name of the virtual network')
param vnetName string = 'vnet-lasource-shared'

@description('Name of the Azure OpenAI workspace')
param openAiName string = 'openai-lasource'

@description('Name of the Azure Firewall')
param firewallName string = 'afw-lasource-outbound'

// 1. Shared VNET
resource vnet 'Microsoft.Network/virtualNetworks@2023-04-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        '10.0.0.0/16'
      ]
    }
    subnets: [
      {
        name: 'snet-pe' // Subnet for Private Endpoints
        properties: {
          addressPrefix: '10.0.1.0/24'
          privateEndpointNetworkPolicies: 'Disabled'
        }
      }
      {
        name: 'AzureFirewallSubnet' // Required named subnet for Azure Firewall
        properties: {
          addressPrefix: '10.0.2.0/24'
        }
      }
    ]
  }
}

// 2. Azure OpenAI Account
resource openAi 'Microsoft.CognitiveServices/accounts@2023-05-01' = {
  name: openAiName
  location: location
  kind: 'OpenAI'
  sku: {
    name: 'S0'
  }
  properties: {
    customSubDomainName: openAiName
    publicNetworkAccess: 'Disabled'
  }
}

// Private Endpoint for Azure OpenAI
resource privateEndpoint 'Microsoft.Network/privateEndpoints@2023-04-01' = {
  name: 'pe-${openAiName}'
  location: location
  properties: {
    subnet: {
      id: vnet.properties.subnets[0].id
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

// 3. Azure Firewall (for Outbound Web Filtering to other providers)
resource publicIp 'Microsoft.Network/publicIPAddresses@2023-04-01' = {
  name: 'pip-${firewallName}'
  location: location
  sku: {
    name: 'Standard'
  }
  properties: {
    publicIPAllocationMethod: 'Static'
  }
}

resource firewall 'Microsoft.Network/azureFirewalls@2023-04-01' = {
  name: firewallName
  location: location
  properties: {
    sku: {
      name: 'AZFW_VNet'
      tier: 'Standard'
    }
    ipConfigurations: [
      {
        name: 'configuration'
        properties: {
          subnet: {
            id: vnet.properties.subnets[1].id
          }
          publicIPAddress: {
            id: publicIp.id
          }
        }
      }
    ]
    applicationRuleCollections: [
      {
        name: 'AllowExternalAIProviders'
        properties: {
          priority: 100
          action: {
            type: 'Allow'
          }
          rules: [
            {
              name: 'AnthropicAndGemini'
              protocols: [
                {
                  protocolType: 'Https'
                  port: 443
                }
              ]
              targetFqdns: [
                'api.anthropic.com'
                'generativelanguage.googleapis.com'
              ]
              sourceAddresses: [
                '10.0.0.0/16'
              ]
            }
          ]
        }
      }
    ]
  }
}
