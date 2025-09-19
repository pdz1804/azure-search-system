from fastapi import APIRouter, HTTPException, UploadFile
from backend.services.azure_blob_service import upload_image

files = APIRouter(prefix="/api/files", tags=["files"])


@files.post("/")
async def upload_file(file: UploadFile):
    if not file:
        raise HTTPException(status_code=400, detail="No file provided")

    try:
        blob_url = upload_image(file.file)
        return {"success": True, "url": blob_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
