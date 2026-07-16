"""导入运行器测试"""

import pytest
from datetime import date
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base, Subject, Episode
from db_writer import DatabaseManager
from import_runner import (
    parse_args,
    ImportRunner,
)


@pytest.fixture
def db_manager():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(bind=engine)
    mgr = DatabaseManager(session=session)
    yield mgr
    session.close()


class TestParseArgs:
    def test_full_mode(self):
        args = parse_args(["--full"])
        assert args.mode == "full"

    def test_recent_mode(self):
        args = parse_args(["--recent"])
        assert args.mode == "recent"

    def test_season_mode(self):
        args = parse_args(["--season", "2024-spring"])
        assert args.mode == "season"
        assert args.season == "2024-spring"

    def test_since_mode(self):
        args = parse_args(["--since", "2024-01-01"])
        assert args.mode == "since"
        assert args.since == "2024-01-01"

    def test_no_args_shows_help(self):
        with pytest.raises(SystemExit):
            parse_args([])


class TestImportRunner:
    @pytest.mark.asyncio
    async def test_import_single_subject_success(self, db_manager):
        """导入单个条目成功"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        runner.client.get_subject.return_value = {
            "id": 12,
            "name": "ちょびっツ",
            "name_cn": "人形电脑天使心",
            "summary": "A story...",
            "type": 2,
            "date": "2002-04-02",
            "eps": 27,
            "images": {"large": "https://example.com/cover.jpg"},
            "rating": {"total": 2289, "score": 7.6},
            "rank": 573,
            "collection_total": 3817,
            "nsfw": False,
        }
        runner.client.get_episodes.return_value = {
            "data": [
                {
                    "id": 1027, "type": 0, "sort": 1,
                    "name": "EP1", "name_cn": "第一集",
                    "airdate": "2002-04-03", "duration": "24m",
                    "desc": "", "status": "Air",
                }
            ],
            "total": 1,
        }

        subject = await runner.import_single_subject(12)
        assert subject is not None
        assert subject.bangumi_id == 12
        assert subject.name_cn == "人形电脑天使心"
        assert subject.import_status == 1

        # 验证剧集也被导入
        ep_count = runner.db.session.query(Episode).filter_by(subject_id=subject.id).count()
        assert ep_count == 1

    @pytest.mark.asyncio
    async def test_import_single_subject_not_found(self, db_manager):
        """条目不存在时返回 None"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        runner.client.get_subject.return_value = None

        result = await runner.import_single_subject(99999)
        assert result is None

    @pytest.mark.asyncio
    async def test_run_season_import(self, db_manager):
        """季度导入"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        # browse_subjects 返回两页数据
        runner.client.browse_subjects = AsyncMock()
        runner.client.browse_subjects.side_effect = [
            {
                "data": [
                    {"id": 1, "name": "Anime A", "name_cn": "", "type": 2, "date": "2024-01-01", "eps": 12},
                    {"id": 2, "name": "Anime B", "name_cn": "", "type": 2, "date": "2024-01-02", "eps": 24},
                ],
                "total": 2,
            },
            {"data": [], "total": 0},  # 结束翻页
        ]
        # get_subject 返回简化为已有数据
        runner.client.get_subject.side_effect = [
            {"id": 1, "name": "Anime A", "name_cn": "", "type": 2, "date": "2024-01-01", "eps": 12, "rating": {}, "images": {}},
            {"id": 2, "name": "Anime B", "name_cn": "", "type": 2, "date": "2024-01-02", "eps": 24, "rating": {}, "images": {}},
        ]
        runner.client.get_episodes.return_value = {"data": [], "total": 0}

        result = await runner.run_season_import(year=2024, month=1)
        assert result > 0

    @pytest.mark.asyncio
    async def test_run_recent_import(self, db_manager):
        """最近数据导入"""
        runner = ImportRunner(db_manager=db_manager)
        runner.client = AsyncMock()
        runner.client.browse_subjects.return_value = {"data": [], "total": 0}

        result = await runner.run_recent_import(years_back=1)
        assert result == 0
