<# 
.SYNOPSIS
Creates or updates a Cost Management Export for a subscription and schedules daily delivery to Blob storage.

.DESCRIPTION
This script replaces the deprecated Usage Details API with the modern Cost Management Exports API.  
It works with Pay-As-You-Go, Visual Studio, Microsoft Customer Agreement, and Enterprise Agreement subscriptions.  

FEATURES
- Creates or updates a daily export of cost data in CSV format
- Writes to an existing Blob Storage container (creates one if needed)
- Optionally triggers the export immediately
- Ready for use in GitHub Actions or Azure DevOps

.REQUIREMENTS
- PowerShell 7+
- Az.Accounts
- Az.Resources
- Az.Storage
- Az.CostManagement

.EXAMPLE
.\Create-Or-Update-AzCostExport.ps1 `
  -SubscriptionId "00000000-0000-0000-0000-000000000000" `
  -ResourceGroupName "finops-rg" `
  -StorageAccountName "finopsstorage01" `
  -ContainerName "exports" `
  -ExportName "DailyCostExport" `
  -TriggerNow
#>

[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)]
  [string] $SubscriptionId,

  [Parameter(Mandatory = $true)]
  [string] $ResourceGroupName,

  [Parameter(Mandatory = $true)]
  [string] $StorageAccountName,

  [Parameter(Mandatory = $true)]
  [string] $ContainerName,

  [string] $ExportName = "DailyCostExport",
  [string] $TimeZone = "Central Standard Time",
  [string] $RootFolderPath = "costexports",
  [switch] $TriggerNow
)

#--------------------------
# Initial setup
#--------------------------
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Log {
  param([string] $Message, [string] $Level = "INFO")
  $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
  Write-Host "[$timestamp][$Level] $Message"
}

Write-Log "Connecting to Azure..."
Connect-AzAccount -ErrorAction Stop | Out-Null
Select-AzSubscription -SubscriptionId $SubscriptionId -ErrorAction Stop | Out-Null

#--------------------------
# Validate or create storage container
#--------------------------
Write-Log "Checking storage account '$StorageAccountName' in resource group '$ResourceGroupName'"
$storageAccount = Get-AzStorageAccount -Name $StorageAccountName -ResourceGroupName $ResourceGroupName -ErrorAction Stop
$ctx = $storageAccount.Context

$container = Get-AzStorageContainer -Name $ContainerName -Context $ctx -ErrorAction SilentlyContinue
if (-not $container) {
  Write-Log "Creating container '$ContainerName'"
  New-AzStorageContainer -Name $ContainerName -Context $ctx | Out-Null
} else {
  Write-Log "Container '$ContainerName' already exists"
}

#--------------------------
# Build export configuration
#--------------------------
$destination = @{
  resourceId     = $storageAccount.Id
  container      = $ContainerName
  rootFolderPath = $RootFolderPath
}

$schedule = @{
  status = "Active"
  recurrence = "Daily"
  recurrencePeriod = @{
    from = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    to   = (Get-Date).AddYears(1).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
  }
  timeZone = $TimeZone
}

$definition = @{
  timeframe = "MonthToDate"
  dataset = @{
    granularity = "Daily"
    configuration = @{
      columns = @(
        "Date",
        "ResourceGroupName",
        "ResourceId",
        "ServiceName",
        "Cost",
        "Currency"
      )
    }
  }
}

$scope = "/subscriptions/$SubscriptionId"

#--------------------------
# Create or update export
#--------------------------
Write-Log "Creating or updating export '$ExportName' in subscription scope '$scope'"
try {
  New-AzCostManagementExport -Name $ExportName `
    -Scope $scope `
    -Schedule $schedule `
    -Format "Csv" `
    -Destination $destination `
    -Definition $definition `
    -ErrorAction Stop | Out-Null

  Write-Log "Export '$ExportName' created or updated successfully"
}
catch {
  Write-Log "Failed to create export: $($_.Exception.Message)" "ERROR"
  throw
}

#--------------------------
# Optional immediate run
#--------------------------
if ($TriggerNow) {
  Write-Log "Triggering immediate export run..."
  $path = "/subscriptions/$SubscriptionId/providers/Microsoft.CostManagement/exports/$ExportName/run?api-version=2023-03-01"
  try {
    Invoke-AzRestMethod -Method POST -Path $path -ErrorAction Stop | Out-Null
    Write-Log "Export triggered successfully"
  }
  catch {
    Write-Log "Failed to trigger export run: $($_.Exception.Message)" "ERROR"
  }
}

Write-Log "Process completed successfully"
