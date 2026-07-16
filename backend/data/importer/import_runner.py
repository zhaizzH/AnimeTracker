"""
导入运行器。

处理 CLI 参数解析，协调导入流程。
支持四种模式: --full / --recent / --season / --since
"""

import argparse
import logging
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Optional

from bangumi_client import BangumiClient
from db_writer import DatabaseManager
from models import Subject

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("import_runner")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """解析命令行参数。"""
    parser = argparse.ArgumentParser(
        description="AnimeTracker 数据导入器 — 从 Bangumi API 导入动漫数据",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full", action="store_true", help="全量导入所有动画条目")
    mode.add_argument("--recent", action="store_true", help="导入近期动画（默认最近2年）")
    mode.add_argument("--season", type=str, metavar="YYYY-SEASON",
                      help='导入指定季度，如 "2024-spring"')
    mode.add_argument("--since", type=str, metavar="YYYY-MM-DD",
                      help="导入指定日期之后播出的条目")
    parser.add_argument("--years-back", type=int, default=2,
                        help="--recent 模式的回溯年数（默认2年）")
    parser.add_argument("--batch-size", type=int, default=50,
                        help="每次分页请求的数量（默认50）")
    parser.add_argument("--max-pages", type=int, default=100,
                        help="最大翻页数（默认100，防止无限循环）")
    args = parser.parse_args(argv)

    # 确定 mode 字符串
    if args.full:
        args.mode = "full"
    elif args.recent:
        args.mode = "recent"
    elif args.season:
        args.mode = "season"
    elif args.since:
        args.mode = "since"

    return args


SEASON_MONTH_MAP = {
    "winter": [1, 2, 3],
    "spring": [4, 5, 6],
    "summer": [7, 8, 9],
    "autumn": [10, 11, 12],
    "fall": [10, 11, 12],
}


class ImportRunner:
    """协调导入流程的主运行器。"""

    def __init__(self, db_manager: DatabaseManager | None = None):
        self.db = db_manager or DatabaseManager()
        self.client = BangumiClient()

    async def run(self, args: argparse.Namespace) -> int:
        """按 args.mode 执行不同导入策略。返回导入的条目数。"""
        record = self.db.create_import_record(
            mode=args.mode,
            season_key=getattr(args, "season", None),
        )
        try:
            if args.mode == "full":
                count = await self.run_full_import(args)
            elif args.mode == "recent":
                count = await self.run_recent_import(years_back=args.years_back, args=args)
            elif args.mode == "season":
                count = await self.run_season_from_str(args.season, args)
            elif args.mode == "since":
                count = await self.run_since_import(args.since, args)
            else:
                raise ValueError(f"未知导入模式: {args.mode}")

            self.db.commit()
            self.db.complete_import_record(record.id, subject_count=count)
            logger.info("导入完成，共处理 %d 个条目", count)
            return count
        except Exception as e:
            self.db.rollback()
            self.db.fail_import_record(record.id, error=str(e))
            logger.exception("导入失败: %s", e)
            raise

    async def import_single_subject(self, bangumi_id: int) -> Subject | None:
        """导入单个条目的详情和剧集。"""
        data = await self.client.get_subject(bangumi_id)
        if data is None:
            logger.warning("条目 %d 不存在（404）", bangumi_id)
            return None

        air_date = None
        if data.get("date"):
            try:
                air_date = datetime.strptime(data["date"], "%Y-%m-%d").date()
            except (ValueError, TypeError):
                pass

        rating = data.get("rating") or {}
        images = data.get("images") or {}
        subject = self.db.upsert_subject(
            bangumi_id=data["id"],
            name=data.get("name", ""),
            name_cn=data.get("name_cn"),
            summary=data.get("summary"),
            type=data.get("type", 2),
            eps=data.get("eps"),
            volumes=data.get("volumes"),
            air_date=air_date,
            image=images.get("large"),
            score=Decimal(str(rating["score"])) if rating.get("score") else None,
            rank=data.get("rank"),
            collection_total=rating.get("total") or data.get("collection_total"),
            nsfw=data.get("nsfw", False),
        )

        # 导入剧集
        await self._import_episodes(subject.id, bangumi_id)

        return subject

    async def _import_episodes(self, local_subject_id: int, bangumi_id: int):
        """获取并写入条目的剧集列表。"""
        episodes_data = await self._fetch_all_episodes(bangumi_id)
        if episodes_data:
            self.db.upsert_episodes(local_subject_id, episodes_data)

    async def _fetch_all_episodes(self, subject_id: int, batch_size: int = 200) -> list[dict]:
        """分页获取某个条目的所有剧集。"""
        all_eps = []
        offset = 0
        while True:
            result = await self.client.get_episodes(
                subject_id=subject_id,
                limit=batch_size,
                offset=offset,
            )
            if result is None:
                break
            batch = result.get("data", [])
            if not batch:
                break
            all_eps.extend(batch)
            offset += len(batch)
            if offset >= result.get("total", 0):
                break
        return all_eps

    async def run_full_import(self, args) -> int:
        """全量导入：遍历所有年份和月份。"""
        logger.info("开始全量导入")
        total = 0
        current_year = datetime.now().year
        # 从 2000 年到当前年遍历
        for year in range(2000, current_year + 1):
            for month in range(1, 13):
                count = await self._browse_and_import(
                    year=year, month=month, args=args
                )
                total += count
                logger.info("全量导入 %d-%02d: %d 条目", year, month, count)
        logger.info("全量导入完成，共 %d 条目", total)
        return total

    async def run_recent_import(self, years_back: int = 2, args=None) -> int:
        """导入最近 N 年的数据。"""
        logger.info("开始导入最近 %d 年数据", years_back)
        total = 0
        current_year = datetime.now().year
        start_year = current_year - years_back + 1
        for year in range(start_year, current_year + 1):
            for month in range(1, 13):
                count = await self._browse_and_import(
                    year=year, month=month, args=args
                )
                total += count
                logger.info("近期导入 %d-%02d: %d 条目", year, month, count)
        return total

    async def run_season_import(self, year: int, month: int) -> int:
        """导入指定年月的条目（供测试和直接调用）。"""
        return await self._browse_and_import(year=year, month=month)

    async def run_season_from_str(self, season_str: str, args) -> int:
        """按季度字符串导入，如 '2024-spring'。"""
        try:
            parts = season_str.split("-")
            year = int(parts[0])
            season_name = parts[1].lower()
        except (IndexError, ValueError):
            raise ValueError(f"季度格式无效: {season_str}，应为 YYYY-season（如 2024-spring）")

        months = SEASON_MONTH_MAP.get(season_name)
        if not months:
            raise ValueError(f"未知季度: {season_name}，可选: winter/spring/summer/autumn")

        logger.info("开始导入 %s", season_str)
        total = 0
        for month in months:
            count = await self._browse_and_import(
                year=year, month=month, args=args
            )
            total += count
        logger.info("季度导入 %s 完成，共 %d 条目", season_str, total)
        return total

    async def run_since_import(self, since_date_str: str, args) -> int:
        """导入指定日期之后的数据（使用 search API 的 air_date 过滤）。"""
        logger.info("开始导入 %s 之后的数据", since_date_str)
        try:
            since_date = datetime.strptime(since_date_str, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError(f"日期格式无效: {since_date_str}，应为 YYYY-MM-DD")

        total = 0
        offset = 0
        while True:
            result = await self.client.search_subjects(
                keyword="",
                filter={"type": [2], "air_date": [f">={since_date_str}"]},
                limit=args.batch_size,
                offset=offset,
            )
            if result is None:
                break
            batch = result.get("data", [])
            if not batch:
                break
            for brief in batch:
                try:
                    await self.import_single_subject(brief["id"])
                    total += 1
                    logger.info("  [%d/%d] 导入条目 %d", total, result.get("total", 0), brief["id"])
                except Exception as e:
                    logger.error("导入条目 %d 失败: %s", brief["id"], e)
            offset += len(batch)
            if offset >= result.get("total", 0):
                break
        return total

    async def _browse_and_import(
        self,
        year: int,
        month: int,
        args=None,
    ) -> int:
        """按年月浏览条目页并逐个导入详情。"""
        batch_size = getattr(args, 'batch_size', 50) if args else 50
        max_pages = getattr(args, 'max_pages', 100) if args else 100
        count = 0
        offset = 0
        while offset // batch_size < max_pages:
            result = await self.client.browse_subjects(
                type=2,
                year=year,
                month=month,
                limit=batch_size,
                offset=offset,
            )
            if result is None:
                break
            batch = result.get("data", [])
            if not batch:
                break
            for brief in batch:
                try:
                    await self.import_single_subject(brief["id"])
                    count += 1
                except Exception as e:
                    logger.error("导入条目 %d 失败: %s", brief["id"], e)
            offset += len(batch)
            if offset >= result.get("total", 0):
                break
        return count

    async def close(self):
        await self.client.close()
        self.db.close()


def run_import():
    """主导入流程（同步入口，由 main.py 调用）。"""
    import asyncio

    async def _main():
        args = parse_args()
        runner = ImportRunner()
        try:
            count = await runner.run(args)
            logger.info("成功导入 %d 个条目", count)
        except Exception as e:
            logger.critical("导入异常: %s", e, exc_info=True)
            sys.exit(1)
        finally:
            await runner.close()

    asyncio.run(_main())
