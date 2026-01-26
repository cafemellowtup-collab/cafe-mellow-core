"""
Cloudflare R2 Storage Adapter (S3-Compatible)
DPDP Compliance: Store files in R2, only URLs in database
"""
import os
import boto3
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UploadResult(BaseModel):
    """File upload result"""
    file_url: str
    file_key: str
    bucket: str
    size_bytes: int
    uploaded_at: datetime


class R2StorageAdapter:
    """
    Cloudflare R2 Storage Adapter
    S3-compatible interface for file storage
    
    Configuration via environment variables:
    - R2_ACCOUNT_ID
    - R2_ACCESS_KEY_ID
    - R2_SECRET_ACCESS_KEY
    - R2_BUCKET_NAME
    """
    
    def __init__(self):
        self.account_id = os.getenv("R2_ACCOUNT_ID", "")
        self.access_key = os.getenv("R2_ACCESS_KEY_ID", "")
        self.secret_key = os.getenv("R2_SECRET_ACCESS_KEY", "")
        self.bucket_name = os.getenv("R2_BUCKET_NAME", "titan-erp-files")
        
        if not all([self.account_id, self.access_key, self.secret_key]):
            raise ValueError("R2 credentials not configured")
        
        endpoint_url = f"https://{self.account_id}.r2.cloudflarestorage.com"
        
        self.client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            region_name="auto"
        )
    
    def upload_file(
        self, 
        file_path: str, 
        object_key: str,
        org_id: str,
        location_id: str,
        content_type: Optional[str] = None
    ) -> UploadResult:
        """
        Upload file to R2
        
        Args:
            file_path: Local file path
            object_key: Object key in R2 (should include org_id/location_id for isolation)
            org_id: Organization ID (for data isolation)
            location_id: Location ID (for data isolation)
            content_type: MIME type
        
        Returns:
            UploadResult with file URL
        """
        prefixed_key = f"{org_id}/{location_id}/{object_key}"
        
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        
        self.client.upload_file(
            file_path,
            self.bucket_name,
            prefixed_key,
            ExtraArgs=extra_args
        )
        
        file_url = f"https://{self.bucket_name}.{self.account_id}.r2.dev/{prefixed_key}"
        
        file_size = os.path.getsize(file_path)
        
        return UploadResult(
            file_url=file_url,
            file_key=prefixed_key,
            bucket=self.bucket_name,
            size_bytes=file_size,
            uploaded_at=datetime.utcnow()
        )
    
    def upload_bytes(
        self,
        file_bytes: bytes,
        object_key: str,
        org_id: str,
        location_id: str,
        content_type: Optional[str] = None
    ) -> UploadResult:
        """Upload file from bytes"""
        prefixed_key = f"{org_id}/{location_id}/{object_key}"
        
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
        
        self.client.put_object(
            Bucket=self.bucket_name,
            Key=prefixed_key,
            Body=file_bytes,
            **extra_args
        )
        
        file_url = f"https://{self.bucket_name}.{self.account_id}.r2.dev/{prefixed_key}"
        
        return UploadResult(
            file_url=file_url,
            file_key=prefixed_key,
            bucket=self.bucket_name,
            size_bytes=len(file_bytes),
            uploaded_at=datetime.utcnow()
        )
    
    def delete_file(self, object_key: str) -> bool:
        """Delete file from R2"""
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=object_key)
            return True
        except Exception:
            return False
    
    def get_presigned_url(self, object_key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for temporary access"""
        url = self.client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self.bucket_name, "Key": object_key},
            ExpiresIn=expires_in
        )
        return url
