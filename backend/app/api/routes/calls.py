import os
import uuid
from pathlib import Path
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.api.deps import AsyncSessionDep
from app.core.config import settings
from app.crud import call_crud
from app.models import CallRead, CallReadWithDetails, CallStatus

router = APIRouter(prefix="/calls", tags=["calls"])

@router.post("/", response_model=dict)
async def upload_call(
    *,
    session: AsyncSessionDep,
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
    
    # Create database record
    call = await call_crud.create(
        session,
        filename=unique_filename,
        original_filename=str(file.filename) or "unknown",
        file_path=str(file_path),
        file_size=file_size,
    )
    
    # TODO: Enqueue Redis job for transcription and analysis of audio call

    return {
        "call_id": call.id,
        "filename": call.original_filename,
        "status": call.status,
        "message": "File uploaded successfully. Processing will start shortly.",
    }

@router.get("/", response_model=dict)
async def list_calls(
    *,
    session: AsyncSessionDep,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Max records to return"),
    status: CallStatus | None = Query(None, description="Filter by status"),
) -> dict:
    """
    List calls with pagination and optional status filter.
    """
    calls = await call_crud.get_multi(
        session,
        skip=skip,
        limit=limit,
        status=status,
    )
    total = await call_crud.count(session, status=status)

    return {
        "calls": [CallRead.model_validate(c) for c in calls],
        "total": total,
        "skip": skip,
        "limit": limit,
    }

@router.get("/{call_id}", response_model=CallReadWithDetails)
async def get_call(
    *,
    call_id: int,
    session: AsyncSessionDep,
) -> CallReadWithDetails:
    """
    Get a single call with its transcripts and insights.
    """
    call = await call_crud.get_with_details(session, id=call_id)

    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    return CallReadWithDetails.model_validate(call)


@router.get("/{call_id}/status", response_model=dict)
async def get_call_status(
    *,
    call_id: int,
    session: AsyncSessionDep,
) -> dict:
    """
    Get just the status of a call (lightweight polling endpoint).
    """
    call = await call_crud.get(session, id=call_id)

    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "call_id": call.id,
        "status": call.status,
        "error_message": call.error_message,
    }


@router.delete("/{call_id}", response_model=dict)
async def delete_call(
    *,
    call_id: int,
    session: AsyncSessionDep,
) -> dict:
    """
    Delete a call and all associated data.

    Also removes the audio file from storage.
    """
    call = await call_crud.get(session, id=call_id)

    if call is None:
        raise HTTPException(status_code=404, detail="Call not found")

    # Delete audio file
    if os.path.exists(call.file_path):
        try:
            os.remove(call.file_path)
        except OSError:
            pass  # File is already gone

    # Delete DB record (cascades to transcripts and insights)
    await call_crud.delete(session, id=call_id)

    return {"message": "Call deleted successfully", "call_id": call_id}
