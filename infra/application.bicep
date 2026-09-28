targetScope = 'resourceGroup'
param location string
param prefix string
param image string
param entraTenantId string
param entraAudience string
param entraClientId string
param entraScope string
param demoEnabled bool = false
param azureOpenAIEndpoint string = ''
param azureOpenAIApiVersion string = ''
param azureOpenAIVisionDeployment string = ''
var suffix = uniqueString(resourceGroup().id)
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = { name: '${prefix}-app' }
resource migrationIdentity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' existing = { name: '${prefix}-migration' }
resource vault 'Microsoft.KeyVault/vaults@2023-07-01' existing = { name: '${prefix}-${suffix}' }
resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' existing = { name: '${prefix}${suffix}' }
resource environment 'Microsoft.App/managedEnvironments@2024-03-01' existing = { name: '${prefix}-environment' }
resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' existing = { name: '${prefix}${suffix}' }
var env = [
  { name: 'DATABASE_URL', secretRef: 'database-url' }
  { name: 'AUTH_MODE', value: 'entra' }
  { name: 'ENTRA_TENANT_ID', value: entraTenantId }
  { name: 'ENTRA_AUDIENCE', value: entraAudience }
  { name: 'ENTRA_CLIENT_ID', value: entraClientId }
  { name: 'ENTRA_SCOPE', value: entraScope }
  { name: 'STORAGE_MODE', value: 'azure' }
  { name: 'AZURE_STORAGE_ACCOUNT_URL', value: storage.properties.primaryEndpoints.blob }
  { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }
  { name: 'AZURE_OPENAI_ENDPOINT', value: azureOpenAIEndpoint }
  { name: 'AZURE_OPENAI_API_VERSION', value: azureOpenAIApiVersion }
  { name: 'AZURE_OPENAI_VISION_DEPLOYMENT', value: azureOpenAIVisionDeployment }
  { name: 'DEMO_ENABLED', value: string(demoEnabled) }
  { name: 'DEMO_SIGNING_SECRET', secretRef: 'demo-signing-secret' }
]
resource apps 'Microsoft.App/containerApps@2024-03-01' = [for kind in ['web', 'worker']: {
  name: '${prefix}-${kind}'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${identity.id}': {} } }
  properties: {
    managedEnvironmentId: environment.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: kind == 'web' ? { external: true, targetPort: 8000, allowInsecure: false, transport: 'auto' } : null
      registries: [{ server: registry.properties.loginServer, identity: identity.id }]
      secrets: [
        { name: 'database-url', keyVaultUrl: '${vault.properties.vaultUri}secrets/database-url', identity: identity.id }
        { name: 'demo-signing-secret', keyVaultUrl: '${vault.properties.vaultUri}secrets/demo-signing-secret', identity: identity.id }
      ]
    }
    template: {
      containers: [{
        name: kind
        image: image
        command: kind == 'worker' ? ['python', '-m', 'backend.worker'] : ['uvicorn', 'backend.main:app', '--host', '0.0.0.0', '--port', '8000', '--no-proxy-headers']
        env: env
        resources: { cpu: json('0.5'), memory: '1Gi' }
        probes: kind == 'web' ? [
          { type: 'Startup', httpGet: { path: '/api/v1/health/live', port: 8000 }, initialDelaySeconds: 5, periodSeconds: 5, failureThreshold: 30 }
          { type: 'Liveness', httpGet: { path: '/api/v1/health/live', port: 8000 }, periodSeconds: 20, failureThreshold: 3 }
          { type: 'Readiness', httpGet: { path: '/api/v1/health/ready', port: 8000 }, periodSeconds: 10, failureThreshold: 3 }
        ] : []
      }]
      scale: { minReplicas: 1, maxReplicas: kind == 'worker' ? 1 : 2 }
    }
  }
}]
resource migration 'Microsoft.App/jobs@2024-03-01' = {
  name: '${prefix}-migrate'
  location: location
  identity: { type: 'UserAssigned', userAssignedIdentities: { '${migrationIdentity.id}': {} } }
  properties: {
    environmentId: environment.id
    configuration: {
      triggerType: 'Manual'
      replicaTimeout: 600
      replicaRetryLimit: 0
      manualTriggerConfig: { parallelism: 1, replicaCompletionCount: 1 }
      registries: [{ server: registry.properties.loginServer, identity: migrationIdentity.id }]
      secrets: [
        { name: 'migration-database-url', keyVaultUrl: '${vault.properties.vaultUri}secrets/migration-database-url', identity: migrationIdentity.id }
        { name: 'database-app-password', keyVaultUrl: '${vault.properties.vaultUri}secrets/database-app-password', identity: migrationIdentity.id }
      ]
    }
    template: {
      containers: [{
        name: 'migrate'
        image: image
        command: ['python', '-m', 'backend.bootstrap']
        resources: { cpu: json('0.5'), memory: '1Gi' }
        env: [
          { name: 'MIGRATION_DATABASE_URL', secretRef: 'migration-database-url' }
          { name: 'APP_DATABASE_PASSWORD', secretRef: 'database-app-password' }
        ]
      }]
    }
  }
}
output webUrl string = 'https://${apps[0].properties.configuration.ingress.fqdn}'
