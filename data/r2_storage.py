"""Cloudflare R2 storage — tải Excel template vào RAM khi bot khởi động."""
from __future__ import annotations

import io
import logging
import os

logger = logging.getLogger(__name__)


def _r2_client():
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=os.environ["R2_ENDPOINT"],
        aws_access_key_id=os.environ["R2_ACCESS_KEY"],
        aws_secret_access_key=os.environ["R2_SECRET_KEY"],
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def download_excel(object_key: str | None = None) -> io.BytesIO:
    """Tải file Excel template từ R2 về RAM. Gọi một lần lúc khởi động."""
    bucket = os.environ.get("R2_BUCKET", "orderbot")
    key = object_key or os.environ.get("R2_OBJECT_KEY", "DAILY_ORDER_MIN_xlsx.xlsx")
    logger.info("Downloading Excel template from R2: s3://%s/%s", bucket, key)
    buf = io.BytesIO()
    _r2_client().download_fileobj(bucket, key, buf)
    buf.seek(0)
    logger.info("Excel template downloaded successfully (%d bytes)", buf.getbuffer().nbytes)
    return buf
