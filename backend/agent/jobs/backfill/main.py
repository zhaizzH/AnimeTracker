"""回填 worker CLI 入口。

用法：
    uv run python -m jobs.backfill.main [--batch-size N] [--max-batches N] [--delay SECONDS]
    uv run python -m jobs.backfill.main --report
    uv run python -m jobs.backfill.main --pause
    uv run python -m jobs.backfill.main --resume
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv
from sqlalchemy.orm import Session

from app.adapters.mysql.import_records import get_engine
from jobs.backfill.repository import EntityDetailJobRepository
from jobs.backfill.worker import BackfillWorker, DEFAULT_REQUEST_DELAY

logger = logging.getLogger(__name__)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Person/Character 详情渐进回填")
    parser.add_argument("--batch-size", type=int, default=5, help="每批认领任务数")
    parser.add_argument("--max-batches", type=int, default=None, help="最大批次数（None=无限）")
    parser.add_argument("--delay", type=float, default=DEFAULT_REQUEST_DELAY, help="请求间隔秒数")
    parser.add_argument("--report", action="store_true", help="生成回填报告")
    parser.add_argument("--report-json", action="store_true", help="以 JSON 输出回填报告")
    parser.add_argument("--pause", action="store_true", help="暂停所有待处理任务")
    parser.add_argument("--resume", action="store_true", help="恢复暂停的任务")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

    from jobs.importer.client import BangumiClient

    load_dotenv()
    engine = get_engine(
        os.getenv("DB_HOST", "127.0.0.1"),
        int(os.getenv("DB_PORT", "3306")),
        os.getenv("DB_USER", "root"),
        os.getenv("DB_PASSWORD", ""),
        os.getenv("DB_NAME", "anime_tracker"),
    )
    session = Session(engine)

    try:
        repo = EntityDetailJobRepository(session)

        if args.report or args.report_json:
            report = repo.generate_report()
            if args.report_json:
                print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
                return 0
            print(f"\n=== 回填报告 ===")
            print(f"总任务数: {report.total_jobs}")
            print(f"已完成:   {report.completed} ({report.coverage_pct:.1f}%)")
            print(f"待处理:   {report.pending}")
            print(f"失败:     {report.failed}")
            print(f"放弃:     {report.abandoned}")
            print(f"stale:    {report.stale_entities}")
            if report.stale_by_kind:
                print("stale 按实体:")
                for kind, count in report.stale_by_kind.items():
                    print(f"  {kind}: {count}")
            if report.failure_reasons:
                print(f"\n失败原因 TOP:")
                for code, cnt in report.failure_reasons.items():
                    print(f"  {code}: {cnt}")
            return 0

        if args.pause:
            count = repo.pause()
            session.commit()
            print(f"已暂停 {count} 条任务")
            return 0

        if args.resume:
            count = repo.resume()
            session.commit()
            print(f"已恢复 {count} 条任务")
            return 0

        # 执行回填
        client = BangumiClient(request_delay=args.delay)
        worker = BackfillWorker(
            client=client,
            repo=repo,
            session=session,
            batch_size=args.batch_size,
            request_delay=args.delay,
            max_batches=args.max_batches,
        )
        stats = worker.run()
        print(f"\n回填完成: processed={stats['processed']}, completed={stats['completed']}, failed={stats['failed']}")
        return 0

    except KeyboardInterrupt:
        logger.info("用户中断")
        return 130
    except Exception as e:
        logger.error("回填失败: %s", e, exc_info=True)
        return 1
    finally:
        session.close()
        engine.dispose()


if __name__ == "__main__":
    sys.exit(main())
