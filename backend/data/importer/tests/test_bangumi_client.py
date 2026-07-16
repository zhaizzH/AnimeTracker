"""Bangumi API 客户端测试"""

from unittest.mock import MagicMock

import pytest
from bangumi_client import BangumiClient


@pytest.fixture
def mock_subject_response():
    return {
        "id": 12,
        "name": "ちょびっツ",
        "name_cn": "人形电脑天使心",
        "summary": "在不久的将来...",
        "type": 2,
        "date": "2002-04-02",
        "eps": 27,
        "images": {
            "large": "https://lain.bgm.tv/pic/cover/l/c2/0a/12_24O6L.jpg",
            "common": "https://lain.bgm.tv/pic/cover/c/c2/0a/12_24O6L.jpg",
        },
        "rating": {"total": 2289, "score": 7.6},
        "rank": 573,
        "collection_total": 3817,
        "nsfw": False,
    }


@pytest.fixture
def client():
    return BangumiClient(base_url="https://api.bgm.tv", request_interval=0.01)


def _mock_response(data, status_code=200):
    """Create a mock httpx response with sync .json() method.

    mocker.patch on async methods may create AsyncMock attributes,
    making .json() return a coroutine instead of the dict.
    Using MagicMock explicitly for .json avoids this issue.
    """
    m = MagicMock()
    m.status_code = status_code
    m.json = MagicMock(return_value=data)
    return m


@pytest.mark.asyncio
async def test_get_subject_success(client, mock_subject_response, mocker):
    """正常获取条目详情"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value = _mock_response(mock_subject_response)

    result = await client.get_subject(12)
    assert result["id"] == 12
    assert result["name_cn"] == "人形电脑天使心"
    mock_get.assert_called_once_with("https://api.bgm.tv/v0/subjects/12", params=None)


@pytest.mark.asyncio
async def test_get_subject_not_found(client, mocker):
    """条目不存在时返回 None"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value = _mock_response(None, status_code=404)

    result = await client.get_subject(999999)
    assert result is None


@pytest.mark.asyncio
async def test_browse_subjects(client, mocker):
    """浏览条目分页"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_response_data = {
        "data": [
            {"id": 1, "name": "Anime A", "name_cn": "", "type": 2, "date": "2024-01-01"},
            {"id": 2, "name": "Anime B", "name_cn": "", "type": 2, "date": "2024-01-02"},
        ],
        "total": 2,
        "limit": 50,
        "offset": 0,
    }
    mock_get.return_value = _mock_response(mock_response_data)

    result = await client.browse_subjects(type=2, year=2024, month=1)
    assert len(result["data"]) == 2
    # GET 参数应该在 params 中
    assert mock_get.call_args[1].get("params", {}).get("type") == 2


@pytest.mark.asyncio
async def test_search_subjects(client, mocker):
    """搜索条目"""
    mock_post = mocker.patch("httpx.AsyncClient.post")
    mock_post.return_value = _mock_response({
        "data": [{"id": 1, "name": "Result"}],
        "total": 1,
    })

    result = await client.search_subjects(keyword="test", limit=10)
    assert result["total"] == 1
    body = mock_post.call_args[1]["json"]
    assert body["keyword"] == "test"


@pytest.mark.asyncio
async def test_get_episodes(client, mocker):
    """获取剧集列表"""
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value = _mock_response({
        "data": [
            {
                "id": 1027,
                "type": 0,
                "sort": 1,
                "name": "ちぃ 目覚める",
                "name_cn": "叽，觉醒了",
                "airdate": "2002-04-03",
                "duration": "24m",
                "desc": "",
                "status": "Air",
            }
        ],
        "total": 1,
    })

    result = await client.get_episodes(subject_id=12)
    assert len(result["data"]) == 1
    assert result["data"][0]["name_cn"] == "叽，觉醒了"


@pytest.mark.asyncio
async def test_rate_limiting(client, mocker):
    """请求间隔控制"""
    import asyncio
    mock_get = mocker.patch("httpx.AsyncClient.get")
    mock_get.return_value = _mock_response({"data": [], "total": 0})

    start = asyncio.get_event_loop().time()
    await client.get_episodes(subject_id=1)
    await client.get_episodes(subject_id=2)
    elapsed = asyncio.get_event_loop().time() - start
    # 测试用 0.01s interval — 验证有延迟即可
    assert elapsed >= 0.009
