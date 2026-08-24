"""MinIO 原始资料与封面对象存储边界。"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
from io import BytesIO
import json
import logging
import os
import time
from typing import Callable, Literal, Mapping
from urllib.parse import urlparse

import requests
from minio import Minio


logger = logging.getLogger(__name__)

EXT_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


@dataclass(frozen=True)
class CoverResult:
    display_url: str
    source_url: str
    object_name: str | None
    status: Literal["STORED", "SOURCE_FALLBACK", "MISSING"]
    checked_at: datetime


class ObjectStorageError(RuntimeError):
    """对象存储失败的安全异常，不携带远端响应内容。"""


class ObjectStorage:
    """隔离 MinIO 与封面下载细节，向导入器暴露稳定结果。"""

    def __init__(
        self,
        minio_client: Minio | None = None,
        download: Callable = requests.get,
        environment: Mapping[str, str] | None = None,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self._environment = environment if environment is not None else os.environ
        self._download = download
        self._sleep = sleep
        self._endpoint = self._environment.get("MINIO_ENDPOINT", "localhost:9000")
        self._secure = self._environment.get("MINIO_SECURE", "false").lower() == "true"
        self._bucket = self._environment.get("MINIO_BUCKET", "anime-tracker")
        self._raw_bucket = self._environment.get("MINIO_RAW_BUCKET", "anime-tracker-private")
        if self._raw_bucket == self._bucket:
            raise ValueError("MINIO_RAW_BUCKET must differ from MINIO_BUCKET")
        self._minio = minio_client or Minio(
            self._endpoint,
            access_key=self._environment.get("MINIO_ACCESS_KEY", "minioadmin"),
            secret_key=self._environment.get("MINIO_SECRET_KEY", "minioadmin"),
            secure=self._secure,
        )

    def put_raw_subject(self, bangumi_id: int, raw: dict) -> str:
        """将原始 Bangumi 响应以私有、可复现的 gzip JSON 快照写入 MinIO。"""
        object_name = f"raw/bangumi/subjects/{bangumi_id}.json.gz"
        raw_bytes = json.dumps(
            raw, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        payload = gzip.compress(raw_bytes)

        try:
            self._retry_object_operation(
                bangumi_id,
                lambda: self._put_bytes(
                    self._raw_bucket, object_name, payload, "application/gzip"
                ),
            )
        except Exception as error:
            logger.warning(
                "raw storage failed subject_id=%d error_type=%s",
                bangumi_id,
                _normalized_error_type(error),
            )
            raise ObjectStorageError("raw storage failed") from None
        return object_name

    def put_cover(self, bangumi_id: int, source_url: str) -> CoverResult:
        """转存封面；只有写入并 stat 成功后才暴露公开 MinIO URL。"""
        checked_at = datetime.now(timezone.utc)
        if not source_url:
            return CoverResult("", source_url, None, "MISSING", checked_at)

        try:
            object_name = self._retry_object_operation(
                bangumi_id,
                lambda: self._store_cover_once(bangumi_id, source_url),
            )
        except Exception as error:
            logger.warning(
                "cover storage failed subject_id=%d error_type=%s",
                bangumi_id,
                _normalized_error_type(error),
            )
            return CoverResult(source_url, source_url, None, "SOURCE_FALLBACK", checked_at)

        return CoverResult(
            self._public_url(object_name), source_url, object_name, "STORED", checked_at
        )

    def _store_cover_once(self, bangumi_id: int, source_url: str) -> str:
        response = self._download(self._download_url(source_url), timeout=15, stream=True)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
        ext = EXT_MAP.get(content_type) or _get_ext_from_url(source_url) or "jpg"
        object_name = f"covers/{bangumi_id}.{ext}"
        self._ensure_bucket(self._bucket)
        self._minio.put_object(
            self._bucket,
            object_name,
            response.raw,
            length=-1,
            part_size=10 * 1024 * 1024,
            content_type=content_type or "image/jpeg",
        )
        self._minio.stat_object(self._bucket, object_name)
        return object_name

    def _put_bytes(self, bucket: str, object_name: str, payload: bytes, content_type: str) -> None:
        self._ensure_bucket(bucket)
        self._minio.put_object(
            bucket,
            object_name,
            BytesIO(payload),
            length=len(payload),
            content_type=content_type,
        )

    def _ensure_bucket(self, bucket: str) -> None:
        if not self._minio.bucket_exists(bucket):
            self._minio.make_bucket(bucket)

    def _retry_object_operation(self, bangumi_id: int, operation: Callable[[], object]) -> object:
        for attempt in range(3):
            try:
                return operation()
            except Exception as error:
                if attempt == 2:
                    raise
                logger.warning(
                    "object storage retry subject_id=%d attempt=%d error_type=%s",
                    bangumi_id,
                    attempt + 1,
                    _normalized_error_type(error),
                )
                self._sleep(attempt + 1)
        raise RuntimeError("unreachable")

    def _download_url(self, source_url: str) -> str:
        proxy = self._environment.get("BANGUMI_IMAGE_PROXY_URL", "").rstrip("/")
        return f"{proxy}/{source_url}" if proxy else source_url

    def _public_url(self, object_name: str) -> str:
        scheme = "https" if self._secure else "http"
        endpoint = self._endpoint.rstrip("/")
        return f"{scheme}://{endpoint}/{self._bucket}/{object_name}"


def _get_ext_from_url(url: str) -> str | None:
    path = urlparse(url).path.lower()
    for ext in (".jpg", ".jpeg", ".png", ".webp"):
        if path.endswith(ext):
            return ext.lstrip(".")
    return None


def _normalized_error_type(error: Exception) -> str:
    return type(error).__name__
