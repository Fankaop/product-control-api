import os
from datetime import timedelta

from minio import Minio
from minio.error import S3Error

from core.config import settings

BUCKETS = ["reports", "exports", "imports"]

CONTENT_TYPES = {
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".csv": "text/csv",
    ".pdf": "application/pdf",
    ".json": "application/json",
}


class MinIOService:
    def __init__(self) -> None:
        self.client = Minio(
            endpoint=settings.minio_endpoint,
            access_key=settings.minio_access_key,
            secret_key=settings.minio_secret_key,
            secure=settings.minio_secure,
        )

    def ensure_buckets(self) -> None:
        for bucket in BUCKETS:
            if not self.client.bucket_exists(bucket):
                self.client.make_bucket(bucket)

    def upload_file(
        self,
        bucket: str,
        file_path: str,
        object_name: str | None = None,
        expires_days: int = 7,
    ) -> str:
        if object_name is None:
            object_name = os.path.basename(file_path)

        ext = os.path.splitext(file_path)[1].lower()
        content_type = CONTENT_TYPES.get(ext, "application/octet-stream")

        self.client.fput_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
            content_type=content_type,
        )

        url = self.client.presigned_get_object(
            bucket_name=bucket,
            object_name=object_name,
            expires=timedelta(days=expires_days),
        )
        return url

    def download_file(self, bucket: str, object_name: str, file_path: str) -> None:
        self.client.fget_object(
            bucket_name=bucket,
            object_name=object_name,
            file_path=file_path,
        )

    def delete_file(self, bucket: str, object_name: str) -> None:
        self.client.remove_object(bucket, object_name)

    def list_files(self, bucket: str, prefix: str | None = None) -> list[str]:
        objects = self.client.list_objects(bucket_name=bucket, prefix=prefix, recursive=True)
        return [obj.object_name for obj in objects if obj.object_name is not None]

    def get_file_size(self, bucket: str, object_name: str) -> int:
        stat = self.client.stat_object(bucket, object_name)
        return stat.size or 0


minio_service = MinIOService()
