from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.integrations.boto3 import generate_presigned_url, delete_file
import uuid

router = APIRouter(prefix="/storage", tags=["Storage"])


class FileUploadRequest(BaseModel):
    filename: str
    content_type: str  # ej: "image/png"


@router.post("/presigned-upload")
async def get_presigned_upload_url(data: FileUploadRequest):
    key = f"uploads/{uuid.uuid4()}-{data.filename}"
    try:
        url = generate_presigned_url(key, content_type=data.content_type)
        return {"upload_url": url, "key": key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete")
async def delete_from_s3(key: str):
    try:
        delete_file(key)
        return {"message": "Archivo eliminado"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
