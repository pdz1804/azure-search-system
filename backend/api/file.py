"""Files router.

This router currently contains only commented-out examples. File
uploads in the project are handled by `backend.services.azure_blob_service`
which uploads image streams to Azure Blob Storage. The router can be
uncommented/expanded if an HTTP file upload endpoint is required.
"""

from fastapi import APIRouter, HTTPException, UploadFile
from fastapi.responses import FileResponse
from backend.services.azure_blob_service import upload_image


files = APIRouter(prefix="/api/files", tags=["files"])

@files.post("/")
async def upload_file(file: UploadFile):
	"""Upload a single file and return the blob URL."""
	if not file:
		raise HTTPException(status_code=400, detail="No file provided")

	try:
		blob_url = upload_image(file.file)
		return {"success": True, "url": blob_url}
	except Exception as e:
		raise HTTPException(status_code=500, detail=f"Upload failed: {e}")
