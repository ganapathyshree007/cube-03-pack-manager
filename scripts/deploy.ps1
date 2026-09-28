param(
  [Parameter(Mandatory)][string]$Subscription,
  [Parameter(Mandatory)][string]$ResourceGroup,
  [Parameter(Mandatory)][string]$ApplicationParameters,
  [Parameter(Mandatory)][string]$Registry,
  [Parameter(Mandatory)][string]$Prefix,
  [Parameter(Mandatory)][string]$ImageTag
)
$ErrorActionPreference = 'Stop'
# Foundation provisioning is separate. This script updates an approved, existing scope.
az account set --subscription $Subscription
if ($LASTEXITCODE -ne 0) { throw 'Unable to select subscription' }
az acr build --registry $Registry --image "pack-manager:$ImageTag" .
if ($LASTEXITCODE -ne 0) { throw 'Image build failed' }
$server = az acr show --name $Registry --query loginServer --output tsv
az deployment group create --resource-group $ResourceGroup --name "pack-$ImageTag" --template-file infra/application.bicep --parameters "@$ApplicationParameters" "image=$server/pack-manager:$ImageTag" --output none
if ($LASTEXITCODE -ne 0) { throw 'Application deployment failed' }
$execution = az containerapp job start --name "$Prefix-migrate" --resource-group $ResourceGroup --query name --output tsv
if ($LASTEXITCODE -ne 0) { throw 'Migration job could not start' }
for ($attempt = 0; $attempt -lt 60; $attempt++) {
  $status = az containerapp job execution show --name "$Prefix-migrate" --resource-group $ResourceGroup --job-execution-name $execution --query properties.status --output tsv
  if ($status -eq 'Succeeded') { break }
  if ($status -eq 'Failed') { throw 'Migration failed; inspect job logs. Do not roll back database destructively.' }
  Start-Sleep -Seconds 10
}
if ($status -ne 'Succeeded') { throw 'Migration completion not confirmed' }
$fqdn = az containerapp show --name "$Prefix-web" --resource-group $ResourceGroup --query properties.configuration.ingress.fqdn --output tsv
Invoke-RestMethod -Uri "https://$fqdn/api/v1/health/ready" -TimeoutSec 30 | Out-Null
Write-Output "Readiness verified: https://$fqdn. Authenticated workflow and real inference still require verification."
