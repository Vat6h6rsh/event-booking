"""Cloudflare R2 image upload utilities (S3-compatible API)."""
import os, uuid
from typing import Optional
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError

CF_ACCOUNT_ID    = os.getenv("CF_ACCOUNT_ID", "")
CF_R2_ACCESS_KEY = os.getenv("CF_R2_ACCESS_KEY", "")
CF_R2_SECRET_KEY = os.getenv("CF_R2_SECRET_KEY", "")
CF_R2_BUCKET     = os.getenv("CF_R2_BUCKET", "jtickets")
CF_R2_PUBLIC_URL = os.getenv("CF_R2_PUBLIC_URL", "")   # optional custom domain

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_BYTES     = 5 * 1024 * 1024  # 5 MB


def _client() -> Optional[object]:
    if not CF_ACCOUNT_ID:
        return None
    return boto3.client(
        "s3",
        endpoint_url=f"https://{CF_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=CF_R2_ACCESS_KEY,
        aws_secret_access_key=CF_R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_image(content: bytes, content_type: str, original_name: str) -> str:
    client = _client()
    if not client:
        raise ValueError(
            "Cloudflare R2 is not configured. "
            "Set CF_ACCOUNT_ID, CF_R2_ACCESS_KEY, CF_R2_SECRET_KEY in your environment."
        )
    ext = original_name.rsplit(".", 1)[-1].lower() if "." in original_name else "jpg"
    key = f"{uuid.uuid4().hex}.{ext}"
    try:
        client.put_object(Bucket=CF_R2_BUCKET, Key=key, Body=content, ContentType=content_type)
    except ClientError as e:
        raise ValueError(f"R2 upload failed: {e}")
    if CF_R2_PUBLIC_URL:
        return f"{CF_R2_PUBLIC_URL.rstrip('/')}/{key}"
    return f"https://{CF_R2_BUCKET}.{CF_ACCOUNT_ID}.r2.dev/{key}"
