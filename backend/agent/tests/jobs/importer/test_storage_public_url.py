"""封面公开 URL 与质量检查的对象名反解必须使用同一契约。"""

from __future__ import annotations

import pytest

from jobs.importer.storage import ObjectStorage
from jobs.importer.quality import canonical_cover_object_path


class _FakeMinio:
    """只提供 ObjectStorage 构造所需的形状，不连接 MinIO。"""

    def bucket_exists(self, bucket):
        return True


def _storage(**environment):
    return ObjectStorage(minio_client=_FakeMinio(), environment=environment)


class _MinioView:
    """模拟 quality.py 读取的存储句柄属性。"""

    def __init__(self, endpoint="127.0.0.1:9000", bucket="anime-tracker", public_base_url=""):
        self.endpoint = endpoint
        self._bucket = bucket
        self.public_base_url = public_base_url


def test_public_url_uses_public_base_url_without_bucket():
    """配置前缀时公开 URL 不重复拼桶名，前缀已指向桶根。"""
    storage = _storage(MINIO_ENDPOINT="127.0.0.1:9000", MINIO_PUBLIC_BASE_URL="http://host/media/")
    assert storage._public_url("covers/244.jpg") == "http://host/media/covers/244.jpg"


def test_public_url_supports_root_relative_prefix():
    """推荐形态：根相对路径，换域名/IP 不需改数据。"""
    storage = _storage(MINIO_ENDPOINT="127.0.0.1:9000", MINIO_PUBLIC_BASE_URL="/media")
    assert storage._public_url("covers/244.jpg") == "/media/covers/244.jpg"


def test_public_url_falls_back_to_endpoint_when_unset():
    """未配置前缀时保持旧行为，避免未升级部署直接失效。"""
    storage = _storage(MINIO_ENDPOINT="127.0.0.1:9000")
    assert storage._public_url("covers/244.jpg") == "http://127.0.0.1:9000/anime-tracker/covers/244.jpg"


def test_generated_public_url_round_trips_through_quality():
    """生成 URL 经质量检查反解必须还原出对象名，否则封面会被判为未引用。"""
    storage = _storage(MINIO_ENDPOINT="127.0.0.1:9000", MINIO_PUBLIC_BASE_URL="http://host/media")
    url = storage._public_url("covers/244.jpg")
    view = _MinioView(public_base_url=storage.public_base_url)
    assert canonical_cover_object_path(url, view) == "covers/244.jpg"


def test_relative_public_url_round_trips_through_quality():
    """根相对路径无 scheme/netloc，质量检查必须优先按前缀匹配，否则封面会被删。"""
    storage = _storage(MINIO_ENDPOINT="127.0.0.1:9000", MINIO_PUBLIC_BASE_URL="/media")
    url = storage._public_url("covers/244.jpg")
    assert url == "/media/covers/244.jpg"
    view = _MinioView(public_base_url=storage.public_base_url)
    assert canonical_cover_object_path(url, view) == "covers/244.jpg"


def test_quality_still_reads_legacy_endpoint_urls():
    """升级前的存量数据（endpoint 形态）仍须能被识别；此时前缀未配置。"""
    url = "http://127.0.0.1:9000/anime-tracker/covers/244.jpg"
    assert canonical_cover_object_path(url, _MinioView()) == "covers/244.jpg"


def test_quality_reads_legacy_urls_with_relative_prefix_configured():
    """迁移过渡期两种形态并存：前缀已配置，存量绝对 URL 也须照常识别。"""
    url = "http://127.0.0.1:9000/anime-tracker/covers/244.jpg"
    assert canonical_cover_object_path(url, _MinioView(public_base_url="/media")) == "covers/244.jpg"


@pytest.mark.parametrize(
    "image",
    [
        None,
        "",
        "/media/covers/244.jpg",  # 相对路径但未配置前缀 → 无法确定归属
        "http://host/media/avatars/1.png",  # 非 covers 目录
        "http://host/media/covers/../../secret",
        "http://evil.test/media/covers/244.jpg",  # 前缀不匹配
    ],
)
def test_quality_rejects_non_cover_or_foreign_urls(image):
    assert canonical_cover_object_path(image, _MinioView(public_base_url="http://host/media")) is None
