import uuid
from backend.config.azure_blob import container_client


def upload_image(file):
    """Upload a file-like object to Azure Blob Storage and return the blob URL.

    The function ensures the incoming file-like object is read from the start
    and uploads the raw bytes. This avoids issues where the file pointer may
    not be at the beginning when called from different FastAPI code paths.
    """
    try:
        # Try to seek to start if the object supports it
        file.seek(0)
    except Exception:
        pass

    # Read bytes (safe for SpooledTemporaryFile / UploadFile.file)
    data = file.read()

    blob_name = f"{uuid.uuid4().hex}.jpg"
    # Upload bytes to blob storage
    container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    return f"https://{container_client.account_name}.blob.core.windows.net/{container_client.container_name}/{blob_name}"
