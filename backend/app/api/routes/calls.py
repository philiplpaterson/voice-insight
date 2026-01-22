import os
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.core.config import settings

router = APIRouter(prefix="/calls", tags=["calls"])

@router.post("/")
async def upload_call(
    *,
    file: UploadFile = File(...)
) -> dict:
    """
    Uploads new call audio file
    """

    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in settings.ALLOWED_AUDIO_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Invalid file type uploaded. Allowed file extensions: {settings.ALLOWED_AUDIO_EXTENSIONS}",
        )
    
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = settings.UPLOAD_PATH / unique_filename

    try:
        contents = await file.read()
        file_size = len(contents)

        if file_size > settings.MAX_UPLOAD_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Max upload size: {settings.MAX_UPLOAD_SIZE}",
            )
        
        with open(file_path, "wb") as f:
            f.write(contents)

    except Exception as e:
        raise HTTPException(status_code=500, details=f"Failed to save file. Exception: {e!s}")
    
    return {
        "filename": file.filename,
        "message": "File upload successful."
    }