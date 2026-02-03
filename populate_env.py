#!/usr/bin/env python3
"""
Helper script to populate .env file with Azure resource parameters.
This script retrieves necessary keys and properties from Azure Resources
deployed using the ARM template and stores them in a .env file.
"""

import subprocess
import sys
import os
from pathlib import Path

def run_az_command(command):
    """Run an Azure CLI command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}")
        print(f"Error: {e.stderr}")
        return None

def get_deployment_name(resource_group):
    """Get the deployment name from the resource group."""
    command = f"az deployment group list --resource-group {resource_group} --query \"[?contains(name, 'Microsoft.Template') || contains(name, 'azuredeploy')].{{name:name}}[0].name\" -o tsv"
    return run_az_command(command)

def get_deployment_outputs(resource_group, deployment_name):
    """Get all deployment outputs."""
    command = f"az deployment group show --resource-group {resource_group} --name {deployment_name} --query properties.outputs -o json"
    import json
    output = run_az_command(command)
    if output:
        return json.loads(output)
    return {}

def get_cosmos_key(resource_group, cosmos_name):
    """Get Cosmos DB primary key."""
    command = f"az cosmosdb keys list --name {cosmos_name} --resource-group {resource_group} --query primaryMasterKey -o tsv"
    return run_az_command(command)

def get_storage_key(resource_group, storage_name):
    """Get Storage account key."""
    command = f"az storage account keys list --account-name {storage_name} --resource-group {resource_group} --query '[0].value' -o tsv"
    return run_az_command(command)

def get_search_key(resource_group, search_name):
    """Get Search service admin key."""
    command = f"az search admin-key show --service-name {search_name} --resource-group {resource_group} --query primaryKey -o tsv"
    return run_az_command(command)

def get_ai_foundry_key(resource_group, ai_foundry_name):
    """Get AI Foundry key."""
    command = f"az cognitiveservices account keys list --name {ai_foundry_name} --resource-group {resource_group} --query key1 -o tsv"
    return run_az_command(command)

def get_acr_password(resource_group, acr_name):
    """Get ACR password."""
    command = f"az acr credential show --name {acr_name} --query passwords[0].value -o tsv"
    return run_az_command(command)

def main():
    if len(sys.argv) != 2:
        print("Usage: python populate_env.py <resource-group>")
        sys.exit(1)

    resource_group = sys.argv[1]

    print(f"Populating .env for resource group: {resource_group}")

    # Get deployment name
    deployment_name = get_deployment_name(resource_group)
    if not deployment_name:
        print("Could not find deployment.")
        sys.exit(1)
    print(f"Found deployment: {deployment_name}")

    # Get outputs
    outputs = get_deployment_outputs(resource_group, deployment_name)
    if not outputs:
        print("Could not get deployment outputs.")
        sys.exit(1)

    # Extract values
    cosmos_name = outputs.get('cosmosDbAccountName', {}).get('value')
    cosmos_endpoint = outputs.get('cosmosDbEndpoint', {}).get('value')
    storage_name = outputs.get('storageAccountName', {}).get('value')
    search_name = outputs.get('searchServiceName', {}).get('value')
    search_endpoint = outputs.get('searchServiceEndpoint', {}).get('value')
    ai_foundry_name = outputs.get('aiFoundryHubName', {}).get('value')
    ai_foundry_project_name = outputs.get('aiFoundryProjectName', {}).get('value')
    ai_foundry_endpoint = outputs.get('aiFoundryHubEndpoint', {}).get('value')
    ai_foundry_project_endpoint = outputs.get('aiFoundryProjectEndpoint', {}).get('value')
    acr_name = outputs.get('containerRegistryName', {}).get('value')
    acr_username = outputs.get('acrUsername', {}).get('value')
    log_analytics_name = outputs.get('logAnalyticsWorkspaceName', {}).get('value')
    apim_name = outputs.get('apimName', {}).get('value') if 'apimName' in outputs else None

    # Get keys
    cosmos_key = get_cosmos_key(resource_group, cosmos_name) if cosmos_name else None
    storage_key = get_storage_key(resource_group, storage_name) if storage_name else None
    search_key = get_search_key(resource_group, search_name) if search_name else None
    ai_foundry_key = get_ai_foundry_key(resource_group, ai_foundry_name) if ai_foundry_name else None
    acr_password = get_acr_password(resource_group, acr_name) if acr_name else None

    # Build .env content
    env_content = f"""# Azure Storage Account
