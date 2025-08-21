"""Azure Blob Storage configuration helpers.

This module creates a BlobServiceClient and container client using
environment variables. Other modules (e.g. services/azure_blob_service)
import the `container_client` to upload blobs.
"""

from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

load_dotenv()

account_name = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
account_key = os.getenv("AZURE_STORAGE_ACCOUNT_KEY")
container_name = os.getenv("AZURE_STORAGE_CONTAINER_NAME")

# Connection string built from environment variables. Keep the client
# instantiation here so other modules can reuse the same client instance.
connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
blob_service_client = BlobServiceClient.from_connection_string(connect_str)
container_client = blob_service_client.get_container_client(container_name)
