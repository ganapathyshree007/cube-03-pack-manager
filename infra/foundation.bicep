targetScope = 'resourceGroup'
param location string
@minLength(3)
@maxLength(11)
param prefix string
@secure()
param databaseAdminPassword string
@secure()
param databaseAppPassword string
@secure()
param demoSigningSecret string
param monthlyBudget int
param budgetContactEmails array
param budgetStartDate string

var suffix = uniqueString(resourceGroup().id)
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-app'
  location: location
}
resource migrationIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: '${prefix}-migration'
  location: location
}
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: '${prefix}${suffix}'
  location: location
  sku: { name: 'Basic' }
  properties: { adminUserEnabled: false }
}
resource acrPull 'Microsoft.Authorization/roleAssignments@2022-04-01' = [for kind in ['app', 'migration']: {
  name: guid(registry.id, kind, 'AcrPull')
  scope: registry
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
    principalId: kind == 'app' ? identity.properties.principalId : migrationIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}]
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: '${prefix}${suffix}'
  location: location
  kind: 'StorageV2'
  sku: { name: 'Standard_LRS' }
  properties: {
    allowBlobPublicAccess: false
    allowSharedKeyAccess: false
    supportsHttpsTrafficOnly: true
    minimumTlsVersion: 'TLS1_2'
  }
}
resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'
}
resource evidence 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: 'evidence'
  properties: { publicAccess: 'None' }
}
resource blobAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: evidence
  name: guid(evidence.id, identity.id, 'blob')
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource vnet 'Microsoft.Network/virtualNetworks@2023-11-01' = {
  name: '${prefix}-network'
  location: location
  properties: {
    addressSpace: { addressPrefixes: ['10.42.0.0/16'] }
    subnets: [
      { name: 'apps', properties: { addressPrefix: '10.42.0.0/23', delegations: [{ name: 'apps', properties: { serviceName: 'Microsoft.App/environments' } }] } }
      { name: 'database', properties: { addressPrefix: '10.42.2.0/27', delegations: [{ name: 'postgres', properties: { serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers' } }] } }
    ]
  }
}
resource dns 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${prefix}.postgres.database.azure.com'
  location: 'global'
}
resource dnsLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: dns
  name: '${prefix}-link'
  location: 'global'
  properties: { registrationEnabled: false, virtualNetwork: { id: vnet.id } }
}
resource database 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: '${prefix}-${suffix}'
  location: location
  sku: { name: 'Standard_B1ms', tier: 'Burstable' }
  properties: {
    version: '17'
    administratorLogin: 'packadmin'
    administratorLoginPassword: databaseAdminPassword
    storage: { storageSizeGB: 32 }
    backup: { backupRetentionDays: 7, geoRedundantBackup: 'Disabled' }
    network: {
      delegatedSubnetResourceId: '${vnet.id}/subnets/database'
      privateDnsZoneArmResourceId: dns.id
      publicNetworkAccess: 'Disabled'
    }
    highAvailability: { mode: 'Disabled' }
  }
  dependsOn: [dnsLink]
}
resource packDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  parent: database
  name: 'pack'
  properties: { charset: 'UTF8', collation: 'en_US.utf8' }
}
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: '${prefix}-${suffix}'
  location: location
  properties: {
    tenantId: tenant().tenantId
    sku: { family: 'A', name: 'standard' }
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 7
  }
}
resource appConnection 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-url'
  properties: { value: 'postgresql+psycopg://pack_app:${uriComponent(databaseAppPassword)}@${database.properties.fullyQualifiedDomainName}/pack?sslmode=require' }
}
resource adminConnection 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'migration-database-url'
  properties: { value: 'postgresql+psycopg://packadmin:${uriComponent(databaseAdminPassword)}@${database.properties.fullyQualifiedDomainName}/pack?sslmode=require' }
}
resource appPassword 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'database-app-password'
  properties: { value: databaseAppPassword }
}
resource demoSecret 'Microsoft.KeyVault/vaults/secrets@2023-07-01' = {
  parent: vault
  name: 'demo-signing-secret'
  properties: { value: demoSigningSecret }
}
resource demoSecretAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: demoSecret
  name: guid(demoSecret.id, identity.id)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource appSecretAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appConnection
  name: guid(appConnection.id, identity.id)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: identity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource migrationSecretAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: adminConnection
  name: guid(adminConnection.id, migrationIdentity.id)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: migrationIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource passwordAccess 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  scope: appPassword
  name: guid(appPassword.id, migrationIdentity.id)
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '4633458b-17de-408a-b874-0445c86b69e6')
    principalId: migrationIdentity.properties.principalId
    principalType: 'ServicePrincipal'
  }
}
resource logs 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: '${prefix}-logs'
  location: location
  properties: { sku: { name: 'PerGB2018' }, retentionInDays: 30, workspaceCapping: { dailyQuotaGb: 1 } }
}
resource environment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: '${prefix}-environment'
  location: location
  properties: {
    workloadProfiles: [{ name: 'Consumption', workloadProfileType: 'Consumption' }]
    vnetConfiguration: { infrastructureSubnetId: '${vnet.id}/subnets/apps' }
    appLogsConfiguration: { destination: 'log-analytics', logAnalyticsConfiguration: { customerId: logs.properties.customerId, sharedKey: logs.listKeys().primarySharedKey } }
  }
}
resource budget 'Microsoft.Consumption/budgets@2023-11-01' = {
  name: '${prefix}-budget'
  properties: {
    category: 'Cost'
    amount: monthlyBudget
    timeGrain: 'Monthly'
    timePeriod: { startDate: budgetStartDate }
    notifications: {
      actual80: { enabled: true, operator: 'GreaterThan', threshold: 80, contactEmails: budgetContactEmails, thresholdType: 'Actual' }
      forecast100: { enabled: true, operator: 'GreaterThan', threshold: 100, contactEmails: budgetContactEmails, thresholdType: 'Forecasted' }
    }
  }
}
output registryName string = registry.name
output registryServer string = registry.properties.loginServer
output identityClientId string = identity.properties.clientId
output identityPrincipalId string = identity.properties.principalId
output storageAccountUrl string = storage.properties.primaryEndpoints.blob
output vaultUrl string = vault.properties.vaultUri
output environmentId string = environment.id
