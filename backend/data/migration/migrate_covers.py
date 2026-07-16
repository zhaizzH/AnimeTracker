"""
封面图片迁移脚本

从第三方 CDN 下载现有番剧封面，上传到 MinIO，更新 DB。
可重复执行：已指向 MinIO 的链接自动跳过。

用法:
    pip install minio requests sqlalchemy pymysql python-dotenv
    cp .env.example .env  # 编辑配置
    python migrate_covers.py
"""

import os
import logging
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv
from minio import Minio
from sqlalchemy import create_engine, text

load_dotenv()

# ---------- 配置 ----------
DB_URL = os.getenv("DB_URL", "mysql+pymysql://root:password@localhost:3306/anime_tracker")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "anime-tracker")
MINIO_PUBLIC_URL = os.getenv("MINIO_PUBLIC_URL", "http://localhost:9000")
DOWNLOAD_TIMEOUT = 15
# -------------------------

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# content-type → 扩展名映射
EXT_MAP = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/webp": "webp",
}


def get_ext_from_url(url: str) -> str | None:
    """从 URL 路径推断扩展名"""
    path = urlparse(url).path.lower()
    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        if path.endswith(ext):
            return ext.lstrip(".")
    return None


def main():
    # 连接 MinIO
    minio_client = Minio(
        MINIO_ENDPOINT,
        access_key=MINIO_ACCESS_KEY,
        secret_key=MINIO_SECRET_KEY,
        secure=False,
    )
    if not minio_client.bucket_exists(MINIO_BUCKET):
        minio_client.make_bucket(MINIO_BUCKET)
        log.info("Bucket '%s' created", MINIO_BUCKET)

    # 连接 MySQL
    engine = create_engine(DB_URL, pool_pre_ping=True)
    minio_prefix = MINIO_PUBLIC_URL.rstrip("/")

    with engine.connect() as conn:
        # 找出所有非 MinIO 的封面
        rows = conn.execute(
            text("SELECT id, image FROM subject WHERE image IS NOT NULL AND image != ''")
        ).fetchall()

    total = len(rows)
    success = 0
    skipped = 0
    failed = 0

    log.info("Found %d subjects with cover images", total)

    for row in rows:
        subject_id, image_url = row

        # 跳过已迁移的
        if image_url.startswith(minio_prefix):
            skipped += 1
            continue

        try:
            # 下载
            resp = requests.get(image_url, timeout=DOWNLOAD_TIMEOUT, stream=True)
            resp.raise_for_status()

            content_type = resp.headers.get("Content-Type", "")
            ext = EXT_MAP.get(content_type) or get_ext_from_url(image_url) or "jpg"

            object_name = f"covers/{subject_id}.{ext}"

            # 上传到 MinIO（未知长度用 -1 + part_size）
            minio_client.put_object(
                MINIO_BUCKET,
                object_name,
                resp.raw,
                length=-1,
                part_size=10 * 1024 * 1024,
                content_type=content_type or "image/jpeg",
            )

            minio_url = f"{minio_prefix}/{MINIO_BUCKET}/{object_name}"

            # 更新 DB
            with engine.begin() as conn:
                conn.execute(
                    text("UPDATE subject SET image = :url WHERE id = :id"),
                    {"url": minio_url, "id": subject_id},
                )

            success += 1
            if success % 100 == 0:
                log.info("Progress: %d/%d", success, total)

        except Exception as e:
            log.warning("Failed to migrate subject %d (%s): %s", subject_id, image_url[:60], e)
            failed += 1

    log.info("Done! total=%d, success=%d, skipped=%d, failed=%d", total, success, skipped, failed)


if __name__ == "__main__":
    main()
