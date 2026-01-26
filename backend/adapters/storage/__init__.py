"""
Storage Adapters - Cloudflare R2 (S3-Compatible)
"""
from .r2_storage import R2StorageAdapter, UploadResult

__all__ = ["R2StorageAdapter", "UploadResult"]
