from fastapi import APIRouter, UploadFile, File, HTTPException
from app.utils.file_parser import parse_file

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        text = parse_file(content, file.filename)
        if text is None:
            raise HTTPException(status_code=415, detail="Unsupported file type")
        return {
            "filename": file.filename,
            "size": len(content),
            "text_preview": text[:500],
            "full_text": text,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