AZURE_STORAGE_ACCOUNT_NAME="{storage_name or ''}"
AZURE_STORAGE_ACCOUNT_KEY="{storage_key or ''}"
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName={storage_name or ''};AccountKey={storage_key or ''};EndpointSuffix=core.windows.net"

# Log Analytics Workspace
LOG_ANALYTICS_WORKSPACE_NAME="{log_analytics_name or ''}"

# Azure AI Search
SEARCH_SERVICE_NAME="{search_name or ''}"
SEARCH_SERVICE_ENDPOINT="{search_endpoint or ''}"
SEARCH_ADMIN_KEY="{search_key or ''}"

# AI Foundry / Azure OpenAI
AI_FOUNDRY_HUB_NAME="{ai_foundry_name or ''}"
AI_FOUNDRY_PROJECT_NAME="{ai_foundry_project_name or ''}"
AI_FOUNDRY_ENDPOINT="https://{ai_foundry_name or ''}.cognitiveservices.azure.com/"
AI_FOUNDRY_KEY="{ai_foundry_key or ''}"
AI_FOUNDRY_HUB_ENDPOINT="{ai_foundry_endpoint or ''}"
AI_FOUNDRY_PROJECT_ENDPOINT="https://{ai_foundry_name or ''}.services.ai.azure.com/api/projects/{ai_foundry_project_name or ''}"
AZURE_AI_CONNECTION_ID="/subscriptions/{run_az_command('az account show --query id -o tsv') or ''}/resourceGroups/{resource_group}/providers/Microsoft.CognitiveServices/accounts/{ai_foundry_name or ''}/connections/{ai_foundry_name or ''}-aisearch"

# Azure Cosmos DB
COSMOS_ENDPOINT="{cosmos_endpoint or ''}"
COSMOS_KEY="{cosmos_key or ''}"
COSMOS_CONNECTION_STRING="AccountEndpoint={cosmos_endpoint or ''};AccountKey={cosmos_key or ''};"

# API Management
APIM_NAME="{apim_name or ''}"
APIM_GATEWAY_URL="https://{apim_name or ''}.azure-api.net"
APIM_SUBSCRIPTION_KEY=""

# Azure Container Registry
ACR_NAME="{acr_name or ''}"
ACR_USERNAME="{acr_username or ''}"
ACR_PASSWORD="{acr_password or ''}"
ACR_LOGIN_SERVER="{acr_name or ''}.azurecr.io"

# Azure OpenAI (for backward compatibility)
AZURE_OPENAI_SERVICE_NAME="{ai_foundry_name or ''}"
AZURE_OPENAI_ENDPOINT="https://{ai_foundry_name or ''}.cognitiveservices.azure.com/"
AZURE_OPENAI_KEY="{ai_foundry_key or ''}"
AZURE_OPENAI_DEPLOYMENT_NAME="gpt-4.1-mini"
MODEL_DEPLOYMENT_NAME="gpt-4.1-mini"

# Memory System Configuration (Challenge 2)
# Memory uses SEARCH_SERVICE_ENDPOINT and SEARCH_ADMIN_KEY from above
# Azure OpenAI embedding model for memory (e.g., text-embedding-ada-002)
AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME="text-embedding-ada-002"
"""

    # Write to .env
    env_path = Path('.env')
    with open(env_path, 'w') as f:
        f.write(env_content)

    print(f".env file populated successfully at {env_path}")

if __name__ == "__main__":
    main()