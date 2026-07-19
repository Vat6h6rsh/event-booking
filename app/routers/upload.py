from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from app import auth, schemas
from app.models import User
from app.r2 import upload_image, ALLOWED_TYPES, MAX_BYTES

router = APIRouter(prefix="/upload", tags=["upload"])

@router.post("/image", response_model=schemas.UploadOut)
async def upload_image_route(
    file: UploadFile = File(...),
    user: User = Depends(auth.get_current_user),
):
    """Upload an image to Cloudflare R2. Returns a public URL. Requires CF_ACCOUNT_ID env var."""
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(400, f"Unsupported file type. Allowed: {', '.join(ALLOWED_TYPES)}")
    content = await file.read()
    if len(content) > MAX_BYTES:
        raise HTTPException(413, "File exceeds 5 MB limit")
    try:
        url = upload_image(content, file.content_type, file.filename or "upload")
    except ValueError as e:
        raise HTTPException(503, str(e))
    return {"url": url, "filename": file.filename, "size": len(content)}
