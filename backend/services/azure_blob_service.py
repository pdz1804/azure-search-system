import uuid
from backend.config.azure_blob import container_client

def upload_image(file):
    try:
        file.seek(0)
    except Exception:
        pass

    data = file.read()

    blob_name = f"{uuid.uuid4().hex}.jpg"
    container_client.upload_blob(name=blob_name, data=data, overwrite=True)
    return f"https://{container_client.account_name}.blob.core.windows.net/{container_client.container_name}/{blob_name}"
