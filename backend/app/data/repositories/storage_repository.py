import os
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
from app.core.logging import logger
from app.domain.interfaces.storage_repository import StorageRepositoryInterface


class StorageRepository(StorageRepositoryInterface):
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.lower()

    def upload_file(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        """Uploads a file and returns its public URL based on provider settings."""
        if self.provider == "s3":
            return self._upload_to_s3(file_bytes, filename, content_type)
        elif self.provider == "supabase":
            return self._upload_to_supabase(file_bytes, filename, content_type)
        else:
            return self._upload_to_local(file_bytes, filename)

    def delete_file(self, file_url: str) -> bool:
        """Deletes a file based on its URL/path."""
        if self.provider == "s3":
            return self._delete_from_s3(file_url)
        elif self.provider == "supabase":
            return self._delete_from_supabase(file_url)
        else:
            return self._delete_from_local(file_url)

    def _upload_to_local(self, file_bytes: bytes, filename: str) -> str:
        os.makedirs(settings.LOCAL_STORAGE_DIR, exist_ok=True)
        file_path = os.path.join(settings.LOCAL_STORAGE_DIR, filename)
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        logger.info(f"File uploaded locally to: {file_path}")
        # Return API path relative to server root
        return f"/static/uploads/{filename}"

    def _delete_from_local(self, file_url: str) -> bool:
        filename = file_url.split("/")[-1]
        file_path = os.path.join(settings.LOCAL_STORAGE_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"File deleted locally from: {file_path}")
            return True
        return False

    def _upload_to_s3(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        try:
            s3_client.put_object(
                Bucket=settings.AWS_BUCKET_NAME,
                Key=filename,
                Body=file_bytes,
                ContentType=content_type
            )
            url = f"https://{settings.AWS_BUCKET_NAME}.s3.{settings.AWS_REGION}.amazonaws.com/{filename}"
            logger.info(f"File uploaded to AWS S3: {url}")
            return url
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            raise RuntimeError(f"S3 upload error: {str(e)}")

    def _delete_from_s3(self, file_url: str) -> bool:
        s3_client = boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION
        )
        filename = file_url.split("/")[-1]
        try:
            s3_client.delete_object(Bucket=settings.AWS_BUCKET_NAME, Key=filename)
            logger.info(f"File deleted from AWS S3: {filename}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete from S3: {str(e)}")
            return False

    def _upload_to_supabase(self, file_bytes: bytes, filename: str, content_type: str) -> str:
        # Note: Supposed to make HTTP POST call to supabase storage bucket REST endpoints
        # Real implementation using requests/httpx or supabase client
        logger.info(f"File upload to Supabase storage simulated for: {filename}")
        # Placeholders for actual supabase structure
        return f"{settings.SUPABASE_URL}/storage/v1/object/public/{settings.SUPABASE_BUCKET}/{filename}"

    def _delete_from_supabase(self, file_url: str) -> bool:
        logger.info(f"File delete from Supabase storage simulated for: {file_url}")
        return True
