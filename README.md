# Azure PAYG API Modernization  
Automate Cost Management Exports with PowerShell and Python  

This repository provides production-ready scripts to replace the deprecated **Usage Details API** for Azure Pay-As-You-Go (PAYG) subscriptions.  
Microsoft is phasing out the old `Microsoft.Commerce/UsageAggregates` endpoint, and the supported replacement is the **Cost Management Exports API**.  

With these scripts, you can:  
- Create or update an Azure Cost Management Export  
- Schedule daily delivery of cost data to a Blob Storage container  
- Trigger exports on demand for validation  
- Integrate with GitHub Actions, Azure DevOps, or any CI/CD workflow  

---

## Table of Contents  
1. [Background](#background)  
2. [Architecture](#architecture)  
3. [Scripts](#scripts)  
4. [Setup](#setup)  
5. [Running the Scripts](#running-the-scripts)  
6. [CI/CD Integration](#cicd-integration)  
7. [Next Steps](#next-steps)  

---

## Background  
The **Usage Details API** is being retired. Microsoft now recommends using **Exports** for PAYG and Visual Studio subscriptions, and **Cost Details** for Enterprise Agreement or Microsoft Customer Agreement subscriptions.  

Exports create recurring jobs that write CSV files to a specified Azure Storage Account. This is the most reliable way to automate cost and usage retrieval for FinOps and platform engineering teams.  

Official documentation:  
- [Get usage details for a legacy PAYG customer (deprecated)](https://learn.microsoft.com/en-us/azure/cost-management-billing/automate/get-usage-details-legacy-customer)  
- [Migrate from Usage Details to Cost Details](https://learn.microsoft.com/en-us/azure/cost-management-billing/automate/migrate-consumption-usage-details-api)  
- [Cost Management Exports REST API](https://learn.microsoft.com/en-us/rest/api/cost-management/exports)  

---

## Architecture  
The scripts create or update a Cost Management Export that:  
1. Runs daily  
2. Writes a CSV file to an Azure Storage container  
3. Includes fields such as Date, ResourceId, ResourceGroupName, ServiceName, Cost, and Currency  

You can then connect the container to:  
- **Azure Data Factory** for ingestion and transformation  
- **Power BI** for visualization  
- **Azure Synapse** or **SQL Database** for cost analytics  

---

## Scripts  

### PowerShell: [`Create-Or-Update-AzCostExport.ps1`](./scripts/Create-Or-Update-AzCostExport.ps1)  
- Creates or updates a daily export. Optionally triggers the export immediately after creation.  
- Requires the Az PowerShell modules (Accounts, Resources, Storage, CostManagement).  

### Python: [`create_or_update_cost_export.py`](./scripts/create_or_update_cost_export.py)  
- Authenticates using Managed Identity or Service Principal via `DefaultAzureCredential` and performs the same export configuration.  

```bash
requirements.txt`  
azure-identity>=1.15.0
requests>=2.31.0
```
yaml
---

## Setup  

1. **Clone the repository**
   ```bash
   git clone https://github.com/<your-org>/azure-payg-modernization.git
   cd azure-payg-modernization

   
Authenticate to Azure

For PowerShell:

```powershell
Connect-AzAccount
```

For Python (inside Azure or locally):

```bash
az login
```

Set environment variables for Python

bash
```export AZURE_SUBSCRIPTION_ID=<subscription-id>
export STORAGE_ACCOUNT_ID="/subscriptions/<subscription-id>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>"
export CONTAINER_NAME=exports
```

Running the Scripts

PowerShell
```powershell
.\scripts\Create-Or-Update-AzCostExport.ps1 `
  -SubscriptionId "00000000-0000-0000-0000-000000000000" `
  -ResourceGroupName "finops-rg" `
  -StorageAccountName "finopsstorage01" `
  -ContainerName "exports" `
  -TriggerNow
```

Python

```bash
python scripts/create_or_update_cost_export.py
```

Both scripts will:

- Validate that the target container exists
- Create or update a scheduled export
- Write files to costexports/ inside the container

CI/CD Integration
- You can schedule the scripts to run automatically using GitHub Actions or Azure DevOps.

Example GitHub Actions Workflow
.github/workflows/export-refresh.yml

```yaml
name: Refresh Azure Cost Export
on:
  schedule:
    - cron: "0 10 * * *"  # Run daily at 10 AM UTC
  workflow_dispatch:

jobs:
  run-export:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repo
        uses: actions/checkout@v4

      - name: Azure login
        uses: azure/login@v2
        with:
          creds: ${{ secrets.AZURE_CREDENTIALS }}

      - name: Run Python export
        run: |
          pip install -r scripts/requirements.txt
          python scripts/create_or_update_cost_export.py
```

This workflow will automatically refresh your export daily.

Next Steps
In the next phase, you can:

- Ingest exported CSV files into Azure Data Factory or Synapse
- Clean and transform cost data for FinOps dashboards
- Connect Power BI to the storage container for automated reporting
- See the companion post “Turning Cost Data Into Insight: Automating PAYG Reports with ADF and Power BI” for details.

License
MIT License
Copyright (c) 2025

##Author
<br><br>Shannon Eldridge-Kuehn
<br><br>Principal Solutions Architect | Cloud, FinOps, and Platform Engineering
<br><br>shankuehn.io
