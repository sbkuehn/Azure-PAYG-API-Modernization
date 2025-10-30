"""
Creates or updates a Cost Management Export for an Azure subscription.

Replaces the deprecated Usage Details API with the modern Exports API.

Features:
- Works for Pay-As-You-Go and Visual Studio subscriptions
- Uses Azure Managed Identity or Service Principal authentication
- Schedules daily exports of cost data to a Storage Account
- Can run in GitHub Actions, Azure DevOps, or local environments

Usage (Linux/macOS):
  export AZURE_SUBSCRIPTION_ID=<subscription-id>
  export STORAGE_ACCOUNT_ID="/subscriptions/<sub>/resourceGroups/<rg>/providers/Microsoft.Storage/storageAccounts/<account>"
  export CONTAINER_NAME=exports
  export EXPORT_NAME=DailyCostExport
  export TIME_ZONE="Central Standard Time"

  python create_or_update_cost_export.py
"""

import os
import sys
import json
import requests
import logging
from datetime import datetime, timedelta, timezone
from azure.identity import DefaultAzureCredential

# ----------------------------------------------------------------------
# Logging configuration
# ----------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# ----------------------------------------------------------------------
# Validate environment variables
# ----------------------------------------------------------------------
subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")
storage_account_id = os.getenv("STORAGE_ACCOUNT_ID")
container_name = os.getenv("CONTAINER_NAME")
export_name = os.getenv("EXPORT_NAME", "DailyCostExport")
time_zone = os.getenv("TIME_ZONE", "Central Standard Time")
root_folder_path = os.getenv("ROOT_FOLDER_PATH", "costexports")

if not all([subscription_id, storage_account_id, container_name]):
    logging.error("Missing required environment variables.")
    logging.info("Required: AZURE_SUBSCRIPTION_ID, STORAGE_ACCOUNT_ID, CONTAINER_NAME")
    sys.exit(1)

# ----------------------------------------------------------------------
# Acquire Azure token
# ----------------------------------------------------------------------
try:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://management.azure.com/.default")
    access_token = token.token
    logging.info("Successfully acquired Azure access token.")
except Exception as ex:
    logging.error(f"Authentication failed: {ex}")
    sys.exit(1)

# ----------------------------------------------------------------------
# Build export payload
# ----------------------------------------------------------------------
start_date = datetime.now(timezone.utc)
end_date = start_date + timedelta(days=365)

payload = {
    "properties": {
        "deliveryInfo": {
            "destination": {
                "resourceId": storage_account_id,
                "container": container_name,
                "rootFolderPath": root_folder_path
            }
        },
        "format": "Csv",
        "schedule": {
            "status": "Active",
            "recurrence": "Daily",
            "recurrencePeriod": {
                "from": start_date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "to": end_date.strftime("%Y-%m-%dT%H:%M:%SZ")
            },
            "timeZone": time_zone
        },
        "timeframe": "MonthToDate",
        "dataSet": {
            "granularity": "Daily",
            "configuration": {
                "columns": [
                    "Date",
                    "ResourceId",
                    "ResourceGroupName",
                    "ServiceName",
                    "Cost",
                    "Currency"
                ]
            }
        }
    }
}

# ----------------------------------------------------------------------
# API call
# ----------------------------------------------------------------------
api_version = "2023-03-01"
url = (
    f"https://management.azure.com/subscriptions/{subscription_id}"
    f"/providers/Microsoft.CostManagement/exports/{export_name}"
    f"?api-version={api_version}"
)
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

logging.info(f"Creating or updating export '{export_name}' for subscription {subscription_id}")

try:
    response = requests.put(url, headers=headers, json=payload)
    if response.status_code in (200, 201):
        logging.info(f"Export '{export_name}' created or updated successfully.")
    else:
        logging.error(f"Error creating export ({response.status_code}): {response.text}")
        sys.exit(1)
except Exception as ex:
    logging.error(f"Request failed: {ex}")
    sys.exit(1)

# ----------------------------------------------------------------------
# Optional: trigger export immediately
# ----------------------------------------------------------------------
trigger_now = os.getenv("TRIGGER_NOW", "false").lower() in ["true", "1", "yes"]
if trigger_now:
    run_url = (
        f"https://management.azure.com/subscriptions/{subscription_id}"
        f"/providers/Microsoft.CostManagement/exports/{export_name}/run"
        f"?api-version={api_version}"
    )
    try:
        run_response = requests.post(run_url, headers=headers)
        if run_response.status_code in (200, 202):
            logging.info(f"Triggered export '{export_name}' successfully.")
        else:
            logging.warning(f"Trigger returned {run_response.status_code}: {run_response.text}")
    except Exception as ex:
        logging.error(f"Failed to trigger export run: {ex}")

logging.info("Process completed successfully.")
